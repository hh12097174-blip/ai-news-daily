# 简历 · 项目描述（AI 博客自动发布系统）

> 复制到简历的项目经历部分。最新版：2026-08-18（Harness 能力前置 + 全量化数据）

---

2026-07 ~ 2026-08   AI 博客自动发布系统（基于 Hermes Agent 多智能体框架）

项目描述：   基于 Hermes Agent 框架构建的多 Agent 协作博客生产系统，5 个专业角色
        （collector / analyst / editor / reviewer / pusher）+ orchestrator 编排者
        协同完成「选题采集 → 智能评估 → 原创撰写 → 质量审核 → GitHub 自动发布」
        全流程；所有 Agent 终端操作在 Docker 容器内隔离执行，部署到 GitHub
        Pages 公开访问，全程无人值守。

职责描述：  • 框架级并行编排：利用 Hermes Kanban Swarm 一键生成「root → 2 个
        worker 并行 → verifier 验证 → synthesizer 汇总」协作拓扑，实测创建
        4 类节点完整任务图；orchestrator 启用 kanban.auto_decompose 自动
        拆解任务，6 个 Profile 角色由看板调度器统一派活

        • 强依赖链流水线：通过 Hermes context_from 机制搭建 5 阶段串行流水线
        （collect→analyze→write→review→push），4 条依赖链确保上游完成才
        触发下游，消除下游抢跑；5 个 Cron 任务每日 07:00 起定时触发，失败
        自动 SKIPPED 不伪造成功

        • 并行委派：analyst 通过 Hermes delegate_task 并行委派 2 个子 Agent
        分头调研，实测 2 个并行子任务同时启动，独立上下文互不污染；Agent
        在 web_search 工具不可用时自主降级 terminal+curl 抓取，非硬编码

        • 多模型差异化：基于 Hermes Provider 机制，从硅基流动 91 个可用模型
        中按角色选型——collector/analyst 用 DeepSeek-V4-Flash，editor 用
        GLM-5.2，2 套模型差异化部署，兼顾成本与质量

        • 持久记忆与自我进化：Hermes Memory 持久化博客写作风格/发布流程等
        长期规范；Agent 高质量产出后自动 skill_manage 沉淀写作 Skill；
        Curator 每 7 天自动去重归档失效技能，技能库持续迭代

        • 三层纵深安全防御：Docker 容器隔离，100% Agent 命令在
        nikolaik/python-nodejs 容器内执行，实测容器 ID 验证隔离，宿主机零
        风险；pre_tool_call Hook 黑名单拦截危险命令（rm -rf / DROP TABLE
        等）；6 个 Profile 最小权限收敛

        • 原创可信度评分插件：自研 Python 插件 score_source，3 维评分体系
        （域名权威度 0-60 + 时效性 0-25 + 署名质量 0-15，满分 100），内置
        22 个主流域名权威库 + 6 个黑名单域 + 标题党正则检测，全自动过滤
        低质选题

        • 多渠道交付与零成本运维：文章自动 git push 部署 GitHub Pages
        公开站点；No-Agent Cron 脚本每日 09:00 检查仓库健康，纯脚本零
        token 消耗

技术栈：    Hermes Agent v0.20 / Python 3.11 / DeepSeek-V4-Flash + GLM-5.2
        / Docker + WSL2 / GitHub Pages / SQLite
在线演示：  https://hh12097174-blip.github.io/ai-news-daily/
GitHub：   github.com/hh12097174-blip/ai-news-daily

---

## 数据真实性核对表（面试前自检）

| 数据 | 核实方式 |
|------|---------|
| 4 类节点任务图 | `hermes kanban list`（t_d5c4bb2c 及子任务） |
| 5 阶段 4 依赖链 | `%LOCALAPPDATA%\hermes\cron\jobs.json` |
| 2 个并行子任务 | 实测 delegate_task 返回 sa-0/sa-1 |
| 91 个模型 | 硅基流动 API /v1/models |
| 7 天 Curator | `hermes curator status` |
| 22 域名 + 6 黑名单 | plugins/score_source/__init__.py 数一遍 |
| 容器隔离实测 | 会话记录中容器 ID cea4948c7e89 |
