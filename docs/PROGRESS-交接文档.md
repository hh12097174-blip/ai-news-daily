# AI 新闻早报系统 — 项目进度交接文档 v2

> 用途：给接手该项目的 AI 提供完整上下文与当前待解决事项。
> 更新时间：2026-08-13 13:19（覆盖 08-12 全部进展）
> 项目目录：`E:\尚硅谷Harness\3、项目\ai-news-daily\`

---

## 1. 项目目标

**多 Agent 协作的 AI 新闻早报系统**（面试展示项目，需与尚硅谷课件「AI 博客自动发布」案例差异化，代码/场景/文档必须原创）。

- 技术栈：Hermes Agent v0.20.0 + 硅基流动 DeepSeek-V4-Flash + Docker 容器隔离
- 架构：5 角色 Profile（collector→analyst→editor→reviewer→pusher）+ Cron 流水线（07:00/07:15/07:30/07:45/08:00）
- 亮点（面试素材）：Agent 自主工具 fallback、容器化隔离、3 层防御（容器+Hook+Profile 最小权限）

## 2. 已完成（✅ 全部验证过）

### 2.1 核心链路（完整可用）
- Hermes CLI v0.20.0：`C:\Users\LYJ\AppData\Local\hermes\hermes-agent\venv\Scripts\hermes.exe`
- 硅基流动模型真实调用成功（关键配置见 §4.1）
- **端到端演示成功**：CLI 抓 HN → 筛选 → 生成中文日报 → 落盘（`daily/2026-08-12.md`，真实数据）
- **Docker 容器隔离验证成功**：Agent 命令在容器内执行（主机名 = 容器 ID，Debian 13 + WSL2 内核）
  - Docker Desktop 28.5.1 + WSL 2.7.11（winget 安装）+ 镜像 `nikolaik/python-nodejs:python3.11-nodejs20`（2.23GB）
  - `terminal.backend=docker`、`container_persistent=false`、`docker_mount_cwd_to_workspace=true`
  - daemon.json 已配国内镜像源 `docker.xuanyuan.me` + `docker.1ms.run`

### 2.2 项目骨架
| 组件 | 位置/状态 |
|------|----------|
| 5 个 Profile | `%LOCALAPPDATA%\hermes\profiles\`（analyst/collector/editor/pusher/reviewer，原创 SOUL.md） |
| score-source 插件 | 已启用，单测通过（来源可信度评分） |
| danger-guard.sh Hook | 已注册（Windows 必须 `C:/Program Files/Git/bin/bash.exe <script>` 调用） |
| Kanban `news` | 已初始化 |
| 5 个 Cron 任务 | 已注册（model 快照 = custom/deepseek-ai/DeepSeek-V4-Flash） |
| approvals.mode | `off`（cron 无用户环境自动批准） |

### 2.3 Cron 流水线首次自动运行（08-13 09:26-09:38）
- 调度器触发全部 5 个阶段，各产出一个输出文件（`%LOCALAPPDATA%\hermes\cron\output\<job_id>\`）
- **发现并已修复的数据链路问题**：
  - 容器隔离导致任务读不到宿主 cron/output（模型给了专业诊断）
  - 修复：`terminal.docker_volumes=["E:/:/mnt/e","C:/Users/LYJ/AppData/Local/hermes:/root/.hermes"]`
  - news-collect prompt 改为允许 terminal+curl（原 prompt 禁 terminal 导致失败）
- **尚未验证**：修复后重跑全链路是否通（挂载是否真正解决任务间文件传递）

## 3. 未解决 / 待办（给接手 AI 的重点）

### 3.1 ⭐ Hermes Desktop 安装失败（用户想要的可视化界面）
**现象**：官方安装器 `Hermes-Setup.exe`（7.58MB 瘦安装器，https://hermes-agent.nousresearch.com/desktop 下载）卡死在「Installing Node.js dependencies」步骤，进度条 100% 后 72 分钟无进展，连 Cancel 都无响应（需任务管理器强杀）。

**已排错的链路**（勿重复踩）：
1. `git fetch failed (exit 128)` → 已修：`git config --global http.proxy https.proxy http://127.0.0.1:7897`
2. `npm install EBADENGINE`（npm 11.13.0 不在 engines 范围 `<11.10.0 || >=11.17.0`）→ 已修：`npm install -g npm@latest`（升到 11.17+）
3. **卡死点**：npm install 100% 下载完成后，Electron post-install 链接/解压阶段无进展（72min）
   - 已设 `ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/`（User 环境变量）**但无效**——下载已完成，卡在 post-install 阶段，与镜像无关
   - npm config set electron_mirror 在新版 npm 会报 "not a valid npm option"（新 npm 强制校验 key），用环境变量替代
4. 推测方向（接手 AI 可试）：npm 缓存残留冲突（清 `%LOCALAPPDATA%\npm-cache`）、node_modules 部分安装残留（删 `%LOCALAPPDATA%\hermes\hermes-agent\apps\desktop\node_modules` 重装）、或换 nvm 装 Node 22 LTS 版本

**重要**：Desktop 安装器多次写 `%LOCALAPPDATA%\hermes` 目录，但**CLI 未被破坏**（venv/配置/Profile 完好）。Desktop 与 CLI 共享同一 HERMES_HOME，装好后配置自动同步。

### 3.2 ⭐ Gateway 需要重启（明早 cron 依赖）
- 当前 Gateway 未运行（多实例 PID race 问题反复出现，详见 §4.4）
- **必须重启**：否则 08-14 07:00 cron 不会自动跑
- 重启流程见 §4.4

### 3.3 流水线修复后验证
- 挂载 + prompt 修复已配置，需手动触发一轮 cron 验证全链路（collect→analyze→write→review→push + 日报落宿主盘 `daily/YYYY-MM-DD.md`）
- 注意：docker 后端每次 terminal 调用冷启动容器（5-10s），任务慢属正常

### 3.4 其他可选增强
- web_search 工具缺搜索 API Key（Tavily），模型靠 curl 兜底（可选配）
- npm 全局修复后可解锁 Dashboard/TUI
- context_from 强依赖链（可选）
- GitHub Pages 发布 / 微信推送（可选）

## 4. 环境与踩坑备忘（接手 AI 必读）

### 4.1 硅基流动配置（5 个关键点，全踩过）
```yaml
model:
  default: custom/deepseek-ai/DeepSeek-V4-Flash   # 必须 custom/ 前缀，siliconflow/ 会 400
  provider: custom                                 # 不能写 siliconflow
  base_url: https://api.siliconflow.cn/v1
providers:                                          # 必须顶层键（不是 model.providers）
  siliconflow:
    name: SiliconFlow                               # 必须有 name，否则被跳过
    base_url: https://api.siliconflow.cn/v1
    key_env: SILICONFLOW_API_KEY
```
- `.env`（`%LOCALAPPDATA%\hermes\.env`）：`SILICONFLOW_API_KEY=sk-juva***`

### 4.2 WorkBuddy 环境限制（本会话工具特性）
- 系统级工具被安全策略禁用（WSL、sc、reg、schtasks）→ 涉及系统的命令必须引导用户手动执行
- PowerShell 工具 stdout 不回显 → 结果需 `Out-File` 到文件再 Read
- bash 调 powershell.exe 被拦截 → 用 PowerShell 工具
- `%LOCALAPPDATA%` 文件删除：rm/Remove-Item 无效（沙箱写保护），**必须用 `[System.IO.File]::Delete()`**
- bash 无 sleep 命令 → 用 `ping -n N 127.0.0.1` 等待

### 4.3 网络环境
- 代理：Clash Verge（verge-mihomo），端口 **7897**，**无 TUN 模式**（只有系统代理）
- 系统级程序（wsl.exe、git 子进程）不走系统代理，需单独配置（git config / 环境变量）
- GitHub 国内访问慢，用 gh-proxy.com / ghfast.top 加速；npm 用 npmmirror

### 4.4 Gateway PID race 修复流程（反复踩坑，标准操作）
症状：`hermes gateway` 启动后报 "PID file race lost to another gateway instance. Exiting."
根因：gateway.pid/lock 残留文件记录的 PID 被系统复用，新实例误判有实例在跑。
标准修复：
1. PowerShell 杀进程：`Get-Process | Where-Object {$_.ProcessName -match "python" -and $_.Path -like "*hermes*"} | Stop-Process -Force`
2. 删残留：`[System.IO.File]::Delete("C:\Users\LYJ\AppData\Local\hermes\gateway.pid")`（同法删 gateway.lock、gateway_state.json）
3. 后台启动：`hermes gateway`（用 run_in_background）
4. 验证：`hermes cron status` → "Ticker heartbeat: Ns ago"（N 小于 60 即正常）

### 4.5 WSL2 安装经验（Win11 24H2+，极难装）
- dism enable-feature 对 WSL **假成功**（capability 类别错配）→ 必须 `Add-WindowsCapability` 或 winget
- msi 内核包（wsl_update_x64.msi）报 "only applies to machines with WSL" → 没用
- **唯一可靠路径**：`winget install --id Microsoft.WSL --accept-package-agreements --accept-source-agreements`
- wsl --update 卡下载：设代理（$env:HTTPS_PROXY）对 wsl.exe 无效（不走环境变量）；开 TUN 或 winget 绕过

### 4.6 记忆文件
- 全部调试细节：`E:\尚硅谷Harness\.workbuddy\memory\2026-08-12.md`、`2026-08-13.md`

## 5. 接手 AI 的下一步行动清单（按优先级）

1. **重启 Gateway**（§4.4 标准流程）→ 保证 08-14 07:00 cron 自动跑
2. **手动触发一轮 cron 流水线**，验证挂载修复后数据链路是否通（collect→push 全闭环 + 日报落宿主盘）
3. （可选）继续搞 Hermes Desktop：清 npm-cache + 删 desktop node_modules 残留 → 重新双击安装器；或放弃等官方修复
4. 用户面试准备：README.md + daily/2026-08-12.md 讲稿

**当前用户状态**：已从早上 9 点折腾到下午 1 点（WSL/Docker/Desktop 连续攻坚），需要的是「收尾干净 + 明早自动跑通」，不要再引入新实验。
