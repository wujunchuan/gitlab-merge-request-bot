#!/usr/bin/env python3
import argparse
import asyncio
import os
import re
import subprocess
import sys
import time
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


async def cmd_create(target_branch: str = "master", assignee: str = None):
    """执行 create 命令逻辑 - 创建 MR 并自动分析"""

    try:
        # 获取当前分支名
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True,
            )
            current_branch = result.stdout.strip()
            print(f"当前分支: {current_branch}")
        except subprocess.CalledProcessError as e:
            print(f"获取当前分支失败: {e}", file=sys.stderr)
            sys.exit(1)

        # 推送当前分支到远程仓库
        print(f"正在推送分支 {current_branch}...")
        try:
            subprocess.run(["git", "push", "origin", current_branch], check=True)
            print(f"分支 {current_branch} 推送成功")
        except subprocess.CalledProcessError as e:
            print(f"推送分支失败: {e}", file=sys.stderr)
            sys.exit(1)

        title = f"feat: {current_branch} -> {target_branch}"

        # 构建 glab mr create 命令
        cmd = [
            "glab",
            "mr",
            "create",
            "--target-branch",
            target_branch,
            "--title",
            title,
            "--description",
            "WIP",
            "--draft",
        ]

        if assignee:
            cmd.extend(["--assignee", assignee])

        print(f"正在创建 MR: {' '.join(cmd)}")

        # 执行 glab mr create 命令
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # 从输出中提取 MR URL
        output = result.stderr + result.stdout  # glab 可能输出到 stderr 或 stdout
        print(f"glab 输出: {output}")

        # 支持不同的 GitLab 实例域名
        url_pattern = r"https?://[^\s]+/-/merge_requests/\d+"
        urls = re.findall(url_pattern, output)

        if not urls:
            print("错误: 无法从 glab 输出中提取 MR URL", file=sys.stderr)
            print(f"glab 原始输出: {output}", file=sys.stderr)
            sys.exit(1)

        mr_url = urls[0]
        print(f"MR 创建成功: {mr_url}")

        # 等待一段时间让 GitLab 处理 MR
        time.sleep(1)

        # 调用 cmd_merge 分析 MR
        print(f"开始分析 MR: {mr_url}")
        await cmd_merge(mr_url)

        print("MR 创建和分析完成！")

    except subprocess.CalledProcessError as e:
        print(f"glab mr create 失败: {e}", file=sys.stderr)
        print(f"错误输出: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"创建 MR 失败: {e}", file=sys.stderr)
        sys.exit(1)


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

    # create 子命令
    create_parser = subparsers.add_parser("create", help="创建 MR 并自动分析")
    create_parser.add_argument(
        "target_branch", nargs="?", default="master", help="目标分支 (默认: master)"
    )
    create_parser.add_argument(
        "assignee", nargs="?", default=os.getenv("GITLAB_ASSIGNEE"), help="指派人"
    )

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
    elif args.command == "create":
        asyncio.run(cmd_create(args.target_branch, args.assignee))


if __name__ == "__main__":
    main()
