# AI 技术博客自动发布系统

基于 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 框架实现的多 Agent 协作系统，**每天自动完成「选题采集 → 智能评估 → 原创撰写 → 质量审核 → 发布上线」全流程**，无人值守产出技术博客文章并部署到 GitHub Pages。

> 🌐 在线博客：https://hh12097174-blip.github.io/ai-news-daily/

## 核心特性

- **多角色 Agent 协作**：5 个职责分离的 Profile（collector / analyst / editor / reviewer / pusher）+ orchestrator 编排者，各自拥有独立人格（SOUL.md）、模型配置与工具权限
- **强依赖链流水线**：Cron + `context_from` 串行执行，前一阶段输出自动成为后一阶段输入，杜绝并行抢跑
- **容器化隔离执行**：所有 Agent 终端操作在 Docker 容器中执行（`terminal.backend = docker`），宿主机零风险——即使 Agent 收到恶意指令也只影响隔离容器
- **来源可信度评分**：自研 Python 插件 `score_source`（域名权威度 0-60 + 时效性 0-25 + 署名质量 0-15），供 analyst 选题决策
- **任务自动编排**：orchestrator profile + `kanban.auto_decompose`，看板自动把复杂任务拆解为多角色子任务图
- **持久记忆 + 自我进化**：Memory 记录写作风格与发布规范；Agent 完成后自动沉淀 Skill，由 Curator 维护
- **零成本运维监控**：No-Agent Cron 纯脚本健康检查（不消耗模型 token）

## 架构设计

```
┌──────────────────────────────────────────────────────────────┐
│  Cron 每日 07:00 启动（context_from 串行）                    │
│                                                              │
│  collector ──► analyst ──► editor ──► reviewer ──► pusher    │
│  (选题采集)   (评分筛选)   (原创文章)   (质量审核)   (发布GitHub)│
│                                                              │
│  orchestrator 拆解复杂任务 ──► Kanban 子任务图                 │
│  所有终端命令在 Docker 容器内执行（E: 盘挂载 /mnt/e）          │
│  blog-health-check（No-Agent）每日 09:00 监控仓库健康          │
└──────────────────────────────────────────────────────────────┘
```

### 角色设计

| Profile | 职责 | 模型 | 关键工具 |
|---------|------|------|---------|
| orchestrator | 任务拆解、角色指派、依赖编排 | DeepSeek-V4-Flash | kanban 全套 |
| collector | 采集 HN / IT之家等候选选题 | DeepSeek-V4-Flash | terminal(curl) |
| analyst | score_source 评分 + 选题简报 | DeepSeek-V4-Flash | score_source, delegate_task |
| editor | 撰写 1500-3000 字原创技术文章 | Qwen3-235B（写作强） | write_file, skill_manage |
| reviewer | 技术准确性/逻辑/时效/原创审核 | DeepSeek-V4-Flash | read_file |
| pusher | git 提交 + 发布 GitHub | DeepSeek-V4-Flash | terminal(git) |

### 流水线调度（context_from 强依赖链）

| Cron | 时间 | 任务 | 上游输入 |
|------|------|------|---------|
| blog-collect | 07:00 | 采集候选选题 | — |
| blog-analyze | 07:15 | 评分筛选 3 选题 | blog-collect |
| blog-write | 07:30 | 撰写原创文章 | blog-analyze |
| blog-review | 07:45 | 质量审核 | blog-write |
| blog-push | 08:00 | 发布 GitHub | blog-review |
| blog-health-check | 09:00 | 仓库健康监控（No-Agent） | — |

## 安全设计（重点）

Agent 框架最大风险是终端权限：模型可能被提示词注入、可能执行危险命令。本项目三层防护：

1. **容器隔离**：所有命令在 `nikolaik/python-nodejs` 容器运行，容器销毁即状态清除
2. **钩子拦截**：`pre_tool_call` Hook 对危险命令（`rm -rf`、`DROP TABLE` 等）黑名单拦截
3. **最小权限**：每个 Profile 只启用业务必需工具，orchestrator 禁用内容工具，pusher 只操作 content/posts/

## 功能覆盖（25 项能力矩阵）

| 能力 | 状态 | 能力 | 状态 |
|------|------|------|------|
| Profile 多角色 | ✅ 6 个 | Delegation 委派 | ✅ SOUL 指引 |
| Provider 多模型 | ✅ editor 差异化 | Kanban Swarm | ✅ 命令就绪 |
| SOUL.md 人格 | ✅ 原创 | Orchestrator | ✅ auto_decompose |
| Cron 流水线 | ✅ 5+1 任务 | Gateway | ✅ 调度器 |
| context_from | ✅ jobs.json 依赖链 | Hooks | ✅ danger-guard |
| Plugins | ✅ score_source | Memory | ✅ MEMORY.md |
| Curator | ✅ ENABLED | skill 沉淀 | ✅ SOUL 指引 |
| 上下文压缩 | ✅ 内置 | No-Agent Cron | ✅ 健康监控 |
| **Docker 隔离** | ✅ **独有** | GitHub Pages | ✅ 已上线 |

## 快速开始

```bash
# 1. 启动调度器
hermes gateway

# 2. 恢复流水线（默认暂停省 token）
hermes cron resume blog-collect

# 3. 手动跑单环节验证
hermes chat -q "你是博客选题采集员，抓 HN 输出候选选题"
```

## 目录结构

```
ai-news-daily/
├── index.html        # GitHub Pages 博客首页
├── content/posts/    # 自动生成的文章（Markdown）
├── plugins/
│   └── score_source/ # 原创来源评分插件
├── scripts/          # 辅助脚本 + 健康检查
├── docs/             # 搭建文档 + 交接 + 面试讲稿
└── daily/            # 早期新闻早报存档
```

## 技术栈

- **框架**：Hermes Agent v0.20.0（Python 3.11）
- **模型**：硅基流动 DeepSeek-V4-Flash / Qwen3-235B
- **隔离**：Docker（nikolaik/python-nodejs，WSL2 后端）
- **发布**：GitHub + GitHub Pages
- **存储**：SQLite（会话 / Kanban / Cron 持久化）
