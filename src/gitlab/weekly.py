from datetime import datetime, timedelta
from typing import Any, Dict, List

import requests

from gitlab.auth import base_url, headers
from gitlab.merge_request import get_merge_request_commits


def get_current_user_info() -> Dict[str, Any]:
    """获取当前用户信息"""
    url = f"{base_url}/user"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def fetch_recent_merge_requests(
    project_id: str = None, days: int = 7
) -> List[Dict[str, Any]]:
    """
    Retrieve merge requests created by the current user within the last specified number of days, including their commit records.
    
    Parameters:
        project_id (str, optional): If provided, limits results to the specified project; otherwise, fetches across all projects.
        days (int, optional): Number of days to look back for merge requests. Defaults to 7.
    
    Returns:
        List[Dict[str, Any]]: A list of merge requests, each containing basic information and associated commit records where available.
    """
    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # 获取当前用户信息
    current_user = get_current_user_info()
    user_id = current_user["id"]

    # 构建API URL和参数
    if project_id:
        # 获取特定项目的MR
        url = f"{base_url}/projects/{project_id}/merge_requests"
    else:
        # 获取用户所有项目的MR
        url = f"{base_url}/merge_requests"

    params = {
        "author_id": user_id,  # 只获取当前用户创建的MR
        "updated_before": end_date.isoformat(),  # 更新时间在指定日期之前
        "updated_after": start_date.isoformat(),  # 更新时间在指定日期之后
        "order_by": "created_at",  # 按创建时间排序
        "sort": "desc",  # 降序排列（最新的在前）
        "per_page": 100,  # 每页100条记录
    }

    all_merge_requests = []
    states = ["opened", "merged"]  # 定义要获取的状态列表

    for state in states:
        page = 1
        while True:
            params["state"] = state  # 设置当前要获取的状态
            params["page"] = page
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            merge_requests = response.json()

            if not merge_requests:
                break

            all_merge_requests.extend(merge_requests)

            # 检查是否还有更多页面
            if len(merge_requests) < params["per_page"]:
                break

            page += 1

    # 为每个MR获取提交记录
    enriched_merge_requests = []
    for mr in all_merge_requests:
        try:
            # 获取MR的提交记录
            commits = get_merge_request_commits(mr["project_id"], str(mr["iid"]))

            # 添加提交记录到MR信息中
            mr_with_commits = mr.copy()
            mr_with_commits["commits"] = commits
            enriched_merge_requests.append(mr_with_commits)

        except Exception as e:
            print(f"获取MR {mr['web_url']} 的提交记录失败: {e}")
            # 即使获取提交记录失败，也保留MR基本信息
            enriched_merge_requests.append(mr)

    return enriched_merge_requests


def print_merge_requests_summary(merge_requests: List[Dict[str, Any]]):
    """打印MR摘要信息"""
    if not merge_requests:
        print("最近7天内没有找到MR")
        return

    print(f"\n找到 {len(merge_requests)} 个最近7天的MR:\n")

    for i, mr in enumerate(merge_requests, 1):
        print(f"{i}. {mr['title']}")
        print(f"   项目: {mr['references']['full']}")
        print(f"   状态: {mr['state']}")
        # print(f"   创建时间: {mr['created_at']}")
        print(f"   URL: {mr['web_url']}")

        # 显示提交记录信息
        # if "commits" in mr and mr["commits"]:
        #     print(f"   提交数量: {len(mr['commits'])}")
        #     for commit in mr["commits"]:  # 只显示前3个提交
        #         print(f"     - {commit['short_id']}: {commit['title']}")
        #     if len(mr["commits"]) > 3:
        #         print(f"     ... 还有 {len(mr['commits']) - 3} 个提交")

        # print()


if __name__ == "__main__":
    try:
        # 获取最近7天的MR
        recent_mrs = fetch_recent_merge_requests()

        # 打印摘要
        print_merge_requests_summary(recent_mrs)

        # 也可以获取特定项目的MR
        # project_id = "your-project-id"  # 替换为实际的项目ID
        # project_mrs = fetch_recent_merge_requests(project_id)
        # print_merge_requests_summary(project_mrs)

    except Exception as e:
        print(f"获取MR失败: {e}")
