#!/usr/bin/env python3
import argparse
import asyncio
import sys

from pocketflow import AsyncFlow

from gitlab.weekly import fetch_recent_merge_requests, print_merge_requests_summary
from workflow.summary_merge_request import SummaryMergeRequest


def cmd_weekly():
    """
    Fetch and display a summary of GitLab merge requests from the past week.
    
    Retrieves merge requests created within the last 7 days and prints a summary to standard output. Exits with an error message if the operation fails.
    """
    try:
        # 获取最近7天的MR
        recent_mrs = fetch_recent_merge_requests()

        # 打印摘要
        print_merge_requests_summary(recent_mrs)

    except Exception as e:
        print(f"获取MR失败: {e}", file=sys.stderr)
        sys.exit(1)


async def cmd_merge(url: str):
    """
    Executes the asynchronous workflow for processing a GitLab merge request by URL.
    
    Parameters:
        url (str): The URL of the GitLab merge request to process.
    """
    try:
        flow = AsyncFlow(start=SummaryMergeRequest())

        shared = {"url": url}
        await flow.run_async(shared)

    except Exception as e:
        print(f"处理 merge request 失败: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """
    Entry point for the GitLab Merge Request CLI tool.
    
    Parses command-line arguments, dispatches to the appropriate subcommand handler, and manages program exit behavior. Supports the `weekly` and `merge` subcommands for summarizing recent merge requests and generating summaries for a specific merge request, respectively.
    """
    parser = argparse.ArgumentParser(
        prog="gitlab-merge-request-bot", description="GitLab Merge Request 工具集"
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # weekly 子命令
    weekly_parser = subparsers.add_parser("weekly", help="获取最近7天的 MR 摘要")

    # merge 子命令
    merge_parser = subparsers.add_parser("merge", help="为指定的 MR 生成摘要并评论")
    merge_parser.add_argument("url", help="GitLab Merge Request URL")

    # 解析参数
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 执行对应的命令
    if args.command == "weekly":
        cmd_weekly()
    elif args.command == "merge":
        asyncio.run(cmd_merge(args.url))


if __name__ == "__main__":
    main()
