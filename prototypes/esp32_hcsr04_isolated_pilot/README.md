# ESP32 + 2x HC-SR04 Isolated Pilot

Throwaway pilot untuk menjawab dua pertanyaan secara terpisah:

1. Apakah ESP32 VROOM-32 dapat dideteksi, di-flash, dan mengirim output serial?
2. Setelah wiring aman dipastikan, apakah kedua HC-SR04 menghasilkan pembacaan jarak valid tanpa dipicu bersamaan?

## Wiring sensor yang diharapkan

| Sensor | HC-SR04 | ESP32 |
|---|---|---|
| Keduanya | VCC | Rel positif dari 5V/VIN |
| Keduanya | GND | Rel negatif/GND bersama |
| Sensor 1 | TRIG | GPIO 5 |
| Sensor 1 | ECHO | GPIO 18 melalui pembagi tegangan/level shifter |
| Sensor 2 | TRIG | GPIO 19 |
| Sensor 2 | ECHO | GPIO 21 melalui pembagi tegangan/level shifter |

Setiap sensor membutuhkan pembagi ECHO sendiri:

- ECHO sensor 1 -> resistor 1 kOhm -> titik GPIO 18; dari titik GPIO 18 -> resistor 2 kOhm -> GND.
- ECHO sensor 2 -> resistor 1 kOhm -> titik GPIO 21; dari titik GPIO 21 -> resistor 2 kOhm -> GND.

Jangan sambungkan ECHO 5 V langsung ke GPIO ESP32. Firmware memicu sensor 1 dan sensor 2 secara bergantian dengan jeda 70 ms untuk mengurangi cross-talk.

## Satu perintah untuk menjalankan

Tes board saja, tanpa memicu sensor:

```powershell
.\run_pilot.ps1 -Mode Board -Port COM7
```

Tes sensor hanya setelah wiring di atas sudah benar:

```powershell
.\run_pilot.ps1 -Mode Sensor -Port COM7 -CaptureSeconds 20 -IConfirmEchoIs3V3
```

GPIO dapat diubah pada environment `hcsr04` di `platformio.ini` bila wiring berbeda.

## Monitor status secara live

Dengan firmware sensor sudah terpasang, jalankan:

```powershell
.\monitor_live.ps1 -Port COM7
```

Monitor terus berjalan sampai `Ctrl+C`. Untuk pengujian berbatas waktu:

```powershell
.\monitor_live.ps1 -Port COM7 -DurationSeconds 20
```

Status hijau berarti sensor menghasilkan ECHO dan jarak valid. Kuning berarti ESP32 dan
firmware aktif tetapi ECHO hanya noise/tidak valid. Merah berarti tidak ada ECHO atau
aliran serial berhenti. HC-SR04 tidak memiliki identitas digital, sehingga kabel yang
sekadar tertancap tidak dapat dideteksi; status sensor disimpulkan dari respons ECHO.

## Kriteria pilot

- Board normal: upload berhasil dan serial memuat `type=board_ready`.
- Sensor terhubung: serial memuat dua `type=sensor_config` dengan `sensor_id` dan GPIO yang benar.
- Pembacaan dasar normal: mayoritas sampel dari masing-masing `sensor_id` bernilai `valid=true`, berada pada 2–400 cm, dan berubah saat target digerakkan.
- `echo_timeout` terus-menerus: periksa VCC/GND, GPIO, pembagi tegangan, orientasi sensor, dan target.

Pilot ini bukan firmware produksi dan belum terintegrasi ke pipeline Bride-Gap.
