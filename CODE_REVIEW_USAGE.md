# GitLab MR 代码审查功能

这个功能可以自动分析 Merge Request 的代码变更，使用 AI 进行代码审查，并将审查意见精确地添加到对应的代码行。

## 功能特性

### 🔍 全面的代码分析

- **代码质量**: 检查可读性、维护性、复杂度、重复代码
- **最佳实践**: 验证设计模式、SOLID 原则、错误处理
- **安全性**: 检查输入验证、SQL 注入、XSS 防护等安全问题
- **性能**: 识别性能问题和优化机会
- **测试覆盖**: 建议测试覆盖和边界条件

### 💬 智能评论系统

- **行级评论**: 精确定位到具体代码行
- **分级反馈**: Critical/Major/Minor/Suggestion 四个级别
- **分类标签**: Security/Performance/Quality/Style/Test 等类别
- **建设性建议**: 不仅指出问题，还提供解决方案

### 🚀 自动化集成

- **重复检测**: 避免重复评论同一个 MR
- **批量处理**: 支持多文件、多变更点的批量分析
- **日志记录**: 完整的操作日志，便于问题排查

## 使用方法

### 1. 基本用法

```bash
# 对指定的 MR 进行代码审查
python -m src.cli code-review <MR_URL>

# 示例
python -m src.cli code-review https://gitlab.com/your-project/-/merge_requests/123
```

### 2. 环境配置

确保设置了必要的环境变量：

```bash
# GitLab 配置
export GITLAB_TOKEN="your_gitlab_token"
export GITLAB_BASE_URL="https://gitlab.com/api/v4"

# AI 配置 (OpenAI 或兼容 API)
export OPENAI_API_KEY="your_api_key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选
export OPENAI_MODEL="gpt-4"  # 可选，默认 gpt-3.5-turbo
```

### 3. 支持的 GitLab 实例

- GitLab.com (gitlab.com)
- GitLab 私有部署实例
- GitLab SaaS

## 审查结果示例

### 总体评论

```markdown
🤖 代码审查报告

📋 总体评估
代码质量良好，但存在一些可以改进的地方。主要关注点包括错误处理和性能优化。

💡 总体建议
1. 建议为所有的外部 API 调用添加超时和重试机制
2. 考虑使用连接池来优化数据库连接性能
3. 建议增加单元测试覆盖率，特别是边界条件的测试

---
*此评论由 AI 代码审查助手自动生成*
```

### 行级评论示例

```markdown
🚨 **CRITICAL** - 🔒 SECURITY

这里存在 SQL 注入风险。直接拼接用户输入到 SQL 查询中是危险的。

💡 **建议**: 使用参数化查询或 ORM 来避免 SQL 注入：
```sql
SELECT * FROM users WHERE id = %s
```

```

## 工作流程

```mermaid
graph LR
    A[输入 MR URL] --> B[解析 MR 信息]
    B --> C[获取 diff 内容]
    C --> D[解析代码变更]
    D --> E[AI 代码分析]
    E --> F[生成审查意见]
    F --> G[创建行级评论]
    G --> H[完成审查]
```

### 详细步骤

1. **解析 MR**: 从 URL 提取项目 ID 和 MR 编号
2. **获取 diff**: 调用 GitLab API 获取代码变更
3. **解析变更**: 使用自定义 diff 解析器分析文件和行变更
4. **AI 分析**: 将格式化的 diff 发送给 AI 进行分析
5. **生成评论**: 将 AI 分析结果转换为结构化评论
6. **添加评论**: 使用 GitLab Discussions API 添加行级评论

## 自定义配置

可以通过修改代码来自定义审查行为：

### 调整审查重点

```python
# 在 src/workflow/code_review.py 中
class CodeReviewOptions:
    def __init__(
        self,
        skip_files: List[str] = None,          # 跳过的文件类型
        focus_on_security: bool = True,        # 重点关注安全性
        focus_on_performance: bool = True,     # 重点关注性能
        max_comments_per_file: int = 10,       # 每个文件最大评论数
        severity_threshold: str = "minor"      # 评论严重性阈值
    ):
        # 配置选项
```

### 修改审查 Prompt

编辑 `src/ai/prompt/code_review.md` 文件来调整 AI 的审查标准和风格。

## 最佳实践

### 1. 团队协作

- 将代码审查集成到 CI/CD 流水线中
- 设置审查规则和标准
- 定期更新审查 prompt 以适应团队需求

### 2. 审查质量

- 结合人工审查和 AI 审查
- 关注 AI 无法检测的业务逻辑问题
- 定期评估和改进审查效果

### 3. 性能优化

- 对大型 MR 可能需要分批处理
- 考虑设置文件大小和数量限制
- 合理设置 API 调用频率限制

## 故障排除

### 常见问题

1. **无法获取 MR diff**
   - 检查 GitLab token 权限
   - 确认 MR URL 格式正确
   - 验证网络连接

2. **AI 分析失败**
   - 检查 OpenAI API key 配置
   - 确认 API 配额和限制
   - 查看日志文件了解具体错误

3. **评论创建失败**
   - 确认 GitLab token 有评论权限
   - 检查 MR 是否已关闭或合并
   - 验证文件路径和行号的有效性

### 日志查看

```bash
# 查看代码审查日志
tail -f code_review.log

# 查看详细调试信息
export LOG_LEVEL=DEBUG
python -m src.cli code-review <MR_URL>
```

## 扩展开发

### 添加新的审查规则

1. 修改 `src/ai/prompt/code_review.md`
2. 在 `src/workflow/code_review.py` 中添加处理逻辑
3. 测试新规则的效果

### 支持新的编程语言

1. 在 prompt 中添加语言特定的规则
2. 更新 diff 解析器以支持语言特定的语法
3. 添加相应的测试用例

### 集成其他代码分析工具

可以结合 ESLint、Pylint、SonarQube 等工具的结果，提供更全面的代码审查。

## 贡献和反馈

欢迎提交 Issue 和 Pull Request 来改进这个工具！

主要改进方向：

- 支持更多编程语言的深度分析
- 改进 AI prompt 的准确性和相关性
- 优化性能和错误处理
- 增加更多自定义配置选项
