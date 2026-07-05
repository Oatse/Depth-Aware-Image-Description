# Depth-Aware Image Description

Prototype penelitian untuk implementasi depth-aware image description pada citra lingkungan indoor. Sistem menggabungkan Gemma sebagai vision-language model dan Depth Anything V2 Metric Indoor Small sebagai model estimasi kedalaman, lalu menghasilkan deskripsi akhir Bahasa Indonesia melalui fusion berbasis aturan.

Proyek ini adalah proof-of-concept implementasi model, bukan aplikasi navigasi production-ready.

## Scope

- Web interface sederhana berbasis HTML, CSS, dan JavaScript vanilla.
- Backend Python FastAPI untuk upload gambar dan pipeline analisis.
- Integrasi Gemma melalui endpoint lokal LM Studio yang kompatibel OpenAI.
- Integrasi Depth Anything V2 Metric Indoor Small dari folder `model_weights/`.
- Rule-based fusion untuk menggabungkan deskripsi visual dan ringkasan depth.
- Logging hasil inferensi dan evaluasi berbasis CSV.

## Non-Scope

- Aplikasi mobile React Native atau Expo.
- Voice trigger, speech recognition, dan text-to-speech sebagai fitur utama.
- Login, database, dashboard kompleks, dan deployment production.
- Klaim navigasi aman, real-time navigation system, atau pengukuran jarak presisi.

## Arsitektur

```text
Web Interface
  -> FastAPI Backend
  -> Image Validation + Preprocessing
  -> Gemma Client
  -> Depth Anything V2 Metric Indoor Small
  -> 9-Region Depth Analysis
  -> Rule-Based Fusion
  -> Prediction Log + Evaluation CSV
```

## Struktur Folder

```text
app/                 FastAPI app, config, schema, routes
models/              Gemma client, Depth Anything adapter, fusion rules
services/            Validation, preprocessing, depth analysis, logging, evaluator
static/              CSS dan JavaScript UI
templates/           HTML template
dataset/             Gambar dan annotation CSV
model_weights/       Bobot Depth Anything lokal
results/             Prediction, evaluation, depth maps
tests/               Pytest suite
scripts/             CLI tools dan smoke test
```

## Setup Development

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Environment aktif saat verifikasi menggunakan Python 3.13.3 dan dependency berhasil terpasang, termasuk `onnxruntime`.

## Konfigurasi

Salin `.env.example` ke `.env` jika ingin mengubah konfigurasi:

```bash
copy .env.example .env
```

Variabel penting:

- `LM_STUDIO_URL=http://localhost:1234`
- `LM_STUDIO_MODEL=gemma-4-e4b-it`
- `LM_STUDIO_HEALTH_TIMEOUT=2`
- `DEPTH_MODEL_PATH=./model_weights/Depth-Anything-V2-Metric-Indoor-Small-hf`
- `GEMMA_MOCK=false`
- `DEPTH_MOCK=false`

Mock hanya aktif jika eksplisit diset ke `true`. Jangan gunakan hasil mock sebagai hasil eksperimen final.

Integrasi Gemma saat ini memakai endpoint OpenAI-compatible LM Studio:

- `GET /v1/models` untuk health check ringan.
- `POST /v1/chat/completions` untuk inferensi vision-language.

LM Studio native v1 REST API di `/api/v1/*` tetap bisa dipertimbangkan nanti, tetapi prototype ini sengaja memakai OpenAI-compatible endpoint karena payload image chat-nya sesuai kebutuhan dan stabil untuk client lokal.

## Menjalankan Backend

```bash
uvicorn app.main:app --reload
```

Buka:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/health`

## Menggunakan UI

1. Pilih gambar JPG, PNG, atau WebP.
2. Pilih mode:
   - `gemma_depth`
   - `gemma_only`
   - `depth_only`
3. Klik `Analyze`.
4. UI menampilkan final description, deskripsi Gemma, depth summary, latency, dan depth map jika tersedia.

Kamera browser tersedia sebagai opsi tambahan. Upload gambar tetap menjadi fallback utama.

## API

### `GET /health`

Mengembalikan status backend, Gemma, dan model depth.

### `POST /analyze`

Form data:

- `image`: file JPG, PNG, atau WebP.
- `mode`: `gemma_only`, `depth_only`, atau `gemma_depth`.
- `save_result`: `true` atau `false`.

Response utama berisi:

- `success`
- `final_description`
- `gemma_description`
- `depth_summary`
- `latency`
- `mode`
- `depth_map_url`
- `mock`
- `error`

## CLI

Menjalankan satu gambar:

```bash
python scripts\run_single_image.py dataset\images\img_001.jpg --mode gemma_depth
```

Membuat annotation template dari folder gambar:

```bash
python scripts\generate_sample_annotations.py
```

Menjalankan evaluasi:

```bash
python scripts\run_evaluation.py --annotations dataset\annotations.csv --predictions results\predictions.csv --output results\evaluation.csv
```

Memeriksa kesiapan eksperimen sebelum inference final:

```bash
python scripts\run_batch_evaluation.py --preflight-only
```

Menjalankan batch inference dan evaluasi perbandingan:

```bash
python scripts\run_batch_evaluation.py --images-dir dataset\images --annotations dataset\annotations.csv
```

Gunakan `--allow-mock` hanya untuk dry run development. Hasil mock tidak boleh dipakai sebagai hasil eksperimen skripsi final.

Smoke test dengan server sementara dan mock eksplisit:

```bash
python scripts\smoke_test.py --start-server
```

## Testing

```bash
python -m pytest -q
```

Coverage test saat ini:

- API health dan analyze dengan mock.
- Validasi upload.
- Preprocessing gambar.
- Depth region analysis.
- Fusion rule.
- Evaluator CSV.

## Evaluasi

`dataset/annotations.csv` adalah ground truth manual. `results/predictions.csv` berisi output pipeline. `scripts/run_evaluation.py` membandingkan keduanya dan menulis `results/evaluation.csv`.

Protokol detail tersedia di [docs/evaluation_protocol.md](docs/evaluation_protocol.md).

Metrik awal:

- object mention accuracy;
- position accuracy;
- distance category accuracy;
- obstacle warning accuracy;
- description quality heuristic 1-5;
- average latency.

Jika prediction belum cocok dengan `image_name` di annotation, skor dapat bernilai 0. Itu berarti dataset/prediction belum selaras, bukan hasil eksperimen final.

## Troubleshooting

- Gemma gagal: pastikan LM Studio berjalan, model vision-language sudah loaded, dan `LM_STUDIO_URL` benar.
- Jika `/health` menampilkan `gemma=model_not_loaded`, buka LM Studio dan load model sesuai `LM_STUDIO_MODEL`.
- Jika `/health` menampilkan `gemma=error`, LM Studio kemungkinan belum berjalan atau port `LM_STUDIO_URL` belum benar.
- Depth gagal: pastikan `DEPTH_MODEL_PATH` mengarah ke folder yang berisi file `.onnx`.
- Untuk demo tanpa model: set `GEMMA_MOCK=true` dan/atau `DEPTH_MOCK=true` secara eksplisit.
- Jika port 8000 dipakai proses lain, jalankan Uvicorn di port berbeda dan sesuaikan URL smoke test.

## Keterbatasan

- Depth digunakan sebagai estimasi kategori, bukan pengukuran centimeter presisi.
- Output fusion bersifat rule-based dan perlu evaluasi dataset yang lebih besar.
- Prototype belum divalidasi untuk penggunaan navigasi nyata.
- Tidak ada database atau sistem multi-user.
