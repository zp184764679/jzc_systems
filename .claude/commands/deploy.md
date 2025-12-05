---
description: 触发 GitHub Actions 自动部署
---

请执行部署流程：

1. 检查是否有未提交的更改 (`git status`)
2. 如果有更改，询问是否提交
3. 触发 GitHub Actions 部署 (`gh workflow run deploy.yml`)
4. 等待并报告部署状态
