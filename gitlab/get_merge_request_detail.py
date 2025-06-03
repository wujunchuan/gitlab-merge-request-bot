from dotenv import load_dotenv
import os
import requests

load_dotenv()

base_url = (
    os.getenv("GITLAB_BASE_URL")
    or os.getenv("GAODING_GITLAB_BASE_URL")
    or "https://git.intra.gaoding.com/api/v4"
)

token = os.getenv("GITLAB_PRIVATE_TOKEN")
if not token:
    raise RuntimeError(
        "GitLab PRIVATE-TOKEN 未设置，请配置 GITLAB_PRIVATE_TOKEN 或 GAODING_GITLAB_PRIVATE_TOKEN 环境变量"
    )
headers = {"PRIVATE-TOKEN": token}


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


def get_merge_request_diff(project_id: str, mr_number: str, with_stats=True):
    """获取 MR 差异"""
    url = f"{base_url}/projects/{project_id}/merge_requests/{mr_number}/raw_diffs"
    params = {
        "with_stats": with_stats,  # 包含统计信息
        "per_page": 100,  # 每页显示的数量
    }
    response = requests.get(url, headers=headers, params=params)
    raw_content = response.content.decode("utf-8")
    return raw_content


if __name__ == "__main__":
    project_id, mr_number = parse_merge_request_url(
        "https://git.intra.gaoding.com/operations-market/market-views/-/merge_requests/168"
    )
    print(get_merge_request_diff(project_id, mr_number))
