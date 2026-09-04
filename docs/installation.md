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

### Install with Homebrew

On Linux x86-64:

```bash
brew tap eunomia-bpf/tap
brew install eunomia-bpf/tap/agentsight
agentsight --version
```

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

### Install shell completions

AgentSight can generate completion scripts for Bash, Elvish, Fish, PowerShell,
and Zsh. For Fish, install the generated script for the current user:

```bash
mkdir -p "$HOME/.config/fish/completions"
agentsight completions fish > "$HOME/.config/fish/completions/agentsight.fish"
```

For Bash or Zsh, load a generated script in the current shell:

```bash
source <(agentsight completions bash)
source <(agentsight completions zsh)
```

Run `agentsight completions --help` to list every supported shell. Regenerate
an installed script after upgrading AgentSight so it matches the installed CLI.

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

### Install a release binary

GitHub Releases publish a Windows x86-64 executable (`agentsight-windows-x86_64.exe`)
along with a SHA-256 checksum file (`agentsight-windows-x86_64.exe.sha256`).
Download and verify the latest release:

```powershell
$installDir = Join-Path $env:LOCALAPPDATA 'Programs\AgentSight'
New-Item -ItemType Directory -Force -Path $installDir | Out-Null
$exe = Join-Path $installDir 'agentsight.exe'
$checksum = Join-Path $env:TEMP 'agentsight-windows-x86_64.exe.sha256'

$base = 'https://github.com/eunomia-bpf/agentsight/releases/latest/download'
Invoke-WebRequest "$base/agentsight-windows-x86_64.exe" -OutFile $exe
Invoke-WebRequest "$base/agentsight-windows-x86_64.exe.sha256" -OutFile $checksum

$expected = ((Get-Content -Raw $checksum).Trim() -split '\s+')[0].ToLowerInvariant()
$actual = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne $expected) {
  Remove-Item -LiteralPath $exe -Force -ErrorAction SilentlyContinue
  throw "SHA-256 mismatch: expected $expected, got $actual"
}
& $exe --version
```

For unreleased commits or custom builds, build
`collector/target/release/agentsight.exe` as described in
[Build From Source](build.md), or download the short-lived
`agentsight-windows-x86_64` CI artifact from a merged **Windows native**
workflow run via `gh run download`.

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

### Live process capture

The experimental Windows process backend uses ETW for an explicitly selected
PID. It records process creation and exit, including short-lived descendants
that may not appear in a snapshot:

```powershell
# Run this terminal as Administrator once for the capture session.
agentsight top --pid <pid>
```

Running `agentsight top` from a normal terminal stays on the existing snapshot
and agent-native session path. AgentSight does not request elevation or open a
UAC prompt on its own.

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

### Keep the tasks self-healing

The logon trigger and restart settings above only re-launch a task that failed to
start. A long-running task that is terminated while it is running (for example
`LastTaskResult = 0xC000013A`) returns to `Ready` and is not started again until
the next sign-in. A third per-user watchdog task covers that state. It runs at
sign-in and on a fixed repetition interval, starts only the Monitor or Bind task
whose process is actually missing, and leaves a healthy manual instance alone
when the process command lines are visible. It requires neither elevation nor
access to stored credentials.

Download the watchdog script and register it:

```powershell
$installDir = Join-Path $env:LOCALAPPDATA 'Programs\AgentSight'
$script = Join-Path $installDir 'agentsight-watchdog.ps1'
Invoke-WebRequest -UseBasicParsing `
  'https://raw.githubusercontent.com/eunomia-bpf/agentsight/master/scripts/agentsight-watchdog.ps1' `
  -OutFile $script
powershell -NoProfile -ExecutionPolicy Bypass -File $script `
  -Mode Register -IntervalMinutes 5
Start-ScheduledTask -TaskName 'AgentSight Health'
```

If you built AgentSight from source, use the repository copy of
`scripts/agentsight-watchdog.ps1` instead of downloading it, and re-register the
watchdog if you later move the script to another path. `-IntervalMinutes` accepts
1 to 60 minutes and defaults to 5.

Check the watchdog health read-only:

```powershell
Get-ScheduledTask -TaskName 'AgentSight Health' | Select-Object TaskName,State
(Get-ScheduledTaskInfo -TaskName 'AgentSight Health').LastTaskResult
```

Recent watchdog decisions and errors are appended to
`%LOCALAPPDATA%\AgentSight\watchdog.log`.

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
Unregister-ScheduledTask -TaskName 'AgentSight Health' -Confirm:$false
Unregister-ScheduledTask -TaskName 'AgentSight Monitor' -Confirm:$false
Unregister-ScheduledTask -TaskName 'AgentSight Bind' -Confirm:$false
```

Remove `AgentSight Health` first so it cannot restart the other tasks while you
clean up; running the watchdog script with `-Mode Unregister` does the same. The
script under `%LOCALAPPDATA%\Programs\AgentSight` and the log at
`%LOCALAPPDATA%\AgentSight\watchdog.log` can be deleted separately.

Removing startup units or tasks does not delete captures under
`~/.agentsight/monitor` or the locally stored Bind access key. Remove those
separately only when their data is no longer needed.
