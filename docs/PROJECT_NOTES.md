# Project Notes

## Implementation Direction

Proyek ini adalah prototype implementasi dan evaluasi model, bukan aplikasi mobile production-ready. Fokus utama adalah pipeline:

```text
Web Interface -> Python Backend -> Gemma -> Depth Anything V2 Metric Indoor Small -> Fusion -> Evaluation Result
```

## Known Issues

| Date | Issue | Impact | Temporary Handling | Next Action |
|---|---|---|---|---|
| 2026-06-30 | Model Gemma dan Depth Anything belum diverifikasi tersedia secara lokal. | Pipeline inferensi belum bisa diuji penuh. | Gunakan konfigurasi `.env.example`; mock hanya boleh aktif lewat `GEMMA_MOCK=true` atau `DEPTH_MOCK=true`. | Implementasikan adapter model dan health check pada step berikutnya. |
| 2026-06-30 | Threshold depth perlu kalibrasi dengan dataset indoor proyek. | Kategori jarak awal dapat bersifat sementara. | Gunakan threshold dari dokumen inisiasi saat modul depth analysis dibuat. | Catat hasil kalibrasi setelah dataset tersedia. |
| 2026-06-30 | Environment aktif menggunakan Python 3.13.3. | Beberapa dependency model seperti `onnxruntime` dapat belum stabil untuk Python 3.13. | Step 1 tetap valid karena hanya scaffold; gunakan Python 3.10 atau 3.11 jika instalasi dependency gagal. | Verifikasi instalasi dependency pada step backend/model berikutnya. |
| 2026-06-30 | Evaluasi contoh dapat menghasilkan skor 0 jika `results/predictions.csv` belum memiliki baris dengan `image_name` yang cocok dengan `dataset/annotations.csv`. | Metrik sample belum merepresentasikan performa model. | Script tetap berjalan dan menulis CSV. | Jalankan analisis pada gambar dataset yang sama sebelum menghitung metrik eksperimen. |
| 2026-06-30 | LM Studio memiliki native `/api/v1/chat`, tetapi prototype memakai OpenAI-compatible `/v1/chat/completions`. | Native API belum digunakan untuk inferensi. | Health check memakai `/v1/models`; inference memakai `/v1/chat/completions`. | Pertimbangkan native API hanya jika payload vision dan response schema sudah dikunci. |

## Verification Notes

| Date | Check | Result |
|---|---|---|
| 2026-06-30 | Dependency install dari `requirements.txt` pada Python 3.13.3 | Berhasil, termasuk `onnxruntime`. |
| 2026-06-30 | Depth Anything ONNX dari `model_weights/Depth-Anything-V2-Metric-Indoor-Small-hf` | Berhasil inference nyata pada gambar dummy, output depth shape `(518, 518)`. |
| 2026-06-30 | LM Studio API info dari user | Implementasi dikonfirmasi memakai endpoint OpenAI-compatible yang didukung LM Studio. |
