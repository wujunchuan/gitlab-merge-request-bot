#!/usr/bin/env python3
import argparse
import asyncio
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from pocketflow import AsyncFlow

from gitlab.weekly import fetch_recent_merge_requests, print_merge_requests_summary
from workflow.summary_merge_request import SummaryMergeRequest


def get_version():
    """获取项目版本信息"""
    try:
        # 获取项目根目录的 pyproject.toml 文件路径
        project_root = Path(__file__).parent.parent
        pyproject_path = project_root / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
            return data.get("project", {}).get("version", "unknown")
    except Exception as e:
        return f"无法获取版本信息: {e}"


def cmd_version():
    """执行 version 命令逻辑"""
    version = get_version()
    print(version)


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

    # version 子命令
    _version_parser = subparsers.add_parser("version", help="显示版本信息")

    # weekly 子命令
    _weekly_parser = subparsers.add_parser("weekly", help="获取最近7天的 MR 摘要")

    # merge 子命令
    merge_parser = subparsers.add_parser("merge", help="为指定的 MR 生成摘要并评论")
    merge_parser.add_argument("url", help="GitLab Merge Request URL")

    # 解析参数
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 执行对应的命令
    if args.command == "version":
        cmd_version()
    elif args.command == "weekly":
        cmd_weekly()
    elif args.command == "merge":
        asyncio.run(cmd_merge(args.url))


if __name__ == "__main__":
    main()
