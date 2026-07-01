<#
Remote Mouse Server - Windows installer
-----------------------------------------
Installs the server into %LOCALAPPDATA%\RemoteMouseServer, creates a
private virtual environment, installs dependencies, and registers the
server to start silently (no console window) every time you log in.

Run via install.bat (double-click), which calls this with the right
execution policy bypass - you don't need to change any Windows settings.
#>

$ErrorActionPreference = "Stop"

function Write-Step($msg) { Write-Host ""; Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "    $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "    $msg" -ForegroundColor Yellow }

# ---------------------------------------------------------------------------
# 0. Locate source files (this script lives in <project>\installer\)
# ---------------------------------------------------------------------------
$sourceDir  = Split-Path -Parent $PSScriptRoot
$installDir = Join-Path $env:LOCALAPPDATA "RemoteMouseServer"

Write-Step "Installing Remote Mouse Server"
Write-Ok "Source:      $sourceDir"
Write-Ok "Install to:  $installDir"

foreach ($required in @("server.py", "gui.py", "requirements.txt", "templates\index.html")) {
    if (-not (Test-Path (Join-Path $sourceDir $required))) {
        Write-Host "ERROR: missing $required next to install.ps1 - run this from the full project folder." -ForegroundColor Red
        exit 1
    }
}

# ---------------------------------------------------------------------------
# 1. Find Python
# ---------------------------------------------------------------------------
Write-Step "Looking for Python"
$pyLauncher = $null
$pyArgs = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
    $pyLauncher = "py"; $pyArgs = @("-3")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pyLauncher = "python"; $pyArgs = @()
}

if (-not $pyLauncher) {
    Write-Host ""
    Write-Host "Python wasn't found on this machine." -ForegroundColor Red
    Write-Host "Install Python 3 from https://www.python.org/downloads/ (check 'Add python.exe to PATH')," -ForegroundColor Red
    Write-Host "then run install.bat again." -ForegroundColor Red
    exit 1
}
Write-Ok "Found Python via '$pyLauncher'"

# ---------------------------------------------------------------------------
# 2. Copy project files
# ---------------------------------------------------------------------------
Write-Step "Copying files"
New-Item -ItemType Directory -Force -Path $installDir | Out-Null
Copy-Item -Path (Join-Path $sourceDir "server.py")           -Destination $installDir -Force
Copy-Item -Path (Join-Path $sourceDir "gui.py")               -Destination $installDir -Force
Copy-Item -Path (Join-Path $sourceDir "requirements.txt")     -Destination $installDir -Force
Copy-Item -Path (Join-Path $sourceDir "templates")            -Destination $installDir -Recurse -Force
if (Test-Path (Join-Path $sourceDir "README.md")) {
    Copy-Item -Path (Join-Path $sourceDir "README.md") -Destination $installDir -Force
}
# Keep a copy of the uninstaller so it still works after the original
# download folder is deleted or moved.
New-Item -ItemType Directory -Force -Path (Join-Path $installDir "installer") | Out-Null
Copy-Item -Path (Join-Path $PSScriptRoot "uninstall.ps1") -Destination (Join-Path $installDir "installer") -Force
Copy-Item -Path (Join-Path $PSScriptRoot "uninstall.bat") -Destination (Join-Path $installDir "installer") -Force
Write-Ok "Done"

# ---------------------------------------------------------------------------
# 3. Create a private virtual environment + install dependencies
# ---------------------------------------------------------------------------
Write-Step "Setting up a private Python environment (this can take a minute)"
$venvDir = Join-Path $installDir "venv"
if (-not (Test-Path $venvDir)) {
    & $pyLauncher @pyArgs -m venv $venvDir
}
$pip      = Join-Path $venvDir "Scripts\pip.exe"
$pythonw  = Join-Path $venvDir "Scripts\pythonw.exe"

& $pip install --upgrade pip --quiet
& $pip install -r (Join-Path $installDir "requirements.txt") --quiet
try {
    & $pip install "qrcode[pil]" --quiet
} catch {
    Write-Warn "Optional QR code support could not be installed - the control panel will still work without it."
}
Write-Ok "Dependencies installed"

# ---------------------------------------------------------------------------
# 4. Shortcuts: run silently at login, plus a Start Menu control panel
# ---------------------------------------------------------------------------
Write-Step "Setting up shortcuts"
$wsh = New-Object -ComObject WScript.Shell

# Startup: launches server.py with no console window, every login
$startupDir = [Environment]::GetFolderPath("Startup")
$startupLnk = $wsh.CreateShortcut((Join-Path $startupDir "Remote Mouse Server.lnk"))
$startupLnk.TargetPath       = $pythonw
$startupLnk.Arguments        = '"' + (Join-Path $installDir "server.py") + '"'
$startupLnk.WorkingDirectory = $installDir
$startupLnk.Description      = "Starts the Remote Mouse phone-control server"
$startupLnk.Save()
Write-Ok "Will start automatically at login"

# Start Menu: opens the GUI control panel (Start/Stop, QR code, etc.)
$startMenuDir = [Environment]::GetFolderPath("Programs")
$panelLnk = $wsh.CreateShortcut((Join-Path $startMenuDir "Remote Mouse Control Panel.lnk"))
$panelLnk.TargetPath       = $pythonw
$panelLnk.Arguments        = '"' + (Join-Path $installDir "gui.py") + '"'
$panelLnk.WorkingDirectory = $installDir
$panelLnk.Description      = "Remote Mouse Server control panel"
$panelLnk.Save()

# Start Menu: uninstaller
$uninstallLnk = $wsh.CreateShortcut((Join-Path $startMenuDir "Uninstall Remote Mouse Server.lnk"))
$uninstallLnk.TargetPath       = "powershell.exe"
$uninstallLnk.Arguments        = '-NoProfile -ExecutionPolicy Bypass -File "' + (Join-Path $installDir "installer\uninstall.ps1") + '"'
$uninstallLnk.WorkingDirectory = $installDir
$uninstallLnk.Description      = "Remove Remote Mouse Server"
$uninstallLnk.Save()
Write-Ok "Added to Start Menu"

# ---------------------------------------------------------------------------
# 5. Start it now (skip if a server is already listening on the port)
# ---------------------------------------------------------------------------
Write-Step "Starting the server"
$alreadyRunning = $false
try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $tcp.Connect("127.0.0.1", 5000)
    $tcp.Close()
    $alreadyRunning = $true
} catch { $alreadyRunning = $false }

if ($alreadyRunning) {
    Write-Ok "A server is already running on port 5000 - leaving it as is"
} else {
    Start-Process -FilePath $pythonw -ArgumentList ('"' + (Join-Path $installDir "server.py") + '"') -WorkingDirectory $installDir
    Start-Sleep -Seconds 1
    Write-Ok "Running"
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Installed! The server is running now and will start"        -ForegroundColor Cyan
Write-Host " automatically every time you log in (silently, no window)." -ForegroundColor Cyan
Write-Host ""
Write-Host " Open 'Remote Mouse Control Panel' from the Start Menu any"  -ForegroundColor Cyan
Write-Host " time to see the QR code / address, or to stop the server." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
