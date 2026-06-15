#!/usr/bin/env pwsh
# build-windows.ps1 -- one-shot Windows build for AgentSight.
#
# Mirrors the Linux `make build` for the Windows port: builds the collector, the
# TLS Detours shim, and the eBPF-for-Windows programs, then (optionally) verifies
# them. Run from the repo root in a Developer PowerShell.
#
#   pwsh ./build-windows.ps1 [-SkipEbpf] [-Verify]
[CmdletBinding()]
param(
    [switch]$SkipEbpf,
    [switch]$Verify,
    [string]$EbpfInclude = $env:EBPF_FOR_WINDOWS_INCLUDE
)
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
New-Item -ItemType Directory -Force "$root\build" | Out-Null

Write-Host "==> Collector (cargo, MSVC target)" -ForegroundColor Cyan
Push-Location "$root\collector"
cargo build --release --target x86_64-pc-windows-msvc
Pop-Location

Write-Host "==> Native producers (Detours shim, eBPF loader, ConPTY stdio, ETW file)" -ForegroundColor Cyan
$toolchain = "$env:VCPKG_INSTALLATION_ROOT\scripts\buildsystems\vcpkg.cmake"
Push-Location "$root\shim"
cmake -B build -S . -DCMAKE_TOOLCHAIN_FILE="$toolchain"
cmake --build build --config Release
Pop-Location

if (-not $SkipEbpf) {
    Write-Host "==> eBPF-for-Windows programs (clang -target bpf)" -ForegroundColor Cyan
    if (-not $EbpfInclude) {
        Write-Warning "EBPF_FOR_WINDOWS_INCLUDE not set; clang will fail to find ebpf headers."
    }
    foreach ($p in @("process_win","sockaddr_win","sockops_win")) {
        clang -target bpf -O2 -g -I "$root\bpf\windows" -I "$EbpfInclude" `
              -c "$root\bpf\windows\$p.bpf.c" -o "$root\build\$p.o"
        Write-Host "    built build\$p.o"
    }
}

if ($Verify) {
    Write-Host "==> Conformance + verification" -ForegroundColor Cyan
    pwsh "$root\bpf\windows\conformance\run_conformance.ps1" -BuildDir "$root\build"
}

Write-Host "Done." -ForegroundColor Green
