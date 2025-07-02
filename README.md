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

### 帮助信息

```bash
# 查看所有命令
gitlab-merge-request-bot --help

# 查看特定命令帮助
gitlab-merge-request-bot version --help
gitlab-merge-request-bot weekly --help
gitlab-merge-request-bot merge --help
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

具体的环境变量配置请参考项目中的相关配置文件。
