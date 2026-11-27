param(
    [Parameter(Mandatory = $true)]
    [string]$BinaryPath,
    [Parameter(Mandatory = $true)]
    [string]$OutputDir,
    [string]$AssetName = "agentsight-windows-x86_64.exe"
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $BinaryPath -PathType Leaf)) {
    throw "Missing Windows binary: $BinaryPath"
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$resolvedOutputDir = (Resolve-Path -LiteralPath $OutputDir).Path
$assetPath = Join-Path $resolvedOutputDir $AssetName
Copy-Item -LiteralPath $BinaryPath -Destination $assetPath -Force

$hash = (Get-FileHash -LiteralPath $assetPath -Algorithm SHA256).Hash.ToLowerInvariant()
$checksumPath = "$assetPath.sha256"
$checksumLine = "$hash  $AssetName`n"
[System.IO.File]::WriteAllText($checksumPath, $checksumLine, [System.Text.UTF8Encoding]::new($false))

Write-Output "Packaged $assetPath ($hash)"
