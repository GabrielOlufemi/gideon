# Gideon installer for Windows
# Usage: irm https://raw.githubusercontent.com/GabrielOlufemi/gideon/master/install.ps1 | iex

$Name = "gideon"
$Repo = "GabrielOlufemi/gideon"
$Binary = "gideon-windows-x86_64.exe"
$DownloadUrl = "https://github.com/$Repo/releases/latest/download/$Binary"

# Install directory — AppData\Local\Programs\Gideon is standard for Windows tools
$InstallDir = "$env:LOCALAPPDATA\Programs\Gideon"
$ExePath = "$InstallDir\gideon.exe"

Write-Host "Downloading $Name for Windows..." -ForegroundColor Cyan

# Create install directory
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null

# Download the binary
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $ExePath -UseBasicParsing
} catch {
    Write-Host "Download failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Installed to $ExePath" -ForegroundColor Green

# Add to PATH if not already there
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$InstallDir*") {
    $NewPath = "$UserPath;$InstallDir"
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    # Also update current session
    $env:Path = "$env:Path;$InstallDir"
    Write-Host "Added $InstallDir to your PATH." -ForegroundColor Yellow
    Write-Host "You may need to restart your terminal for the change to take effect." -ForegroundColor Yellow
} else {
    Write-Host "Gideon is already on your PATH." -ForegroundColor Green
}

Write-Host ""
Write-Host "Done. Run 'gideon' to start." -ForegroundColor Cyan