$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

function Write-Log([string]$Text) {
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -LiteralPath (Join-Path $PSScriptRoot "setup.log") -Value "[$stamp] $Text" -Encoding UTF8
}

try {
    Write-Host ""
    Write-Host "ROIDMI EVE Plus Control v21.5 GITHUB AUTO UPDATE" -ForegroundColor Cyan
    Write-Host "Model: roidmi.vacuum.v60"
    Write-Host "Recommended runtime: Python 3.11 x64"
    Write-Host ""

    $chosenExe = $null
    $chosenArgs = @()

    # Prefer Python 3.11, then 3.10.
    try {
        & py -3.11 -c "import sys; print(sys.executable)" *> $null
        if ($LASTEXITCODE -eq 0) {
            $chosenExe = "py"
            $chosenArgs = @("-3.11")
        }
    } catch {}

    if (-not $chosenExe) {
        try {
            & py -3.10 -c "import sys; print(sys.executable)" *> $null
            if ($LASTEXITCODE -eq 0) {
                $chosenExe = "py"
                $chosenArgs = @("-3.10")
            }
        } catch {}
    }

    if (-not $chosenExe) {
        $detected = ""
        try {
            $detected = & python --version 2>&1
            $detected = ($detected | Out-String).Trim()
        } catch {}
        throw ("Python 3.11 or 3.10 was not found. Detected default Python: " + $detected +
               ". Install Python 3.11 x64 side-by-side and rerun START_SAFE.cmd.")
    }

    $version = & $chosenExe @chosenArgs -c "import sys; print(str(sys.version_info.major)+'.'+str(sys.version_info.minor)+'.'+str(sys.version_info.micro))"
    $version = ($version | Out-String).Trim()

    Write-Host "Selected Python: $version" -ForegroundColor Green
    Write-Log "Selected Python $version via $chosenExe $($chosenArgs -join ' ')"

    $venvDir = Join-Path $PSScriptRoot ".venv"
    $venvPython = Join-Path $venvDir "Scripts\python.exe"

    if (Test-Path -LiteralPath $venvPython) {
        $venvVersion = & $venvPython -c "import sys; print(str(sys.version_info.major)+'.'+str(sys.version_info.minor))"
        $venvVersion = ($venvVersion | Out-String).Trim()

        if ($venvVersion -ne "3.11" -and $venvVersion -ne "3.10") {
            Write-Host "Removing incompatible old .venv (Python $venvVersion)..." -ForegroundColor Yellow
            Remove-Item -LiteralPath $venvDir -Recurse -Force
        }
    }

    if (-not (Test-Path -LiteralPath $venvPython)) {
        Write-Host "Creating local environment .venv..."
        & $chosenExe @chosenArgs -m venv ".venv"
        if ($LASTEXITCODE -ne 0) {
            throw "Could not create .venv."
        }
    }

    # First try to use an already prepared environment. This avoids unnecessary
    # network access and prevents a harmless pip-upgrade failure from blocking startup.
    $runtimeReady = $false
    try {
        & $venvPython -c "import netifaces, miio, requests; from Crypto.Cipher import ARC4; from PIL import Image, ImageTk; from vacuum_map_parser_roidmi.map_data_parser import RoidmiMapDataParser; import pystray; print('runtime already ready')" *> $null
        if ($LASTEXITCODE -eq 0) {
            $runtimeReady = $true
        }
    } catch {}

    if (-not $runtimeReady) {
        Write-Host "Checking pip..."
        & $venvPython -m pip --version *> $null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "pip is missing. Running ensurepip..." -ForegroundColor Yellow
            & $venvPython -m ensurepip --upgrade
            if ($LASTEXITCODE -ne 0) {
                throw "pip is not available and ensurepip failed."
            }
        }

        # Upgrade is OPTIONAL. Some Windows/ISP/proxy configurations block PyPI
        # metadata or certificate checks even though normal package installation works.
        Write-Host "Optional: trying to update pip/setuptools/wheel..."
        & $venvPython -m pip install --disable-pip-version-check --upgrade pip setuptools wheel
        if ($LASTEXITCODE -ne 0) {
            Write-Host "WARNING: pip upgrade failed. Continuing with bundled pip." -ForegroundColor Yellow
            Write-Log "WARNING: pip/setuptools/wheel upgrade failed; continuing."
        }

        Write-Host "Installing Windows-compatible netifaces replacement..."
        & $venvPython -m pip install --disable-pip-version-check --prefer-binary "netifaces2==0.0.22"
        if ($LASTEXITCODE -ne 0) {
            throw "netifaces2 installation failed. See setup.log."
        }

        Write-Host "Installing python-miio dependencies..."
        $deps = @(
            "PyYAML>=5,<7",
            "android_backup>=0,<1",
            "appdirs>=1,<2",
            "attrs",
            "click>=8,<8.3",
            "construct>=2.10.56,<3.0.0",
            "croniter>=1",
            "cryptography>=35",
            "defusedxml>=0,<1",
            "micloud",
            "pytz",
            "tqdm>=4,<5",
            "zeroconf>=0,<1",
            "requests>=2,<3",
            "pycryptodome>=3.20,<4",
            "Pillow>=10,<12",
            "vacuum-map-parser-base==0.1.5",
            "vacuum-map-parser-roidmi",
            "pystray>=0.19,<1"
        )

        & $venvPython -m pip install --disable-pip-version-check --prefer-binary $deps
        if ($LASTEXITCODE -ne 0) {
            throw "One or more dependencies failed to install. See setup.log."
        }

        Write-Host "Installing python-miio 0.5.12 without old netifaces dependency..."
        & $venvPython -m pip install --disable-pip-version-check --no-deps --prefer-binary "python-miio==0.5.12"
        if ($LASTEXITCODE -ne 0) {
            throw "python-miio installation failed. See setup.log."
        }
    } else {
        Write-Host "Python environment is already ready. Package installation skipped." -ForegroundColor Green
    }

    Write-Host "Testing imports..." -ForegroundColor Cyan
    & $venvPython -c "import netifaces, miio, requests; from Crypto.Cipher import ARC4; from PIL import Image, ImageTk; from vacuum_map_parser_roidmi.map_data_parser import RoidmiMapDataParser; import pystray; print('base imports OK')"
    if ($LASTEXITCODE -ne 0) {
        throw "Base import test failed."
    }

    $roidmiOk = $false

    try {
        & $venvPython -c "from miio.integrations.roidmi.vacuum.roidmivacuum_miot import RoidmiVacuumMiot; print('ROIDMI import OK')" *> $null
        if ($LASTEXITCODE -eq 0) {
            $roidmiOk = $true
        }
    } catch {}

    if (-not $roidmiOk) {
        try {
            & $venvPython -c "from miio.integrations.vacuum.roidmi.roidmivacuum_miot import RoidmiVacuumMiot; print('ROIDMI legacy import OK')" *> $null
            if ($LASTEXITCODE -eq 0) {
                $roidmiOk = $true
            }
        } catch {}
    }

    if (-not $roidmiOk) {
        throw "ROIDMI EVE Plus module could not be imported."
    }

    Write-Host ""
    Write-Host "Installation OK. Starting control panel in crash-safe mode..." -ForegroundColor Green
    Write-Host "Keep this window open while testing. If the GUI fails, the traceback will remain visible." -ForegroundColor Yellow

    $app = Join-Path $PSScriptRoot "roidmi_control.py"
    Write-Log "Starting application with console-visible python.exe."

    & $venvPython $app
    $appCode = $LASTEXITCODE

    if ($appCode -ne 0) {
        Write-Host ""
        Write-Host "The application exited with code $appCode." -ForegroundColor Red
        Write-Host "Please send CRASH_REPORT.txt and error.log if present." -ForegroundColor Yellow
        Write-Log "Application exited with code $appCode."
        pause
        exit $appCode
    }

    Write-Log "Application closed normally."
    exit 0
}
catch {
    $msg = $_ | Out-String
    $errPath = Join-Path $PSScriptRoot "setup_error.txt"
    Set-Content -LiteralPath $errPath -Value $msg -Encoding UTF8
    Write-Log "ERROR: $msg"

    Write-Host ""
    Write-Host "ERROR:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Details saved to setup_error.txt"
    exit 1
}
