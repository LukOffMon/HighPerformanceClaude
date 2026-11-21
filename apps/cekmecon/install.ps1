# Toilet Bamboo Paper Cekmecon - Windows installer.
#   irm https://raw.githubusercontent.com/LukOffMon/HighPerformanceClaude/main/apps/cekmecon/install.ps1 | iex
# Installs the app for your user (no admin), adds Start Menu + Desktop shortcuts, connects it to Claude Code and opens it.
$ErrorActionPreference = "Stop"
$Name = [string][char]0x00C7 + "ekmec" + [char]0x00F3 + "n"
$Src = "https://github.com/LukOffMon/HighPerformanceClaude/archive/refs/heads/main.zip#subdirectory=apps/cekmecon"
if ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot "pyproject.toml"))) { $Src = $PSScriptRoot }

function Find-Python {
  foreach ($c in @(@("py", "-3"), @("python"), @("python3"))) {
    try {
      $v = & $c[0] $c[1..9] -c "import sys; print(sys.version_info >= (3, 9))" 2>$null
      if ($v -eq "True") { return ,$c }
    } catch {}
  }
  return $null
}

Write-Host "-> Installing $Name" -ForegroundColor Green
$py = Find-Python
if (-not $py) {
  Write-Host "-> Python 3 not found; installing it with winget (one time)..."
  winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements | Out-Null
  $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" + [Environment]::GetEnvironmentVariable("Path", "Machine")
  $py = Find-Python
  if (-not $py) { throw "Python 3.9+ is required. Install it from https://www.python.org/downloads/ and run this again." }
}
$PyExe = $py[0]; $PyArgs = @($py | Select-Object -Skip 1)

& $PyExe @PyArgs -m pip install --user --upgrade --quiet $Src
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

$info = & $PyExe @PyArgs -c "import sys, os, cekmecon; d=os.path.dirname(sys.executable); print(os.path.join(d,'pythonw.exe')); print(sys.executable); print(os.path.join(os.path.dirname(cekmecon.__file__),'ui','icon.ico'))"
$Pythonw, $Python, $Icon = $info[0], $info[1], $info[2]
if (-not (Test-Path $Pythonw)) { $Pythonw = $Python }

$shell = New-Object -ComObject WScript.Shell
$targets = @((Join-Path ([Environment]::GetFolderPath("Programs")) "$Name.lnk"), (Join-Path ([Environment]::GetFolderPath("Desktop")) "$Name.lnk"))
foreach ($lnkPath in $targets) {
  $lnk = $shell.CreateShortcut($lnkPath)
  $lnk.TargetPath = $Pythonw
  $lnk.Arguments = "-m cekmecon"
  $lnk.IconLocation = $Icon
  $lnk.Description = "Toilet Bamboo Paper $Name - Claude's memory drawer"
  $lnk.WorkingDirectory = $env:USERPROFILE
  $lnk.Save()
}
Write-Host "-> Shortcuts added to the Start Menu and Desktop"

& $Python -m cekmecon connect
Start-Process -FilePath $Pythonw -ArgumentList "-m cekmecon"
Write-Host "Done. $Name is open. Start Claude Code in any project; the first time, click 'Permitir siempre'." -ForegroundColor Green
