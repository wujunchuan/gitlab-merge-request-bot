import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class DiffLine:
    """表示 diff 中的一行"""

    line_number: int
    content: str
    line_type: str  # "added", "removed", "context"
    old_line_number: Optional[int] = None
    new_line_number: Optional[int] = None


@dataclass
class DiffHunk:
    """表示 diff 中的一个 hunk（变更块）"""

    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[DiffLine]
    header: str


@dataclass
class DiffFile:
    """表示 diff 中的一个文件"""

    old_path: str
    new_path: str
    hunks: List[DiffHunk]
    is_new_file: bool = False
    is_deleted_file: bool = False
    is_binary: bool = False


class DiffParser:
    """Git diff 解析器"""

    def __init__(self):
        self.file_header_pattern = re.compile(r"^diff --git a/(.*?) b/(.*?)$")
        self.hunk_header_pattern = re.compile(
            r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$"
        )
        self.new_file_pattern = re.compile(r"^new file mode")
        self.deleted_file_pattern = re.compile(r"^deleted file mode")
        self.binary_file_pattern = re.compile(r"^Binary files")

    def parse_diff(self, diff_content: str) -> List[DiffFile]:
        """
        解析 diff 内容

        Args:
            diff_content: Git diff 的原始内容

        Returns:
            List[DiffFile]: 解析后的文件列表
        """
        if not diff_content.strip():
            return []

        lines = diff_content.split("\n")
        files = []
        current_file = None
        current_hunk = None

        i = 0
        while i < len(lines):
            line = lines[i]

            # 检查文件头
            file_match = self.file_header_pattern.match(line)
            if file_match:
                # 保存上一个文件
                if current_file:
                    if current_hunk:
                        current_file.hunks.append(current_hunk)
                    files.append(current_file)

                # 创建新文件
                old_path = file_match.group(1)
                new_path = file_match.group(2)
                current_file = DiffFile(old_path=old_path, new_path=new_path, hunks=[])
                current_hunk = None

                # 检查后续行的文件状态
                j = i + 1
                while (
                    j < len(lines)
                    and not lines[j].startswith("@@")
                    and not lines[j].startswith("diff --git")
                ):
                    if self.new_file_pattern.match(lines[j]):
                        current_file.is_new_file = True
                    elif self.deleted_file_pattern.match(lines[j]):
                        current_file.is_deleted_file = True
                    elif self.binary_file_pattern.match(lines[j]):
                        current_file.is_binary = True
                    j += 1

                i = j - 1

            # 检查 hunk 头
            elif line.startswith("@@"):
                hunk_match = self.hunk_header_pattern.match(line)
                if hunk_match:
                    # 保存上一个 hunk
                    if current_hunk:
                        current_file.hunks.append(current_hunk)

                    # 创建新 hunk
                    old_start = int(hunk_match.group(1))
                    old_count = int(hunk_match.group(2)) if hunk_match.group(2) else 1
                    new_start = int(hunk_match.group(3))
                    new_count = int(hunk_match.group(4)) if hunk_match.group(4) else 1
                    header = hunk_match.group(5).strip() if hunk_match.group(5) else ""

                    current_hunk = DiffHunk(
                        old_start=old_start,
                        old_count=old_count,
                        new_start=new_start,
                        new_count=new_count,
                        lines=[],
                        header=header,
                    )

            # 处理 diff 行内容
            elif current_hunk is not None and (
                line.startswith("+") or line.startswith("-") or line.startswith(" ")
            ):
                if line.startswith("+"):
                    line_type = "added"
                    content = line[1:]
                elif line.startswith("-"):
                    line_type = "removed"
                    content = line[1:]
                else:  # 以空格开始的上下文行
                    line_type = "context"
                    content = line[1:]

                diff_line = DiffLine(
                    line_number=len(current_hunk.lines) + 1,
                    content=content,
                    line_type=line_type,
                )
                current_hunk.lines.append(diff_line)

            i += 1

        # 保存最后的文件和 hunk
        if current_file:
            if current_hunk:
                current_file.hunks.append(current_hunk)
            files.append(current_file)

        # 计算实际行号
        for file in files:
            self._calculate_line_numbers(file)

        return files

    def _calculate_line_numbers(self, diff_file: DiffFile):
        """计算每一行在原文件和新文件中的实际行号"""
        for hunk in diff_file.hunks:
            old_line_num = hunk.old_start
            new_line_num = hunk.new_start

            for line in hunk.lines:
                if line.line_type == "removed":
                    line.old_line_number = old_line_num
                    line.new_line_number = None
                    old_line_num += 1
                elif line.line_type == "added":
                    line.old_line_number = None
                    line.new_line_number = new_line_num
                    new_line_num += 1
                else:  # context
                    line.old_line_number = old_line_num
                    line.new_line_number = new_line_num
                    old_line_num += 1
                    new_line_num += 1

    def get_changed_lines(
        self, diff_files: List[DiffFile]
    ) -> Dict[str, List[Tuple[int, str, str]]]:
        """
        获取所有变更的行，用于代码审查

        Args:
            diff_files: 解析后的 diff 文件列表

        Returns:
            Dict[str, List[Tuple[int, str, str]]]:
            文件路径 -> [(行号, 行类型, 内容), ...]
        """
        changed_lines = {}

        for file in diff_files:
            if file.is_binary:
                continue

            file_changes = []
            for hunk in file.hunks:
                for line in hunk.lines:
                    if line.line_type in ["added", "removed"]:
                        line_number = (
                            line.new_line_number
                            if line.line_type == "added"
                            else line.old_line_number
                        )
                        if line_number:
                            file_changes.append(
                                (line_number, line.line_type, line.content)
                            )

            if file_changes:
                changed_lines[file.new_path] = file_changes

        return changed_lines

    def get_added_lines(
        self, diff_files: List[DiffFile]
    ) -> Dict[str, List[Tuple[int, str]]]:
        """
        只获取新增的行，用于添加评论

        Args:
            diff_files: 解析后的 diff 文件列表

        Returns:
            Dict[str, List[Tuple[int, str]]]: 文件路径 -> [(行号, 内容), ...]
        """
        added_lines = {}

        for file in diff_files:
            if file.is_binary:
                continue

            file_additions = []
            for hunk in file.hunks:
                for line in hunk.lines:
                    if line.line_type == "added" and line.new_line_number:
                        file_additions.append((line.new_line_number, line.content))

            if file_additions:
                added_lines[file.new_path] = file_additions

        return added_lines


def format_diff_for_review(
    diff_files: List[DiffFile], max_context_lines: int = 3
) -> str:
    """
    将解析后的 diff 格式化为适合代码审查的文本

    Args:
        diff_files: 解析后的 diff 文件列表
        max_context_lines: 最大上下文行数

    Returns:
        str: 格式化后的 diff 文本
    """
    result = []

    for file in diff_files:
        if file.is_binary:
            result.append(f"## 文件: {file.new_path} (二进制文件)")
            continue

        if file.is_new_file:
            result.append(f"## 新文件: {file.new_path}")
        elif file.is_deleted_file:
            result.append(f"## 删除文件: {file.old_path}")
        else:
            result.append(f"## 文件: {file.new_path}")

        for hunk in file.hunks:
            result.append(
                f"\n### 变更块 @@ -{hunk.old_start},{hunk.old_count} +{hunk.new_start},{hunk.new_count} @@"
            )

            context_count = 0
            for line in hunk.lines:
                if line.line_type == "context":
                    context_count += 1
                    if context_count <= max_context_lines:
                        result.append(f"  {line.content}")
                    elif context_count == max_context_lines + 1:
                        result.append("  ...")
                else:
                    context_count = 0
                    if line.line_type == "added":
                        result.append(f"+ {line.content}")
                    elif line.line_type == "removed":
                        result.append(f"- {line.content}")

        result.append("")  # 文件间空行

    return "\n".join(result)


if __name__ == "__main__":
    # 测试示例
    sample_diff = """diff --git a/src/example.py b/src/example.py
index 1234567..abcdefg 100644
--- a/src/example.py
+++ b/src/example.py
@@ -1,7 +1,8 @@
 def hello():
-    print("Hello")
+    print("Hello World")
     return True
 
 def goodbye():
+    print("Goodbye")
     return False
     
@@ -15,6 +16,7 @@ def main():
     hello()
     goodbye()
+    print("Done")
"""

    parser = DiffParser()
    files = parser.parse_diff(sample_diff)

    print("解析结果:")
    for file in files:
        print(f"文件: {file.new_path}")
        for hunk in file.hunks:
            print(
                f"  Hunk: @@ -{hunk.old_start},{hunk.old_count} +{hunk.new_start},{hunk.new_count} @@"
            )
            for line in hunk.lines:
                print(
                    f"    {line.line_type}: {line.content} (old: {line.old_line_number}, new: {line.new_line_number})"
                )

    print("\n格式化输出:")
    print(format_diff_for_review(files))

    print("\n变更行:")
    changed = parser.get_changed_lines(files)
    for file_path, lines in changed.items():
        print(f"{file_path}:")
        for line_num, line_type, content in lines:
            print(f"  行 {line_num} ({line_type}): {content}")
