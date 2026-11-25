# Toilet Bamboo Paper GeekMcON - update the local app on Windows to the latest release (the same version as the web app).
#   irm https://raw.githubusercontent.com/LukOffMon/HighPerformanceClaude/main/apps/cekmecon/update.ps1 | iex
# Works for every version, including 1.0 (which has no `cekmecon update` command yet). Your notes are never touched.
$ErrorActionPreference = "Stop"
$Repo = "LukOffMon/HighPerformanceClaude"
$Dir = Join-Path $env:LOCALAPPDATA "Programs\Cekmecon"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

if (-not (Test-Path (Join-Path $Dir "Cekmecon.exe"))) {
  # Installed from source (install.ps1 / pip): re-running the installer upgrades it in place.
  Write-Host "-> GeekMcON was installed from source; upgrading with install.ps1" -ForegroundColor Green
  Invoke-RestMethod "https://raw.githubusercontent.com/$Repo/main/apps/cekmecon/install.ps1" | Invoke-Expression
  return
}

$rel = Invoke-RestMethod "https://api.github.com/repos/$Repo/releases/latest" -Headers @{ "User-Agent" = "cekmecon-updater" }
$latest = ($rel.tag_name -replace '^.*v', '')
$current = try { (& (Join-Path $Dir "cekmecon-cli.exe") --version 2>$null | Select-Object -First 1).Trim() } catch { "0.0.0" }
Write-Host "-> GeekMcON installed $current, latest $latest" -ForegroundColor Green
if ([version]$current -ge [version]$latest -and -not $env:CEKMECON_FORCE) { Write-Host "Already up to date." -ForegroundColor Green; return }

$asset = $rel.assets | Where-Object { $_.name -eq "Cekmecon-Setup-Windows.exe" } | Select-Object -First 1
if (-not $asset) { throw "The latest release has no Windows installer yet. Try again in a few minutes." }
$setup = Join-Path $env:TEMP "Cekmecon-Setup-Windows.exe"
Write-Host "-> Downloading $($asset.name) ($([math]::Round($asset.size / 1MB, 1)) MB)"
Invoke-WebRequest $asset.browser_download_url -OutFile $setup -UseBasicParsing

Write-Host "-> Closing GeekMcON and installing $latest"
Get-Process -Name "Cekmecon", "cekmecon-cli" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
# Wait for the installer only: Start-Process -Wait would also wait for the app it reopens (Windows PowerShell 5.1).
$p = Start-Process -FilePath $setup -ArgumentList "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART" -PassThru
$p.WaitForExit()
Remove-Item $setup -ErrorAction SilentlyContinue

& (Join-Path $Dir "cekmecon-cli.exe") connect | Out-Null
if (-not (Get-Process -Name "Cekmecon" -ErrorAction SilentlyContinue)) { Start-Process (Join-Path $Dir "Cekmecon.exe") }
Write-Host "Done. GeekMcON $latest is open. Restart Claude Code so it uses the new version." -ForegroundColor Green
