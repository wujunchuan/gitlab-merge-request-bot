#!/usr/bin/env python3
import argparse
import asyncio
import sys

from pocketflow import AsyncFlow

from gitlab.weekly import fetch_recent_merge_requests, print_merge_requests_summary
from workflow.summary_merge_request import SummaryMergeRequest


def cmd_weekly():
    """执行 weekly 命令逻辑"""
    try:
        # 获取最近7天的MR
        recent_mrs = fetch_recent_merge_requests()

        # 打印摘要
        print_merge_requests_summary(recent_mrs)

    except Exception as e:
        print(f"获取MR失败: {e}", file=sys.stderr)
        sys.exit(1)


async def cmd_merge(url: str):
    """执行 merge 命令逻辑"""
    try:
        flow = AsyncFlow(start=SummaryMergeRequest())

        shared = {"url": url}
        await flow.run_async(shared)

    except Exception as e:
        print(f"处理 merge request 失败: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """主入口函数"""
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
