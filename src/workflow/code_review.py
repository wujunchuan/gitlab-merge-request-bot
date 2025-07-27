import asyncio
import json
from typing import Any, Dict

from pocketflow import AsyncFlow, AsyncNode

from ai.auth import client, get_openai_model
from ai.get_prompt import prompt_manager
from gitlab.comment import (
    create_diff_discussion,
    create_discussion,
    get_merge_request_versions,
)
from gitlab.diff_parser import DiffParser, format_diff_for_review
from gitlab.merge_request import get_merge_request_raw_diff
from gitlab.util import parse_merge_request_url
from utils.logger import get_logger

# 创建专用的日志记录器
logger = get_logger(__name__, log_file="code_review.log")

code_review_prompt = prompt_manager.load_prompt("code_review.md")


def call_llm_for_review(diff_content: str) -> Dict[str, Any]:
    """调用 LLM 进行代码审查"""
    logger.info("Sending diff to LLM for code review")
    logger.debug(f"Diff content length: {len(diff_content)} characters")

    try:
        chat_completion = client.chat.completions.create(
            model=get_openai_model(),
            temperature=0.3,  # 较低的 temperature 以获得更一致的审查结果
            messages=[
                {"role": "system", "content": code_review_prompt},
                {"role": "user", "content": diff_content},
            ],
            response_format={"type": "json_object"},
        )

        result = chat_completion.choices[0].message.content
        logger.info("Received code review from LLM")
        logger.debug(f"LLM response length: {len(result)} characters")

        # 尝试解析 JSON 格式的响应
        try:
            review_data = json.loads(result)
            return review_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            # 如果解析失败，返回原始文本作为总结
            return {
                "overall_summary": result,
                "line_comments": [],
                "general_suggestions": [],
            }

    except Exception as e:
        logger.error(f"Error calling LLM for code review: {e}")
        raise


class CodeReviewMergeRequest(AsyncNode):
    """
    对 Merge Request 进行代码审查，分析代码变更并添加行级评论
    """

    async def prep_async(self, shared):
        """准备阶段：解析 Merge Request 并获取 diff 信息"""
        url = shared.get("url")
        if not url:
            raise ValueError("url is required")

        # 获取 project_id 与 merge_number
        project_id, merge_number = parse_merge_request_url(url)
        shared["project_id"] = project_id
        shared["merge_number"] = merge_number

        logger.info(
            f"Starting code review for MR {merge_number} in project {project_id}"
        )

        # 获取 MR 的原始 diff
        raw_diff = get_merge_request_raw_diff(project_id, merge_number)
        if not raw_diff.strip():
            logger.warning("No diff content found for the merge request")
            shared["has_changes"] = False
            return shared

        shared["raw_diff"] = raw_diff
        shared["has_changes"] = True

        # 解析 diff 内容
        diff_parser = DiffParser()
        diff_files = diff_parser.parse_diff(raw_diff)
        shared["diff_files"] = diff_files

        # 格式化 diff 用于 LLM 分析
        formatted_diff = format_diff_for_review(diff_files)
        shared["formatted_diff"] = formatted_diff

        # 获取变更行信息，用于后续添加评论
        changed_lines = diff_parser.get_changed_lines(diff_files)
        shared["changed_lines"] = changed_lines

        # 获取 MR 版本信息，用于创建行级评论
        try:
            versions = get_merge_request_versions(project_id, merge_number)
            if versions:
                latest_version = versions[0]
                shared["base_sha"] = latest_version.get("base_commit_sha")
                shared["head_sha"] = latest_version.get("head_commit_sha")
                shared["start_sha"] = latest_version.get("start_commit_sha")
            else:
                logger.warning("No version information found for the merge request")
                shared["base_sha"] = None
                shared["head_sha"] = None
                shared["start_sha"] = None
        except Exception as e:
            logger.error(f"Failed to get MR versions: {e}")
            shared["base_sha"] = None
            shared["head_sha"] = None
            shared["start_sha"] = None

        logger.info(f"Parsed {len(diff_files)} files with changes")
        return shared

    async def exec_async(self, prep_res):
        """执行阶段：调用 LLM 进行代码审查"""
        if not prep_res.get("has_changes", False):
            logger.info("No changes to review")
            return {
                "overall_summary": "没有发现代码变更，无需审查。",
                "line_comments": [],
                "general_suggestions": [],
            }

        formatted_diff = prep_res.get("formatted_diff", "")
        if not formatted_diff:
            logger.warning("No formatted diff available for review")
            return {
                "overall_summary": "无法获取代码变更内容。",
                "line_comments": [],
                "general_suggestions": [],
            }

        logger.info("Starting LLM code review analysis")
        review_result = call_llm_for_review(formatted_diff)
        logger.info("Code review analysis completed")

        return review_result

    async def post_async(self, shared, prep_res, exec_res):
        """后处理阶段：将审查结果添加为评论"""
        if not prep_res.get("has_changes", False):
            logger.info("No changes to comment on")
            return "No changes to review"

        project_id = shared["project_id"]
        merge_number = shared["merge_number"]

        logger.info(f"Adding code review comments to MR {merge_number}")

        # 添加总体评论
        overall_summary = exec_res.get("overall_summary", "代码审查完成")
        general_suggestions = exec_res.get("general_suggestions", [])

        overall_comment = f"""<!-- code-review-bot -->
## 🤖 代码审查报告

### 📋 总体评估
{overall_summary}
"""

        if general_suggestions:
            overall_comment += "\n### 💡 总体建议\n"
            for i, suggestion in enumerate(general_suggestions, 1):
                overall_comment += f"{i}. {suggestion}\n"

        overall_comment += "\n---\n*此评论由 AI 代码审查助手自动生成*"

        # 创建总体评论
        try:
            create_discussion(project_id, merge_number, overall_comment)
            logger.info("Created overall review comment")
        except Exception as e:
            logger.error(f"Failed to create overall comment: {e}")

        # 添加行级评论
        line_comments = exec_res.get("line_comments", [])
        line_comment_count = 0

        for comment in line_comments:
            try:
                file_path = comment.get("file_path")
                line_number = comment.get("line_number")
                severity = comment.get("severity", "suggestion")
                category = comment.get("category", "quality")
                message = comment.get("message", "")
                suggestion = comment.get("suggestion", "")

                if not all([file_path, line_number, message]):
                    logger.warning(f"Incomplete comment data: {comment}")
                    continue

                # 构建评论内容
                severity_emoji = {
                    "critical": "🚨",
                    "major": "⚠️",
                    "minor": "💡",
                    "suggestion": "💭",
                }.get(severity, "💬")

                category_emoji = {
                    "security": "🔒",
                    "performance": "⚡",
                    "quality": "✨",
                    "style": "🎨",
                    "test": "🧪",
                }.get(category, "📝")

                comment_text = f"""{severity_emoji} **{severity.upper()}** - {category_emoji} {category.upper()}

{message}"""

                if suggestion:
                    comment_text += f"\n\n💡 **建议**: {suggestion}"
                elif severity in ["suggestion", "minor"]:
                    # 只跳过低严重性且无建议的评论，避免彩虹屁
                    continue

                comment_text += "\n\n<!-- code-review-bot -->"

                # 映射 AI 返回的 line_type 到 GitLab API 格式
                # AI 输出: "added", "removed", "modified"
                # GitLab API: "new", "old", "both"
                # 注意：line_number 应该对应正确的行号：
                # - "removed" 行使用 old_line_number
                # - "added" 或 "modified" 行使用 new_line_number
                ai_line_type = comment.get("line_type", "added")  # 默认为 added
                gitlab_line_type = "new"  # 默认值
                if ai_line_type == "removed":
                    gitlab_line_type = "old"
                elif ai_line_type == "modified":
                    gitlab_line_type = "new"
                elif ai_line_type == "added":
                    gitlab_line_type = "new"

                logger.debug(
                    f"Line comment mapping: AI line_type='{ai_line_type}' -> GitLab line_type='{gitlab_line_type}' for {file_path}:{line_number}"
                )

                # 创建行级评论
                create_diff_discussion(
                    project_id=project_id,
                    mr_number=merge_number,
                    content=comment_text,
                    file_path=file_path,
                    line_number=line_number,
                    line_type=gitlab_line_type,
                    base_sha=prep_res.get("base_sha"),
                    head_sha=prep_res.get("head_sha"),
                    start_sha=prep_res.get("start_sha"),
                )

                line_comment_count += 1
                logger.debug(f"Created line comment for {file_path}:{line_number}")

            except Exception as e:
                logger.error(f"Failed to create line comment: {e}")
                continue

        logger.info(
            f"Code review completed. Created {line_comment_count} line comments"
        )
        return f"Created {line_comment_count} line comments and 1 overall summary"


if __name__ == "__main__":
    flow = AsyncFlow(start=CodeReviewMergeRequest())

    async def main():
        shared = {
            "url": "https://git.intra.gaoding.com/chuanpu/gitlab-merge-request-bot/-/merge_requests/15"
        }
        result = await flow.run_async(shared)
        print(f"Code review result: {result}")

    asyncio.run(main())
