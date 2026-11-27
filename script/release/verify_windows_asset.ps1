param(
    [Parameter(Mandatory = $true)]
    [string]$AssetPath,
    [Parameter(Mandatory = $true)]
    [string]$ChecksumPath,
    [string]$ExpectedVersion = ""
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $AssetPath -PathType Leaf)) {
    throw "Missing Windows release asset: $AssetPath"
}
if (-not (Test-Path -LiteralPath $ChecksumPath -PathType Leaf)) {
    throw "Missing Windows checksum file: $ChecksumPath"
}

$rawBytes = [System.IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $ChecksumPath).Path)
if ($rawBytes.Length -ge 3 -and $rawBytes[0] -eq 0xEF -and $rawBytes[1] -eq 0xBB -and $rawBytes[2] -eq 0xBF) {
    throw "Checksum file must not contain a UTF-8 BOM: $ChecksumPath"
}
if ($rawBytes -contains 0x0D) {
    throw "Checksum file must use LF line endings without CR: $ChecksumPath"
}

$checksumContent = [System.Text.Encoding]::UTF8.GetString($rawBytes)
if ($checksumContent -notmatch '^([0-9a-f]{64})  ([^\r\n]+)\n$') {
    throw "Unexpected checksum format in ${ChecksumPath}: '$checksumContent'"
}
$expectedHash = $Matches[1]
$expectedName = $Matches[2]
$actualName = [System.IO.Path]::GetFileName($AssetPath)
if ($expectedName -ne $actualName) {
    throw "Checksum filename '$expectedName' does not match asset '$actualName'"
}

$actualHash = (Get-FileHash -LiteralPath $AssetPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualHash -ne $expectedHash) {
    throw "SHA-256 mismatch for ${AssetPath}: expected $expectedHash, got $actualHash"
}

$versionOutput = & (Resolve-Path -LiteralPath $AssetPath).Path --version
if ($LASTEXITCODE -ne 0) {
    throw "Asset --version failed with exit code $LASTEXITCODE"
}
$versionText = ($versionOutput | Out-String).Trim()
Write-Output "Verified $actualName ($actualHash): $versionText"
if ($ExpectedVersion -and $versionText -notmatch [regex]::Escape($ExpectedVersion)) {
    throw "Unexpected version output '$versionText' (expected '$ExpectedVersion')"
}
