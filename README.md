# Depth-Aware Image Description

Prototype penelitian untuk implementasi depth-aware image description pada citra lingkungan indoor. Sistem menggabungkan Gemma sebagai vision-language model dan Depth Anything V2 Metric Indoor Small sebagai model estimasi kedalaman, lalu menghasilkan deskripsi akhir Bahasa Indonesia melalui fusi regional berbatas bukti.

Proyek ini adalah proof-of-concept implementasi model, bukan aplikasi navigasi production-ready.

## Scope

- Web interface sederhana berbasis HTML, CSS, dan JavaScript vanilla.
- Backend Python FastAPI untuk upload gambar dan pipeline analisis.
- Integrasi Gemma melalui endpoint lokal LM Studio yang kompatibel OpenAI.
- Integrasi Depth Anything V2 Metric Indoor Small dari folder `model_weights/`.
- Fusi regional berbasis aturan yang tidak mengikat estimasi depth suatu area ke objek tanpa bukti lokalisasi.
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
  -> Camera Frame Metadata + Reconnecting ESP32 Serial Bridge
  -> Image Validation + Preprocessing
  -> Bounded In-Process Analysis Queue (polling API)
  -> Gemma Client
  -> Depth Anything V2 Metric Indoor Small
  -> 9-Region Depth Analysis (grid-p10)
  -> Evidence-Constrained Regional Fusion
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

Gunakan `requirements-lock.txt` jika perlu mereplikasi versi environment verifikasi 14 Juli 2026 secara lebih ketat.

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
- `ANALYSIS_QUEUE_CAPACITY=8`
- `ANALYSIS_RETAINED_JOBS=100`
- `EXPERIMENT_ARTIFACT_PROFILE=final_44_gemma_e2b_20260708`
- `EXPERIMENT_IMAGES_DIR=./dataset/final_images`
- `EXPERIMENT_ANNOTATIONS_PATH=./dataset/final_annotations.csv`
- `EXPERIMENT_PREDICTIONS_PATH=./results/final_predictions_active_20260714.csv`
- `EXPERIMENT_EVALUATION_PATH=./results/final_evaluation_metrics_20260714.csv`
- `GEMMA_MOCK=false`
- `DEPTH_MOCK=false`
- `SENSOR_SERIAL_PORT=COM7`
- `SENSOR_SERIAL_BAUD=115200`
- `SENSOR_MATCH_WINDOW_MS=250`
- `SENSOR_MAX_CLOCK_SKEW_MS=5000`
- `SENSOR_RECONNECT_INTERVAL_MS=1000`
- `SENSOR_STATUS_WINDOW_MS=1000`

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
- `http://127.0.0.1:8000/sensor-status`

## Menggunakan UI

1. Pilih gambar JPG, PNG, atau WebP.
2. Pilih mode:
   - `gemma_depth`
   - `gemma_only`
   - `depth_only`
3. Klik `Analyze`.
4. UI menampilkan final description, deskripsi Gemma, depth summary, latency, dan depth map jika tersedia.

Pada tab Kamera, panel Sensor IoT menampilkan koneksi serial dan bacaan dua kanal secara live. Saat frame diambil, browser mengirim `capture_id`, waktu frame, dan arah kamera. Backend memilih sampel valid terdekat dalam jendela `SENSOR_MATCH_WINDOW_MS`. Upload gambar tetap menjadi fallback utama dan tidak membutuhkan sensor.

## API

### `GET /health`

Mengembalikan status backend, Gemma, dan model depth.

### `GET /experiment-status`

Mengembalikan readiness snapshot beserta `artifact_profile` dan semua path sumber. Default menunjuk snapshot final 44 citra, bukan dataset development 30 citra. Path dapat dioverride melalui environment agar dashboard selalu menyatakan artefak yang sedang dibaca.

### `GET /sensor-status`

Mengembalikan status koneksi serial, jumlah percobaan reconnect, bacaan terbaru `sensor_1` dan `sensor_2`, serta umur masing-masing sampel. Reader akan mencoba tersambung kembali secara otomatis sehingga backend tidak perlu direstart ketika ESP32 baru dipasang.

### `POST /analyze`

Form data:

- `image`: file JPG, PNG, atau WebP.
- `mode`: `gemma_only`, `depth_only`, atau `gemma_depth`.
- `save_result`: `true` atau `false`.
- `capture_id`: ID unik frame kamera (opsional untuk upload).
- `capture_time_ms`: Unix time milidetik saat frame kamera diambil (opsional untuk upload).
- `camera_facing_mode`: `environment` atau `user` (opsional untuk upload).

Response utama berisi:

- `success`
- `final_description`
- `gemma_description`
- `depth_summary`
- `latency`
- `mode`
- `depth_map_url`
- `sensor_evidence` untuk capture kamera; evidence ini adalah referensi jarak frontal yang dipasangkan menurut waktu, bukan depth-map atau pengukuran objek terkalibrasi.

Jika penyimpanan hasil aktif, capture kamera juga ditulis ke `results/sensor_captures.jsonl` agar pasangan timestamp, status, dan sampel dua sensor dapat diaudit ulang.
- `mock`
- `error`

### `POST /analysis-jobs`

Menerima form data yang sama dan mengembalikan HTTP 202 beserta `job_id` dan `poll_url`. UI memakai endpoint ini agar request browser tidak menunggu koneksi HTTP tunggal selama inferensi.

### `GET /analysis-jobs/{job_id}`

Mengembalikan status `queued`, `running`, `completed`, atau `failed`. Antrean ini bounded, hanya berlaku pada satu process, tidak persisten, dan kehilangan job saat server restart. Untuk deployment multi-worker/production, gunakan queue eksternal; implementasi saat ini sengaja dibatasi pada kebutuhan prototype lokal.

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

Menjalankan LLM judge image-aware secara blinded dan tiga kali pengulangan melalui 9router lokal:

```powershell
$env:NINEROUTER_API_KEY="<secret>"
python scripts\run_llm_judge.py `
  --predictions results\final_predictions_active_20260714.csv `
  --images-dir dataset\final_images `
  --modes gemma_only depth_only gemma_depth `
  --model cx/gpt-5.5 `
  --base-url http://127.0.0.1:20128/v1 `
  --api-key-env NINEROUTER_API_KEY `
  --repeats 3
```

Judge menerima citra sumber yang dinormalisasi ke JPEG dan dibatasi maksimal 768 piksel sebagai bukti utama, serta anotasi terstruktur sebagai pembanding sekunder. Perintah membutuhkan 9router lokal aktif serta `NINEROUTER_API_KEY`; script berhenti sebelum request bila variabel tersebut tidak tersedia. Jangan menyimpan API key di repo.

Endpoint 9router berada di localhost, tetapi hal itu tidak membuktikan inferensi berlangsung lokal: citra dapat diteruskan ke provider upstream sesuai konfigurasi router. Jalankan hanya pada citra yang izin pemrosesannya mencakup provider tersebut. `cx/gpt-5.5` juga dicatat sebagai label rute/model yang dipakai saat run, bukan otomatis dianggap snapshot provider yang immutable.

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

`dataset/annotations.csv` berisi label manual visual-relatif, bukan ground truth jarak fisik. `results/predictions.csv` berisi output pipeline. `scripts/run_evaluation.py` membandingkan keduanya dan menulis `results/evaluation.csv`.

Protokol detail tersedia di [docs/evaluation_protocol.md](docs/evaluation_protocol.md).
Hash dan jumlah baris artefak aktif tersedia di [docs/evaluation_artifact_manifest_20260714.md](docs/evaluation_artifact_manifest_20260714.md).
Dasar arsitektur, koreksi evaluator, kontrol pasangan, dan trade-off lengkap tersedia di [docs/evidence_constrained_fusion_upgrade_20260714.md](docs/evidence_constrained_fusion_upgrade_20260714.md).

Metrik awal:

- object mention accuracy;
- position accuracy;
- object-position joint accuracy;
- distance category accuracy;
- obstacle warning accuracy;
- obstacle precision, recall, F1, dan TP/FP/TN/FN;
- LLM judge berulang sebagai evaluasi tambahan, bukan ground truth tunggal;
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
- Model checkpoint bertipe metric-indoor, sedangkan label evaluasi adalah visual-relative; keluaran tidak diperlakukan sebagai sensor terkalibrasi.
- Post-processing depth sengaja dibatasi pada grid 3x3 dengan statistik p10; kandidat adaptive bands dihapus setelah eksperimen internal menurunkan obstacle recall dan F1 serta menambah parameter yang harus dipertanggungjawabkan.
- Output fusion bersifat rule-based, membatasi klaim depth pada level area, dan belum mempunyai object box/mask untuk object-depth grounding.
- Judge image-aware menambah biaya, latensi, risiko bias visual/rubric, serta risiko privasi bila router meneruskan citra ke provider eksternal.
- Prototype belum divalidasi untuk penggunaan navigasi nyata.
- Tidak ada database atau sistem multi-user.
