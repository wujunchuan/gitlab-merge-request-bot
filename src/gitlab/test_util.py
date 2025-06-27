from gitlab.util import filter_files_from_diff, parse_merge_request_url


class TestFilterFilesFromDiff:
    """测试 filter_files_from_diff 函数"""

    def test_empty_content(self):
        """测试空内容"""
        result = filter_files_from_diff("", ["file.txt"])
        assert result == ""

    def test_no_files_to_filter(self):
        """测试没有需要过滤的文件时返回原内容"""
        content = """diff --git a/file1.py b/file1.py
index 1234567..abcdefg 100644
--- a/file1.py
+++ b/file1.py
@@ -1,3 +1,4 @@
 def hello():
+    print("hello")
     pass
"""
        result = filter_files_from_diff(content, ["nonexistent.txt"])
        assert result == content

    def test_filter_single_file(self):
        """测试过滤单个文件"""
        content = """diff --git a/file1.py b/file1.py
index 1234567..abcdefg 100644
--- a/file1.py
+++ b/file1.py
@@ -1,3 +1,4 @@
 def hello():
+    print("hello")
     pass
diff --git a/file2.py b/file2.py
index 2345678..bcdefgh 100644
--- a/file2.py
+++ b/file2.py
@@ -1,3 +1,4 @@
 def world():
+    print("world")
     pass
"""
        result = filter_files_from_diff(content, ["file1.py"])
        assert "file1.py" not in result
        assert "file2.py" in result
        assert "def world():" in result

    def test_filter_multiple_files(self):
        """测试过滤多个文件"""
        content = """diff --git a/file1.py b/file1.py
index 1234567..abcdefg 100644
--- a/file1.py
+++ b/file1.py
@@ -1,3 +1,4 @@
 def hello():
+    print("hello")
     pass
diff --git a/file2.py b/file2.py
index 2345678..bcdefgh 100644
--- a/file2.py
+++ b/file2.py
@@ -1,3 +1,4 @@
 def world():
+    print("world")
     pass
diff --git a/file3.py b/file3.py
index 3456789..cdefghi 100644
--- a/file3.py
+++ b/file3.py
@@ -1,3 +1,4 @@
 def test():
+    print("test")
     pass
"""
        result = filter_files_from_diff(content, ["file1.py", "file3.py"])
        assert "file1.py" not in result
        assert "file3.py" not in result
        assert "file2.py" in result
        assert "def world():" in result

    def test_filter_all_files(self):
        """测试过滤所有文件"""
        content = """diff --git a/file1.py b/file1.py
index 1234567..abcdefg 100644
--- a/file1.py
+++ b/file1.py
@@ -1,3 +1,4 @@
 def hello():
+    print("hello")
     pass
diff --git a/file2.py b/file2.py
index 2345678..bcdefgh 100644
--- a/file2.py
+++ b/file2.py
@@ -1,3 +1,4 @@
 def world():
+    print("world")
     pass
"""
        result = filter_files_from_diff(content, ["file1.py", "file2.py"])
        # 当所有文件都被过滤时，应该返回空字符串或者只包含空的diff标识
        assert "file1.py" not in result
        assert "file2.py" not in result
        assert "def hello():" not in result
        assert "def world():" not in result

    def test_partial_filename_match(self):
        """测试部分文件名匹配"""
        content = """diff --git a/src/utils/helper.py b/src/utils/helper.py
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
        result = filter_files_from_diff(content, ["helper.py"])
        assert "helper.py" not in result
        assert "main.py" in result
        assert "def main():" in result

    def test_complex_diff_with_special_characters(self):
        """测试包含特殊字符的复杂diff"""
        content = """diff --git a/src/test with spaces.py b/src/test with spaces.py
index 1234567..abcdefg 100644
--- a/src/test with spaces.py
+++ b/src/test with spaces.py
@@ -1,5 +1,6 @@
 # Test file with special characters
 def test_function():
+    # Added comment
     return "Hello, World!"
 
 if __name__ == "__main__":
diff --git a/src/normal_file.py b/src/normal_file.py
index 2345678..bcdefgh 100644
--- a/src/normal_file.py
+++ b/src/normal_file.py
@@ -1,3 +1,4 @@
 def normal():
+    print("normal")
     pass
"""
        result = filter_files_from_diff(content, ["test with spaces.py"])
        assert "test with spaces.py" not in result
        assert "normal_file.py" in result
        assert "def normal():" in result

    def test_empty_filter_list(self):
        """测试空的过滤列表"""
        content = """diff --git a/file1.py b/file1.py
index 1234567..abcdefg 100644
--- a/file1.py
+++ b/file1.py
@@ -1,3 +1,4 @@
 def hello():
+    print("hello")
     pass
"""
        result = filter_files_from_diff(content, [])
        assert result == content

    def test_single_diff_section(self):
        """测试只有一个diff段落的情况"""
        content = """diff --git a/single_file.py b/single_file.py
index 1234567..abcdefg 100644
--- a/single_file.py
+++ b/single_file.py
@@ -1,3 +1,4 @@
 def single():
+    print("single")
     pass
"""
        result = filter_files_from_diff(content, ["single_file.py"])
        # 当唯一的文件被过滤时，结果应该为空或接近空
        assert "single_file.py" not in result
        assert "def single():" not in result

    def test_diff_without_git_prefix(self):
        """测试不标准的diff格式"""
        content = """Some other content
that doesn't follow
the expected format"""
        result = filter_files_from_diff(content, ["file.py"])
        # 对于不标准的格式，应该返回原内容
        assert result == content

    def test_unicode_filenames(self):
        """测试包含Unicode字符的文件名"""
        content = """diff --git a/测试文件.py b/测试文件.py
index 1234567..abcdefg 100644
--- a/测试文件.py
+++ b/测试文件.py
@@ -1,3 +1,4 @@
 def 测试函数():
+    # 添加注释
     pass
diff --git a/normal.py b/normal.py
index 2345678..bcdefgh 100644
--- a/normal.py
+++ b/normal.py
@@ -1,3 +1,4 @@
 def normal():
+    print("normal")
     pass
"""
        result = filter_files_from_diff(content, ["测试文件.py"])
        assert "测试文件.py" not in result
        assert "normal.py" in result
        assert "def normal():" in result

    def test_nested_path_filtering(self):
        """测试嵌套路径的文件过滤"""
        content = """diff --git a/src/utils/deep/nested/file.py b/src/utils/deep/nested/file.py
index 1234567..abcdefg 100644
--- a/src/utils/deep/nested/file.py
+++ b/src/utils/deep/nested/file.py
@@ -1,3 +1,4 @@
 def nested():
+    print("nested")
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
        result = filter_files_from_diff(content, ["src/utils/deep/nested/file.py"])
        assert "src/utils/deep/nested/file.py" not in result
        assert "src/main.py" in result
        assert "def main():" in result

    def test_case_sensitive_filtering(self):
        """测试大小写敏感的过滤"""
        content = """diff --git a/File.py b/File.py
index 1234567..abcdefg 100644
--- a/File.py
+++ b/File.py
@@ -1,3 +1,4 @@
 def CamelCase():
+    print("CamelCase")
     pass
diff --git a/file.py b/file.py
index 2345678..bcdefgh 100644
--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
 def lowercase():
+    print("lowercase")
     pass
"""
        # 过滤大写File.py，小写file.py应该保留
        result = filter_files_from_diff(content, ["File.py"])
        assert "File.py" not in result
        assert "file.py" in result
        assert "def lowercase():" in result

    def test_very_long_diff(self):
        """测试很长的diff内容"""
        # 创建一个包含多个文件的长diff
        sections = []
        for i in range(5):
            section = f"""diff --git a/file{i}.py b/file{i}.py
index {i}234567..abcdefg 100644
--- a/file{i}.py
+++ b/file{i}.py
@@ -1,10 +1,15 @@
 def function{i}():
+    # Added comment for file {i}
     for j in range(10):
+        print(f"Processing {{j}} in file {i}")
         pass
+    return "result{i}"
"""
            sections.append(section)

        content = "".join(sections)
        result = filter_files_from_diff(content, ["file1.py", "file3.py"])

        assert "file1.py" not in result
        assert "file3.py" not in result
        assert "file0.py" in result
        assert "file2.py" in result
        assert "file4.py" in result

    def test_binary_file_diff(self):
        """测试二进制文件的diff"""
        content = """diff --git a/image.png b/image.png
index 1234567..abcdefg 100644
Binary files a/image.png and b/image.png differ
diff --git a/text.py b/text.py
index 2345678..bcdefgh 100644
--- a/text.py
+++ b/text.py
@@ -1,3 +1,4 @@
 def text():
+    print("text")
     pass
"""
        result = filter_files_from_diff(content, ["image.png"])
        assert "image.png" not in result
        assert "text.py" in result
        assert "def text():" in result

    def test_empty_diff_sections(self):
        """测试空的diff段落"""
        content = """diff --git a/empty1.py b/empty1.py
diff --git a/file.py b/file.py
index 1234567..abcdefg 100644
--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
 def hello():
+    print("hello")
     pass
diff --git a/empty2.py b/empty2.py
"""
        result = filter_files_from_diff(content, ["empty1.py"])
        assert "empty1.py" not in result
        assert "file.py" in result
        assert "empty2.py" in result

    def test_filter_folder(self):
        """测试路径匹配"""
        content = """diff --git a/icon/gd.vue b/icon/gd.vue
index 1234567890abcdef1234567890abcdef12345678..1234567890abcdef1234567890abcdef12345678 100644
--- a/icon/gd.vue
<insert> b/icon/gd.vue
diff --git a/icon/button.vue b/icon/button.vue
--- a/icon/button.vue
<insert> b/icon/gd.vue
        """
        result = filter_files_from_diff(content, ["icon/"])
        assert "gd.vue" not in result
        assert "button.vue" not in result

    def test_filter_folder_with_file(self):
        """测试路径匹配"""
        content = """diff --git a/icon/gd.vue b/icon/gd.vue
index 1234567890abcdef1234567890abcdef12345678..1234567890abcdef1234567890abcdef12345678 100644
--- a/icon/gd.vue
<insert> b/icon/gd.vue
diff --git a/icon/button.vue b/icon/button.vue
--- a/icon/button.vue
<insert> b/icon/gd.vue
        """
        result = filter_files_from_diff(content, ["icon/button.vue"])
        assert "gd.vue" in result
        assert "button.vue" not in result

    def test_filter_when_file_in_diff_body(self):
        """当 diff 内容中包含匹配的结果时"""
        content = """diff --git a/icon/gd.vue b/icon/gd.vue
index 1234567890abcdef1234567890abcdef12345678..1234567890abcdef1234567890abcdef12345678 100644
package-lock.json asdasdas
--- a/icon/gd.vue
<insert> b/icon/gd.vue
diff --git a/icon/button.vue b/icon/button.vue
--- a/icon/button.vue
<insert> b/icon/gd.vue
        """
        result = filter_files_from_diff(content, ["package-lock.json"])
        assert "package-lock.json" in result
        assert "diff --git a/icon/gd.vue b/icon/gd.vue" in result


class TestParseMergeRequestUrl:
    """测试 parse_merge_request_url 函数"""

    def test_parse_merge_request_url(self):
        """测试解析 MR 地址"""
        url = "https://git.intra.gaoding.com/npm/gdicon-cli/-/merge_requests/7"
        project_id, mr_number = parse_merge_request_url(
            url, "https://git.intra.gaoding.com"
        )
        assert project_id == "npm%2Fgdicon-cli"
        assert mr_number == "7"

    def test_parse_merge_request_url_with_origin_url(self):
        """测试解析 MR 地址"""
        url = "https://git.gaoding.com/npm/gdicon-cli/-/merge_requests/7"
        project_id, mr_number = parse_merge_request_url(url, "https://git.gaoding.com")
        assert project_id == "npm%2Fgdicon-cli"
        assert mr_number == "7"
