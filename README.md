# GitLab Merge Request Bot

GitLab Merge Request 工具集，提供 MR 摘要生成、代码审查和周报功能。

## 🌟 主要功能

### 📝 MR 摘要生成

- 自动生成 Merge Request 的变更摘要
- 支持增量分析，只分析新的 commit
- 智能识别变更类型和影响范围

### 🔍 AI 代码审查

- **全面分析**: 代码质量、安全性、性能、最佳实践
- **行级评论**: 精确定位问题到具体代码行
- **分级反馈**: Critical/Major/Minor/Suggestion 四个级别
- **智能建议**: 不仅指出问题，还提供解决方案

### 📊 周报统计

- 统计团队最近的 MR 活动
- 生成结构化的周报内容

## 🚀 CLI 使用方法

### 安装

```bash
# 开发模式安装
pip install -e .

# 或者正式安装
pip install .
```

### 环境配置

```bash
# GitLab 配置
export GITLAB_TOKEN="your_gitlab_token"
export GITLAB_BASE_URL="https://gitlab.com/api/v4"

# AI 配置 (OpenAI 或兼容 API)
export OPENAI_API_KEY="your_api_key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选
export OPENAI_MODEL="gpt-4"  # 可选，默认 gpt-3.5-turbo
```

### 命令

#### 1. 查看版本 (`version`)

显示当前版本信息：

```bash
gitlab-merge-request-bot version
```

#### 2. 获取周报 (`weekly`)

获取最近7天的 MR 摘要：

```bash
gitlab-merge-request-bot weekly
```

#### 3. 生成 MR 摘要 (`merge`)

为指定的 MR 生成摘要并评论：

```bash
gitlab-merge-request-bot merge <MR_URL>

# 示例
gitlab-merge-request-bot merge https://gitlab.com/your-project/-/merge_requests/123
```

#### 4. 🆕 AI 代码审查 (`code-review`)

对指定的 MR 进行全面的代码审查：

```bash
gitlab-merge-request-bot code-review <MR_URL>

# 示例
gitlab-merge-request-bot code-review https://gitlab.com/your-project/-/merge_requests/123
```

**代码审查功能特性**：

- 🔒 **安全分析**: SQL 注入、XSS、输入验证等安全问题检测
- ⚡ **性能检查**: 识别性能瓶颈和优化机会
- ✨ **代码质量**: 可读性、维护性、复杂度分析
- 🎨 **代码风格**: 命名规范、格式化建议
- 🧪 **测试建议**: 测试覆盖率和边界条件检查

#### 5. 创建 MR 并分析 (`create`)

创建新的 MR 并自动生成摘要：

```bash
gitlab-merge-request-bot create [target_branch] [assignee]

# 示例
gitlab-merge-request-bot create master john.doe
gitlab-merge-request-bot create develop
gitlab-merge-request-bot create  # 默认目标分支为 master
```

## 💡 代码审查示例

### 审查结果展示

**总体评论**:

```markdown
🤖 代码审查报告

📋 总体评估
代码质量良好，主要关注点：安全性和错误处理

💡 总体建议
1. 建议为所有的外部 API 调用添加超时和重试机制
2. 考虑使用参数化查询避免 SQL 注入风险
```

**行级评论**:

```markdown
🚨 **CRITICAL** - 🔒 SECURITY

这里存在 SQL 注入风险。直接拼接用户输入到 SQL 查询中是危险的。

💡 **建议**: 使用参数化查询：
SELECT * FROM users WHERE id = %s
```

更多详细信息请参考 [代码审查使用文档](./CODE_REVIEW_USAGE.md)。

## 🛠️ API 开发

项目提供了完整的 Python API，可以集成到其他应用中：

```python
from workflow.summary_merge_request import SummaryMergeRequest
from workflow.code_review import CodeReviewMergeRequest
from pocketflow import AsyncFlow

# MR 摘要
async def generate_summary(mr_url):
    flow = AsyncFlow(start=SummaryMergeRequest())
    result = await flow.run_async({"url": mr_url})
    return result

# 代码审查
async def review_code(mr_url):
    flow = AsyncFlow(start=CodeReviewMergeRequest())
    result = await flow.run_async({"url": mr_url})
    return result
```

## 📁 项目结构

```
src/
├── ai/                    # AI 相关模块
│   ├── auth.py           # AI 服务认证
│   ├── get_prompt.py     # Prompt 管理
│   └── prompt/           # Prompt 模板
│       ├── summary_merge_request.md
│       └── code_review.md
├── gitlab/               # GitLab API 集成
│   ├── auth.py          # GitLab 认证
│   ├── comment.py       # 评论和讨论功能
│   ├── merge_request.py # MR 操作
│   ├── diff_parser.py   # Diff 解析器
│   └── util.py          # 工具函数
├── workflow/            # 工作流模块
│   ├── summary_merge_request.py  # MR 摘要工作流
│   └── code_review.py           # 代码审查工作流
├── utils/               # 通用工具
└── cli.py              # 命令行接口
```

## 🔧 高级配置

### 自定义审查规则

可以通过修改 `src/ai/prompt/code_review.md` 来自定义审查标准：

```markdown
# 在 prompt 中添加特定的规则
- 检查函数长度不超过 50 行
- 确保所有公共方法都有文档字符串
- 验证错误处理的完整性
```

### 配置文件过滤

```python
# 在代码中配置跳过特定文件
skip_files = [
    "package-lock.json",
    "yarn.lock", 
    "*.min.js",
    "vendor/*"
]
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙋‍♂️ 支持

如果遇到问题或有功能建议，请：

1. 查看 [Issues](../../issues) 了解已知问题
2. 创建新的 Issue 描述问题或建议
3. 参考 [代码审查使用文档](./CODE_REVIEW_USAGE.md) 了解详细功能

## 🔗 相关链接

- [GitLab API 文档](https://docs.gitlab.com/api/)
- [OpenAI API 文档](https://platform.openai.com/docs/api-reference)
- [代码审查最佳实践](./CODE_REVIEW_USAGE.md)
