from dataclasses import dataclass

import requests

from gitlab.auth import base_url, headers
from gitlab.util import filter_files_from_diff, parse_merge_request_url


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


def get_merge_request_commits(project_id: str, mr_number: str) -> list[Commit]:
    """
    获取 MR 提交记录

    https://docs.gitlab.com/api/merge_requests/#get-single-merge-request-commits
    """
    url = f"{base_url}/projects/{project_id}/merge_requests/{mr_number}/commits"
    response = requests.get(url, headers=headers)
    return response.json()


# todo: GET /projects/:id/repository/compare
def get_compare_diff_from_commits(
    project_id: str, from_commit: str, to_commit: str
) -> str:
    """
    获取两个 commit 之间的差异

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


if __name__ == "__main__":
    project_id, mr_number = parse_merge_request_url(
        # "https://git.intra.gaoding.com/operations-market/market-views/-/merge_requests/168"
        "https://git.intra.gaoding.com/npm/gdicon-cli/-/merge_requests/7"
    )
    print(get_merge_request_diff(project_id, mr_number))
    # print(get_merge_request_raw_diff(project_id, mr_number))
    # print(get_merge_request_commits(project_id, mr_number))
