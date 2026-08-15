# Build tools/launcher/dep_pm_launcher.py into Start-DEP-PM.exe at the repo root.
#
#   .\tools\launcher\build.ps1
#
# Requires PyInstaller in the backend venv (install once):
#   backend\.venv\Scripts\pip install -r tools\launcher\requirements-build.txt
#
# The resulting .exe does NOT embed Python or Node - it is a button that drives what is
# already installed on this machine (backend venv + node), so it must stay inside the repo.
#
# ASCII ONLY, on purpose: Windows PowerShell 5.1 reads .ps1 as ANSI unless the file has a
# BOM, and the house rule is UTF-8 without BOM (WORKING_RULES 6.1b). Thai text here parsed
# as garbage and broke the script - keep messages English so both rules can hold at once.
$ErrorActionPreference = "Stop"

$root = (Resolve-Path "$PSScriptRoot\..\..").Path
$python = Join-Path $root "backend\.venv\Scripts\python.exe"

if (-not (Test-Path $python)) { throw "backend venv not found at $python" }

# PyInstaller writes progress and warnings to stderr. Under $ErrorActionPreference = "Stop"
# Windows PowerShell turns any native stderr line into a terminating error, which killed the
# build on a harmless DEPRECATION notice. Exit code is the only reliable signal here.
$ErrorActionPreference = "Continue"

& $python -m PyInstaller `
    --onefile `
    --console `
    --name "Start-DEP-PM" `
    --distpath $root `
    --workpath "$PSScriptRoot\build" `
    --specpath $PSScriptRoot `
    --noconfirm `
    "$PSScriptRoot\dep_pm_launcher.py"

if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed (exit $LASTEXITCODE)" }

Write-Output ""
Write-Output "Done -> $root\Start-DEP-PM.exe"
Write-Output "Double-click it to start the platform (it must stay in the repo folder)."
