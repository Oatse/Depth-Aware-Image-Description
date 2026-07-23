# Bridge-Gap

Bridge-Gap adalah prototipe teknis untuk menghasilkan **deskripsi gambar indoor berbahasa Indonesia** menggunakan `google/gemma-4-e2b` yang dijalankan secara lokal melalui LM Studio. Dua HC-SR04 menyediakan referensi jarak frontal berbasis bidang cakupan (*cone*) sensor. Referensi tersebut adalah bukti tambahan yang terpisah dari isi citra, bukan jarak ke objek yang disebut Gemma.

## Scope kanonik

- Input visual: satu citra RGB dari kamera belakang atau unggahan.
- Model deskripsi: Gemma 4 E2B.
- Sensor: dua HC-SR04 yang dipasang sejajar dan dibaca melalui ESP32-WROOM-32.
- Output utama: satu deskripsi gambar indoor berbahasa Indonesia.
- Output sensor: nilai tiap sensor, status bukti, dan—hanya untuk pasangan valid—rata-rata sebagai referensi jarak frontal.
- Evaluasi: kualitas deskripsi dan akurasi sensor dinilai sebagai dua jalur terpisah.
- Sensor conditioning: hanya referensi `applied` yang masuk ke prompt; backend tetap menambahkan bagian sensor dan provenance secara terpisah.

Sistem tidak mengklaim bahwa angka sensor melekat pada objek bernama, tidak melakukan pemetaan ruang, serta tidak mengklaim keselamatan navigasi atau manfaat bagi pengguna tunanetra tanpa pengujian yang sesuai.

## Arsitektur ringkas

```text
Camera -> capture + snapshot sensor -> results/captures/incoming
                                      -> validasi/kalibrasi evidence
citra RGB + konteks frontal bila applied -> Gemma 4 E2B
deskripsi Gemma + bagian sensor berprovenance -> API/UI/log
```

Tujuan perbandingan `gemma_only` dan `sensor_assisted` adalah mengamati pengaruh
konteks sensor terhadap keluaran dan latency, bukan membuktikan bahwa sensor membuat
deskripsi lebih baik.

Setelah gate pasangan terpenuhi, koreksi linear dari profil kalibrasi diterapkan terpisah pada kedua sensor sebelum rata-rata frontal dibuat:

```text
sensor_1_corrected_cm = intercept_1 + slope_1 * sensor_1_cm
sensor_2_corrected_cm = intercept_2 + slope_2 * sensor_2_cm
frontal_reference_cm = (sensor_1_corrected_cm + sensor_2_corrected_cm) / 2
```

Nilai tersebut ditulis sebagai “referensi jarak frontal sekitar X cm”, bukan “objek X berjarak X cm”. Status `partial`, `stale`, `pair_conflict`, `direction_mismatch`, atau `unavailable` tidak menghasilkan rata-rata pasangan.

## Struktur folder

```text
app/           FastAPI app, routes, konfigurasi, dan schema
models/        klien Gemma dan logika kontribusi sensor
services/      pipeline, sinkronisasi sensor, validasi, dan logging
static/        JavaScript dan CSS UI
templates/     template HTML
scripts/       CLI, preflight, dan alat pengujian
tests/         Pytest suite
docs/          dokumentasi aktif dan pustaka penelitian
instructions/  scope akademik dan kontrak implementasi
results/       paket evaluasi final dan keluaran runtime terpisah
```

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --requirement requirements-lock.txt
Copy-Item .env.example .env
```

Konfigurasi minimum:

```text
LM_STUDIO_URL=http://localhost:1234
LM_STUDIO_MODEL=google/gemma-4-e2b
SENSOR_SERIAL_BAUD=115200
SENSOR_MATCH_WINDOW_MS=250
SENSOR_FRESHNESS_MAX_AGE_MS=1000
SENSOR_PAIR_DISAGREEMENT_CM=15
GEMMA_MOCK=false
```

Nilai konfigurasi aktual tetap mengikuti `app/config.py` dan `.env`; dokumentasi tidak boleh dipakai untuk menebak nilai runtime yang belum diverifikasi.

## Menjalankan backend

Pastikan Gemma sudah dimuat di LM Studio, kemudian jalankan:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Permukaan pemeriksaan:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/readiness`
- `http://127.0.0.1:8000/sensor-status`

Akses perangkat eksternal menggunakan `https://api.mbridgegap.my.id` melalui Cloudflare Tunnel yang meneruskan request ke `http://127.0.0.1:8000`. Origin lokal tetap HTTP dan bind ke loopback.

## Prinsip pengukuran HC-SR04

Sensor ultrasonik mengukur waktu tempuh pulang-pergi gelombang. Prinsip dasarnya:

```text
d = v * t / 2
```

`d` adalah jarak ke permukaan pantul, `v` adalah cepat rambat suara, dan `t` adalah waktu tempuh echo pulang-pergi. Pembagian dua diperlukan karena gelombang bergerak dari sensor ke permukaan lalu kembali. Firmware mengirim `distance_cm`; backend menyimpan nilai, umur sampel, waktu penerimaan, status, dan identitas sensor untuk audit.

Rumus ini tidak mengubah pembacaan cone menjadi identitas objek atau jarak pada piksel tertentu. Koreksi empiris hanya boleh diterapkan setelah kalibrasi terhadap `ground_truth_cm` eksternal pada setup yang ditetapkan dan harus dilaporkan bersama residualnya.

## Alur UI

Alur kamera dipisahkan dari analisis. Masukkan identitas target/scene dan jarak aktual dari bidang kamera (20–200 cm), lalu tekan **Ambil dan simpan**. Backend langsung menyimpan gambar, timestamp, batch runtime, `ground_truth_cm`, acuan muka sensor setelah offset 3 cm, nomor pengulangan otomatis, serta snapshot sensor ke `results/captures/incoming/`. Nilai jarak tetap terisi untuk pengulangan berikutnya. Capture tidak memanggil Gemma.

Dataset v2 final tetap berada di `results/captures/images/dataset_v2_clean/`
beserta manifest dan artefak evaluasinya. Endpoint runtime tidak menulis ke paket
tersebut.

Analisis capture tersimpan dijalankan dari backend sebagai satu job untuk satu capture. Runner menunggu job mencapai status terminal sebelum mengirim capture berikutnya:

```powershell
python scripts/analyze_saved_captures.py
```

Gunakan `--batch-id <batch_id>` hanya bila backend perlu membatasi analisis pada satu batch tertentu.

Panel kalibrasi memakai lima jarak (20, 60, 100, 150, dan 200 cm) dengan 30 pembacaan berpasangan per jarak. Setelah 150 pembacaan valid, profil koreksi dibekukan. Verifikasi dilakukan pada jarak baru 40, 80, 125, dan 175 cm dengan 30 pembacaan per jarak (120 pasangan) untuk mengevaluasi rentang 20–200 cm. Hasil verifikasi disimpan terpisah dan tidak membentuk ulang koefisien. Klaim kinerja sampai 200 cm hanya dibuat setelah seluruh titik verifikasi lengkap dan memenuhi kriteria evaluasi.

Tidak ada pemilih metode, peta jarak visual, atau jarak yang dilekatkan pada objek bernama.

## API utama

- `POST /analyze`: menerima citra dan metadata capture; menghasilkan deskripsi dan evidence sensor bila tersedia.
- `POST /captures`: menyimpan gambar, sensor evidence, dan metadata tanpa menjalankan Gemma.
- `GET /captures` dan `GET /captures/count`: membaca capture tersimpan dari backend.
- `POST /captures/{capture_id}/analysis-jobs`: membuat tepat satu job analisis untuk satu capture tersimpan.
- `GET /sensor-status`: memeriksa koneksi serta sampel sensor terakhir.
- `GET /sensor-calibration`: profil, jumlah sampel, dan model koreksi kalibrasi.
- `POST /sensor-calibration/verification/captures`: menyimpan satu pasangan verifikasi tanpa mengubah kalibrasi.
- `GET /sensor-calibration/verification`: ringkasan MAE/RMSE mentah dan terkoreksi.
- `GET /health`: status proses backend.
- `GET /readiness`: kesiapan dependensi runtime.

Field kompatibilitas lama pada response tidak boleh ditafsirkan sebagai fitur aktif. Kontrak aktif dijelaskan pada `docs/architecture.md`.

## Pengujian

```powershell
python -m pytest -q
```

Selain regression test, pengujian fisik wajib:

- mengukur tiap HC-SR04 terhadap `ground_truth_cm` eksternal pada target planar terkendali;
- menyimpan nilai mentah, kegagalan baca, status, waktu, dan kondisi setup;
- menilai deskripsi Gemma dengan rubrik terpisah yang tidak memakai nilai sensor sebagai ground truth isi citra.

Template pencatatan tersedia di `docs/sensor_evaluation_template.csv` dan protokol lengkap di `docs/evaluation_protocol.md`.

## Dokumentasi aktif

| Dokumen | Fungsi |
|---|---|
| `CONTEXT.md` | istilah dan batas klaim |
| `instructions/PROJECT_INITIALIZATION.md` | scope akademik dan implementasi |
| `docs/architecture.md` | arsitektur dan kontrak data |
| `docs/evaluation_protocol.md` | protokol pengujian terpisah |
| `docs/DESIGN.md` | aturan UI |
| `docs/README.md` | indeks dokumen aktif dan historis |
