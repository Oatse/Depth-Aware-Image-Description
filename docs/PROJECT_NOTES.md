# Project Notes

> Catatan kronologis. Keputusan aktif terbaru mengikuti `methodological_upgrade_20260714.md`; Depth-to-Spatial Prompting tidak lagi menjadi fitur sistem.

## Implementation Direction

Proyek ini adalah prototype implementasi dan evaluasi model, bukan aplikasi mobile production-ready. Fokus utama adalah pipeline:

```text
Web Interface -> Python Backend -> Gemma -> Depth Anything V2 Metric Indoor Small -> Fusion -> Evaluation Result
```

Per 2026-07-05, fusion dibagi menjadi dua strategi eksplisit:

1. `gemma_only`: Gemma Baseline. Gemma membaca deskripsi visual dan relasi spasial kualitatif dari gambar saja, tanpa metadata depth eksplisit.
2. `gemma_depth`: late/rule-based fusion. Gemma dan depth dijalankan terpisah, lalu sistem menyusun deskripsi akhir dari deskripsi visual dan ringkasan depth.
3. `gemma_depth_prompted`: Depth-to-Spatial Prompting. Depth dijalankan lebih dulu, metadata region/kategori kedalaman relatif masuk ke prompt Gemma, lalu Gemma menghasilkan deskripsi visual-spasial.

`gemma_depth` dipertahankan sebagai baseline ablation, bukan metode utama. UI juga menampilkan provenance highlighting agar pembaca dapat membedakan sumber teks Gemma, depth, inferensi, dan template.

## Known Issues

| Date | Issue | Impact | Temporary Handling | Next Action |
|---|---|---|---|---|
| 2026-06-30 | Model Gemma dan Depth Anything belum diverifikasi tersedia secara lokal. | Pipeline inferensi belum bisa diuji penuh. | Gunakan konfigurasi `.env.example`; mock hanya boleh aktif lewat `GEMMA_MOCK=true` atau `DEPTH_MOCK=true`. | Implementasikan adapter model dan health check pada step berikutnya. |
| 2026-06-30 | Threshold depth perlu kalibrasi dengan dataset indoor proyek. | Kategori jarak awal dapat bersifat sementara. | Gunakan threshold dari dokumen inisiasi saat modul depth analysis dibuat. | Catat hasil kalibrasi setelah dataset tersedia. |
| 2026-06-30 | Environment aktif menggunakan Python 3.13.3. | Beberapa dependency model seperti `onnxruntime` dapat belum stabil untuk Python 3.13. | Step 1 tetap valid karena hanya scaffold; gunakan Python 3.10 atau 3.11 jika instalasi dependency gagal. | Verifikasi instalasi dependency pada step backend/model berikutnya. |
| 2026-06-30 | Evaluasi contoh dapat menghasilkan skor 0 jika `results/predictions.csv` belum memiliki baris dengan `image_name` yang cocok dengan `dataset/annotations.csv`. | Metrik sample belum merepresentasikan performa model. | Script tetap berjalan dan menulis CSV. | Jalankan analisis pada gambar dataset yang sama sebelum menghitung metrik eksperimen. |
| 2026-06-30 | LM Studio memiliki native `/api/v1/chat`, tetapi prototype memakai OpenAI-compatible `/v1/chat/completions`. | Native API belum digunakan untuk inferensi. | Health check memakai `/v1/models`; inference memakai `/v1/chat/completions`. | Pertimbangkan native API hanya jika payload vision dan response schema sudah dikunci. |
| 2026-07-05 | `gemma_depth` lama terlalu mudah dibaca sebagai tempelan late fusion jika dijadikan metode utama. | Kontribusi depth terhadap proses deskripsi kurang kuat secara eksperimen. | Tambahkan `gemma_depth_prompted` sebagai mode Depth-to-Spatial Prompting dan pertahankan `gemma_depth` sebagai ablation. | Evaluasi ulang dataset untuk mode baru sebelum memakai angka final terbaru. |
| 2026-07-05 | Tabel compare dapat membuat Gemma Baseline tampak tidak powerful karena field depth tampil sebagai tidak tersedia. | Pembaca dapat salah memahami metadata depth yang tidak diekstrak sebagai kegagalan Gemma. | Prompt Gemma Baseline diperkuat untuk relasi spasial visual kualitatif, UI memakai istilah "tidak diekstrak sebagai metadata depth", compare UI memakai late fusion kontrol dari hasil Gemma Baseline + Depth-only yang sama, dan evaluator menandai metrik depth Gemma-only sebagai N/A. | Evaluasi dataset ulang dari predictions bersih setelah perubahan ini. |
| 2026-07-05 | Deskripsi akhir prompted mode dapat tidak menyebut potensi halangan walau depth insight sudah mendeteksinya. | Output utama kurang lengkap untuk variabel evaluasi obstacle warning. | Final description prompted mode kini menambahkan kalimat potensi halangan visual secara guarded, dan peta kedalaman memakai overlay grid 3x3 untuk menjelaskan arti area seperti tengah-kiri atau bawah-tengah. | Recheck UI dan evaluasi ulang dataset setelah perubahan final-description. |

## Verification Notes

| Date | Check | Result |
|---|---|---|
| 2026-06-30 | Dependency install dari `requirements.txt` pada Python 3.13.3 | Berhasil, termasuk `onnxruntime`. |
| 2026-06-30 | Depth Anything ONNX dari `model_weights/Depth-Anything-V2-Metric-Indoor-Small-hf` | Berhasil inference nyata pada gambar dummy, output depth shape `(518, 518)`. |
| 2026-06-30 | LM Studio API info dari user | Implementasi dikonfirmasi memakai endpoint OpenAI-compatible yang didukung LM Studio. |
| 2026-07-05 | Subset test mode baru | `python -m pytest tests\test_depth_prompting.py tests\test_fusion.py::test_prompted_fusion_marks_final_description_as_prompted_gemma tests\test_api.py::test_analyze_endpoint_accepts_depth_to_spatial_prompted_mode tests\test_experiment_preflight.py::test_preflight_accepts_depth_to_spatial_prompted_mode tests\test_depth_analysis.py::test_analyze_depth_regions_prioritizes_nearest_front_region -q` -> 5 passed. |
