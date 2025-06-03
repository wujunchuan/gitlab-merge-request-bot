def filter_files_from_diff(
    content: str, files_to_filter: list[str] = ["pnpm-lock.yaml"]
) -> str:
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

    return filtered_content


if __name__ == "__main__":
    content = """
diff --git a/src/utils/helper.py b/src/utils/helper.py
index 1234567..abcdefg 100644
--- a/src/utils/helper.py
+++ b/src/utils/helper.py
@@ -1,3 +1,4 @@
def helper():
+    print("helper")
    pass
diff --git a/src/main.py b/src/main.py
index 2345678..bcdefgh 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
def main():
+    print("main")
    pass
"""
    print(filter_files_from_diff(content, ["helper.py"]))
