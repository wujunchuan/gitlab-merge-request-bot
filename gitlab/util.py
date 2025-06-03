def filter_files_from_diff(content: str, files_to_filter: list[str]) -> str:
    """过滤掉指定文件的 diff 内容"""
    # 如果没有需要过滤的文件，直接返回原内容
    if not any(file in content for file in files_to_filter):
        return content

    # 按 diff 头部分割内容
    diff_sections = content.split("diff --git")
    # 过滤掉指定文件的 sections
    filtered_sections = [
        section
        for section in diff_sections
        if not any(file in section for file in files_to_filter)
    ]

    # 重新组合内容
    filtered_content = "diff --git".join(filtered_sections)
    # 处理开头的 diff --git
    if filtered_content.startswith("diff --git"):
        filtered_content = filtered_content[len("diff --git") :]

    return filtered_content
