# GitLab Merge Request Bot

GitLab Merge Request 工具集，提供 MR 摘要生成和周报功能。

## 🚀 CLI 使用方法

### 安装

```bash
# 开发模式安装
pip install -e .

# 或者正式安装
pip install .
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

#### 3. MR 摘要 (`merge`)

为指定的 MR 生成 AI 摘要并添加评论：

```bash
gitlab-merge-request-bot merge <MR_URL>
```

**示例：**

```bash
gitlab-merge-request-bot merge https://git.intra.gaoding.com/hex/hex-editor/-/merge_requests/8191
```

#### 4. 创建 MR 并自动分析 (`create`)

创建 Merge Request 并自动生成 AI 摘要：

```bash
gitlab-merge-request-bot create [TARGET_BRANCH] [ASSIGNEE]
```

**功能说明：**

- 推送当前分支到远程仓库
- 使用 `glab` CLI 工具创建 MR（草稿状态）
- 自动调用 AI 分析并添加摘要评论

**参数：**

- `TARGET_BRANCH`（可选）：目标分支，默认为 `master`
- `ASSIGNEE`（可选）：指派人，默认使用环境变量 `GITLAB_USER`

**示例：**

```bash
# 创建到 master 分支的 MR
gitlab-merge-request-bot create

# 创建到 dev 分支的 MR
gitlab-merge-request-bot create dev

# 创建 MR 并指定指派人
gitlab-merge-request-bot create dev username
```

**前置条件：**

- 需要安装并配置 `glab` CLI 工具
- 确保当前分支有待推送的更改

### 帮助信息

```bash
# 查看所有命令
gitlab-merge-request-bot --help

# 查看特定命令帮助
gitlab-merge-request-bot version --help
gitlab-merge-request-bot weekly --help
gitlab-merge-request-bot merge --help
gitlab-merge-request-bot create --help
```

## 🔧 开发模式

### 直接运行模块

开发阶段可以直接运行模块，运行之前需要在 shell 上配置环境变量

`export PYTHONPATH="${PYTHONPATH}:./src"`

### Unit test

#### 运行所有测试

```bash
pytest tests/
```

#### 运行详细模式

```bash
pytest tests/test_util.py -v
```

#### 运行特定测试

```bash
pytest tests/test_util.py::TestFilterFilesFromDiff::test_filter_single_file -v
```

#### watch mode

```bash
ptw -- -s
```

## 📋 环境配置

在使用之前，请确保配置了必要的环境变量：

- **GitLab 访问令牌**：用于访问 GitLab API
- **OpenAI API 密钥**：用于 AI 摘要生成

### 必需的环境变量

| 环境变量              | 说明                  | 必需程度        |
| --------------------- | --------------------- | --------------- |
| `GITLAB_BASE_URL`     | GitLab 实例的基础 URL | 必需            |
| `GITLAB_ACCESS_TOKEN` | GitLab 访问令牌       | 必需            |
| `OPENAI_API_KEY`      | OpenAI API 密钥       | 必需            |
| `GITLAB_ASSIGNEE`     | GitLab 用户名         | create 命令可选 |

### 外部工具依赖

#### glab CLI（create 命令必需）

`create` 命令依赖 GitLab 官方 CLI 工具 `glab`：

```bash
# macOS
brew install glab

# 其他平台参考：https://gitlab.com/gitlab-org/cli
```

配置 `glab`：

```bash
# 认证到你的 GitLab 实例
glab auth login

# 验证配置
glab api user
```

具体的环境变量配置请参考项目中的相关配置文件。
