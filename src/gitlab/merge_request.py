from dataclasses import dataclass

import requests
from auth import base_url, headers
from util import filter_files_from_diff


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


def parse_merge_request_url(url: str):
    """
    输入 MR 地址，提取 project_id 与 mr_number
    """
    # Split URL by '/-/' to get the project path and MR number
    parts = url.split("/-/")
    if len(parts) != 2 or not parts[1].startswith("merge_requests/"):
        raise ValueError("Invalid merge request URL format")

    # Get project path (remove base URL)
    project_id = (
        parts[0].replace("https://git.intra.gaoding.com/", "").replace("/", "%2F")
    )

    # Get MR number
    mr_number = parts[1].replace("merge_requests/", "")

    return project_id, mr_number


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


if __name__ == "__main__":
    project_id, mr_number = parse_merge_request_url(
        # "https://git.intra.gaoding.com/operations-market/market-views/-/merge_requests/168"
        "https://git.intra.gaoding.com/npm/gdicon-cli/-/merge_requests/7"
    )
    # print(get_merge_request_diff(project_id, mr_number))
    print(get_merge_request_raw_diff(project_id, mr_number))
    # print(get_merge_request_commits(project_id, mr_number))
