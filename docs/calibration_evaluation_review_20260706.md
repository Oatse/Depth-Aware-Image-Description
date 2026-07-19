# Calibration Evaluation Review

> Arsip historis. Status metode aktif mengikuti `methodological_upgrade_20260714.md`; mode Depth-to-Spatial Prompting telah dipensiunkan setelah evaluasi image-aware 44 citra.

Tanggal: 2026-07-06

## Perubahan Yang Dilakukan

Kalibrasi dilakukan pada threshold kategori kedalaman di `services/depth_analysis.py`.

Threshold lama:

- `sangat_dekat`: `< 0.5`
- `dekat`: `< 1.0`
- `sedang`: `< 2.0`
- `jauh`: `>= 2.0`

Threshold baru:

- `sangat_dekat`: `< 1.0`
- `dekat`: `< 1.6`
- `sedang`: `< 2.4`
- `jauh`: `>= 2.4`

Alasan perubahan: profil `results/depth_calibration_profile_20260706.csv` menunjukkan mayoritas objek yang dianotasi `dekat` memiliki nilai p10 depth pada rentang sekitar 1.0-1.9, sehingga threshold lama terlalu ketat dan hampir selalu mengubah `dekat` menjadi `sedang`.

## Perbaikan Evaluator

Evaluator sekarang menulis `prediction_coverage` agar mode yang incomplete tidak terlihat seolah-olah valid. Ini penting karena `gemma_depth_prompted` sempat gagal/timeout dan sebelumnya dapat menyesatkan pembacaan summary.

## Artefak Evaluasi Baru

- `results/predictions_calibrated_20260706.csv`
- `results/evaluation_calibrated_20260706.csv`
- `results/evaluation_calibrated_cli_20260706.csv`
- `results/per_image_calibrated_20260706.csv`
- `results/depth_calibrated_profile_20260706.csv`

## Hasil Sebelum vs Sesudah

| Mode | Metric | Sebelum | Sesudah |
|---|---:|---:|---:|
| `depth_only` | Distance accuracy | 26.67% | 70.00% |
| `depth_only` | Obstacle accuracy | 26.67% | 80.00% |
| `depth_only` | Quality | 2.20/5 | 3.17/5 |
| `gemma_depth` | Distance accuracy | 26.67% | 70.00% |
| `gemma_depth` | Obstacle accuracy | 26.67% | 80.00% |
| `gemma_depth` | Quality | 2.90/5 | 3.87/5 |
| `gemma_depth` | Object accuracy | 50.00% | 50.00% |
| `gemma_depth` | Position accuracy | 86.67% | 86.67% |

Hasil akhir dari CLI evaluator:

| Mode | Coverage | Object | Position | Distance | Obstacle | Quality | Latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| `gemma_only` | 100% | 50.00% | 66.67% | N/A | N/A | 3.61/5 | 106.3s |
| `depth_only` | 100% | 0.00% | 66.67% | 70.00% | 80.00% | 3.17/5 | 0.98s |
| `gemma_depth` | 100% | 50.00% | 86.67% | 70.00% | 80.00% | 3.87/5 | 105.4s |

## Confusion Setelah Kalibrasi

Distribusi prediksi depth setelah kalibrasi:

- `dekat`: 22 gambar
- `sedang`: 4 gambar
- `jauh`: 3 gambar
- `sangat_dekat`: 1 gambar

Confusion penting:

- Dari 21 label `dekat`, 17 benar menjadi `dekat`.
- Dari 2 label `jauh`, 2 benar menjadi `jauh`.
- Dari 5 label `sedang`, hanya 2 benar; 3 bergeser menjadi `dekat`.
- Dari 2 label `sangat_dekat`, 0 benar; keduanya menjadi `dekat`.

## Analisis Keras

Kalibrasi berhasil memperbaiki masalah utama: threshold lama terlalu sering membaca objek dekat sebagai sedang. Namun hasil ini belum boleh dibaca sebagai bukti umum bahwa depth-aware description sudah kuat.

Kelemahan yang masih tersisa:

1. `sangat_dekat` belum berhasil dibaca sebagai `sangat_dekat`.
2. Sebagian label `sedang` sekarang bergeser menjadi `dekat`.
3. Dataset hanya 30 gambar dan sangat homogen.
4. Threshold baru dipilih dari dataset yang sama dengan data evaluasi, sehingga ada risiko overfit.
5. `gemma_depth_prompted` belum punya evaluasi valid karena runtime Gemma gagal/timeout.
6. Latency Gemma sekitar 105 detik per gambar, terlalu lambat untuk klaim aplikasi interaktif.

## Implikasi Akademik

Narasi yang sekarang lebih aman:

> Setelah kalibrasi threshold depth terhadap dataset lokal, integrasi depth meningkatkan akurasi kategori kedalaman relatif dan peringatan potensi halangan pada dataset pilot 30 gambar. Namun, hasil ini masih terbatas pada dataset lokal dan belum membuktikan generalisasi ke lingkungan indoor lain.

Narasi yang belum aman:

> Sistem ini sudah terbukti membantu navigasi indoor.

Narasi itu harus dihindari karena tidak ada user study, tidak ada sensor jarak aktual, dan latency masih terlalu tinggi.

## Rekomendasi Berikutnya

1. Pisahkan dataset kalibrasi dan dataset uji. Minimal 15 gambar untuk kalibrasi dan 30-50 gambar berbeda untuk uji.
2. Tambah gambar dari lokasi indoor lain agar threshold tidak overfit ke rumah/kamar yang sama.
3. Ukur jarak manual dengan meteran untuk subset data agar label `sangat_dekat`, `dekat`, `sedang`, dan `jauh` lebih defensible.
4. Jalankan ulang `gemma_depth_prompted` hanya setelah LM Studio stabil; jika tidak, turunkan mode itu menjadi future work.
5. Tambahkan evaluasi manual kualitas deskripsi dari minimal dua penilai.

## Putusan

Perbaikan ini membuat penelitian lebih defensible daripada sebelumnya. Sebelum kalibrasi, klaim depth lemah karena distance accuracy hanya 26.67%. Setelah kalibrasi, klaim depth mulai punya bukti awal karena distance accuracy naik menjadi 70.00% dan obstacle accuracy menjadi 80.00%.

Tetapi sebagai dosbing/penguji, saya tetap akan menekan bagian ini: hasil tersebut masih pilot, belum general, dan berisiko overfit karena threshold dikalibrasi dan diuji pada dataset yang sama.
