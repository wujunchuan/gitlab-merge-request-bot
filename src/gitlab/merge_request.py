import json
import os
from dataclasses import dataclass

import requests

from gitlab.auth import base_url, headers
from gitlab.util import (
    filter_files_from_diff,
    parse_merge_request_url,
    parse_project_name,
)


@dataclass
class Commit:
    id: str
    short_id: str
    created_at: str
    parent_ids: list[str]
    title: str
    message: str
    author_name: str
    author_email: str
    authored_date: str
    committer_name: str
    committer_email: str
    committed_date: str
    trailers: dict
    extended_trailers: dict
    web_url: str


def get_merge_request_detail(project_id: str, mr_number: str):
    """获取 MR 详情"""
    url = f"{base_url}/projects/{project_id}/merge_requests/{mr_number}"
    response = requests.get(url, headers=headers)
    return response.json()


def get_merge_request_raw_diff(
    project_id: str,
    mr_number: str,
    files_to_filter: list[str] = ["pnpm-lock.yaml", "package-lock.json"],
):
    """获取 MR 原始差异"""
    url = f"{base_url}/projects/{project_id}/merge_requests/{mr_number}/raw_diffs"
    response = requests.get(url, headers=headers)
    original_raw_content = response.content.decode("utf-8")

    # 过滤掉 pnpm-lock.yaml 文件
    raw_content = filter_files_from_diff(original_raw_content, files_to_filter)

    return raw_content


def get_merge_request_diff(project_id: str, mr_number: str):
    """
    获取 MR 差异
    @link https://docs.gitlab.com/api/merge_requests/#list-merge-request-diffs
    """
    url = f"{base_url}/projects/{project_id}/merge_requests/{mr_number}/diffs"
    params = {
        # "per_page": 999,  # 每页显示的数量
    }
    response = requests.get(url, headers=headers, params=params)

    return response.json()


def get_merge_request_commits(
    project_id: str,
    mr_number: str,
    start_commit_hash: str = None,
) -> list[Commit]:
    """
    获取 MR 提交记录

    Args:
        project_id: 项目 ID
        mr_number: MR 编号
        start_commit_hash: 可选，起始 commit hash (包含)，返回从该 commit 开始到最新的所有 commits

    Returns:
        list[Commit]: 如果指定了 start_commit_hash，则返回从该 commit 开始到最新的所有 commits；
                     否则返回所有 commits

    https://docs.gitlab.com/api/merge_requests/#get-single-merge-request-commits
    """
    url = f"{base_url}/projects/{project_id}/merge_requests/{mr_number}/commits"
    response = requests.get(url, headers=headers)
    all_commits = response.json()

    # 如果没有指定起始 commit，返回所有 commits
    if not start_commit_hash:
        return all_commits

    # 查找起始 commit 的索引
    start_index = None

    for i, commit in enumerate(all_commits):
        # 匹配 commit hash (支持完整 hash 和 short hash)
        if (
            commit["id"] == start_commit_hash
            or commit["short_id"] == start_commit_hash
            or commit["id"].startswith(start_commit_hash)
        ):
            start_index = i
            break

    # 如果找不到指定的 commit，返回所有 commits
    if start_index is None:
        return all_commits

    # 返回从指定 commit 开始到最新的所有 commits（包含起始 commit）
    # GitLab API 返回的 commits 是倒序的，最新的在前面
    # 所以从索引 0 到 start_index（包含）就是从最新到起始 commit
    return all_commits[0 : start_index + 1]


def get_compare_diff_from_commits(
    project_id: str, from_commit: str, to_commit: str
) -> str:
    """
    获取两个 commit 之间的差异

    docs: https://docs.gitlab.com/api/repositories/#compare-branches-tags-or-commits

    Args:
        project_id (str): 项目 ID
        from_commit (str): 起始 commit
        to_commit (str): 结束 commit

    Returns:
        str: 差异内容
    """
    url = f"{base_url}/projects/{project_id}/repository/compare"
    params = {
        "from": from_commit,
        "to": to_commit,
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()


def create_merge_request(
    project_id: str,
    source_branch: str,
    target_branch: str,
    title: str,
    description: str = "",
    assignee_id: int = None,
    remove_source_branch: bool = True,
    draft: bool = True,
) -> dict:
    """
    创建 Merge Request

    Args:
        project_id: 项目 ID
        source_branch: 源分支
        target_branch: 目标分支
        title: MR 标题
        description: MR 描述
        assignee_id: 指派人 ID（可选）
        remove_source_branch: 合并后是否删除源分支
        draft: 是否创建为草稿

    Returns:
        dict: 创建的 MR 信息

    Docs: https://docs.gitlab.com/ee/api/merge_requests.html#create-mr
    """
    url = f"{base_url}/projects/{project_id}/merge_requests"

    data = {
        "source_branch": source_branch,
        "target_branch": target_branch,
        "title": title,
        "description": description,
        "remove_source_branch": remove_source_branch,
    }

    # 添加草稿前缀
    if draft and not title.startswith("Draft:"):
        data["title"] = f"Draft: {title}"

    if assignee_id:
        data["assignee_id"] = assignee_id

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def get_user_by_username(username: str) -> dict:
    """
    根据用户名获取用户信息

    Args:
        username: GitLab 用户名

    Returns:
        dict: 用户信息，包含 id 等字段
    """
    url = f"{base_url}/users"
    params = {"username": username}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    users = response.json()
    if not users:
        raise ValueError(f"未找到用户名为 '{username}' 的用户")

    return users[0]  # 返回第一个匹配的用户


def get_project_by_path(project_path: str) -> dict:
    """
    根据项目路径获取项目信息

    Args:
        project_path: 项目路径，如 'username/project-name'

    Returns:
        dict: 项目信息，包含 id 等字段
    """
    # URL encode 项目路径
    encoded_path = parse_project_name(project_path)
    url = f"{base_url}/projects/{encoded_path}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_merge_request_by_source_branch(project_id: str, source_branch: str) -> dict:
    """
    根据源分支获取对应的 Merge Request

    Args:
        project_id: 项目 ID
        source_branch: 源分支名

    Returns:
        dict: MR 信息，如果找不到则返回 None

    Raises:
        ValueError: 如果找不到对应分支的 MR
    """
    url = f"{base_url}/projects/{project_id}/merge_requests"
    params = {
        "source_branch": source_branch,
        "state": "opened",  # 只查找打开状态的 MR
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    mrs = response.json()
    if not mrs:
        raise ValueError(f"未找到源分支为 '{source_branch}' 的 MR")

    # 返回第一个匹配的 MR
    return mrs[0]


if __name__ == "__main__":
    project_id, mr_number = parse_merge_request_url(
        # "https://git.intra.gaoding.com/operations-market/market-views/-/merge_requests/168"
        "https://gitlab.com/wujunchuan/gitlab-merge-request-bot/-/merge_requests/2"
    )

    # print(get_merge_request_diff(project_id, mr_number))
    # print(get_merge_request_raw_diff(project_id, mr_number))
    # print(get_merge_request_commits(project_id, mr_number))

    json_res = get_compare_diff_from_commits(
        parse_project_name("wujunchuan/gitlab-merge-request-bot"), "6f11909", "ddcaeb5"
    )

    # print(json_res)

    skip_files = os.getenv("SKIP_FILES")
    if skip_files:
        skip_files = json.loads(skip_files)

    print('os.getenv("GITLAB_BASE_URL")', skip_files)
    print(len(skip_files))
