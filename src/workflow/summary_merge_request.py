import asyncio

from pocketflow import AsyncFlow, AsyncNode

from ai.auth import client, get_openai_model
from ai.get_prompt import prompt_manager
from gitlab.comment import create_comment
from gitlab.merge_request import get_merge_request_commits, get_merge_request_raw_diff
from gitlab.util import parse_merge_request_url
from utils.logger import get_logger

# 创建专用的日志记录器
logger = get_logger(__name__, log_file="summary_merge_request.log")

summary_merge_request_prompt = prompt_manager.load_prompt("summary_merge_request.md")


def call_llm(content: str):
    """调用 LLM 生成摘要"""
    # 记录发送给 LLM 的 prompt 内容
    logger.info("Sending prompt to LLM")
    logger.debug(f"System prompt: {summary_merge_request_prompt}")
    logger.info(f"User content: {content}")

    chat_completion = client.chat.completions.create(
        model=get_openai_model(),
        temperature=1.0,
        messages=[
            {"role": "system", "content": summary_merge_request_prompt},
            {"role": "user", "content": content},
        ],
    )

    result = chat_completion.choices[0].message.content
    logger.info("Received response from LLM")
    logger.debug(f"LLM response length: {len(result)} characters")

    return result


class SummaryMergeRequest(AsyncNode):
    """
    总结 Merge Request 的变更内容，生成摘要并且发送评论到对应的 Merge Request
    """

    async def prep_async(self, shared):
        """准备阶段：解析 Merge Request 的变更内容"""
        url = shared.get("url")
        if not url:
            raise ValueError("url is required")

        # 获取 project_id 与 merge_number
        project_id, merge_number = parse_merge_request_url(url)
        shared["project_id"] = project_id
        shared["merge_number"] = merge_number

        # 获取 raw diff
        raw_diff = get_merge_request_raw_diff(project_id, merge_number)
        shared["raw_diff"] = raw_diff

        # 获取 commits
        commits = get_merge_request_commits(project_id, merge_number)
        shared["commits"] = "\n".join(
            [f"{commit['short_id']}\n{commit['message']}\n" for commit in commits]
        )

        return shared

    async def exec_async(self, prep_res):
        content = f"""## 原始 diff\n\n{prep_res.get("raw_diff")}\n\n## 详细 commit 信息\n\n{prep_res.get("commits")}"""

        logger.info("Starting LLM execution for merge request summary")
        exec_res = call_llm(content)

        # 记录执行结果
        logger.info("LLM execution completed successfully")
        logger.info(f"Generated summary: {exec_res}")

        return exec_res

    async def post_async(self, shared, prep_res, exec_res):
        logger.info(
            f"Creating comment for merge request {shared['merge_number']} in project {shared['project_id']}"
        )
        create_comment(shared["project_id"], shared["merge_number"], exec_res)
        logger.info("Comment created successfully")
        return "Done"


if __name__ == "__main__":
    flow = AsyncFlow(start=SummaryMergeRequest())

    async def main():
        shared = {
            "url": "https://git.intra.gaoding.com/chuanpu/gitlab-merge-request-bot/-/merge_requests/1"
        }
        await flow.run_async(shared)

    asyncio.run(main())
