# Gitlab Merge Request Bot

这是一个 Gitlab 合并请求机器人，包含一些在工作中的 Workflow，目标是提供以下功能。

## Gitlab API 封装

项目中，`src/gitlab` 提供一些对 [Gitlab API](https://docs.gitlab.com/api/merge_requests/#get-single-merge-request-commits) 的封装，用于获取 Merge Request 信息。

1. 解析 URL，提取 project_id 与 merge_number
2. 获取 Merge Request raw diff
   1. 可传入 `files_to_filter` 忽略一些自动生成文件的 diff， 默认为 `pnpm-lock.yaml` 与 `package-lock.json`
3. 获取 Merge Request 提交记录
4. 获取 Merge Request diff
5. 获取两个 Commit Hash 之间的差异
6. 获取该用户下最近一周活跃的 Merge Request

## OPEN AI 封装

项目中，`src/ai` 提供一些对 OpenAI 的调用封装，兼容 OpenAI 的 Provider 都可以使用。

## Workflow 封装

项目中，`src/workflow` 提供一些工作流的封装

1. Merge Request，调用 AI 生成摘要
2. WIP：根据 Merge Request，生成 Code Review 建议并将修改意见评论到 Merge Request
3. 再次 Review，基于上一次生成的 Code Review 的 commit_hash，获取与最新的 commit_hash 之间的 Diff，继续生成 Code Review 建议并将修改意见提交到 Merge Request
