# A/B Test Prompt Fusion - Gemma vs Qwen - 2026-07-07

## Tujuan

Eksperimen ini membandingkan runtime dan kualitas awal antara `google/gemma-4-e4b` dan `qwen3.5-4b` pada mode `gemma_depth_prompted` atau Depth-to-Spatial Prompting.

Pengujian dilakukan secara serial, satu gambar per job, menggunakan `--resume --limit-jobs 1`. Tidak ada batch inference besar yang dijalankan sekaligus.

## Subset Uji

Subset berisi 10 gambar dari `dataset/sample_new`:

| Image | Distance GT | Obstacle GT | Position GT |
|---|---|---|---|
| `1 (5).jpg` | dekat | yes | tengah |
| `1 (31).jpg` | dekat | yes | kanan |
| `1 (8390).jpg` | dekat | yes | kiri |
| `1 (40).jpg` | dekat | yes | tengah |
| `1 (34).jpg` | sedang | no | tengah |
| `1 (6083).jpg` | sedang | no | kanan |
| `1 (6082).jpg` | sedang | no | kanan |
| `1 (6845).jpg` | sedang | no | tengah |
| `1 (7248).jpg` | jauh | no | tengah |
| `1 (7254).jpg` | jauh | no | tengah |

Distribusi subset:

- `dekat`: 4
- `sedang`: 4
- `jauh`: 2
- `has_obstacle=yes`: 4
- `has_obstacle=no`: 6

## Artifact

- `results/ab_model_prompted_20260707/annotations.csv`
- `results/ab_model_prompted_20260707/gemma_predictions.csv`
- `results/ab_model_prompted_20260707/gemma_predictions_1200.csv`
- `results/ab_model_prompted_20260707/qwen_predictions_4096.csv`
- `results/ab_model_prompted_20260707/qwen_evaluation_4096.csv`
- `results/ab_model_prompted_20260707/gemma_serial.log`
- `results/ab_model_prompted_20260707/gemma_serial_1200.log`
- `results/ab_model_prompted_20260707/qwen_serial_4096.log`

## Konfigurasi

### Gemma

Model:

`google/gemma-4-e4b`

Diuji dua kali:

1. `LM_STUDIO_MAX_TOKENS=4096`
2. `LM_STUDIO_MAX_TOKENS=1200`

### Qwen

Model:

`qwen3.5-4b`

Konfigurasi:

`LM_STUDIO_MAX_TOKENS=4096`

Qwen menggunakan 4096 token karena uji sebelumnya dengan 1200 token menghasilkan JSON yang terpotong akibat reasoning content.

## Hasil Gemma

Gemma gagal pada gambar pertama `1 (31).jpg` dalam dua konfigurasi:

| Konfigurasi | Success | Error | Latency |
|---|---:|---:|---:|
| Gemma 4096 | 0 | 2 retry gagal | sekitar 242 detik per retry |
| Gemma 1200 | 0 | 2 retry gagal | sekitar 243 detik per retry |

Error:

`Gemma inference failed. Please ensure LM Studio is running and the model is loaded.`

Loop dihentikan agar tidak mengulang gambar yang sama berulang kali, karena mekanisme `--resume` hanya melewati job yang sukses.

## Hasil Qwen

Qwen menyelesaikan 10/10 gambar tanpa error runtime.

| Metric | Nilai |
|---|---:|
| Prediction coverage | 100.00% |
| Object accuracy | 0.00% |
| Position accuracy | 100.00% |
| Distance category accuracy | 40.00% |
| Obstacle warning accuracy | 70.00% |
| Description quality | 3.10/5 |
| Average latency | 98,911.8 ms |

Latency per gambar:

| Image | Latency |
|---|---:|
| `1 (31).jpg` | 175,781 ms |
| `1 (34).jpg` | 104,529 ms |
| `1 (40).jpg` | 80,499 ms |
| `1 (5).jpg` | 71,843 ms |
| `1 (6082).jpg` | 110,716 ms |
| `1 (6083).jpg` | 75,974 ms |
| `1 (6845).jpg` | 64,975 ms |
| `1 (7248).jpg` | 90,690 ms |
| `1 (7254).jpg` | 108,628 ms |
| `1 (8390).jpg` | 105,483 ms |

## Temuan Kritis

Qwen lebih stabil daripada Gemma pada kondisi uji ini, tetapi hasil semantik objek buruk. Semua `main_object` gagal exact match.

Contoh mismatch:

| Image | Ground Truth | Qwen |
|---|---|---|
| `1 (31).jpg` | rak toko | ruangan dengan lantai kayu |
| `1 (34).jpg` | meja konsol | tempat tidur |
| `1 (6083).jpg` | bangku ruang ganti | tempat tidur dengan selimut |
| `1 (8390).jpg` | pot tanaman | tempat tidur |

Ini menunjukkan risiko bahwa model `qwen3.5-4b` yang aktif di LM Studio belum cocok sebagai vision-language model untuk identifikasi objek, atau image input tidak dipahami dengan baik oleh model tersebut.

## Keputusan Sementara

Qwen belum aman dijadikan model utama final.

Alasannya:

1. Qwen memang lebih stabil secara runtime pada subset ini.
2. Qwen menyelesaikan semua job tanpa error.
3. Namun object accuracy 0.00% terlalu lemah untuk sistem image description.
4. Beberapa prediksi objek tampak tidak sesuai gambar, sehingga perlu verifikasi apakah model Qwen yang dipakai benar-benar vision-capable.
5. Gemma saat ini gagal pada runtime subset ini, tetapi hasil historis Gemma sebelumnya masih lebih baik pada semantik objek.

## Rekomendasi Lanjut

1. Verifikasi apakah `qwen3.5-4b` di LM Studio benar model vision, bukan text-only model.
2. Jalankan uji `gemma_only`/visual-only satu gambar pada Qwen tanpa metadata depth untuk melihat apakah model benar-benar membaca gambar.
3. Jika ingin Qwen sebagai model utama, gunakan varian Qwen-VL atau Qwen vision-capable yang stabil di LM Studio.
4. Jangan mengganti model utama hanya berdasarkan latency sampai semantic object test lulus.
5. Untuk naskah skripsi, istilah mode sebaiknya digeneralisasi menjadi `Vision-Language Model Only`, `Depth Only`, `Late Fusion`, dan `Depth-to-Spatial Prompting`, agar model bisa diganti tanpa merusak struktur metodologi.
