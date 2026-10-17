$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv .venv
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv .venv
    } else {
        throw 'Python 3 is not installed. Install Python, then rerun this script.'
    }
    if ($LASTEXITCODE -ne 0) { throw 'Unable to create Python virtual environment.' }
}
& $python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }

if (-not $env:NGO_ADMIN_PASSWORD) {
    $password = Read-Host 'Choose a local admin password (will not be displayed)' -AsSecureString
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
    try { $env:NGO_ADMIN_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
    if (-not $env:NGO_ADMIN_PASSWORD) { throw 'Admin password cannot be empty.' }
}

Write-Host 'Starting HopeLink at http://127.0.0.1:5000' -ForegroundColor Green
Write-Host 'Admin username: admin | Password: the one you just entered'
& $python app.py
