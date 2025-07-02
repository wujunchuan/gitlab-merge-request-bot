import asyncio

from pocketflow import AsyncFlow, AsyncNode

from ai.auth import client, get_openai_model
from ai.get_prompt import prompt_manager
from gitlab.comment import create_comment, get_comment
from gitlab.merge_request import (
    get_compare_diff_from_commits,
    get_merge_request_commits,
    get_merge_request_raw_diff,
)
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

        comments = get_comment(project_id, merge_number)
        # 遍历 comments, 找出 start_commit_hash 与 end_commit_hash
        start_commit_hash = None
        end_commit_hash = None
        for comment in comments:
            if start_commit_hash and end_commit_hash:
                break
            if "<!-- start-commit-hash" in comment["body"]:
                start_commit_hash = (
                    comment["body"]
                    .split("<!-- start-commit-hash: ")[1]
                    .split(" -->")[0]
                )
            if "<!-- end-commit-hash" in comment["body"]:
                end_commit_hash = (
                    comment["body"].split("<!-- end-commit-hash: ")[1].split(" -->")[0]
                )

        # 如果有 start_commit_hash 与 end_commit_hash, 则获取区间 diff 和从 start_commit_hash 开始的 commits
        if start_commit_hash and end_commit_hash:
            # 获取从 start_commit_hash 后的所有 commits
            commits = get_merge_request_commits(
                project_id, merge_number, end_commit_hash
            )
            start_commit_hash = commits[-1]["short_id"]
            end_commit_hash = commits[0]["short_id"]

            commits = commits[
                :-1
            ]  # end_commit_hash 是最后一个 commit，已经进行总结过了所以需要移掉
            shared["commits"] = "\n".join(
                [f"{commit['short_id']}\n{commit['message']}\n" for commit in commits]
            )

            diff = get_compare_diff_from_commits(
                project_id, start_commit_hash, end_commit_hash
            )
            shared["raw_diff"] = diff
            shared["start_commit_hash"] = start_commit_hash
            shared["end_commit_hash"] = end_commit_hash
            return shared
        else:
            # 如果没有 start_commit_hash 与 end_commit_hash, 则获取 raw diff 并解析出 start_commit_hash 与 end_commit_hash
            raw_diff = get_merge_request_raw_diff(project_id, merge_number)
            shared["raw_diff"] = raw_diff
            # 获取所有 commits
            commits = get_merge_request_commits(project_id, merge_number)
            start_commit_hash = commits[-1]["short_id"]
            end_commit_hash = commits[0]["short_id"]
            shared["start_commit_hash"] = start_commit_hash
            shared["end_commit_hash"] = end_commit_hash
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
        create_comment(
            shared["project_id"],
            shared["merge_number"],
            f"""
<!-- gitlab-merge-request-bot meta info -->
<!-- Don't Remove This Comment -->
<!-- start-commit-hash: {shared["start_commit_hash"]} -->
<!-- end-commit-hash: {shared["end_commit_hash"]} -->
<!-- gitlab-merge-request-bot meta info -->

{exec_res}

        """,
        )
        logger.info("Comment created successfully")
        return "Done"


if __name__ == "__main__":
    flow = AsyncFlow(start=SummaryMergeRequest())

    async def main():
        shared = {
            "url": "https://git.intra.gaoding.com/chuanpu/gitlab-merge-request-bot/-/merge_requests/2"
        }
        await flow.run_async(shared)

    asyncio.run(main())
