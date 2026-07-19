[CmdletBinding()]
param(
    [string]$Port = "COM7",
    [int]$BaudRate = 115200,
    [int]$RefreshMilliseconds = 500,
    [int]$DurationSeconds = 0
)

$ErrorActionPreference = "Stop"
$serial = [System.IO.Ports.SerialPort]::new($Port, $BaudRate, "None", 8, "One")
$serial.ReadTimeout = 100
$serial.DtrEnable = $false
$serial.RtsEnable = $false

$startedAt = Get-Date
$lastLineAt = $null
$lastSampleAt = $null
$lastRenderAt = [DateTime]::MinValue
$sensorId = "menunggu data"
$lastPulseUs = $null
$lastDistanceCm = $null
$lastSensorStatus = $null
$validCount = 0
$timeoutCount = 0
$noiseCount = 0
$sampleCount = 0
$sensorStats = @{}

function Get-SensorState {
    param([datetime]$Now)

    if ($null -eq $lastLineAt -or ($Now - $lastLineAt).TotalSeconds -gt 2) {
        return @{ Label = "FIRMWARE TIDAK MENGIRIM DATA"; Color = "Red" }
    }
    if ($null -eq $lastSampleAt -or ($Now - $lastSampleAt).TotalSeconds -gt 2) {
        return @{ Label = "ESP32 ONLINE, DATA SENSOR TIDAK ADA"; Color = "Yellow" }
    }
    if ($lastSensorStatus -eq "ok") {
        return @{ Label = "SENSOR MERESPONS NORMAL"; Color = "Green" }
    }
    if ($lastSensorStatus -eq "out_of_range") {
        return @{ Label = "SENSOR BELUM VALID (ECHO NOISE)"; Color = "Yellow" }
    }
    if ($lastSensorStatus -eq "echo_timeout") {
        return @{ Label = "SENSOR TIDAK MEMBERI ECHO"; Color = "Red" }
    }
    return @{ Label = "MENUNGGU STATUS SENSOR"; Color = "Yellow" }
}

function Show-Dashboard {
    param([datetime]$Now)

    $state = Get-SensorState -Now $Now
    Clear-Host
    Write-Host "ESP32 + HC-SR04 LIVE MONITOR" -ForegroundColor Cyan
    Write-Host "Tekan Ctrl+C untuk berhenti"
    Write-Host ""
    Write-Host ("Serial        : {0} @ {1} baud" -f $Port, $BaudRate)
    Write-Host "ESP32         : ONLINE / DATA SERIAL MASUK" -ForegroundColor Green
    Write-Host ("Sampel terakhir: {0}" -f $sensorId)
    foreach ($id in @("sensor_1", "sensor_2")) {
        if ($sensorStats.ContainsKey($id)) {
            $item = $sensorStats[$id]
            $itemState = switch ($item.Status) {
                "ok" { @{ Label = "NORMAL"; Color = "Green" } }
                "out_of_range" { @{ Label = "NOISE/INVALID"; Color = "Yellow" } }
                default { @{ Label = "TIDAK ADA ECHO"; Color = "Red" } }
            }
            $age = [math]::Round(((Get-Date) - $item.At).TotalSeconds, 1)
            Write-Host ("{0,-14}: {1,-16} pulse={2} us, jarak={3}, umur={4}s" -f $id, $itemState.Label, $item.PulseUs, $(if ($null -eq $item.DistanceCm) { "-" } else { "$($item.DistanceCm) cm" }), $age) -ForegroundColor $itemState.Color
        }
        else {
            Write-Host ("{0,-14}: MENUNGGU DATA" -f $id) -ForegroundColor Yellow
        }
    }
    Write-Host ("Status terakhir : {0}" -f $state.Label) -ForegroundColor $state.Color
    Write-Host ""
    Write-Host ("Total sampel  : {0}" -f $sampleCount)
    Write-Host ("Valid         : {0}" -f $validCount) -ForegroundColor Green
    Write-Host ("Timeout       : {0}" -f $timeoutCount) -ForegroundColor Red
    Write-Host ("Noise/invalid : {0}" -f $noiseCount) -ForegroundColor Yellow
    Write-Host ("Pulse terakhir: {0}" -f $(if ($null -eq $lastPulseUs) { "-" } else { "$lastPulseUs us" }))
    Write-Host ("Jarak terakhir: {0}" -f $(if ($null -eq $lastDistanceCm) { "-" } else { "$lastDistanceCm cm" }))
    Write-Host ""
    Write-Host "Arti status:"
    Write-Host "- HIJAU  : ECHO valid dan jarak terbaca."
    Write-Host "- KUNING : serial aktif, tetapi ECHO hanya noise/tidak valid."
    Write-Host "- MERAH  : tidak ada ECHO atau firmware berhenti mengirim data."
}

try {
    $serial.Open()
    Start-Sleep -Milliseconds 500
    $serial.DiscardInBuffer()

    while ($true) {
        $now = Get-Date
        if ($DurationSeconds -gt 0 -and ($now - $startedAt).TotalSeconds -ge $DurationSeconds) {
            break
        }

        try {
            $line = $serial.ReadLine().Trim()
            if ($line) {
                $lastLineAt = Get-Date
                try {
                    $message = $line | ConvertFrom-Json
                    if ($message.type -eq "sample") {
                        $lastSampleAt = $lastLineAt
                        $sensorId = [string]$message.sensor_id
                        $lastPulseUs = $message.pulse_us
                        $lastDistanceCm = $message.distance_cm
                        $lastSensorStatus = [string]$message.status
                        $sensorStats[$sensorId] = @{ Status = $lastSensorStatus; PulseUs = $message.pulse_us; DistanceCm = $message.distance_cm; At = $lastSampleAt }
                        $sampleCount++
                        if ($message.valid -eq $true) {
                            $validCount++
                        }
                        elseif ($message.status -eq "echo_timeout") {
                            $timeoutCount++
                        }
                        else {
                            $noiseCount++
                        }
                    }
                }
                catch {
                    # Abaikan baris bootloader/non-JSON; keberadaannya tetap membuktikan serial aktif.
                }
            }
        }
        catch [System.TimeoutException] {
            # Timeout singkat diperlukan agar dashboard tetap diperbarui saat data berhenti.
        }

        $now = Get-Date
        if (($now - $lastRenderAt).TotalMilliseconds -ge $RefreshMilliseconds) {
            Show-Dashboard -Now $now
            $lastRenderAt = $now
        }
    }

    Show-Dashboard -Now (Get-Date)
}
catch {
    Write-Host ("GAGAL MEMBUKA {0}: {1}" -f $Port, $_.Exception.Message) -ForegroundColor Red
    exit 1
}
finally {
    if ($serial.IsOpen) {
        $serial.Close()
    }
    $serial.Dispose()
}
