<#
Remote Mouse Server - uninstaller
------------------------------------
Stops the server, removes the Startup/Start Menu shortcuts, and deletes
the installed copy of the app from %LOCALAPPDATA%\RemoteMouseServer.
#>

$ErrorActionPreference = "SilentlyContinue"

function Write-Step($msg) { Write-Host ""; Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "    $msg" -ForegroundColor Green }

$installDir   = Join-Path $env:LOCALAPPDATA "RemoteMouseServer"
$startupDir   = [Environment]::GetFolderPath("Startup")
$startMenuDir = [Environment]::GetFolderPath("Programs")

Write-Step "Stopping the server (if running)"
Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe'" |
    Where-Object { $_.CommandLine -and $_.CommandLine -like "*$installDir*" } |
    ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force
        Write-Ok "Stopped process $($_.ProcessId)"
    }

Write-Step "Removing shortcuts"
Remove-Item -Force (Join-Path $startupDir "Remote Mouse Server.lnk")
Remove-Item -Force (Join-Path $startMenuDir "Remote Mouse Control Panel.lnk")
Remove-Item -Force (Join-Path $startMenuDir "Uninstall Remote Mouse Server.lnk")
Write-Ok "Removed"

Write-Step "Removing installed files"
# This script may itself live inside $installDir, so delete from a separate
# process after this one exits to avoid a file-in-use error.
$cleanupCmd = "Start-Sleep -Seconds 1; Remove-Item -Recurse -Force '$installDir' -ErrorAction SilentlyContinue"
Start-Process -WindowStyle Hidden powershell -ArgumentList "-NoProfile", "-Command", $cleanupCmd
Write-Ok "Scheduled for removal"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Remote Mouse Server has been uninstalled." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Start-Sleep -Seconds 2
