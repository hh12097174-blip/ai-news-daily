# Git 快照回滚操作手册

> 目的：防止其他 AI 或手动操作改坏系统，提供一键快照与回滚。
> 创建：2026-08-13

## 1. 两个仓库（都要保护）

| 仓库 | 位置 | 保护内容 |
|------|------|----------|
| **项目仓库** | `E:\尚硅谷Harness\3、项目\ai-news-daily\` | README、日报、文档、插件源码 |
| **Hermes 配置仓库** | `C:\Users\LYJ\AppData\Local\hermes\` | config.yaml、5 个 Profile、插件、Hook、Cron 任务、看板（**最致命**） |

两个仓库都已打快照标签：**`v1.0-before-ai`**

## 2. 每次让 AI 动手前（必做）

在**两个仓库**里各打一个快照标签（1 秒钟）：

```
cd C:\Users\LYJ\AppData\Local\hermes
git add -A && git commit -m "快照: <改什么> 之前" && git tag before-edit-$(date +%m%d-%H%M)

cd E:\尚硅谷Harness\3、项目\ai-news-daily
git add -A && git commit -m "快照: <改什么> 之前" && git tag before-edit-$(date +%m%d-%H%M)
```

## 3. 怀疑改坏了（检查）

```
cd C:\Users\LYJ\AppData\Local\hermes
git status          # 看哪些文件被改了
git diff            # 看具体改了什么
```

## 4. 一键回滚（改坏时）

**回到最近快照**（推荐，保留后续提交历史）：
```
git reset --hard before-edit-XXXX
```

**回到最初快照**（v1.0-before-ai）：
```
git reset --hard v1.0-before-ai
```

**只撤销某个文件的修改**：
```
git checkout -- <文件路径>
```

## 5. 安全须知

- **`.env`（API Key）永不提交**——已被 .gitignore 排除，回滚不会碰它
- **`git reset --hard` 不删未跟踪文件**（.env、日志、缓存安全）
- **千万别跑 `git clean -fdx`**——它会删掉所有未跟踪文件（包括 .env！）
- gitignore 已排除：源码(hermes-agent/)、venv、日志、缓存、会话、内置技能模板等（只跟踪配置资产）
- 两个仓库的 `user.name`/`user.email` 已设为 `LYJ`/`lyj@local`（无需全局配置）

## 6. 给其他 AI 的交接说明（复制给它）

> 本项目已用 git 管理，两处仓库：项目目录 和 C:\Users\LYJ\AppData\Local\hermes。
> 动手前先 `git add -A && git commit -m "改动前快照"`；
> 改完 `git status` 自检；
> 若需回滚用 `git reset --hard <tag>`。
> .env 含密钥已排除，绝对不要动它。
