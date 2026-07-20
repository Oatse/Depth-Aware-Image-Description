# Acceptance recheck: Gemma E2B dan kalibrasi sensor

Tanggal: 2026-07-21  
Branch: `feat/complete-iot-assisted-analysis`

## Runtime yang terverifikasi

- LM Studio hanya memuat `google/gemma-4-e2b`, context 4096, parallel 1.
- `/health` melaporkan backend, Gemma E2B, dan depth model `ready`.
- `/sensor-status` melaporkan COM7 `paired` dengan dua sampel segar.
- Inference nyata `gemma_only` melalui `/analyze` berhasil dengan `mock=false`, Gemma latency sekitar 9,9 detik, dan evidence sensor `paired` ikut tercatat.
- Panggilan `iot_assisted` tanpa profil kalibrasi ditolak dengan `sensor_calibration_required`.

## Workflow baru

Panel Kamera menyediakan **Kalibrasi jarak sensor**. Operator memasukkan jarak fisik bidang datar, backend mengambil bacaan dua sensor pada waktu yang sama, menyimpan provenance lokal, dan membangun profil setelah minimal tiga jarak referensi berbeda. Profil hanya `validated` jika residual maksimum tidak melebihi 10 cm.

`/readiness` tetap `ready=false` sampai operator melakukan pengukuran fisik tersebut. Tidak ada profil valid yang dibuat dari bacaan sensor saja.

## QA

- Pytest: 130 passed.
- JavaScript syntax check: passed.
- Python compile check: passed.
- Browser QA: tab Upload/Kamera, panel sensor, status COM7, panel kalibrasi, validasi input jarak tidak valid, dan cache-busting aset UI terverifikasi.
- Browser file chooser tidak tersedia pada lingkungan in-app, sehingga inference real divalidasi melalui endpoint HTTP yang sama.
