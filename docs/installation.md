# Installation and Automatic Startup

This guide installs the portable AgentSight CLI for one user and keeps its
background processes running after restart.

`monitor` and `bind` have different jobs:

- `monitor` samples active agent sessions and writes weekly databases under
  `~/.agentsight/monitor`.
- `bind` serves the authenticated Node API and maintains the outbound Controller
  relay. The examples below listen only on `127.0.0.1:7395`; they do not expose a
  new LAN or public port.

The portable commands use native Claude, Codex, Gemini, OpenCode, and OpenClaw
session files on Windows, macOS, and Linux. The eBPF-backed `record` and debug
commands remain Linux-only and have additional privilege requirements.

## Linux

### Install a release binary

GitHub Releases publish Linux binaries for x86-64 and ARM64:

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

Before running the binary in a sensitive environment, compare its SHA-256
digest with the digest shown for that asset on the GitHub Release page. Ensure
`~/.local/bin` is in `PATH`, or keep using the absolute path.

### Start the monitor at boot

AgentSight creates and starts its systemd user unit:

```bash
"$HOME/.local/bin/agentsight" monitor install-service
systemctl --user is-enabled agentsight-monitor.service
systemctl --user is-active agentsight-monitor.service
```

On a headless machine, enable systemd user lingering so the unit starts during
boot without waiting for an interactive login:

```bash
loginctl enable-linger "$USER"
loginctl show-user "$USER" -p Linger --value
```

Some distributions require an administrator to enable lingering. The expected
final value is `yes`.

### Keep a bound Node running

Run the first binding interactively so you can open its URL in a trusted
browser:

```bash
"$HOME/.local/bin/agentsight" bind --no-open
```

The binding URL contains a bootstrap key. Treat it as a secret and do not paste
it into public logs. Stop the foreground command after the browser completes
binding; the key is stored in the user's platform config directory and is
reused across Node restarts.

When a browser sends a follow-up to a stopped Codex session, AgentSight reads
the session's recorded `cli_version` and prefers that exact installed Codex
standalone release. This avoids resuming a newer transcript with an older
global `codex` from a background service's `PATH`. If that release is no longer
installed, AgentSight falls back to `PATH`. Advanced installations can set
`AGENTSIGHT_CODEX_BIN`, `AGENTSIGHT_CLAUDE_BIN`, or `AGENTSIGHT_GEMINI_BIN` to
an explicit provider executable; these values are paths, not credentials.

For a headless remote host, forward its loopback port to the workstation that
runs the browser:

```bash
ssh -L 17400:127.0.0.1:7395 user@remote-host
```

In that SSH session, run:

```bash
"$HOME/.local/bin/agentsight" bind --no-open \
  --endpoint http://127.0.0.1:17400
```

Then open its URL on the workstation. If a persistent Bind service already
occupies the remote port 7395, stop it before this one-time pairing and start it
again afterward. The SSH tunnel is not needed once Controller relay is
registered. Choose another unused workstation port if 17400 is also occupied.

Create `~/.config/systemd/user/agentsight-bind.service`:

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

Enable and verify it:

```bash
systemctl --user daemon-reload
systemctl --user enable --now agentsight-bind.service
systemctl --user is-enabled agentsight-bind.service
systemctl --user is-active agentsight-bind.service
curl -fsS http://127.0.0.1:7395/api/v1/info
```

The public info response should say `"authorization_required":true`. A request
to `/api/v1/snapshot` without an access token should return HTTP `401`.

## Windows

### Install the native artifact

Until a Windows asset is attached to GitHub Releases, the repository's
successful **Windows native** workflow uploads `agentsight-windows-x86_64`.
Download the latest successful artifact with an authenticated GitHub CLI:

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

Actions artifacts are retained for a limited time. If none is available, build
`collector/target/release/agentsight.exe` as described in
[Build From Source](build.md). The merged-PR check above excludes successful
artifacts from unmerged pull-request heads, including in repositories that use
squash merges.

Optionally add the install directory to the user `PATH`:

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

New terminals see the updated `PATH`. Use the absolute executable path in the
current terminal.

### Start after sign-in

The built-in `monitor install-service` command currently targets Linux systemd.
On Windows, register two per-user scheduled tasks. They start after this user
signs in, run without elevation, restart after failures, and are allowed to run
on battery power:

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

Keep the Bind task at `RunLevel Limited`. Session discovery and read-only views
still work from an elevated process, but AgentSight deliberately refuses to
resume or message an agent from an elevated Windows process because the selected
provider executable is owned by the transcript user. Run Bind as that same
non-administrator user to enable messaging.

If this Windows machine has not been added to the hosted app, run
`agentsight bind` once in an interactive terminal before relying on the
background Bind task. Its binding URL also contains a secret bootstrap key.

Verify the tasks and API authorization boundary:

```powershell
Get-ScheduledTask -TaskName 'AgentSight Monitor','AgentSight Bind' |
  Select-Object TaskName,State
Get-Process agentsight
Get-NetTCPConnection -State Listen -LocalPort 7395
try {
  Invoke-WebRequest http://127.0.0.1:7395/api/v1/snapshot -TimeoutSec 5
} catch {
  [int]$_.Exception.Response.StatusCode  # expected: 401
}
```

## Upgrade or remove automatic startup

After replacing the installed binary, restart the Linux services with
`systemctl --user restart agentsight-monitor.service agentsight-bind.service`,
or restart both Windows scheduled tasks.

To remove automatic startup on Linux:

```bash
systemctl --user disable --now agentsight-monitor.service agentsight-bind.service
rm -f ~/.config/systemd/user/agentsight-monitor.service \
  ~/.config/systemd/user/agentsight-bind.service
systemctl --user daemon-reload
```

To remove the Windows tasks:

```powershell
Unregister-ScheduledTask -TaskName 'AgentSight Monitor' -Confirm:$false
Unregister-ScheduledTask -TaskName 'AgentSight Bind' -Confirm:$false
```

Removing startup units or tasks does not delete captures under
`~/.agentsight/monitor` or the locally stored Bind access key. Remove those
separately only when their data is no longer needed.
