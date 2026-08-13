# Profile 搭建文档

本文档记录 AI News Daily 系统中 5 个角色 Profile 的创建与配置。

## 创建命令

```bash
hermes profile create collector --clone --description "负责抓取多源新闻,输出结构化列表"
hermes profile create analyst   --clone --description "负责聚类、评分、筛选候选新闻"
hermes profile create editor    --clone --description "负责生成中文日报"
hermes profile create reviewer  --clone --description "负责质量审核,不达标打回"
hermes profile create pusher    --clone --description "负责投递审核通过的日报"
```

`--clone` 会继承 default profile 的 config.yaml / .env / SOUL.md，之后逐个定制。

## 角色设定（SOUL.md）

每个 Profile 的 SOUL.md 定义了职责边界、输出格式、工作原则，位于
`~/.hermes/profiles/<name>/SOUL.md`。核心设计原则：

1. **职责单一**：collector 只采集不评价，analyst 只筛选不写作，reviewer 只审核不修改
2. **输出契约**：每个角色的输出格式在 SOUL.md 中硬性规定，保证流水线各阶段数据可解析
3. **交叉约束**：pusher 明确"只投递审核通过的日报"，阻断未审核内容外流

## 工具权限

生产环境建议按最小权限收紧（`hermes tools disable`）：

| Profile | 保留工具 | 禁用 |
|---------|---------|------|
| collector | web_search, web_extract | terminal, patch |
| analyst | score_source, read_file | browser, video_analyze |
| editor | read_file, patch, write_file | web_search, browser |
| reviewer | read_file, kanban_comment | terminal, web |
| pusher | read_file, terminal, send_message | web_search, browser |

## 验证

```bash
hermes profile list          # 查看全部 Profile
collector doctor             # 检查 collector Profile 健康状态
collector config get model.default
```
