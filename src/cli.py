#!/usr/bin/env python3
import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

import requests

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from pocketflow import AsyncFlow

from gitlab.merge_request import (
    create_merge_request,
    get_merge_request_by_source_branch,
    get_project_by_path,
    get_user_by_username,
)
from gitlab.util import (
    get_current_git_branch,
    get_git_remote_project_path,
    push_current_branch,
)
from gitlab.weekly import (
    fetch_recent_merge_requests,
    get_current_user_info,
    print_merge_requests_summary,
)
from workflow.code_review import CodeReviewMergeRequest
from workflow.summary_merge_request import SummaryMergeRequest


def get_mr_url_from_current_branch() -> str:
    """根据当前分支获取对应的 MR URL"""
    try:
        # 获取当前分支名
        current_branch = get_current_git_branch()
        print(f"当前分支: {current_branch}")

        # 获取项目路径
        project_path = get_git_remote_project_path()
        print(f"项目路径: {project_path}")

        # 获取项目信息
        project_info = get_project_by_path(project_path)
        project_id = str(project_info["id"])

        # 根据分支获取 MR
        mr_info = get_merge_request_by_source_branch(project_id, current_branch)
        mr_url = mr_info["web_url"]

        print(f"找到对应的 MR: {mr_url}")
        return mr_url

    except Exception as e:
        raise RuntimeError(f"无法获取当前分支对应的 MR URL: {e}")


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
        print("获取当前分支信息...")
        current_branch = get_current_git_branch()
        print(f"当前分支: {current_branch}")

        # 获取项目路径
        print("获取项目信息...")
        project_path = get_git_remote_project_path()
        print(f"项目路径: {project_path}")

        # 推送当前分支到远程仓库
        print(f"正在推送分支 {current_branch}...")
        push_current_branch()
        print(f"分支 {current_branch} 推送成功")

        # 获取项目信息
        print("获取项目详情...")
        project_info = get_project_by_path(project_path)
        project_id = str(project_info["id"])
        print(f"项目 ID: {project_id}")

        # 处理 assignee
        assignee_id = None
        # 如果没有 assignee, 则取当前用户
        if not assignee:
            try:
                current_user = get_current_user_info()
                assignee_id = current_user["id"]
                assignee = current_user["username"]
                print(
                    f"使用当前用户作为 assignee: {current_user['name']} (ID: {assignee_id})"
                )
            except Exception as e:
                print(f"警告: 无法获取当前用户信息: {e}")
        else:
            if assignee:
                print(f"查找用户: {assignee}")
                try:
                    user_info = get_user_by_username(assignee)
                    assignee_id = user_info["id"]
                    print(f"找到用户: {user_info['name']} (ID: {assignee_id})")
                except Exception as e:
                    print(f"警告: 无法找到用户 '{assignee}': {e}")
                    print("将不设置 assignee")

        # 生成 MR 标题
        title = f"feat: {current_branch} -> {target_branch}"

        # 使用 GitLab API 创建 MR
        print("正在通过 GitLab API 创建 MR...")
        try:
            mr_data = create_merge_request(
                project_id=project_id,
                source_branch=current_branch,
                target_branch=target_branch,
                title=title,
                description="WIP",
                assignee_id=assignee_id,
                remove_source_branch=True,
                draft=True,
            )

            mr_url = mr_data["web_url"]
            print(f"MR 创建成功: {mr_url}")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                # MR 已存在，根据源分支获取已存在的 MR
                print(f"分支 {current_branch} 的 MR 已存在，正在获取已存在的 MR...")
                try:
                    existing_mr = get_merge_request_by_source_branch(
                        project_id, current_branch
                    )
                    mr_url = existing_mr["web_url"]
                    print(f"找到已存在的 MR: {mr_url}")
                except ValueError as ve:
                    print(f"获取已存在的 MR 失败: {ve}")
                    raise e  # 重新抛出原始异常
            else:
                raise e  # 不是 409 异常，重新抛出

        # 等待一段时间让 GitLab 处理 MR
        time.sleep(1)

        # 调用 cmd_merge 分析 MR
        print(f"开始分析 MR: {mr_url}")
        await cmd_merge(mr_url)

        print(f"MR 创建和分析完成！请在 {mr_url} 查看")

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


async def cmd_merge(url: str = None):
    """执行 merge 命令逻辑"""
    try:
        # 如果没有提供 URL，则根据当前分支获取
        if not url:
            print("未提供 MR URL，正在根据当前分支获取...")
            url = get_mr_url_from_current_branch()

        print(f"开始分析 MR: {url}")

        flow = AsyncFlow(start=SummaryMergeRequest())

        shared = {"url": url}
        await flow.run_async(shared)

    except Exception as e:
        print(f"处理 merge request 失败: {e}", file=sys.stderr)
        sys.exit(1)


async def cmd_code_review(url: str = None):
    """执行代码审查命令逻辑"""
    try:
        # 如果没有提供 URL，则根据当前分支获取
        if not url:
            print("未提供 MR URL，正在根据当前分支获取...")
            url = get_mr_url_from_current_branch()

        print(f"开始对 MR 进行代码审查: {url}")
        flow = AsyncFlow(start=CodeReviewMergeRequest())

        shared = {"url": url}
        result = await flow.run_async(shared)

        print(f"代码审查完成: {result}")

    except Exception as e:
        print(f"代码审查失败: {e}", file=sys.stderr)
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
    merge_parser.add_argument(
        "url",
        nargs="?",
        help="GitLab Merge Request URL (可选，如果为空则根据当前分支获取对应的 MR)",
    )

    # code-review 子命令
    review_parser = subparsers.add_parser(
        "code-review", help="对指定的 MR 进行代码审查"
    )
    review_parser.add_argument(
        "url",
        nargs="?",
        help="GitLab Merge Request URL (可选，如果为空则根据当前分支获取对应的 MR)",
    )

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
    elif args.command == "code-review":
        asyncio.run(cmd_code_review(args.url))
    elif args.command == "create":
        asyncio.run(cmd_create(args.target_branch, args.assignee))


if __name__ == "__main__":
    main()
