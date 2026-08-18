# Kanban 人工审批闭环（半自动协作）

> 用途：展示系统支持"人工在关键决策点介入"——Agent 自动干，人把关审批。
> 实测通过：2026-08-18

## 流程（4 步）

```
reviewer 发现问题 → kanban_block → 任务进入 blocked
        ↓
负责人查看审批意见 → kanban_comment（提出修改要求）
        ↓
审批通过 → kanban_unblock → 任务回 ready，writer 继续
```

## 实测命令记录

```bash
# 1. 创建任务
hermes kanban create "撰写深度学习文章" --assignee editor
# → Created t_a78647fc (ready, assignee=editor)

# 2. reviewer 审核发现问题，阻断任务（reason 为位置参数）
hermes kanban block t_a78647fc "第3节代码示例缺少try/catch异常处理，需修正后重新提交"
# → Blocked t_a78647fc
# → 状态: ⊘ blocked

# 3. 负责人复核并留言
hermes kanban comment t_a78647fc "已复核，同意修改意见"

# 4. 审批通过，解除阻断（writer 可继续修正）
hermes kanban unblock t_a78647fc
# → Unblocked
# → 状态: ▶ ready
```

## 面试讲法

> "我的系统不是完全黑盒自动化——设计上是'Agent 自动干，人在关键决策点把关'。
> 审核阶段 reviewer 发现质量问题会调用 kanban_block 把任务卡住，负责人（我）
> 看到 blocked 状态后留言审批意见，通过后 unblock 让流程继续。
> 这避免了 AI 单方面放行的风险，也是生产环境多 Agent 系统的常见设计。"

## 真实价值

- 质量兜底：AI 可能误判，人工是最后一道闸
- 可追溯：block 原因 + comment 意见都在看板留痕
- 与课件 3.6 节"人工审批"设计对齐
