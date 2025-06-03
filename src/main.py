from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()


api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY 未设置，请配置 OPENAI_API_KEY 环境变量")

client = OpenAI(
    api_key=api_key,
    base_url=os.getenv("OPENAI_BASE_URL"),
)


def main():
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Say this is a test",
            }
        ],
        model="gpt-4o-mini",
    )
    print(chat_completion.choices[0].message.content)


if __name__ == "__main__":
    main()
