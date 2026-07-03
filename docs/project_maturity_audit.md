# Project Maturity Audit

Tanggal audit: 2026-07-01.

Dokumen ini menilai kematangan proyek **Depth-Aware Image Description** dari sisi sistem, UI, evaluasi, dan kesiapan skripsi. Penilaian dibuat agar dapat digunakan sebagai bahan penulisan Bab 3, Bab 4, batasan penelitian, serta rencana penyempurnaan tanpa mengubah proyek menjadi over-engineered.

## 1. Ringkasan Skor Kematangan

| Aspek | Skor | Status | Catatan Singkat |
|---|---:|---|---|
| Backend dan arsitektur sistem | 82% | Matang untuk prototype | FastAPI, route, pipeline, model adapter, fusion, logging, dan evaluator sudah ada. |
| Integrasi Gemma | 70% | Berfungsi secara desain, perlu runtime konsisten | Client LM Studio sudah ada, tetapi saat audit LM Studio tidak reachable di `localhost:1234`. |
| Integrasi Depth Anything | 85% | Matang untuk prototype | ONNX adapter, preprocessing, inference, dan save depth map sudah tersedia. |
| Depth analysis dan fusion | 78% | Cukup matang | Region analysis dan rule-based fusion sudah ada, perlu kalibrasi threshold dengan dataset aktual. |
| UI web | 76% | Layak demo eksperimen | UI sudah informatif, responsif secara struktur, dan menampilkan metric/debug; visual QA browser penuh belum dilakukan pada audit ini. |
| Testing teknis | 84% | Baik | `python -m pytest -q` lulus 14 test dan smoke test lulus. |
| Dataset dan anotasi | 12% | Belum siap eksperimen final | `dataset/images` belum berisi gambar aktual; anotasi baru contoh satu baris. |
| Evaluasi skripsi | 45% | Tool siap, bukti belum siap | Script evaluasi ada, tetapi hasil belum bermakna karena dataset/prediction belum sinkron. |
| Dokumentasi akademik | 88% | Matang | `instructions/PROJECT_INITIALIZATION.md`, README, protocol evaluasi, dan pustaka sudah tersedia. |
| Kesiapan Bab 4 hasil eksperimen | 35% | Belum matang | Belum ada hasil eksperimen aktual yang cukup untuk dianalisis. |

Skor keseluruhan:

- **Kematangan software prototype: 76%**
- **Kematangan skripsi sebagai penelitian lengkap: 58%**
- **Kematangan gabungan proyek saat ini: 67%**

Interpretasi: proyek sudah cukup matang sebagai prototype sistem, tetapi belum cukup matang sebagai penelitian final karena data eksperimen, anotasi, evaluasi aktual, dan analisis hasil belum selesai.

## 2. Dasar Penilaian

Audit ini berdasarkan:

1. Struktur repo dan modul implementasi.
2. Isi `instructions/PROJECT_INITIALIZATION.md`.
3. Isi `README.md`.
4. Isi `docs/evaluation_protocol.md`.
5. Hasil test lokal.
6. Isi `dataset/annotations.csv`, `dataset/images/`, `results/predictions.csv`, dan `results/evaluation.csv`.
7. Inspeksi kode UI pada `templates/index.html`, `static/app.js`, dan `static/style.css`.

Hasil verifikasi teknis:

- Pytest: `14 passed`.
- Smoke test: passed.
- Jumlah gambar aktual di `dataset/images`: 0.
- LM Studio saat audit: tidak reachable pada `http://localhost:1234/v1/models`.
- `results/evaluation.csv` saat ini bernilai 0 karena prediction dan annotation belum sinkron.

## 3. Dokumen Mana yang Dipilih

Dokumen yang dipertahankan sebagai single source of truth adalah:

> `instructions/PROJECT_INITIALIZATION.md`

Alasannya:

1. Lebih matang secara akademik karena memuat deskripsi proyek, tujuan, rumusan masalah, batasan, gap, rujukan, dan struktur penulisan.
2. Lebih sesuai dengan kebutuhan skripsi karena membatasi klaim agar tidak menjadi aplikasi navigasi aman.
3. Sudah memuat tanggung jawab modul berdasarkan implementasi aktual.
4. Sudah menyerap informasi penting dari `.agents/instructions/global.md`, seperti kontrak API, frontend requirements, failure handling, acceptance criteria, development phases, dan deliverables.

Dokumen `.agents/instructions/global.md` dihapus karena isinya lebih tua, lebih berorientasi instruksi agent, dan berpotensi membuat kebingungan scope.

## 4. Apa yang Sudah Dilakukan

### 4.1 Sistem dan Backend

Yang sudah tersedia:

1. FastAPI application.
2. Endpoint `/`, `/health`, dan `/analyze`.
3. Validasi upload gambar.
4. Preprocessing gambar.
5. Client Gemma via LM Studio OpenAI-compatible endpoint.
6. Prompt Gemma Bahasa Indonesia dengan output JSON terstruktur.
7. Adapter Depth Anything V2 ONNX.
8. Region-based depth analysis.
9. Rule-based fusion.
10. Prediction logging ke CSV.
11. Evaluation script berbasis annotation/prediction CSV.
12. CLI single image, batch evaluation, dan smoke test.
13. Unit/integration tests untuk API, validation, depth analysis, fusion, dan evaluator.

Penilaian: backend sudah melewati tahap scaffold dan sudah berada pada level prototype fungsional.

### 4.2 UI

Yang sudah tersedia:

1. Halaman web eksperimen.
2. Upload gambar.
3. Camera browser sebagai opsi tambahan.
4. Preview gambar input.
5. Mode selector: `gemma_depth`, `gemma_only`, `depth_only`.
6. Status backend/Gemma/depth.
7. Loading state.
8. Error state.
9. Final description panel.
10. Metric tiles untuk mode, kategori depth, nearest region, dan latency.
11. Gemma structured summary.
12. Depth interpretation.
13. Depth map preview.
14. Debug JSON.

Penilaian: UI sudah cocok sebagai **experiment console**, bukan landing page atau produk final. Ini sudah sesuai tujuan skripsi karena output eksperimen mudah dibaca.

### 4.3 Dokumentasi dan Pustaka

Yang sudah tersedia:

1. `instructions/PROJECT_INITIALIZATION.md` sebagai dokumen utama.
2. `README.md` untuk setup dan penggunaan.
3. `docs/evaluation_protocol.md` untuk protokol evaluasi.
4. `docs/pustaka/` berisi 11 rujukan utama.
5. Penjelasan batasan agar tidak overclaim.

Penilaian: dokumentasi akademik sudah cukup kuat untuk mulai menyusun Bab 1 sampai Bab 3.

### 4.4 Testing

Yang sudah dilakukan:

1. `python -m pytest -q` lulus 14 test.
2. `python scripts/smoke_test.py --start-server` lulus.
3. API test memakai mock/fake model untuk memastikan route dan fusion berjalan.

Penilaian: test sudah baik untuk stabilitas prototype, tetapi belum membuktikan kualitas model pada data nyata.

## 5. Apa yang Belum Dilakukan

Prioritas paling penting:

1. Dataset gambar indoor aktual belum tersedia.
2. Anotasi manual belum lengkap.
3. Evaluasi final belum bisa dipercaya.
4. Belum ada tabel hasil eksperimen aktual untuk Bab 4.
5. Belum ada analisis output model terhadap kasus benar/salah.
6. Belum ada kalibrasi threshold depth berdasarkan dataset lokal.
7. Belum ada human/manual evaluation untuk kualitas deskripsi.
8. Belum ada pembanding model alternatif, walaupun ini bisa menjadi future work agar tidak overengineering.
9. Belum ada visual QA browser penuh yang terdokumentasi pada audit ini karena `agent-browser` tidak tersedia.
10. LM Studio tidak reachable saat audit, sehingga full real inference tidak diverifikasi pada sesi audit ini.

## 6. Grill Keras: Pertanyaan yang Harus Dijawab Sebelum Bab 4

### 6.1 Apakah proyek ini sudah cukup sebagai skripsi?

Jawaban: cukup sebagai topik dan prototype, belum cukup sebagai hasil penelitian final.

Alasannya: masalah, metode, model, arsitektur, dan evaluator sudah ada. Namun skripsi membutuhkan bukti eksperimen. Saat ini dataset aktual belum tersedia, sehingga klaim peningkatan `gemma_depth` dibanding `gemma_only` belum dapat dibuktikan.

### 6.2 Apa yang sebenarnya diuji?

Yang diuji bukan "apakah AI bisa mendeskripsikan gambar", tetapi:

> Apakah penambahan depth estimation membuat deskripsi gambar indoor lebih informatif secara spasial dibanding deskripsi Gemma-only.

Variabel bebas:

- Mode `gemma_only`.
- Mode `gemma_depth`.

Variabel terikat:

- Object mention accuracy.
- Position accuracy.
- Distance category accuracy.
- Obstacle warning accuracy.
- Description quality.
- Latency.

### 6.3 Apa target hasil yang realistis?

Target realistis:

1. `gemma_depth` lebih baik pada distance category dan obstacle warning.
2. `gemma_depth` tidak harus lebih baik pada object accuracy karena depth tidak mengenali objek.
3. `gemma_depth` kemungkinan lebih lambat dari `gemma_only`.
4. Hasil terbaik untuk skripsi adalah analisis trade-off, bukan klaim semua metrik meningkat.

### 6.4 Apakah UI harus dibuat lebih canggih?

Jawaban: tidak perlu terlalu canggih.

UI saat ini sudah cukup untuk skripsi karena menampilkan input, mode, final description, structured summary, depth interpretation, latency, dan debug JSON. Yang perlu ditingkatkan adalah kejelasan eksperimen, bukan dekorasi visual.

### 6.5 Apakah perlu database?

Jawaban: belum perlu.

CSV sudah cukup untuk scope skripsi karena eksperimen masih lokal, dataset terbatas, dan tujuan utama adalah evaluasi pipeline. Database akan menjadi overengineering kecuali nanti ada kebutuhan multi-user atau dashboard historis besar.

### 6.6 Apakah perlu aplikasi mobile?

Jawaban: tidak untuk scope sekarang.

Mobile app, TTS, voice trigger, dan real-time navigation harus tetap menjadi future work. Jika dimasukkan sekarang, fokus skripsi akan melebar dan risiko tidak selesai meningkat.

### 6.7 Apakah boleh menyebut tunanetra sebagai target?

Jawaban: boleh sebagai konteks pengembangan, tetapi bukan klaim validasi.

Kalimat aman:

> Sistem ini berpotensi dikembangkan sebagai komponen awal assistive scene understanding untuk membantu memberikan deskripsi visual-spasial.

Kalimat yang harus dihindari:

> Sistem ini membantu tunanetra bernavigasi dengan aman.

## 7. Yang Perlu Ditingkatkan

### 7.1 Prioritas P0 - Wajib untuk Skripsi

1. Isi `dataset/images/` dengan minimal 30 gambar indoor aktual.
2. Lengkapi `dataset/annotations.csv` sesuai gambar aktual.
3. Pastikan nama file annotation sama persis dengan nama file gambar.
4. Jalankan batch evaluation untuk `gemma_only` dan `gemma_depth`.
5. Simpan hasil final ke `results/predictions.csv` dan `results/evaluation.csv`.
6. Buat tabel perbandingan metrik untuk Bab 4.
7. Ambil 5 sampai 10 contoh output untuk analisis kualitatif.

### 7.2 Prioritas P1 - Sangat Disarankan

1. Tambahkan kolom manual rating untuk kualitas deskripsi.
2. Buat ringkasan error analysis: salah objek, salah posisi, salah depth, atau deskripsi terlalu umum.
3. Kalibrasi threshold distance category berdasarkan dataset lokal.
4. Tambahkan dokumentasi cara pengambilan gambar: jarak, sudut, pencahayaan, dan objek dominan.
5. Tambahkan screenshot UI final untuk lampiran.

### 7.3 Prioritas P2 - Opsional, Jangan Dipaksakan

1. Pembanding model lain seperti PaliGemma, LLaVA, atau Qwen-VL.
2. Export report otomatis.
3. Dashboard visualisasi metrik.
4. TTS output.
5. Real-time camera mode.

P2 hanya dikerjakan jika P0 dan P1 sudah selesai. Jangan mengorbankan evaluasi utama demi fitur tambahan.

## 8. Yang Perlu Diperbaiki

### 8.1 Data dan Evaluasi

Masalah terbesar: dataset belum siap.

Saat audit, `dataset/images` tidak berisi gambar eksperimen aktual dan `dataset/annotations.csv` hanya berisi satu baris contoh. `results/predictions.csv` berisi prediksi untuk `A.jpeg`, sedangkan annotation contoh memakai `img_001.jpg`. Akibatnya `results/evaluation.csv` menunjukkan skor 0.

Perbaikan:

1. Bersihkan atau arsipkan prediction lama yang tidak sesuai dataset.
2. Isi dataset aktual.
3. Generate annotation template dari nama file aktual.
4. Isi anotasi manual.
5. Jalankan ulang batch evaluation.

### 8.2 Runtime Model

Masalah: LM Studio tidak reachable saat audit.

Perbaikan:

1. Pastikan LM Studio berjalan.
2. Pastikan model Gemma yang dipakai sama dengan `LM_STUDIO_MODEL`.
3. Jalankan `/health` sebelum eksperimen.
4. Catat status model dan tanggal eksperimen di Bab 4.

### 8.3 UI

UI sudah cukup, tetapi bisa diperbaiki:

1. Tambahkan label "hasil belum valid untuk navigasi" di dekat final description.
2. Tambahkan indikator mock/non-mock agar hasil eksperimen tidak tercampur.
3. Tambahkan tombol download JSON/CSV output jika diperlukan.
4. Pastikan status Gemma error tampil lebih mencolok.
5. Dokumentasikan screenshot desktop dan mobile.

### 8.4 Evaluator

Evaluator sudah cukup untuk baseline, tetapi masih perlu hati-hati:

1. String matching raw bisa terlalu kaku.
2. Description quality heuristic belum menggantikan penilaian manusia.
3. Perlu manual review agar Bab 4 tidak hanya bergantung pada angka otomatis.

Perbaikan paling aman adalah menambahkan rubrik manual 1-5 pada sampel output, bukan membuat evaluator NLP kompleks.

## 9. Rekomendasi Metrik untuk Penulisan

Gunakan metrik berikut di Bab 4:

| Metrik | Tujuan | Cara Baca |
|---|---|---|
| Object accuracy | Mengukur apakah objek utama disebut | Dipengaruhi Gemma, bukan depth. |
| Position accuracy | Mengukur apakah posisi objek sesuai | Dipengaruhi Gemma dan prompt. |
| Distance category accuracy | Mengukur kontribusi depth | Harus menjadi fokus utama `gemma_depth`. |
| Obstacle warning accuracy | Mengukur apakah area dekat/hambatan tertangkap | Cocok untuk membahas manfaat depth. |
| Description quality | Mengukur keterbacaan dan kelengkapan | Gunakan automatic heuristic + manual rating. |
| Average latency | Mengukur biaya runtime | Bahas trade-off kualitas vs waktu. |
| Failure rate | Mengukur stabilitas model | Catat Gemma timeout, depth error, invalid output. |

Skor kematangan skripsi harus tidak hanya berdasarkan akurasi. Skripsi implementatif juga dinilai dari kejelasan pipeline, batasan, evaluasi, dan analisis error.

## 10. Rubrik Kematangan Proyek

Rubrik ini dapat dipakai untuk menulis "evaluasi kesiapan sistem":

| Level | Rentang | Arti |
|---|---:|---|
| Sangat awal | 0-25% | Baru konsep atau scaffold. |
| Prototype awal | 26-50% | Modul ada, tetapi belum stabil/teruji. |
| Prototype fungsional | 51-75% | Sistem berjalan, test ada, data belum kuat. |
| Prototype siap eksperimen | 76-90% | Dataset dan evaluasi sudah jalan, hasil bisa dianalisis. |
| Siap publikasi/demo kuat | 91-100% | Eksperimen matang, dokumentasi lengkap, analisis kuat. |

Posisi proyek saat ini:

- Software: prototype siap eksperimen awal.
- Skripsi: prototype fungsional, belum siap hasil final.

## 11. Rekomendasi Langkah Berikutnya

Urutan kerja paling sehat:

1. Jangan tambah fitur besar dulu.
2. Siapkan dataset aktual 30-50 gambar.
3. Lengkapi anotasi manual.
4. Pastikan LM Studio dan Depth Anything ready.
5. Jalankan batch evaluation.
6. Review 10 output secara manual.
7. Kalibrasi threshold depth jika banyak kategori salah.
8. Update Bab 4 berdasarkan hasil aktual.
9. Baru pertimbangkan polish UI kecil.

## 12. Rujukan Akademik untuk Menguatkan Audit

Rujukan utama yang mendukung arah proyek sudah tersedia di `docs/pustaka/`.

Rujukan yang paling relevan untuk alasan masalah dan gap:

1. Valipoor et al. (2024), *Analysis and design framework for the development of indoor scene understanding assistive solutions for the person with visual impairment/blindness*. Relevan untuk kebutuhan scene description, object location, dan obstacle awareness.
2. Chen et al. (2024), *SpatialVLM*. Relevan untuk keterbatasan VLM dalam spatial reasoning dan kebutuhan informasi 3D.
3. Cheng et al. (2024), *SpatialRGPT*. Relevan untuk penggunaan depth/spatial information dalam grounded spatial reasoning.
4. Yang et al. (2024), *Depth Anything V2*. Relevan untuk dasar pemilihan model depth.
5. Gemma Team (2025), *Gemma 3 Technical Report*. Relevan untuk dasar pemilihan Gemma sebagai model multimodal lokal.
6. Wang et al. (2023), *Dense captioning and multidimensional evaluations for indoor robotic scenes*. Relevan untuk RGB-D/depth-aware captioning indoor.

## 13. Kesimpulan Audit

Proyek ini sudah kuat sebagai prototype implementasi. Struktur sistem, pipeline model, UI eksperimen, test, dokumentasi, dan rujukan sudah berada di jalur yang benar. Bagian yang belum matang adalah data dan evaluasi aktual.

Kesimpulan paling jujur:

> Proyek sudah sekitar 76% matang sebagai software prototype, tetapi baru sekitar 58% matang sebagai skripsi lengkap karena hasil eksperimen aktual belum tersedia.

Fokus berikutnya harus sangat disiplin: dataset, anotasi, evaluasi, analisis hasil. Jangan menambah fitur besar sebelum Bab 4 punya data yang bisa dipertanggungjawabkan.
