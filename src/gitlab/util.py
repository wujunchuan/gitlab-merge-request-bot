import json
import os
import re
from typing import List
from urllib.parse import quote


def get_skip_files():
    """获取跳过的文件列表"""
    skip_files = os.getenv("SKIP_FILES")
    if skip_files:
        return json.loads(skip_files)
    return ["pnpm-lock.yaml"]


def parse_project_name(project_name: str):
    """将项目名转义为 URL 编码"""
    return quote(project_name, safe="")


def parse_merge_request_url(url: str, origin_url: str | None = None):
    """
    输入 MR 地址，提取 project_id 与 mr_number
    """
    # Split URL by '/-/' to get the project path and MR number
    parts = url.split("/-/")
    if len(parts) != 2 or not parts[1].startswith("merge_requests/"):
        raise ValueError("Invalid merge request URL format")

    if origin_url is None:
        origin_url = os.getenv("GITLAB_BASE_URL")

    # Get project path (remove base URL)
    project_id = parse_project_name(parts[0].replace(f"{origin_url}/", ""))

    # Get MR number
    mr_number = parts[1].replace("merge_requests/", "")

    return project_id, mr_number


def filter_files_from_diff(
    content: str, files_to_filter: List[str] = ["pnpm-lock.yaml"]
) -> str:
    """过滤掉指定文件的 diff 内容"""
    if not content.strip():
        return content

    # 如果没有需要过滤的文件，直接返回原内容
    if not files_to_filter:
        files_to_filter = get_skip_files()

    if "diff --git" not in content:
        return content

    # 按 diff 头部分割内容
    diff_sections = content.split("diff --git")

    # 非标准 diff 格式时，返回原始内容
    if len(diff_sections) == 0:
        return content

    # 过滤掉指定文件的 sections
    filtered_sections = []

    for section in diff_sections:
        if not section.strip():
            # 空的section直接跳过
            continue

        # 检查是否应该过滤这个section
        should_filter = _should_filter_section(section, files_to_filter)

        if not should_filter:
            filtered_sections.append(section)

    # 重新组合内容
    if not filtered_sections:
        return ""

    # 第一个section前面需要加上 "diff --git"
    filtered_content = "diff --git" + "diff --git".join(filtered_sections)

    return filtered_content


def _should_filter_section(section: str, files_to_filter: List[str]) -> bool:
    """检查是否应该过滤这个diff section"""

    # 提取文件路径的正则表达式
    # 匹配 diff --git 头部的文件路径：a/path/to/file b/path/to/file
    path_pattern = r"^[\s]*a/(.+?)\s+b/(.+?)(?:\s|$)"

    # 查找section的第一行（包含文件路径信息）
    first_line = section.split("\n")[0].strip()

    match = re.match(path_pattern, first_line)
    if not match:
        # 如果无法匹配到标准的git diff格式，fallback到简单的文件名检查
        return _fallback_filter_check(section, files_to_filter)

    # 获取源文件和目标文件路径
    source_path = match.group(1)
    target_path = match.group(2)

    # 检查是否需要过滤
    for filter_file in files_to_filter:
        # 检查完整路径是否包含要过滤的文件名
        if _path_contains_file(source_path, filter_file) or _path_contains_file(
            target_path, filter_file
        ):
            return True

    return False


def _path_contains_file(file_path: str, filter_file: str) -> bool:
    """检查文件路径是否包含要过滤的文件"""

    # 方法1: 完全匹配文件名
    file_name = file_path.split("/")[-1]  # 获取文件名部分
    if file_name == filter_file:
        return True

    # 方法2: 文件名包含匹配（更宽松）
    if filter_file in file_name:
        return True

    # 方法3: 路径包含匹配（最宽松，用于处理目录等情况）
    if filter_file in file_path:
        return True

    return False


def _fallback_filter_check(section: str, files_to_filter: List[str]) -> bool:
    """备用的过滤检查方法，用于处理非标准格式"""

    # 在section的前几行中查找文件路径信息
    lines = section.split("\n")[:5]  # 只检查前5行

    for line in lines:
        # 查找包含文件路径的行
        if ("---" in line and ("a/" in line or "b/" in line)) or (
            "+++" in line and ("a/" in line or "b/" in line)
        ):
            for filter_file in files_to_filter:
                if filter_file in line:
                    return True

    return False


if __name__ == "__main__":
    content = """diff --git a/.github/workflows/npm-publish.yml b/.github/workflows/npm-publish.yml
deleted file mode 100644
index 2f1ed659af9a206d69c35742a566964eb3af2dde..0000000000000000000000000000000000000000
--- a/.github/workflows/npm-publish.yml
+++ /dev/null
@@ -1,170 +0,0 @@
-# This workflow will run tests using node and then publish a package to GitHub Packages when a release is created
-# For more information see: https://help.github.com/actions/language-and-framework-guides/publishing-nodejs-packages
-
-name: Node.js Package
-
-on:
-  push:
-    branches:
-      - master  # 新仓库主分支默认是 main，可替换为您的目标分支名称
-
-jobs:
-  check-pr:
-    runs-on: [ self-hosted ]
-    steps:
-      - uses: actions/checkout@v3
-
-      # 确认是 PR 合并
-      - name: Verify PR merge
-        run: |
-          if [[ "${{ github.event.head_commit.message }}" != "Merge pull request"* ]]; then
-            echo "This push is not from a PR merge. Skipping..."
-            exit 1
-          else
-            echo "This push is from a PR merge!"
-          fi
-
-
-  publish-npm:
-    needs: check-pr
-    runs-on: [ self-hosted ]  # 请不要修改执行的自托管 actions runner集群，该集群是默认提供的
-    steps:
-      - uses: actions/checkout@v3
-
-      - name: Set up Node.js
-        uses: actions/setup-node@v3
-        with:
-          node-version: '20'
-          registry-url: https://registry-npm.gaoding.com/
-        env:
-          NODE_AUTH_TOKEN: ${{secrets.NPM_TOKEN}}
-
-     # 缓存 npm 缓存目录
-      - name: Cache npm dependencies
-        uses: gd-actions/cache@v4.0.5
-        id: cache-node-modules
-        with:
-          path: node_modules
-          key: ${{ runner.os }}-node-node_modules-${{ hashFiles('package-lock.json') }}
-          restore-keys: |
-            ${{ runner.os }}-node-node_modules-
-
-
-      # 安装依赖
-      - name: Install dependencies
-        run: |
-          if [ "${{ steps.cache-node-modules.outputs.cache-hit }}" != "true" ]; then
-            echo "Cache miss, running npm ci..."
-            npm ci --audit=false --no-audit
-          else
-            echo "Cache hit, using cached node modules."
-          fi
-
-      - name: Compile Code
-        run: npm run build
-
-      - name: Publish package
-        run: npm publish
-        env:
-          NODE_AUTH_TOKEN: ${{secrets.NPM_TOKEN}}
-
-  release:
-    needs: publish-npm
-    runs-on: [ self-hosted ]
-    steps:
-      - uses: actions/checkout@v3
-
-      - name: Set up Node.js
-        uses: actions/setup-node@v3
-        with:
-          node-version: '20'
-          registry-url: https://registry-npm.gaoding.com/
-
-      - name: Get version from package.json
-        id: version
-        run: |
-          VERSION=$(node -p "require('./package.json').version")
-          echo "PACKAGE_VERSION=${VERSION}" >> $GITHUB_ENV
-          echo "Package version is: $VERSION"
-
-      # 检查并删除旧的 Tag 和 Release（如果存在）
-      - name: Check and delete existing Tag and Release
-        env:
-          GITHUB_TOKEN: ${{ secrets.ACTION_TOKEN }}
-        run: |
-          TAG="v-${{ env.PACKAGE_VERSION }}"
-
-          # 检查并删除旧 Release
-          RELEASE_ID=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
-            "https://git.gaoding.com/api/v3/repos/${{ github.repository }}/releases" | \
-            grep -B 2 "\"tag_name\": \"$TAG\"" | grep '"id":' | head -n 1 | awk '{print $2}' | tr -d ',')
-          if [ -n "$RELEASE_ID" ]; then
-            echo "Release $TAG exists with ID $RELEASE_ID. Deleting..."
-            curl -s -X DELETE -H "Authorization: token $GITHUB_TOKEN" \
-              "https://git.gaoding.com/api/v3/repos/${{ github.repository }}/releases/$RELEASE_ID"
-          else
-            echo "Release $TAG does not exist. Proceeding..."
-          fi
-
-
-          # 1. 删除本地 Tag（如果存在）
-          if git tag -l | grep -q "$TAG"; then
-            echo "Local Tag $TAG exists. Deleting..."
-            git tag -d $TAG
-          else
-            echo "Local Tag $TAG does not exist."
-          fi
-
-          # 2. 删除远程 Tag（如果存在）
-          if git ls-remote --tags origin | grep -q "refs/tags/$TAG"; then
-            echo "Remote Tag $TAG exists. Deleting..."
-            git push --delete origin $TAG
-          else
-            echo "Remote Tag $TAG does not exist."
-          fi
-
-          # 3. 更新远程仓库状态
-          echo "Fetching and pruning remote references..."
-          git fetch --prune
-
-      # 创建 Git Tag
-      - name: Create Git Tag
-        run: |
-          git config user.name "github-actions[bot]"
-          git config user.email "github-actions[bot]@users.noreply.github.com"
-          git tag v-${{ env.PACKAGE_VERSION }}
-          git push --force  origin v-${{ env.PACKAGE_VERSION }}
-
-      # 获取 PR 的完整 commits 信息
-      - name: Get all PR commit messages
-        id: set_output
-        run: |
-          PR_NUMBER=$(echo "${{ github.event.head_commit.message }}" | grep -oP '(?<=Merge pull request #)\d+')
-          if [ -z "$PR_NUMBER" ]; then
-            echo "No PR number found. Skipping..."
-            exit 1
-          fi
-
-          # 获取 PR 提交消息
-          PR_COMMITS=$(curl -s -H "Authorization: token ${{ secrets.ACTION_TOKEN }}" \
-            "https://git.gaoding.com/api/v3/repos/${{ github.repository }}/pulls/$PR_NUMBER/commits" | \
-            grep '"message":' | sed -E 's/.*"message": "(.*)",/\1/')
-
-          # 输出并将提交消息保存为环境变量
-          # 将提交消息保存到文件
-          echo "::set-output name=pr_commits::$PR_COMMITS"
-          echo "$PR_COMMITS"
-
-      # 创建 GitHub Release
-      - name: Create GitHub Release
-        uses: actions/create-release@v1
-        with:
-          tag_name: v-${{ env.PACKAGE_VERSION }}
-          release_name: v-${{ env.PACKAGE_VERSION }}
-          body: |
-            ## Changelog
-            ${{ steps.set_output.outputs.pr_commits }}
-          draft: false
-          prerelease: false
-        env:
-          GITHUB_TOKEN: ${{ secrets.ACTION_TOKEN }}
diff --git a/package-lock.json b/package-lock.json
index bc34b60648f650ba7b5b5b82dc084071f2c16dc1..36deb6395b30a73d3bed41a815c1be028c7253b0 100644
--- a/package-lock.json
+++ b/package-lock.json
@@ -1,12 +1,12 @@
 {
   "name": "@gaoding/gdicon-cli",
-  "version": "1.1.2",
+  "version": "1.2.0",
   "lockfileVersion": 3,
   "requires": true,
   "packages": {
     "": {
       "name": "@gaoding/gdicon-cli",
-      "version": "1.1.2",
+      "version": "1.2.0",
       "license": "UNLICENSED",
       "dependencies": {
         "bundle-require": "^3.1.0",
"""
    result = filter_files_from_diff(content, ["package-lock.json"])
    print(result)
