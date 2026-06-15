# run_conformance.ps1 -- prove eBPF conformance on a Windows host, two layers:
#
#   (1) RUNTIME ISA conformance: run Alan-Jowett/bpf_conformance against the
#       eBPF-for-Windows execution plugins (bpf2c / JIT / interpreter). This is
#       what "passing the conformance suite on Windows" actually means -- it is a
#       property of the runtime's instruction-set implementation.
#
#   (2) PROGRAM verification: run PREVAIL (`netsh ebpf show verification`) over
#       AgentSight's own programs. This is the meaningful conformance gate for
#       *our* programs: it proves they are in the verifiable/conformant subset.
#
# Usage:
#   pwsh bpf\windows\conformance\run_conformance.ps1 `
#        -PluginPath "C:\Program Files\ebpf-for-windows\bpf2c_plugin.exe" `
#        -BuildDir   ".\build"
#
# Exit code is non-zero if either layer reports a failure, so CI can gate on it.
[CmdletBinding()]
param(
    [string]$PluginPath = $env:EBPF_CONFORMANCE_PLUGIN,
    [string]$BuildDir   = ".\build",
    [string]$ConformanceRepo = "https://github.com/Alan-Jowett/bpf_conformance.git",
    [string]$WorkDir    = "$env:TEMP\bpf_conformance"
)

$ErrorActionPreference = "Stop"
$failures = 0

function Section($t) { Write-Host "`n=== $t ===" -ForegroundColor Cyan }

# ---- Layer 1: runtime ISA conformance ---------------------------------------
Section "Layer 1: runtime ISA conformance (bpf_conformance)"
if (-not $PluginPath -or -not (Test-Path $PluginPath)) {
    Write-Warning "No conformance plugin found (set -PluginPath or `$env:EBPF_CONFORMANCE_PLUGIN)."
    Write-Warning "eBPF-for-Windows ships conformance plugins for bpf2c/JIT/interpreter."
    $failures++
} else {
    if (-not (Test-Path "$WorkDir\.git")) {
        git clone --depth 1 $ConformanceRepo $WorkDir
    }
    Push-Location $WorkDir
    try {
        cmake -B build -S . | Out-Host
        cmake --build build --config Release | Out-Host
        $runner = Get-ChildItem -Recurse -Filter "bpf_conformance_runner.exe" |
                  Select-Object -First 1
        if (-not $runner) { throw "bpf_conformance_runner.exe not built" }
        # The repo's own ISA test vectors are the authoritative set (mirrors the
        # Linux kernel reference). Our local vectors/ are added as smoke tests.
        $localVectors = Join-Path $PSScriptRoot "vectors"
        & $runner.FullName --test_file_directory "tests" --plugin_path $PluginPath
        if ($LASTEXITCODE -ne 0) { $failures++ }
        & $runner.FullName --test_file_directory $localVectors --plugin_path $PluginPath
        if ($LASTEXITCODE -ne 0) { $failures++ }
    } finally { Pop-Location }
}

# ---- Layer 2: AgentSight program verification (PREVAIL) ---------------------
Section "Layer 2: AgentSight program verification (netsh ebpf show verification)"
$programs = @(
    @{ obj = "process_win.o";  section = "process" },
    @{ obj = "sockaddr_win.o"; section = "cgroup/connect4" },
    @{ obj = "sockaddr_win.o"; section = "cgroup/connect6" },
    @{ obj = "sockops_win.o";  section = "sockops" }
)
foreach ($p in $programs) {
    $obj = Join-Path $BuildDir $p.obj
    if (-not (Test-Path $obj)) {
        Write-Warning "Missing $obj -- build the programs first (see ..\README.md)."
        $failures++
        continue
    }
    Write-Host "verify $($p.obj) :: $($p.section)"
    netsh ebpf show verification $obj $p.section | Out-Host
    if ($LASTEXITCODE -ne 0) { $failures++ }
}

Section "Summary"
if ($failures -eq 0) {
    Write-Host "PASS: runtime is ISA-conformant and all AgentSight programs verify." -ForegroundColor Green
    exit 0
} else {
    Write-Host "FAIL: $failures conformance/verification check(s) failed." -ForegroundColor Red
    exit 1
}
