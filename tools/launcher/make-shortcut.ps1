# Put a shortcut to Start-DEP-PM.exe on the current user's Desktop.
#
#   .\tools\launcher\make-shortcut.ps1
#
# Run it again after moving the repo or rebuilding the exe - it overwrites the same shortcut.
#
# ASCII ONLY (see build.ps1 for why). The Thai display name and description are read from
# shortcut-name.txt, which is UTF-8 without BOM: line 1 = shortcut name, line 2 = description.
# Reading them from a file instead of embedding them keeps the script parseable under the
# Windows PowerShell 5.1 ANSI default while the shortcut still shows Thai.
$ErrorActionPreference = "Stop"

$root = (Resolve-Path "$PSScriptRoot\..\..").Path
$exe = Join-Path $root "Start-DEP-PM.exe"
if (-not (Test-Path -LiteralPath $exe)) {
    throw "Start-DEP-PM.exe not found. Build it first: .\tools\launcher\build.ps1"
}

$lines = [System.IO.File]::ReadAllLines("$PSScriptRoot\shortcut-name.txt", [System.Text.Encoding]::UTF8)
$name = $lines[0].Trim()
$description = if ($lines.Length -gt 1) { $lines[1].Trim() } else { "" }

$desktop = [Environment]::GetFolderPath('Desktop')
$lnk = Join-Path $desktop ($name + ".lnk")

$shell = New-Object -ComObject WScript.Shell
$sc = $shell.CreateShortcut($lnk)
$sc.TargetPath = $exe
$sc.WorkingDirectory = $root          # the launcher finds the repo from its own location anyway
$sc.IconLocation = "$exe,0"
$sc.Description = $description
$sc.WindowStyle = 1
$sc.Save()

Write-Output "Created: $lnk"
Write-Output "  -> $exe"
