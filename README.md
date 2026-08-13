# AI News Daily — 多 Agent 协作的新闻早报系统

基于 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 框架实现的多 Agent 协作流水线，每天自动完成「新闻采集 → 智能筛选 → 日报成稿 → 质量审核 → 结果推送」全流程。

## 核心特性

- **多角色 Agent 协作**：5 个职责分离的 Profile（collector / analyst / editor / reviewer / pusher），各自拥有独立的人格设定、模型配置与工具权限
- **阶段化流水线**：通过 Cron + `context_from` 将 5 个阶段串联，前一阶段的输出自动成为后一阶段的输入
- **容器化隔离执行**：所有 Agent 终端操作在 Docker 容器中执行（`terminal.backend = docker`），宿主机零风险——即使 Agent 收到恶意指令或执行破坏性命令，也只影响隔离容器
- **来源可信度评分**：自研 Python 插件 `score_source`，对新闻来源进行权威度/时效性/历史准确率多维评分，供 analyst 排序决策
- **个性化学习**：通过 Hermes 持久记忆（Memory）记录用户关注领域，日报内容随使用自动倾斜
- **自维护技能库**：Agent 将日报编辑规范沉淀为 Skill，由 Curator 自动维护去重

## 架构设计

```
┌──────────────────────────────────────────────────────────┐
│  Cron 每日 07:00 启动                                     │
│                                                          │
│  collector ──► analyst ──► editor ──► reviewer ──► pusher│
│   (采集)      (筛选聚类)    (成稿)      (审核)     (推送)  │
│                                                          │
│  每阶段输出经 context_from 注入下一阶段                    │
│  所有终端命令在 Docker 容器内执行                          │
└──────────────────────────────────────────────────────────┘
```

### 角色设计

| Profile | 职责 | 模型 | 关键工具 |
|---------|------|------|---------|
| collector | 抓取多源新闻（HN / 知乎热榜 / 虎嗅），输出结构化列表 | deepseek-chat | web_search, web_extract |
| analyst | 主题聚类、重要性评估、低质剔除，调用来源评分插件 | deepseek-chat | score_source, terminal |
| editor | 生成中文日报（摘要 + 观点 + 延伸阅读） | deepseek-chat | patch, read_file |
| reviewer | 事实性 / 来源可靠性 / 格式检查，不达标打回 | deepseek-chat | check_facts(插件), kanban_comment |
| pusher | 日报投递（本地文件 / 邮件） | deepseek-chat | send_message, terminal |

### 流水线调度

| Cron | 时间 | 任务 | 上游输入 |
|------|------|------|---------|
| news-collect | 07:00 | 采集原始新闻 | — |
| news-analyze | 07:15 | 筛选 + 聚类 + 评分 | news-collect |
| news-write | 07:30 | 生成日报草稿 | news-analyze |
| news-review | 07:45 | 质量审核 | news-write |
| news-push | 08:00 | 推送最终日报 | news-review |

## 安全设计（重点）

Agent 框架最大的风险在于终端权限：模型可能被提示词注入、可能执行危险命令。本项目采用三层防护：

1. **容器隔离**：`terminal.backend = docker`，所有命令在 `nikolaik/python-nodejs` 镜像容器中运行，容器销毁即状态清除
2. **钩子拦截**：`pre_tool_call` Hook 对危险命令（`rm -rf /`、`DROP TABLE`、未授权 SSH 等）黑名单拦截
3. **最小权限**：每个 Profile 只启用业务必需工具集，pusher 禁用浏览器，collector 无文件写权限

## 快速开始

```bash
# 1. 配置模型 Provider（DeepSeek）
hermes model

# 2. 创建 5 个角色 Profile（见 docs/profiles-setup.md）
hermes profile create collector --clone
hermes profile create analyst --clone
# ... editor / reviewer / pusher

# 3. 切换终端到 Docker 后端
hermes config set terminal.backend docker

# 4. 安装自定义插件
hermes plugins enable score-source

# 5. 初始化 Kanban 看板并创建流水线 Cron（见 docs/pipeline-setup.md）
hermes kanban init
```

## 目录结构

```
ai-news-daily/
├── plugins/          # 自定义 Python 插件源码
│   └── score_source/ # 来源可信度评分插件
├── scripts/          # 辅助脚本
├── docs/             # 搭建文档（Profile / 流水线 / 安全）
└── README.md
```

## 技术栈

- **框架**：Hermes Agent v0.16（Python 3.11）
- **模型**：DeepSeek（低成本、推理强）
- **隔离**：Docker（nikolaik/python-nodejs 镜像）
- **存储**：SQLite（会话 / Kanban 任务板持久化）
