# 流水线与安全配置文档

## 一、Cron 流水线

5 个任务按阶段串联，调度器运行在 Gateway daemon 中（每 60s tick）。

| Job | 时间 | 职责 | 输入来源 |
|-----|------|------|---------|
| news-collect | 07:00 | 采集 15+ 条多源新闻 | 网络 |
| news-analyze | 07:15 | 聚类 + score_source 评分 + 筛选 6-8 条 | news-collect 输出文件 |
| news-write | 07:30 | 生成中文日报并落盘 | news-analyze 输出 |
| news-review | 07:45 | 质量审核（[PASS]/[BLOCK]） | news-write 日报 |
| news-push | 08:00 | 投递审核通过的日报 | news-review 结果 |

创建方式（CLI 版，通过文件传递衔接）：

```bash
hermes cron create "0 7 * * *"  "<collect prompt>"  --name news-collect --deliver local
hermes cron create "15 7 * * *" "<analyze prompt>" --name news-analyze --deliver local
# ...
```

> 升级为 `context_from` 强依赖链：在 hermes 会话中让 Agent 用 cronjob 工具
> 创建任务并指定 `context_from=<上游job_id>`，输出将自动注入下游 prompt。

## 二、容器化隔离（安全核心）

所有 Agent 终端命令在 Docker 容器中执行：

```bash
# 1. 配置终端后端为 docker
hermes config set terminal.backend docker

# 2. 拉取隔离镜像（含 Python 3.11 + Node 20）
docker pull nikolaik/python-nodejs:python3.11-nodejs20
```

config.yaml 中的相关配置：

```yaml
terminal:
  backend: docker
  docker_image: nikolaik/python-nodejs:python3.11-nodejs20
  container_cpu: 1
  container_memory: 5120
  container_disk: 51200
  container_persistent: false   # 容器用完即销毁，不留状态
  docker_mount_cwd_to_workspace: false  # 不挂载宿主机目录，双向隔离
```

**隔离效果**：Agent 执行 `rm -rf /`、恶意下载、提权尝试等命令时，
影响范围仅限一次性容器，宿主机文件系统与进程完全不受影响。

## 三、危险命令拦截（第二道防线）

即使配置了 docker 后端，仍建议保留 `pre_tool_call` Hook 做黑名单拦截，
形成纵深防御：

```yaml
hooks:
  pre_tool_call:
    - command: "~/.hermes/agent-hooks/danger-guard.sh"
      timeout: 5
```

拦截规则（脚本内容见 scripts/danger-guard.sh）：
- `rm -rf /`、`mkfs.*`、`shutdown`、`> /dev/sda` 等破坏性命令
- `DROP TABLE` 等数据库危险操作
- 未授权的 SSH / 外连行为

## 四、验证方法

```bash
hermes doctor                 # 整体健康检查
hermes config get terminal.backend   # 确认隔离后端生效
docker ps                     # 查看运行中的 Agent 容器
hermes cron tick              # 手动触发一次调度检查
```
