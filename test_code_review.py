#!/usr/bin/env python3
"""
代码审查功能测试脚本

这个脚本用于测试代码审查功能的各个组件，包括：
1. Diff 解析器
2. 代码审查工作流
3. GitLab API 集成

使用方法：
python test_code_review.py
"""

import asyncio
import os
import sys

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from pocketflow import AsyncFlow

from gitlab.diff_parser import DiffParser, format_diff_for_review
from workflow.code_review import CodeReviewMergeRequest, call_llm_for_review


def test_diff_parser():
    """测试 diff 解析器"""
    print("🧪 测试 Diff 解析器...")

    # 示例 diff 内容
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

def new_function():
+    # TODO: 这里需要输入验证
+    user_input = input("Enter something: ")
+    query = f"SELECT * FROM users WHERE name = '{user_input}'"
+    return query
"""

    parser = DiffParser()
    files = parser.parse_diff(sample_diff)

    print(f"✅ 解析了 {len(files)} 个文件")

    for file in files:
        print(f"📁 文件: {file.new_path}")
        print(f"   - 新文件: {file.is_new_file}")
        print(f"   - 删除文件: {file.is_deleted_file}")
        print(f"   - 变更块数量: {len(file.hunks)}")

        for i, hunk in enumerate(file.hunks):
            print(
                f"   📝 变更块 {i + 1}: 新增 {hunk.new_count} 行，删除 {hunk.old_count} 行"
            )

    # 测试变更行提取
    changed_lines = parser.get_changed_lines(files)
    print("📊 变更行统计:")
    for file_path, lines in changed_lines.items():
        print(f"   {file_path}: {len(lines)} 行变更")
        for line_num, line_type, content in lines[:3]:  # 只显示前3行
            print(f"     行 {line_num} ({line_type}): {content[:50]}...")

    # 测试格式化输出
    formatted = format_diff_for_review(files)
    print(f"📄 格式化后的 diff 长度: {len(formatted)} 字符")

    return True


def test_llm_integration():
    """测试 LLM 集成（需要 API key）"""
    print("\n🤖 测试 LLM 集成...")

    # 检查环境变量
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  跳过 LLM 测试 - 未配置 OPENAI_API_KEY")
        return True

    # 简单的 diff 用于测试
    test_diff = """## 文件: src/test.py

### 变更块 @@ -1,3 +1,5 @@
+ def process_user_input(user_input):
+     query = f"SELECT * FROM users WHERE name = '{user_input}'"
+     return query
+ 
+ def main():
+     user_input = input("Enter name: ")
+     result = process_user_input(user_input)
+     print(result)
"""

    try:
        result = call_llm_for_review(test_diff)
        print("✅ LLM 响应成功")
        print(f"   - 总体摘要: {result.get('overall_summary', 'N/A')[:100]}...")
        print(f"   - 行级评论数量: {len(result.get('line_comments', []))}")
        print(f"   - 总体建议数量: {len(result.get('general_suggestions', []))}")

        # 显示第一个行级评论示例
        line_comments = result.get("line_comments", [])
        if line_comments:
            first_comment = line_comments[0]
            print(f"   - 示例评论: {first_comment.get('message', 'N/A')[:100]}...")

        return True
    except Exception as e:
        print(f"❌ LLM 测试失败: {e}")
        return False


async def test_code_review_workflow():
    """测试代码审查工作流（需要真实的 MR）"""
    print("\n🔄 测试代码审查工作流...")

    # 检查环境变量
    required_vars = ["GITLAB_TOKEN", "GITLAB_BASE_URL"]
    for var in required_vars:
        if not os.getenv(var):
            print(f"⚠️  跳过工作流测试 - 未配置 {var}")
            return True

    # 这里需要一个真实的 MR URL 进行测试
    # 在实际测试中，你需要替换为你的 MR URL
    test_mr_url = os.getenv("TEST_MR_URL")
    if not test_mr_url:
        print("⚠️  跳过工作流测试 - 未配置 TEST_MR_URL")
        print(
            "    设置示例: export TEST_MR_URL='https://gitlab.com/project/-/merge_requests/123'"
        )
        return True

    try:
        print(f"📝 测试 MR: {test_mr_url}")
        flow = AsyncFlow(start=CodeReviewMergeRequest())
        result = await flow.run_async({"url": test_mr_url})

        print(f"✅ 工作流执行成功: {result}")
        return True
    except Exception as e:
        print(f"❌ 工作流测试失败: {e}")
        return False


def test_environment():
    """测试环境配置"""
    print("🔧 检查环境配置...")

    required_vars = {
        "GITLAB_TOKEN": "GitLab API token",
        "GITLAB_BASE_URL": "GitLab base URL",
        "OPENAI_API_KEY": "OpenAI API key",
    }

    all_configured = True
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if value:
            masked_value = value[:8] + "..." if len(value) > 8 else value
            print(f"✅ {var}: {masked_value}")
        else:
            print(f"❌ {var}: 未配置 ({desc})")
            all_configured = False

    return all_configured


async def main():
    """主测试函数"""
    print("🚀 GitLab MR 代码审查功能测试")
    print("=" * 50)

    # 测试结果
    results = []

    # 1. 环境检查
    results.append(("环境配置", test_environment()))

    # 2. Diff 解析器测试
    results.append(("Diff 解析器", test_diff_parser()))

    # 3. LLM 集成测试
    results.append(("LLM 集成", test_llm_integration()))

    # 4. 工作流测试
    results.append(("代码审查工作流", await test_code_review_workflow()))

    # 输出测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1

    print(f"\n🎯 测试通过: {passed}/{total}")

    if passed == total:
        print("🎉 所有测试通过！代码审查功能准备就绪。")
        print("\n💡 使用方法:")
        print("   python -m src.cli code-review <MR_URL>")
    else:
        print("⚠️  部分测试失败，请检查配置和依赖。")


if __name__ == "__main__":
    asyncio.run(main())
