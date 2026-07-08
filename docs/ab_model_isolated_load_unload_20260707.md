# A/B Test Isolated Load/Unload - Gemma e2b vs Qwen - 2026-07-07

## Tujuan

Eksperimen ini mengulang A/B test dengan kontrol runtime yang lebih ketat: hanya satu model LLM yang dimuat pada satu waktu. Model di-load hanya saat dipakai, diuji secara serial satu gambar per job, lalu di-unload setelah selesai.

## Prosedur

1. Unload semua LLM aktif dari LM Studio.
2. Load satu model.
3. Jalankan `gemma_depth_prompted` dengan `--resume --limit-jobs 1`.
4. Ulangi sampai 10 gambar sukses.
5. Unload model.
6. Pindah ke model berikutnya.

Subset uji sama dengan A/B test sebelumnya:

`results/ab_model_isolated_20260707/images`

## Catatan Load Model

Qwen dapat di-load lewat REST API:

`POST /api/v1/models/load`

Gemma e2b gagal di-load lewat REST API default dan sempat gagal juga lewat CLI default. Gemma e2b baru berhasil di-load lewat CLI dengan konfigurasi ringan:

```powershell
lms load google/gemma-4-e2b --identifier google/gemma-4-e2b --context-length 4096 --parallel 1 --gpu max -y
```

Konfigurasi ini penting karena hasil latency berubah drastis.

## Hasil Utama

| Model | Load Mode | Success | Error Row | Object | Position | Distance | Obstacle | Quality | Avg Latency |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Gemma e2b | CLI, context 4096, parallel 1 | 10/10 | 0 | 10.00% | 100.00% | 40.00% | 70.00% | 3.20/5 | 13,661.0 ms |
| Qwen | REST API default | 10/10 | 1 retry | 40.00% | 100.00% | 40.00% | 70.00% | 3.50/5 | 100,248.2 ms |

## Interpretasi

Gemma e2b menjadi jauh lebih cepat dan stabil ketika diuji sendirian dengan konfigurasi load ringan. Rata-rata latency turun menjadi sekitar 13.7 detik per gambar, tanpa error.

Qwen juga menyelesaikan 10 gambar sukses, tetapi membutuhkan 11 attempt karena satu error pada `1 (6845).jpg`. Qwen lebih baik pada object accuracy dan description quality, tetapi jauh lebih lambat.

## Temuan Per Model

### Gemma e2b

Kelebihan:

- Runtime paling cepat.
- 10/10 sukses tanpa error.
- Cocok untuk evaluasi dataset lebih besar karena biaya waktu jauh lebih rendah.

Kelemahan:

- Object accuracy hanya 10.00%.
- Beberapa objek masih generik, misalnya `meja konsol` menjadi `interior ruangan`.

### Qwen

Kelebihan:

- Object accuracy lebih baik dari Gemma e2b pada subset ini.
- Description quality lebih tinggi.

Kelemahan:

- Latency rata-rata sekitar 100 detik per gambar.
- Sempat error satu kali dan butuh retry.
- Tetap gagal pada sebagian distance karena prediksi depth menghasilkan kategori yang sama-sama meleset dari ground truth.

## Keputusan Sementara

Jika prioritas utama adalah eksperimen skripsi yang selesai dan stabil, `google/gemma-4-e2b` dengan load config ringan lebih masuk akal sebagai model utama runtime.

Jika prioritas utama adalah kualitas semantik objek, Qwen menarik sebagai pembanding, tetapi latency-nya terlalu mahal untuk evaluasi dataset besar.

Rekomendasi praktis:

1. Gunakan Gemma e2b sebagai model utama final untuk run dataset penuh.
2. Load Gemma e2b dengan:
   `context-length 4096`, `parallel 1`, `gpu max`.
3. Simpan Qwen sebagai pembanding tambahan terbatas, bukan main model.
4. Jangan mencampur hasil dari model yang loaded bersamaan dengan hasil isolated; untuk Bab 4, gunakan hasil isolated karena kontrol eksperimennya lebih bersih.

## Artifact

- `results/ab_model_isolated_20260707/gemma_e2b_isolated_predictions_1200.csv`
- `results/ab_model_isolated_20260707/gemma_e2b_isolated_evaluation_1200.csv`
- `results/ab_model_isolated_20260707/qwen_isolated_predictions_4096.csv`
- `results/ab_model_isolated_20260707/qwen_isolated_evaluation_4096.csv`
- `results/ab_model_isolated_20260707/gemma_e2b_isolated_lifecycle.log`
- `results/ab_model_isolated_20260707/qwen_isolated_lifecycle.log`
