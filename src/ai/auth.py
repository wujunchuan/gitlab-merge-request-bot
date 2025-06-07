import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY 未设置，请配置 OPENAI_API_KEY 环境变量")

client = OpenAI(
    api_key=api_key,
    base_url=os.getenv("OPENAI_BASE_URL"),
)
