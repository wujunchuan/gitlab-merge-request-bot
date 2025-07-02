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
