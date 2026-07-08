# Prompt Fusion Serial Validation - 2026-07-07

## Tujuan

Validasi ulang mode `gemma_depth_prompted` dilakukan secara serial satu gambar per proses evaluasi untuk menghindari timeout akibat beban batch. Setiap iterasi memakai `--limit-jobs 1` dan `--resume`, sehingga job berikutnya hanya dijalankan setelah job sebelumnya selesai dan berhasil dicatat.

## Perintah

```powershell
python scripts\run_batch_evaluation.py `
  --images-dir dataset\images `
  --annotations dataset\annotations.csv `
  --predictions results\predictions_prompted_serial_20260707_0705.csv `
  --output results\evaluation_prompted_serial_20260707_0705.csv `
  --modes gemma_depth_prompted `
  --resume `
  --limit-jobs 1
```

Perintah di atas dijalankan dalam loop 30 kali agar setiap gambar diproses sebagai satu job terpisah.

## Artifact

- `results/predictions_prompted_serial_20260707_0705.csv`
- `results/evaluation_prompted_serial_20260707_0705.csv`
- `results/predictions_calibrated_with_prompted_20260707.csv`
- `results/evaluation_calibrated_with_prompted_20260707.csv`
- `results/per_image_prompted_serial_20260707.csv`
- `results/prompted_serial_20260707_0705.log`

## Hasil Resmi Evaluator

| Mode | Coverage | Object | Position | Distance | Obstacle | Quality | Avg Latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| gemma_only | 100.00% | 50.00% | 66.67% | N/A | N/A | 3.61/5 | 106,283.5 ms |
| depth_only | 100.00% | 0.00% | 66.67% | 70.00% | 80.00% | 3.17/5 | 978.9 ms |
| gemma_depth | 100.00% | 50.00% | 86.67% | 70.00% | 80.00% | 3.87/5 | 105,423.9 ms |
| gemma_depth_prompted | 100.00% | 46.67% | 93.33% | 70.00% | 80.00% | 3.90/5 | 157,163.7 ms |

## Interpretasi Akademik

Mode `gemma_depth_prompted` berhasil divalidasi secara penuh pada 30 gambar lokal dengan coverage 100% dan tanpa error runtime. Ini memperbaiki status sebelumnya, saat mode Prompt Fusion belum valid karena gagal pada batch awal.

Namun, hasil ini tidak boleh dibaca sebagai kemenangan mutlak. Dibanding `gemma_depth` late fusion, Prompt Fusion hanya menaikkan metrik posisi dari 86.67% menjadi 93.33% dan kualitas deskripsi dari 3.87 menjadi 3.90, tetapi menurunkan object accuracy dari 50.00% menjadi 46.67% dan menaikkan latency rata-rata dari 105.4 detik menjadi 157.2 detik per gambar.

Kesimpulan yang aman: `gemma_depth_prompted` valid sebagai mode pembanding dan menunjukkan sedikit peningkatan pada aspek spasial/tekstual, tetapi trade-off latensinya besar dan akurasi objek tidak membaik.

## Temuan Gagal

Audit exact-match per gambar menunjukkan:

- `main_object` exact mismatch: 24 dari 30 gambar.
- `object_position` exact mismatch: 15 dari 30 gambar.
- `distance_category` mismatch: 9 dari 30 gambar.
- `has_obstacle` mismatch turunan kategori jarak: 6 dari 30 gambar.

Catatan: evaluator resmi memakai aturan evaluasi proyek yang lebih toleran untuk beberapa aspek posisi/spasial, sehingga hasil exact-match manual tidak sama dengan metrik resmi.

## Distance Confusion

| Ground Truth | Prediksi | Jumlah |
|---|---|---:|
| dekat | dekat | 17 |
| dekat | sedang | 2 |
| dekat | sangat_dekat | 1 |
| dekat | jauh | 1 |
| sedang | sedang | 2 |
| sedang | dekat | 3 |
| sangat_dekat | dekat | 2 |
| jauh | jauh | 2 |

## Risiko Sidang

1. Dataset masih kecil, sehingga mode terbaik belum bisa diklaim general.
2. Prompt Fusion jauh lebih lambat dari Late Fusion.
3. Peningkatan kualitas deskripsi sangat kecil, hanya 0.03 poin dari Late Fusion.
4. Prompt Fusion tidak memperbaiki identifikasi objek utama.
5. Kalibrasi threshold depth masih diuji pada dataset yang sama, sehingga perlu split kalibrasi/test atau tambahan data.

## Narasi yang Defensible

Penelitian dapat menyatakan bahwa Depth-to-Spatial Prompting berhasil dijalankan penuh setelah strategi evaluasi serial, dan menghasilkan peningkatan terbatas pada metrik posisi serta kualitas deskripsi dibanding Late Fusion. Namun, mode ini tidak lebih unggul secara keseluruhan karena latency jauh lebih tinggi dan object accuracy sedikit lebih rendah.

## Narasi yang Tidak Aman

Jangan menyatakan bahwa Prompt Fusion adalah mode terbaik secara umum, jangan menyatakan sistem siap real-time, dan jangan menyatakan sistem sudah aman untuk navigasi indoor.
