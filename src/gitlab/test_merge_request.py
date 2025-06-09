import os
from unittest.mock import Mock, patch

import pytest

from gitlab.merge_request import (
    Commit,
    get_merge_request_commits,
    get_merge_request_detail,
    get_merge_request_diff,
    get_merge_request_raw_diff,
    parse_merge_request_url,
)


class TestCommit:
    """测试 Commit 数据类"""

    def test_commit_dataclass_creation(self):
        """测试 Commit 数据类的创建"""
        commit = Commit(
            id="abc123",
            short_id="abc123",
            created_at="2023-01-01T00:00:00Z",
            parent_ids=["def456"],
            title="Test commit",
            message="Test commit message",
            author_name="Test Author",
            author_email="test@example.com",
            authored_date="2023-01-01T00:00:00Z",
            committer_name="Test Committer",
            committer_email="committer@example.com",
            committed_date="2023-01-01T00:00:00Z",
            trailers={},
            extended_trailers={},
            web_url="https://gitlab.com/project/commit/abc123",
        )

        assert commit.id == "abc123"
        assert commit.title == "Test commit"
        assert commit.author_name == "Test Author"
        assert isinstance(commit.parent_ids, list)
        assert isinstance(commit.trailers, dict)


class TestParseMergeRequestUrl:
    """测试 parse_merge_request_url 函数"""

    @patch.dict(os.environ, {"GITLAB_BASE_URL": "https://gitlab.example.com"})
    def test_parse_valid_url(self):
        """测试解析有效的MR URL"""
        url = "https://gitlab.example.com/group/project/-/merge_requests/123"
        project_id, mr_number = parse_merge_request_url(url)

        assert project_id == "group%2Fproject"
        assert mr_number == "123"

    @patch.dict(os.environ, {"GITLAB_BASE_URL": "https://gitlab.example.com"})
    def test_parse_nested_group_url(self):
        """测试解析嵌套组的MR URL"""
        url = "https://gitlab.example.com/group/subgroup/project/-/merge_requests/456"
        project_id, mr_number = parse_merge_request_url(url)

        assert project_id == "group%2Fsubgroup%2Fproject"
        assert mr_number == "456"

    def test_parse_invalid_url_format(self):
        """测试解析无效格式的URL"""
        invalid_urls = [
            "https://gitlab.example.com/group/project/issues/123",
            "https://gitlab.example.com/group/project/-/commits/abc123",
            "invalid-url",
            "https://gitlab.example.com/group/project",
        ]

        for url in invalid_urls:
            with pytest.raises(ValueError, match="Invalid merge request URL format"):
                parse_merge_request_url(url)

    @patch.dict(os.environ, {"GITLAB_BASE_URL": "https://gitlab.example.com"})
    def test_parse_url_missing_mr_number(self):
        """测试缺少MR编号的URL"""
        url = "https://gitlab.example.com/group/project/-/merge_requests/"
        project_id, mr_number = parse_merge_request_url(url)

        assert project_id == "group%2Fproject"
        assert mr_number == ""

    @patch.dict(os.environ, {"GITLAB_BASE_URL": "https://git.internal.company.com"})
    def test_parse_internal_gitlab_url(self):
        """测试解析内部GitLab实例的URL"""
        url = (
            "https://git.internal.company.com/team/awesome-project/-/merge_requests/789"
        )
        project_id, mr_number = parse_merge_request_url(url)

        assert project_id == "team%2Fawesome-project"
        assert mr_number == "789"


class TestGetMergeRequestDetail:
    """测试 get_merge_request_detail 函数"""

    @patch("gitlab.merge_request.requests.get")
    def test_get_merge_request_detail_success(self, mock_get):
        """测试成功获取MR详情"""
        # 模拟响应数据
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": 123,
            "title": "Test MR",
            "description": "Test description",
            "state": "opened",
            "author": {"name": "Test User", "username": "testuser"},
        }
        mock_get.return_value = mock_response

        result = get_merge_request_detail("group%2Fproject", "123")

        # 验证请求参数
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "projects/group%2Fproject/merge_requests/123" in args[0]
        assert "headers" in kwargs

        # 验证返回结果
        assert result["id"] == 123
        assert result["title"] == "Test MR"
        assert result["state"] == "opened"

    @patch("gitlab.merge_request.requests.get")
    def test_get_merge_request_detail_api_error(self, mock_get):
        """测试API请求错误"""
        mock_response = Mock()
        mock_response.json.side_effect = Exception("JSON decode error")
        mock_get.return_value = mock_response

        with pytest.raises(Exception):
            get_merge_request_detail("group%2Fproject", "123")


class TestGetMergeRequestRawDiff:
    """测试 get_merge_request_raw_diff 函数"""

    @patch("gitlab.merge_request.requests.get")
    @patch("gitlab.merge_request.filter_files_from_diff")
    def test_get_raw_diff_success(self, mock_filter, mock_get):
        """测试成功获取原始diff"""
        # 模拟响应
        mock_response = Mock()
        mock_response.content = b"diff --git a/file.py b/file.py\n+added line"
        mock_get.return_value = mock_response

        # 模拟过滤函数
        mock_filter.return_value = "filtered diff content"

        result = get_merge_request_raw_diff("group%2Fproject", "123")

        # 验证请求
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "projects/group%2Fproject/merge_requests/123/raw_diffs" in args[0]

        # 验证过滤函数调用
        mock_filter.assert_called_once_with(
            "diff --git a/file.py b/file.py\n+added line",
            ["pnpm-lock.yaml", "package-lock.json"],
        )

        assert result == "filtered diff content"

    @patch("gitlab.merge_request.requests.get")
    @patch("gitlab.merge_request.filter_files_from_diff")
    def test_get_raw_diff_custom_filter(self, mock_filter, mock_get):
        """测试自定义过滤文件列表"""
        mock_response = Mock()
        mock_response.content = b"diff content"
        mock_get.return_value = mock_response
        mock_filter.return_value = "filtered content"

        custom_filters = ["test.txt", "config.json"]
        get_merge_request_raw_diff("group%2Fproject", "123", custom_filters)

        # 验证过滤函数使用了自定义过滤列表
        mock_filter.assert_called_once_with("diff content", custom_filters)

    @patch("gitlab.merge_request.requests.get")
    def test_get_raw_diff_encoding_error(self, mock_get):
        """测试编码错误处理"""
        mock_response = Mock()
        mock_response.content = b"\xff\xfe invalid utf-8"
        mock_get.return_value = mock_response

        with pytest.raises(UnicodeDecodeError):
            get_merge_request_raw_diff("group%2Fproject", "123")


class TestGetMergeRequestDiff:
    """测试 get_merge_request_diff 函数"""

    @patch("gitlab.merge_request.requests.get")
    def test_get_diff_success(self, mock_get):
        """测试成功获取diff"""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "old_path": "file1.py",
                "new_path": "file1.py",
                "a_mode": "100644",
                "b_mode": "100644",
                "diff": "@@ -1,3 +1,4 @@\n def test():\n+    print('hello')\n     pass",
            }
        ]
        mock_get.return_value = mock_response

        result = get_merge_request_diff("group%2Fproject", "123")

        # 验证请求
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "projects/group%2Fproject/merge_requests/123/diffs" in args[0]
        assert "params" in kwargs

        # 验证返回结果
        assert len(result) == 1
        assert result[0]["old_path"] == "file1.py"
        assert result[0]["new_path"] == "file1.py"

    @patch("gitlab.merge_request.requests.get")
    def test_get_diff_empty_response(self, mock_get):
        """测试空的diff响应"""
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        result = get_merge_request_diff("group%2Fproject", "123")

        assert result == []


class TestGetMergeRequestCommits:
    """测试 get_merge_request_commits 函数"""

    @patch("gitlab.merge_request.requests.get")
    def test_get_commits_success(self, mock_get):
        """测试成功获取提交记录"""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "id": "abc123",
                "short_id": "abc123",
                "created_at": "2023-01-01T00:00:00Z",
                "parent_ids": ["def456"],
                "title": "Test commit",
                "message": "Test commit message",
                "author_name": "Test Author",
                "author_email": "test@example.com",
                "authored_date": "2023-01-01T00:00:00Z",
                "committer_name": "Test Committer",
                "committer_email": "committer@example.com",
                "committed_date": "2023-01-01T00:00:00Z",
                "trailers": {},
                "extended_trailers": {},
                "web_url": "https://gitlab.com/project/commit/abc123",
            }
        ]
        mock_get.return_value = mock_response

        result = get_merge_request_commits("group%2Fproject", "123")

        # 验证请求
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "projects/group%2Fproject/merge_requests/123/commits" in args[0]

        # 验证返回结果
        assert len(result) == 1
        assert result[0]["id"] == "abc123"
        assert result[0]["title"] == "Test commit"
        assert result[0]["author_name"] == "Test Author"

    @patch("gitlab.merge_request.requests.get")
    def test_get_commits_multiple_commits(self, mock_get):
        """测试获取多个提交记录"""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "id": "commit1",
                "short_id": "commit1",
                "title": "First commit",
                "author_name": "Author 1",
                "created_at": "2023-01-01T00:00:00Z",
                "parent_ids": [],
                "message": "First commit message",
                "author_email": "author1@example.com",
                "authored_date": "2023-01-01T00:00:00Z",
                "committer_name": "Author 1",
                "committer_email": "author1@example.com",
                "committed_date": "2023-01-01T00:00:00Z",
                "trailers": {},
                "extended_trailers": {},
                "web_url": "https://gitlab.com/project/commit/commit1",
            },
            {
                "id": "commit2",
                "short_id": "commit2",
                "title": "Second commit",
                "author_name": "Author 2",
                "created_at": "2023-01-02T00:00:00Z",
                "parent_ids": ["commit1"],
                "message": "Second commit message",
                "author_email": "author2@example.com",
                "authored_date": "2023-01-02T00:00:00Z",
                "committer_name": "Author 2",
                "committer_email": "author2@example.com",
                "committed_date": "2023-01-02T00:00:00Z",
                "trailers": {},
                "extended_trailers": {},
                "web_url": "https://gitlab.com/project/commit/commit2",
            },
        ]
        mock_get.return_value = mock_response

        result = get_merge_request_commits("group%2Fproject", "123")

        assert len(result) == 2
        assert result[0]["id"] == "commit1"
        assert result[1]["id"] == "commit2"
        assert result[0]["title"] == "First commit"
        assert result[1]["title"] == "Second commit"

    @patch("gitlab.merge_request.requests.get")
    def test_get_commits_empty_response(self, mock_get):
        """测试空的提交记录响应"""
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        result = get_merge_request_commits("group%2Fproject", "123")

        assert result == []

    @patch("gitlab.merge_request.requests.get")
    def test_get_commits_api_error(self, mock_get):
        """测试API错误"""
        mock_get.side_effect = Exception("Network error")

        with pytest.raises(Exception, match="Network error"):
            get_merge_request_commits("group%2Fproject", "123")


class TestIntegration:
    """集成测试"""

    @patch.dict(os.environ, {"GITLAB_BASE_URL": "https://gitlab.example.com"})
    @patch("gitlab.merge_request.requests.get")
    def test_full_workflow(self, mock_get):
        """测试完整工作流程"""

        # 设置mock响应
        def mock_requests_get(url, **kwargs):
            mock_response = Mock()
            if "merge_requests/123" in url and url.endswith("/123"):
                # MR详情
                mock_response.json.return_value = {
                    "id": 123,
                    "title": "Test MR",
                    "state": "opened",
                }
            elif "raw_diffs" in url:
                # 原始diff
                mock_response.content = b"diff --git a/test.py b/test.py\n+test content"
            elif "diffs" in url:
                # 结构化diff
                mock_response.json.return_value = [{"old_path": "test.py"}]
            elif "commits" in url:
                # 提交记录
                mock_response.json.return_value = [{"id": "abc123"}]
            return mock_response

        mock_get.side_effect = mock_requests_get

        # 解析URL
        url = "https://gitlab.example.com/test/project/-/merge_requests/123"
        project_id, mr_number = parse_merge_request_url(url)

        # 获取各种信息
        detail = get_merge_request_detail(project_id, mr_number)
        diff = get_merge_request_diff(project_id, mr_number)
        commits = get_merge_request_commits(project_id, mr_number)

        # 验证结果
        assert project_id == "test%2Fproject"
        assert mr_number == "123"
        assert detail["id"] == 123
        assert len(diff) == 1
        assert len(commits) == 1
