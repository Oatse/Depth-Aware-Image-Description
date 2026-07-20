param(
    [string]$Certificate = ".\certs\localhost.pem",
    [string]$PrivateKey = ".\certs\localhost-key.pem",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$certificatePath = [System.IO.Path]::GetFullPath((Join-Path $projectRoot $Certificate))
$privateKeyPath = [System.IO.Path]::GetFullPath((Join-Path $projectRoot $PrivateKey))
if (-not (Test-Path -LiteralPath $certificatePath)) { throw "TLS certificate tidak ditemukan: $certificatePath" }
if (-not (Test-Path -LiteralPath $privateKeyPath)) { throw "TLS private key tidak ditemukan: $privateKeyPath" }
$lanAddress = Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -notlike "127.*" -and $_.PrefixOrigin -ne "WellKnown" } |
    Select-Object -First 1 -ExpandProperty IPAddress
if (-not $lanAddress) { throw "Alamat IPv4 LAN tidak ditemukan." }
$firewallRule = Get-NetFirewallRule -DisplayName "Bride-Gap Mobile $Port" -ErrorAction SilentlyContinue
Write-Host "URL HP: https://${lanAddress}:$Port"
Write-Host "Firewall rule: $(if ($firewallRule) { 'tersedia' } else { 'belum tersedia' })"
Write-Host "Pastikan certificate dipercaya oleh HP dan kedua perangkat memakai Wi-Fi yang sama."
$env:APP_HOST = "0.0.0.0"
$env:APP_PORT = "$Port"
Set-Location -LiteralPath $projectRoot
python -m uvicorn app.main:app --host 0.0.0.0 --port $Port --ssl-certfile $certificatePath --ssl-keyfile $privateKeyPath
