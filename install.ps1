# Gideon installer for Windows
# Usage: irm https://raw.githubusercontent.com/GabrielOlufemi/gideon/master/install.ps1 | iex

$Name = "gideon"
$Repo = "GabrielOlufemi/gideon"
$Archive = "gideon-windows-x86_64.tar.gz"
$DownloadUrl = "https://github.com/$Repo/releases/latest/download/$Archive"

# Install directory — AppData\Local\Programs\Gideon is standard for Windows tools
$InstallDir = "$env:LOCALAPPDATA\Programs\Gideon"
$ExtractDir = "$InstallDir\gideon-windows-x86_64"
$ExePath = "$ExtractDir\gideon.exe"

Write-Host "Downloading $Name for Windows..." -ForegroundColor Cyan

# Create install directory
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null

# Download the archive
$ArchivePath = "$InstallDir\$Archive"
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $ArchivePath -UseBasicParsing
} catch {
    Write-Host "Download failed: $_" -ForegroundColor Red
    exit 1
}

# Extract — clean old extract first
if (Test-Path "$ExtractDir") {
    Remove-Item -Recurse -Force "$ExtractDir"
}

Write-Host "Extracting..." -ForegroundColor Cyan

# Windows 10+ ships with tar.exe; fall back to 7-Zip
if (Get-Command "tar" -ErrorAction SilentlyContinue) {
    & tar -xzf "$ArchivePath" -C "$InstallDir"
} elseif (Get-Command "7z" -ErrorAction SilentlyContinue) {
    & 7z x "$ArchivePath" -o"$InstallDir" -y
} else {
    Remove-Item "$ArchivePath"
    Write-Host "Need either tar or 7-Zip to extract." -ForegroundColor Red
    Write-Host "" -ForegroundColor Red
    Write-Host "Install 7-Zip (https://7-zip.org) and run:" -ForegroundColor Yellow
    Write-Host "  7z x `$Archive` -o`$InstallDir` -y" -ForegroundColor Yellow
    Write-Host "" -ForegroundColor Yellow
    Write-Host "Then run this installer again." -ForegroundColor Yellow
    exit 1
}

Remove-Item "$ArchivePath"

if (!(Test-Path "$ExePath")) {
    Write-Host "Extraction failed: gideon.exe not found in the archive." -ForegroundColor Red
    exit 1
}

Write-Host "Installed to $ExtractDir" -ForegroundColor Green

# Add to PATH if not already there
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$ExtractDir*") {
    $NewPath = "$UserPath;$ExtractDir"
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    $env:Path = "$env:Path;$ExtractDir"
    Write-Host "Added $ExtractDir to your PATH." -ForegroundColor Yellow
    Write-Host "You may need to restart your terminal for the change to take effect." -ForegroundColor Yellow
} else {
    Write-Host "Gideon is already on your PATH." -ForegroundColor Green
}

Write-Host ""
Write-Host "Done. Run 'gideon' to start." -ForegroundColor Cyan