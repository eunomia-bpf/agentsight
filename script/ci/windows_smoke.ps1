param(
    [Parameter(Mandatory = $true)]
    [string]$BinaryPath,
    [string]$ExpectedVersion = ""
)

$ErrorActionPreference = 'Stop'

$agentsight = (Resolve-Path -LiteralPath $BinaryPath).Path
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path

$versionOutput = & $agentsight --version
if ($LASTEXITCODE -ne 0) {
    throw "agentsight --version failed with exit code $LASTEXITCODE"
}
$versionText = ($versionOutput | Out-String).Trim()
Write-Output $versionText
if ($ExpectedVersion -and $versionText -notmatch [regex]::Escape($ExpectedVersion)) {
    throw "Unexpected version output '$versionText' (expected '$ExpectedVersion')"
}

$tempBase = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { [System.IO.Path]::GetTempPath() }
$smokeRoot = Join-Path $tempBase ("agentsight-windows-smoke-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $smokeRoot | Out-Null

$originalHome = $env:HOME
$originalPath = $env:PATH
$bindProcess = $null

Push-Location $repoRoot
try {
    $env:HOME = Join-Path $smokeRoot "agentsight-home"
    $fixtureDir = Join-Path $env:HOME ".codex/sessions/2026/06/18"
    New-Item -ItemType Directory -Force -Path $fixtureDir | Out-Null
    $fixturePath = Join-Path $fixtureDir "public-agentpprof-fixture.jsonl"
    Get-Content "ext/pprof/examples/codex/sessions/2026/06/18/public-agentpprof-fixture.jsonl" |
        ForEach-Object {
            $record = $_ | ConvertFrom-Json
            if ($record.payload.cwd) {
                $record.payload.cwd = $PWD.Path
            }
            $record | ConvertTo-Json -Compress -Depth 100
        } |
        Set-Content -Encoding utf8NoBOM $fixturePath

    $snapshotPath = Join-Path $smokeRoot "agentsight-snapshot.json"
    & $agentsight report --local export --output $snapshotPath
    if ($LASTEXITCODE -ne 0) {
        throw "agentsight report --local export failed"
    }
    $snapshot = Get-Content -Raw $snapshotPath | ConvertFrom-Json
    if (-not ($snapshot.sessions | Where-Object agent_type -eq "codex")) {
        throw "agentsight report export did not discover the Windows Codex fixture"
    }

    & $agentsight top --plain --once
    if ($LASTEXITCODE -ne 0) {
        throw "agentsight top failed"
    }

    $visHtml = Join-Path $smokeRoot "agent-nebula.html"
    $visPng = Join-Path $smokeRoot "agent-nebula.png"
    & $agentsight vis . --output $visHtml --output $visPng
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $visHtml) -or -not (Test-Path $visPng)) {
        throw "agentsight vis browser smoke failed"
    }
    if (-not (Select-String -Quiet -SimpleMatch "agentpprof/src/main.rs" $visHtml)) {
        throw "agentsight vis did not render the Windows session fixture"
    }

    $fakeBin = Join-Path $smokeRoot "agentsight-fake-provider"
    New-Item -ItemType Directory -Force -Path $fakeBin | Out-Null
    @'
@echo off
node "%~dp0\codex.js" %*
'@ | Set-Content -Encoding ascii (Join-Path $fakeBin "codex.cmd")
    @'
const readline = require("readline");
const lines = readline.createInterface({ input: process.stdin });
lines.on("line", (line) => {
  const request = JSON.parse(line);
  if (request.id === 1 || request.id === 2) {
    console.log(JSON.stringify({ id: request.id, result: {} }));
  } else if (request.method === "turn/start") {
    console.log(JSON.stringify({ id: request.id, result: { turn: { id: "fake-turn" } } }));
    setTimeout(() => process.exit(0), 100);
  }
});
'@ | Set-Content -Encoding utf8NoBOM (Join-Path $fakeBin "codex.js")
    $env:PATH = "$fakeBin;$originalPath"

    $listener = [System.Net.Sockets.TcpListener]::new(
        [System.Net.IPAddress]::Loopback,
        0
    )
    $listener.Start()
    $bindPort = $listener.LocalEndpoint.Port
    $listener.Stop()

    $bindOut = Join-Path $smokeRoot "agentsight-bind.out"
    $bindErr = Join-Path $smokeRoot "agentsight-bind.err"
    $bindProcess = Start-Process `
        -FilePath $agentsight `
        -ArgumentList @(
            "--listen", "127.0.0.1", "bind", "--no-open",
            "--server-port", "$bindPort", "--app-url", "http://127.0.0.1:17400/"
        ) `
        -RedirectStandardOutput $bindOut `
        -RedirectStandardError $bindErr `
        -PassThru

    $bindBase = "http://127.0.0.1:$bindPort"
    $tokenPath = Join-Path $env:APPDATA "agentsight/access-token"
    $ready = $false
    for ($attempt = 0; $attempt -lt 80; $attempt++) {
        if ($bindProcess.HasExited) {
            throw "agentsight bind exited during startup"
        }
        if (Test-Path $tokenPath) {
            try {
                $publicInfo = Invoke-RestMethod -Uri "$bindBase/api/v1/info"
                if ($publicInfo.authorization_required -and -not $publicInfo.node) {
                    $ready = $true
                    break
                }
            } catch {
                # The listener may not have started yet.
            }
        }
        Start-Sleep -Milliseconds 250
    }
    if (-not $ready) {
        throw "agentsight bind did not expose its authenticated API"
    }

    $snapshotProbe = Invoke-WebRequest `
        -Uri "$bindBase/api/v1/snapshot" `
        -SkipHttpErrorCheck
    if ([int]$snapshotProbe.StatusCode -ne 401) {
        throw "agentsight bind exposed session data without a token"
    }

    $token = (Get-Content -Raw $tokenPath).Trim()
    $headers = @{ Authorization = "Bearer $token" }
    $info = Invoke-RestMethod -Uri "$bindBase/api/v1/info" -Headers $headers
    if (-not $info.node -or -not $info.capabilities.session_messages) {
        throw "agentsight bind returned incomplete Node capabilities"
    }

    $messageProbe = Invoke-WebRequest `
        -Uri "$bindBase/api/v1/sessions/agentpprof-public-fixture-session/messages" `
        -Method Post `
        -Headers $headers `
        -ContentType "application/json" `
        -Body '{"message":"windows bind smoke"}' `
        -SkipHttpErrorCheck

    $principal = [Security.Principal.WindowsPrincipal]::new(
        [Security.Principal.WindowsIdentity]::GetCurrent()
    )
    $elevated = $principal.IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator
    )
    if ($elevated) {
        if ([int]$messageProbe.StatusCode -ne 502 -or
            $messageProbe.Content -notmatch "elevated Windows") {
            throw "elevated agentsight bind did not fail closed before starting the provider"
        }
    } elseif ([int]$messageProbe.StatusCode -ne 202) {
        throw "agentsight bind did not submit through the Windows codex.cmd shim"
    }
} finally {
    if ($bindProcess -and -not $bindProcess.HasExited) {
        Stop-Process -Id $bindProcess.Id -Force
        Wait-Process -Id $bindProcess.Id -ErrorAction SilentlyContinue
    }
    Pop-Location
    $env:HOME = $originalHome
    $env:PATH = $originalPath
    if (Test-Path $smokeRoot) {
        Remove-Item -LiteralPath $smokeRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
