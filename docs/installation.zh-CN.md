# 安装与开机启动

本手册把 AgentSight CLI 安装到当前用户目录，并让后台进程在重启后自动运行。

`monitor` 和 `bind` 的作用不同：

- `monitor` 采样活动 Agent session，并把每周数据库写入 `~/.agentsight/monitor`。
- `bind` 提供需要鉴权的 Node API，并维持出站 Controller relay。下文只监听
  `127.0.0.1:7395`，不会新增局域网或公网监听端口。

Windows、macOS 和 Linux 上的可移植命令可以读取 Claude、Codex、Gemini、OpenCode 和
OpenClaw 原生 session 文件。`record` 和基于 eBPF 的调试命令只支持 Linux，还需要额外权限。

## Linux

### 安装 Release 二进制

GitHub Release 提供 Linux x86-64 和 ARM64 二进制：

```bash
set -euo pipefail
case "$(uname -m)" in
  x86_64) asset=agentsight-x86_64 ;;
  aarch64|arm64) asset=agentsight-aarch64 ;;
  *) echo "unsupported architecture: $(uname -m)" >&2; exit 1 ;;
esac
mkdir -p "$HOME/.local/bin"
curl -fL --retry 3 \
  "https://github.com/eunomia-bpf/agentsight/releases/latest/download/$asset" \
  -o "$HOME/.local/bin/agentsight"
chmod 0755 "$HOME/.local/bin/agentsight"
"$HOME/.local/bin/agentsight" --version
```

在敏感环境运行前，请把下载文件的 SHA-256 与 GitHub Release 页面展示的对应资产摘要比较。
确保 `~/.local/bin` 在 `PATH` 中，否则继续使用绝对路径。

### 随系统启动 monitor

AgentSight 可以自动创建并启动 systemd user unit：

```bash
"$HOME/.local/bin/agentsight" monitor install-service
systemctl --user is-enabled agentsight-monitor.service
systemctl --user is-active agentsight-monitor.service
```

无人值守主机还应开启 systemd user linger，避免必须先 SSH 登录才启动：

```bash
loginctl enable-linger "$USER"
loginctl show-user "$USER" -p Linger --value
```

部分发行版要求管理员开启 linger；最终输出应为 `yes`。

### 让绑定的 Node 长期运行

第一次绑定先在前台运行，以便在可信浏览器中打开绑定 URL：

```bash
"$HOME/.local/bin/agentsight" bind --no-open
```

绑定 URL 包含 bootstrap key，必须按密钥处理，不能粘贴到公开日志。浏览器完成绑定后停止前台命令；
密钥保存在当前用户的平台配置目录中，Node 重启后继续复用。

对于无图形界面的远程主机，把它的 loopback 端口转发到运行浏览器的工作站：

```bash
ssh -L 17400:127.0.0.1:7395 user@remote-host
```

在这个 SSH session 中运行：

```bash
"$HOME/.local/bin/agentsight" bind --no-open \
  --endpoint http://127.0.0.1:17400
```

再在工作站打开它输出的 URL。如果常驻 Bind service 已占用远端 7395，先停止它，完成一次性配对后
再启动。Controller relay 注册完成后不再需要保留 SSH tunnel。如果工作站的 17400 也已占用，
请选择另一个未使用的本地端口，并同步修改 `--endpoint`。

创建 `~/.config/systemd/user/agentsight-bind.service`：

```ini
[Unit]
Description=AgentSight local Node API and Controller relay
Documentation=https://github.com/eunomia-bpf/agentsight
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
ExecStart=%h/.local/bin/agentsight --listen 127.0.0.1 bind --no-open --server-port 7395 --app-url https://app.agentsight.us/
Restart=on-failure
RestartSec=5
KillSignal=SIGTERM
UMask=0077
StandardOutput=null
StandardError=journal

[Install]
WantedBy=default.target
```

启用并验证：

```bash
systemctl --user daemon-reload
systemctl --user enable --now agentsight-bind.service
systemctl --user is-enabled agentsight-bind.service
systemctl --user is-active agentsight-bind.service
curl -fsS http://127.0.0.1:7395/api/v1/info
```

公开 info 应包含 `"authorization_required":true`；不带 access token 请求
`/api/v1/snapshot` 应返回 HTTP `401`。

## Windows

### 安装原生 artifact

在 GitHub Release 正式附带 Windows 资产之前，仓库成功的 **Windows native** workflow 会上传
`agentsight-windows-x86_64`。使用已登录的 GitHub CLI 下载最新成功 artifact：

```powershell
$repo = 'eunomia-bpf/agentsight'
$runs = gh run list --repo $repo --workflow windows.yml --limit 50 `
  --json databaseId,conclusion,headSha,url | ConvertFrom-Json
$run = $runs | Where-Object conclusion -eq 'success' | Where-Object {
  $prs = gh api -H 'Accept: application/vnd.github+json' `
    "repos/$repo/commits/$($_.headSha)/pulls" | ConvertFrom-Json
  $prs | Where-Object { $_.merged_at -and $_.base.ref -eq 'master' }
} | Select-Object -First 1
if (-not $run) { throw 'No successful merged Windows workflow was found.' }
$run | Select-Object databaseId,headSha,url

$download = Join-Path $env:TEMP 'agentsight-windows'
New-Item -ItemType Directory -Force -Path $download | Out-Null
gh run download $run.databaseId --repo $repo `
  --name agentsight-windows-x86_64 --dir $download

$installDir = Join-Path $env:LOCALAPPDATA 'Programs\AgentSight'
New-Item -ItemType Directory -Force -Path $installDir | Out-Null
Copy-Item (Join-Path $download 'agentsight.exe') $installDir -Force
& (Join-Path $installDir 'agentsight.exe') --version
```

Actions artifact 只保留有限时间。如果当前没有可下载的 artifact，请按照
[从源码构建](build.md)生成 `collector/target/release/agentsight.exe`。上面的 PR 合并状态检查会排除
尚未合并的 pull request head 所生成的成功 artifact，并兼容 squash merge。

可以把安装目录加入当前用户的 `PATH`：

```powershell
$installDir = Join-Path $env:LOCALAPPDATA 'Programs\AgentSight'
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$parts = @($userPath -split ';' | Where-Object { $_ })
if ($parts -notcontains $installDir) {
  [Environment]::SetEnvironmentVariable(
    'Path', (($parts + $installDir) -join ';'), 'User'
  )
}
```

新终端会读取更新后的 `PATH`；当前终端请继续使用绝对路径。

### 用户登录后自动启动

内置 `monitor install-service` 当前只支持 Linux systemd。Windows 使用两个用户级计划任务：
当前用户登录后启动、无需提权、失败后重启，并允许在电池供电时运行。

```powershell
$installDir = Join-Path $env:LOCALAPPDATA 'Programs\AgentSight'
$exe = Join-Path $installDir 'agentsight.exe'
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal = New-ScheduledTaskPrincipal `
  -UserId $currentUser -LogonType Interactive -RunLevel Limited
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $currentUser
$settings = New-ScheduledTaskSettingsSet `
  -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
  -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) `
  -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew

$monitor = New-ScheduledTaskAction -Execute $exe -Argument 'monitor' `
  -WorkingDirectory $installDir
$bind = New-ScheduledTaskAction -Execute $exe `
  -Argument '--listen 127.0.0.1 bind --no-open --server-port 7395 --app-url https://app.agentsight.us/' `
  -WorkingDirectory $installDir

Register-ScheduledTask -TaskName 'AgentSight Monitor' -Action $monitor `
  -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
Register-ScheduledTask -TaskName 'AgentSight Bind' -Action $bind `
  -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
Start-ScheduledTask -TaskName 'AgentSight Monitor'
Start-ScheduledTask -TaskName 'AgentSight Bind'
```

如果这台 Windows 机器还没有加入托管应用，请先在交互终端运行一次 `agentsight bind`，再依赖后台
Bind 任务。与 Linux 相同，绑定 URL 包含秘密 bootstrap key。

验证任务和 API 鉴权边界：

```powershell
Get-ScheduledTask -TaskName 'AgentSight Monitor','AgentSight Bind' |
  Select-Object TaskName,State
Get-Process agentsight
Get-NetTCPConnection -State Listen -LocalPort 7395
try {
  Invoke-WebRequest http://127.0.0.1:7395/api/v1/snapshot -TimeoutSec 5
} catch {
  [int]$_.Exception.Response.StatusCode  # 预期为 401
}
```

## 升级或删除自动启动

替换安装的二进制后，使用
`systemctl --user restart agentsight-monitor.service agentsight-bind.service`
重启 Linux 服务，或重启两个 Windows 计划任务。

删除 Linux 自动启动：

```bash
systemctl --user disable --now agentsight-monitor.service agentsight-bind.service
rm -f ~/.config/systemd/user/agentsight-monitor.service \
  ~/.config/systemd/user/agentsight-bind.service
systemctl --user daemon-reload
```

删除 Windows 计划任务：

```powershell
Unregister-ScheduledTask -TaskName 'AgentSight Monitor' -Confirm:$false
Unregister-ScheduledTask -TaskName 'AgentSight Bind' -Confirm:$false
```

删除 unit 或计划任务不会删除 `~/.agentsight/monitor` 下的采集数据，也不会删除本地保存的 Bind
access key。只有确认这些数据不再需要时，才单独删除。
