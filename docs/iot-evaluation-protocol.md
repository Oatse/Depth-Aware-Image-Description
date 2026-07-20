# Protokol evaluasi IoT

Gunakan target planar yang sama untuk capture paired pada beberapa jarak terukur. Catat `ground_truth_cm` dari alat ukur eksternal, dua pembacaan sensor, waktu capture yang telah dinormalisasi, status evidence, versi calibration profile, latency Gemma + depth, dan skor deskripsi untuk `gemma_depth` serta `iot_assisted`.

Manifest harus memuat kolom pada `dataset/iot_capture_manifest.example.csv`. Jalankan:

```powershell
python scripts/run_iot_capture_protocol.py dataset/iot_capture_manifest.csv --output results/iot_metrics.json
```

Laporkan pairing coverage, partial/conflict/stale rate, offset waktu, sensor disagreement, absolute error terhadap ground truth, sensor-depth consistency, latency overhead, dan delta kualitas deskripsi secara terpisah. Jangan menggunakan pembacaan sensor sebagai ground truth untuk sensor itu sendiri.
