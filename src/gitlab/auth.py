import os

from dotenv import load_dotenv

load_dotenv()

base_url = os.getenv("GITLAB_BASE_URL") or "https://git.intra.gaoding.com/api/v4"

token = os.getenv("GITLAB_PRIVATE_TOKEN")

if not token:
    raise RuntimeError(
        "GitLab PRIVATE-TOKEN 未设置，请配置 GITLAB_PRIVATE_TOKEN 环境变量"
    )

headers = {"PRIVATE-TOKEN": token}
