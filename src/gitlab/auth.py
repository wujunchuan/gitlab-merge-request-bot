import os

from dotenv import load_dotenv

load_dotenv()

base_url = f"{os.getenv('GITLAB_BASE_URL')}/api/v4"

if not base_url:
    raise RuntimeError("GITLAB_BASE_URL 未设置，请配置 GITLAB_BASE_URL 环境变量")

token = os.getenv("GITLAB_PRIVATE_TOKEN")

if not token:
    raise RuntimeError(
        "GitLab PRIVATE-TOKEN 未设置，请配置 GITLAB_PRIVATE_TOKEN 环境变量"
    )

headers = {"PRIVATE-TOKEN": token}
