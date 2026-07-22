# Arsip Historis Eksperimen Depth 2026-07-22

> **Status: HISTORICAL — NOT ACTIVE.** Arsip ini hanya menyimpan provenance eksperimen yang menyebabkan Depth Anything V2 Metric Indoor Small dikeluarkan dari scope dan runtime aktif. Berkas di direktori ini tidak boleh dibaca oleh runtime sebagai konfigurasi, dataset aktif, atau bukti akurasi jarak.

## Keputusan

Depth Anything V2 Metric Indoor Small tidak lagi digunakan dalam scope aktif proyek. Bukti enam capture berpasangan menunjukkan selisih yang besar terhadap pembacaan frontal HC-SR04, sedangkan rancangan capture tidak menyediakan ground truth fisik dan tidak memastikan kedua sumber mengukur permukaan atau piksel yang sama. Karena itu, selisih ini tidak dapat diperbaiki atau dibela hanya dengan rumus skala global, dan juga tidak boleh diklaim sebagai pengukuran akurasi model depth.

Paper, CSV evaluasi lama, serta prototype depth dipertahankan di lokasi asalnya sebagai provenance penelitian/negative finding. Keberadaannya bukan penanda fitur aktif.

## Snapshot bukti inti

- `analysis_runs.jsonl`: snapshot lengkap log analisis; menjadi sumber utama untuk enam output `hybrid_fusion` berstatus sensor `paired` pada 2026-07-22.
- `sensor_captures.jsonl`: snapshot delapan capture sensor, termasuk enam capture `hybrid_fusion` berpasangan yang digunakan pada ringkasan di bawah.
- `predictions.csv`: snapshot ekspor prediksi lama. Hanya lima dari enam capture tersebut memiliki kolom sensor/depth terisi; capture 03:12 tetap tersedia secara lengkap di `analysis_runs.jsonl` dan `sensor_captures.jsonl`.
- `SHA256SUMS`: checksum dan ukuran byte untuk memverifikasi bahwa ketiga snapshot tidak berubah.

## Enam capture berpasangan

Angka sensor efektif pada implementasi historis adalah nilai minimum dari dua HC-SR04, bukan rata-ratanya.

| Waktu UTC | Depth (cm) | Sensor 1 (cm) | Sensor 2 (cm) | Sensor historis min (cm) | Selisih historis (cm) |
|---|---:|---:|---:|---:|---:|
| 2026-07-22 03:12:18 | 89.45 | 37.27 | 36.17 | 36.17 | +53.28 |
| 2026-07-22 05:52:30 | 134.94 | 43.48 | 43.96 | 43.48 | +91.46 |
| 2026-07-22 06:56:36 | 125.13 | 47.30 | 48.24 | 47.30 | +77.83 |
| 2026-07-22 07:38:52 | 109.27 | 48.12 | 48.45 | 48.12 | +61.15 |
| 2026-07-22 07:45:26 | 140.23 | 54.19 | 54.66 | 54.19 | +86.04 |
| 2026-07-22 07:53:26 | 273.51 | 94.50 | 95.18 | 94.50 | +179.01 |

Dengan definisi historis `error = depth_cm - min(sensor_1_cm, sensor_2_cm)`:

- signed bias = **+91.462 cm**;
- MAE = **91.462 cm**;
- RMSE = **100.373 cm**.

Jika snapshot yang sama dihitung ulang menggunakan base case baru `sensor_mean = (sensor_1 + sensor_2) / 2`, hasilnya tetap besar: signed bias/MAE **+91.128 cm** dan RMSE **100.076 cm**. Perubahan agregasi sensor tidak menyelesaikan ketidakcocokan observasi.

## Batas interpretasi

- Tidak ada jarak ground truth yang diukur dengan meter/alat referensi independen pada enam capture ini.
- Estimasi depth merupakan statistik full-frame (`full_frame_metric_low_tail_median`), sedangkan HC-SR04 membaca cone frontal yang jarang.
- Tidak tersedia kalibrasi ekstrinsik, ROI yang sama, atau bukti bahwa depth dan sensor mengenai permukaan yang sama.
- HC-SR04 tidak memberikan identitas objek dan tidak dapat dianggap sebagai ground truth untuk objek yang disebut VLM.
- Enam capture pada satu rangkaian uji tidak cukup untuk mempelajari rumus koreksi yang dapat digeneralisasi. Fitting offset/skala pada data ini akan menjadi overfitting tanpa target ground truth yang sah.

Arsip ini mendukung keputusan penghapusan depth dari sistem aktif, bukan klaim bahwa HC-SR04 membuktikan error absolut Depth Anything V2 sebesar angka di atas.
