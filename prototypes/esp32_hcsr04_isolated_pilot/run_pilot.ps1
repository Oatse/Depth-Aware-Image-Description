param(
    [ValidateSet("Board", "Sensor")]
    [string]$Mode = "Board",
    [string]$Port = "COM7",
    [int]$CaptureSeconds = 15,
    [switch]$IConfirmEchoIs3V3
)

$pilotRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $pilotRoot ".venv\Scripts\python.exe"
$platformio = Join-Path $pilotRoot ".venv\Scripts\platformio.exe"

if ($Mode -eq "Sensor" -and -not $IConfirmEchoIs3V3) {
    throw "Sensor mode locked: use a divider/level shifter so ECHO is <= 3.3 V, then pass -IConfirmEchoIs3V3."
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    py -m venv (Join-Path $pilotRoot ".venv")
    & $venvPython -m pip install --disable-pip-version-check platformio
}

$environment = if ($Mode -eq "Sensor") { "hcsr04" } else { "board_check" }

& $platformio run --project-dir $pilotRoot --environment $environment
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $platformio run --project-dir $pilotRoot --environment $environment --target upload --upload-port $Port
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $venvPython (Join-Path $pilotRoot "capture_serial.py") --port $Port --seconds $CaptureSeconds
exit $LASTEXITCODE

