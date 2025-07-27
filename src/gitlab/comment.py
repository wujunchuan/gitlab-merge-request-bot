import requests

from gitlab.auth import base_url, headers
from gitlab.merge_request import parse_merge_request_url


def create_comment(project_id: str, mr_number: str, content: str):
    """
    ref: https://docs.gitlab.com/api/notes/#create-new-merge-request-note

    创建评论，在 Merge Request 中添加评论

    Args:
        content: The content of the comment
        project_id: The ID of the project
        mr_number: The number of the merge request
    """
    # POST /projects/:id/merge_requests/:merge_request_iid/notes
    url = f"{base_url}/projects/{project_id}/merge_requests/{mr_number}/notes"
    response = requests.post(url, headers=headers, json={"body": content})
    response.raise_for_status()
    return response.json()


def get_comment(project_id: str, mr_number: str, sort="desc", order_by="created_at"):
    """
    ref: https://docs.gitlab.com/api/notes/#list-merge-request-notes

    获取 Merge Request 的评论

    Args:
        project_id: The ID of the project
        mr_number: The number of the merge request
        sort: Return merge request notes sorted in asc or desc order. Default is desc
        order_by: Return merge request notes ordered by created_at or updated_at fields. Default is created_at
    """
    url = f"{base_url}/projects/{project_id}/merge_requests/{mr_number}/notes"
    response = requests.get(
        url, headers=headers, params={"sort": sort, "order_by": order_by}
    )
    response.raise_for_status()
    return response.json()


def get_merge_request_versions(project_id: str, mr_number: str):
    """
    获取 Merge Request 的版本信息，用于获取创建行级评论所需的 SHA 值

    Args:
        project_id: The ID of the project
        mr_number: The number of the merge request

    Returns:
        List of version objects containing SHA information
    """
    url = f"{base_url}/projects/{project_id}/merge_requests/{mr_number}/versions"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def create_discussion(project_id: str, mr_number: str, content: str):
    """
    创建讨论（普通评论，不是行级评论）

    Args:
        project_id: The ID of the project
        mr_number: The number of the merge request
        content: The content of the discussion
    """
    url = f"{base_url}/projects/{project_id}/merge_requests/{mr_number}/discussions"
    response = requests.post(url, headers=headers, json={"body": content})
    response.raise_for_status()
    return response.json()


def create_diff_discussion(
    project_id: str,
    mr_number: str,
    content: str,
    file_path: str,
    line_number: int,
    line_type: str = "new",
    base_sha: str = None,
    head_sha: str = None,
    start_sha: str = None,
):
    """
    创建行级讨论（diff note）

    Args:
        project_id: The ID of the project
        mr_number: The number of the merge request
        content: The content of the discussion
        file_path: The file path
        line_number: The line number
        line_type: "new" for added lines, "old" for removed lines, "both" for unchanged lines
        base_sha: Base commit SHA (if not provided, will be fetched)
        head_sha: Head commit SHA (if not provided, will be fetched)
        start_sha: Start commit SHA (if not provided, will be fetched)
    """
    # 如果没有提供 SHA 值，则获取最新的版本信息
    if not all([base_sha, head_sha, start_sha]):
        versions = get_merge_request_versions(project_id, mr_number)
        if versions:
            latest_version = versions[0]  # 最新版本在第一个
            base_sha = base_sha or latest_version.get("base_commit_sha")
            head_sha = head_sha or latest_version.get("head_commit_sha")
            start_sha = start_sha or latest_version.get("start_commit_sha")

    url = f"{base_url}/projects/{project_id}/merge_requests/{mr_number}/discussions"

    # 构建 position 参数
    position = {
        "position_type": "text",
        "base_sha": base_sha,
        "head_sha": head_sha,
        "start_sha": start_sha,
        "old_path": file_path,
        "new_path": file_path,
    }

    # 根据行类型设置行号
    if line_type == "new":
        position["new_line"] = line_number
    elif line_type == "old":
        position["old_line"] = line_number
    else:  # both (unchanged line)
        position["new_line"] = line_number
        position["old_line"] = line_number

    data = {"body": content, "position": position}

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def get_discussions(project_id: str, mr_number: str):
    """
    获取 Merge Request 的所有讨论

    Args:
        project_id: The ID of the project
        mr_number: The number of the merge request
    """
    url = f"{base_url}/projects/{project_id}/merge_requests/{mr_number}/discussions"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


# todo 为 Merge Request 创建 Thread 讨论
def create_thread(project_id: str, mr_number: str, content: str):
    """
    ref: https://docs.gitlab.com/api/discussions/#create-a-new-thread-in-the-merge-request-diff

    Create new merge request note
    """
    pass


if __name__ == "__main__":
    project_id, mr_number = parse_merge_request_url(
        "https://git.intra.gaoding.com/gdesign/meta/-/merge_requests/11124"
    )
    result = get_comment(project_id, mr_number)
    print(result[4]["body"])
