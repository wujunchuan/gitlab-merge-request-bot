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


def get_merge_request_commits(project_id: str, mr_number: str) -> list[Commit]:
    """
    Retrieve the list of commits associated with a specific merge request.

    Parameters:
        project_id (str): The unique identifier of the GitLab project.
        mr_number (str): The merge request number.

    Returns:
        list: A list of commit data in JSON format for the specified merge request.
    """
    url = f"{base_url}/projects/{project_id}/merge_requests/{mr_number}/commits"
    response = requests.get(url, headers=headers)
    return response.json()


def get_compare_diff_from_commits(
    project_id: str, from_commit: str, to_commit: str
) -> str:
    """
    Retrieve the diff between two commits in a GitLab project.

    Parameters:
        project_id (str): The unique identifier of the GitLab project.
        from_commit (str): The commit SHA or reference to compare from.
        to_commit (str): The commit SHA or reference to compare to.

    Returns:
        str: The JSON response containing the diff information between the specified commits.
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
