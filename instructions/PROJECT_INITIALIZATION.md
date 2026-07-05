# Project Initialization - Depth-Aware Image Description

Dokumen ini menjadi dokumentasi pusat untuk inisialisasi, arah akademik, dan konteks teknis proyek skripsi. Isi dokumen merangkum keputusan desain, pembahasan topik, dasar penelitian, arsitektur sistem, tanggung jawab modul, serta rujukan utama yang sudah disimpan ke `docs/pustaka/`.

Status dokumen: draft kerja untuk Bab 1, Bab 2, Bab 3, dan dokumentasi implementasi.

Tanggal pembaruan: 2026-07-05.

## 1. Deskripsi Proyek

Proyek ini adalah prototype penelitian untuk membuat sistem **depth-aware image description** pada citra lingkungan indoor. Sistem menerima gambar ruangan, memproses gambar dengan Depth Anything V2 Metric Indoor Small untuk memperkirakan informasi kedalaman relatif, lalu memakai vision-language model Gemma untuk menghasilkan deskripsi visual atau deskripsi visual-spasial. Strategi fusi yang tersedia mencakup late/rule-based fusion dan Depth-to-Spatial Prompting agar kontribusi depth dapat dibandingkan secara lebih jelas.

Fokus proyek bukan membuat aplikasi navigasi siap produksi, melainkan membangun dan mengevaluasi pipeline AI yang dapat memperkaya deskripsi gambar indoor dengan konteks spasial. Karena itu, klaim utama proyek adalah peningkatan kelengkapan informasi visual-spasial, bukan jaminan keselamatan navigasi.

Ringkasan posisi proyek:

- Domain: computer vision, vision-language model, monocular depth estimation, assistive scene understanding.
- Objek penelitian: citra lingkungan indoor.
- Output utama: deskripsi Bahasa Indonesia yang menggabungkan deskripsi semantik dan ringkasan kedalaman relatif.
- Mode pembanding: `gemma_only` sebagai Gemma Baseline, `depth_only`, `gemma_depth`, dan `gemma_depth_prompted`.
- Karakter penelitian: implementatif dan evaluatif.

## 2. Tujuan Proyek Baru

### 2.1 Tujuan Utama

Tujuan utama proyek adalah mengembangkan prototype sistem deskripsi gambar indoor yang menggabungkan kemampuan deskripsi visual dari Gemma dengan estimasi kedalaman dari Depth Anything V2 Metric Indoor Small untuk menghasilkan deskripsi yang lebih sadar ruang.

Secara praktis, sistem diharapkan mampu:

1. Menerima input gambar indoor dari web interface.
2. Menghasilkan deskripsi visual menggunakan Gemma melalui LM Studio lokal.
3. Menghasilkan depth map menggunakan Depth Anything V2 Metric Indoor Small.
4. Menganalisis depth map ke dalam region sederhana, seperti area atas, tengah, bawah, kiri, kanan, dan sekitarnya.
5. Menentukan kategori kedalaman relatif, area terdekat, status area depan, serta area yang relatif lebih lapang.
6. Menghasilkan final description Bahasa Indonesia melalui Gemma-only, depth-only, late fusion, atau Depth-to-Spatial Prompting.
7. Menyimpan hasil prediksi dan menjalankan evaluasi berbasis anotasi manual.

### 2.2 Tujuan Akademik

Tujuan akademik proyek adalah membuktikan secara terukur apakah penambahan informasi kedalaman dapat membuat deskripsi gambar indoor lebih informatif dibanding deskripsi berbasis vision-language model saja.

Tujuan akademik dapat dirumuskan sebagai berikut:

1. Mengimplementasikan pipeline depth-aware image description berbasis Gemma dan Depth Anything V2.
2. Mengevaluasi perbedaan output antara mode `gemma_only`, `depth_only`, `gemma_depth`, dan `gemma_depth_prompted`.
3. Menganalisis kontribusi depth estimation terhadap informasi posisi, kategori kedalaman relatif, potensi hambatan, dan kelengkapan deskripsi.
4. Mengukur trade-off antara peningkatan informasi spasial dan waktu inferensi.
5. Menyusun batasan sistem agar hasil penelitian tidak overclaim sebagai alat navigasi aman.

## 3. Rekomendasi Judul Penelitian

Judul utama yang direkomendasikan:

> Implementasi dan Evaluasi Depth-Aware Image Description Menggunakan Gemma dan Depth Anything V2 pada Citra Lingkungan Indoor

Alternatif judul:

1. Implementasi Sistem Deskripsi Gambar Indoor Berbasis Vision-Language Model dan Estimasi Kedalaman Monokular.
2. Evaluasi Pengaruh Informasi Kedalaman terhadap Kualitas Deskripsi Gambar Indoor Menggunakan Gemma dan Depth Anything V2.
3. Pengembangan Prototype Depth-Aware Image Description untuk Pemahaman Lingkungan Indoor.
4. Integrasi Gemma dan Depth Anything V2 untuk Deskripsi Visual-Spasial pada Citra Indoor.

Judul yang paling kuat adalah judul utama karena memuat metode, objek, dan fokus evaluasi secara langsung.

## 4. Rumusan Masalah

Rumusan masalah yang disarankan:

1. Bagaimana merancang pipeline depth-aware image description yang menggabungkan Gemma dan Depth Anything V2 pada citra lingkungan indoor?
2. Bagaimana informasi depth map dapat diterjemahkan menjadi informasi spasial seperti kategori kedalaman relatif, area terdekat, status area depan, dan area yang relatif lebih lapang?
3. Apakah mode `gemma_depth_prompted` menghasilkan deskripsi yang lebih informatif dibanding `gemma_only`, `depth_only`, dan `gemma_depth` late fusion?
4. Bagaimana pengaruh penambahan depth estimation terhadap waktu pemrosesan sistem?
5. Apa keterbatasan sistem dalam menghasilkan deskripsi visual-spasial pada citra indoor?

## 5. Batasan Masalah

Batasan masalah diperlukan agar penelitian tetap realistis untuk skripsi dan tidak mengklaim hal yang belum diuji.

Batasan yang disarankan:

1. Input sistem berupa gambar statis, bukan video real-time.
2. Objek penelitian dibatasi pada citra lingkungan indoor.
3. Model vision-language yang digunakan adalah Gemma yang berjalan secara lokal melalui LM Studio.
4. Model kedalaman yang digunakan adalah Depth Anything V2 Metric Indoor Small dari folder `model_weights/`.
5. Depth map digunakan untuk kategori kedalaman relatif, bukan pengukuran jarak presisi centimeter.
6. Fusion mencakup late/rule-based fusion dan Depth-to-Spatial Prompting, bukan training model baru.
7. Evaluasi menggunakan anotasi manual pada dataset lokal.
8. Prototype tidak diklaim sebagai sistem navigasi aman untuk pengguna tunanetra.
9. Output sistem berupa deskripsi teks Bahasa Indonesia dan metadata analisis, bukan audio guidance sebagai fitur utama.
10. Akurasi sistem sangat bergantung pada kualitas gambar, pencahayaan, objek dominan, dan kemampuan model lokal.

## 6. Tech Stack

Tech stack yang digunakan:

| Lapisan | Teknologi | Fungsi |
|---|---|---|
| Backend | Python, FastAPI, Uvicorn | API upload gambar, routing, orchestration pipeline |
| Model VLM | Gemma via LM Studio OpenAI-compatible API | Deskripsi visual dan ekstraksi informasi semantik |
| Model Depth | Depth Anything V2 Metric Indoor Small ONNX | Estimasi kedalaman dari satu gambar RGB |
| Runtime Depth | ONNX Runtime | Inferensi model depth lokal |
| Image Processing | Pillow, NumPy | Validasi, resize, normalisasi gambar, depth analysis |
| Frontend | HTML, CSS, JavaScript vanilla | Web interface untuk upload, mode, dan hasil analisis |
| Evaluation | CSV, Python scripts | Logging prediksi dan evaluasi terhadap anotasi |
| Testing | Pytest | Unit test dan API test |
| Local AI Server | LM Studio | Menjalankan Gemma secara lokal |

Konfigurasi penting:

- `LM_STUDIO_URL=http://localhost:1234`
- `LM_STUDIO_MODEL=gemma-4-e4b-it`
- `DEPTH_MODEL_PATH=./model_weights/Depth-Anything-V2-Metric-Indoor-Small-hf`
- `GEMMA_MOCK=false`
- `DEPTH_MOCK=false`

Mock hanya boleh digunakan untuk development atau smoke test, bukan eksperimen final.

## 7. Arsitektur Sistem Baru

### 7.1 Arsitektur Ringkas

```text
User / Web Browser
  -> FastAPI Backend
  -> Upload Validation
  -> Image Preprocessing
  -> Depth Anything V2 ONNX
  -> 9-Region Depth Analysis
  -> Gemma Client via LM Studio
  -> Late Fusion or Depth-to-Spatial Prompting
  -> Final Indonesian Description
  -> Prediction Log + Evaluation CSV + Depth Map
```

Arsitektur ini sengaja dibuat modular agar setiap bagian bisa diuji dan dibahas dalam skripsi. Gemma bertanggung jawab pada pemahaman semantik gambar, sedangkan Depth Anything bertanggung jawab pada informasi kedalaman relatif. Fusion layer menyediakan dua strategi: late fusion sebagai baseline ablation dan Depth-to-Spatial Prompting sebagai metode prompt-level. Ringkasan region depth memakai grid 3x3 aplikasi; grid ini adalah post-processing atas peta kedalaman kontinu, bukan keluaran asli Depth Anything.

### 7.2 Alur Utama

Alur utama sistem:

1. Pengguna membuka web interface.
2. Pengguna memilih gambar dan mode analisis.
3. Frontend mengirim gambar ke endpoint `POST /analyze`.
4. Backend memvalidasi jenis file, ukuran file, dan mode analisis.
5. Gambar diproses agar sesuai batas ukuran sistem.
6. Jika mode menggunakan depth, gambar diproses oleh Depth Anything V2 ONNX.
7. Output depth map dianalisis menjadi region dan kategori kedalaman relatif.
8. Jika mode menggunakan Gemma, gambar dikirim ke LM Studio untuk deskripsi visual.
9. Pada `gemma_depth`, output Gemma dan output depth digabung oleh late/rule-based fusion; pada `gemma_depth_prompted`, metadata depth masuk ke prompt Gemma sebelum deskripsi akhir dibuat.
10. Jika metadata depth menunjukkan potensi halangan visual, deskripsi akhir mode depth-aware harus menyebutnya dengan bahasa guarded seperti "berpotensi menjadi halangan visual".
10. Sistem mengembalikan final description, metadata display, latency, depth map URL, dan debug output.
11. Jika `save_result=true`, sistem menyimpan prediction row ke `results/predictions.csv`.
12. Evaluasi dapat dijalankan dengan membandingkan prediction CSV dan annotation CSV.

## 8. Tanggung Jawab Setiap Modul

| Modul/File | Tanggung Jawab |
|---|---|
| `app/main.py` | Membuat FastAPI app, mount static/template/result, menyediakan endpoint health. |
| `app/config.py` | Menyimpan konfigurasi aplikasi, LM Studio, model depth, limit gambar, dan direktori hasil. |
| `app/schemas.py` | Mendefinisikan response schema untuk hasil analisis. |
| `app/routes/analyze.py` | Endpoint upload gambar, validasi awal, pemanggilan pipeline, dan response JSON. |
| `services/validation.py` | Validasi tipe file, ukuran file, dan mode analisis. |
| `services/image_preprocess.py` | Membaca image bytes, konversi RGB, resize, dan encoding base64 untuk model. |
| `models/gemma_client.py` | Client HTTP ke LM Studio, prompt Gemma, parsing JSON terstruktur, sanitasi deskripsi. |
| `models/depth_prompting.py` | Menyusun Depth-to-Spatial Prompting Schema dari metadata depth relatif untuk prompt Gemma. |
| `models/depth_anything.py` | Adapter ONNX Runtime untuk Depth Anything, preprocessing tensor, inference, dan simpan depth map. |
| `services/depth_analysis.py` | Membagi depth map menjadi region, menentukan nearest region, kategori kedalaman relatif, front status, warning, dan area relatif lapang. |
| `models/fusion.py` | Mengelola final description, strategi fusi, display payload, dan provenance segments. |
| `services/pipeline.py` | Orchestrator utama analisis gambar, menghubungkan preprocessing, Gemma, depth, fusion, dan prediction row. |
| `services/result_logger.py` | Menulis hasil prediksi ke `results/predictions.csv`. |
| `services/evaluator.py` | Membandingkan annotation dan prediction untuk menghasilkan metrik evaluasi. |
| `scripts/run_single_image.py` | CLI untuk menjalankan analisis pada satu gambar. |
| `scripts/run_batch_evaluation.py` | CLI untuk batch inference dan evaluasi per mode. |
| `scripts/run_evaluation.py` | CLI untuk menghitung evaluasi dari CSV yang sudah ada. |
| `scripts/smoke_test.py` | Smoke test backend/API dengan server sementara. |
| `templates/index.html` | Struktur UI web. |
| `static/app.js` | Interaksi upload, request API, dan render hasil. |
| `static/style.css` | Desain visual web interface. |
| `dataset/annotations.csv` | Ground truth manual untuk evaluasi. |
| `results/predictions.csv` | Log hasil prediksi sistem. |
| `results/evaluation.csv` | Output evaluasi otomatis. |
| `docs/evaluation_protocol.md` | Protokol evaluasi eksperimen skripsi. |
| `docs/pustaka/` | Arsip PDF/HTML rujukan utama. |

## 9. Inti Pembahasan Skripsi

Inti pembahasan proyek adalah:

> Deskripsi gambar biasa dari vision-language model dapat menjelaskan isi gambar, tetapi belum tentu memberikan informasi spasial yang cukup. Penelitian ini menguji apakah penambahan estimasi kedalaman dapat membuat deskripsi gambar indoor lebih informatif dalam aspek posisi, jarak, area dekat, dan potensi hambatan.

Dengan framing ini, topik utama bukan sekadar web app atau penggunaan model AI, melainkan **fusion antara pemahaman semantik gambar dan estimasi kedalaman monokular untuk menghasilkan deskripsi visual-spasial**.

Kontribusi yang dapat ditulis:

1. Merancang pipeline depth-aware image description berbasis model lokal.
2. Mengintegrasikan Gemma dan Depth Anything V2 dalam satu sistem web.
3. Mengubah depth map menjadi informasi linguistik seperti kategori jarak dan area terdekat.
4. Menyusun rule-based fusion untuk menghasilkan final description Bahasa Indonesia.
5. Menyediakan evaluasi perbandingan antara deskripsi tanpa depth dan deskripsi dengan depth.

## 10. Alasan Pemilihan Model

### 10.1 Alasan Pemilihan Gemma

Gemma dipilih karena sesuai dengan kebutuhan prototype lokal. Gemma merupakan keluarga open model dari Google yang dapat digunakan untuk eksperimen vision-language secara lebih reproducible dibanding API tertutup. Dalam konteks proyek ini, Gemma dijalankan melalui LM Studio dengan endpoint OpenAI-compatible sehingga sistem tidak bergantung pada cloud API saat eksperimen lokal.

Alasan teknis:

1. Dapat dijalankan lokal melalui LM Studio.
2. Mendukung prompt instruction untuk menghasilkan output Bahasa Indonesia.
3. Dapat diarahkan menghasilkan JSON terstruktur.
4. Lebih sesuai untuk skripsi implementatif karena konfigurasi, model ID, dan endpoint dapat dicatat.
5. Mengurangi ketergantungan pada API komersial tertutup.

Alasan tidak memilih model lain sebagai model utama:

- GPT-4o/Gemini cloud dapat lebih kuat, tetapi bergantung pada layanan eksternal, biaya, kuota, dan perubahan API.
- BLIP-2 relevan untuk captioning, tetapi kurang cocok untuk kebutuhan output instruksional Bahasa Indonesia terstruktur dalam pipeline lokal ini.
- LLaVA/PaliGemma/Qwen-VL valid sebagai alternatif, tetapi proyek sudah memiliki Gemma berjalan di LM Studio sehingga lebih realistis untuk eksperimen skripsi yang dapat direplikasi di perangkat lokal.

Klaim yang aman: Gemma bukan diklaim sebagai model terbaik secara mutlak, tetapi sebagai model vision-language lokal yang cocok untuk prototype dan evaluasi sistem ini.

### 10.2 Alasan Pemilihan Depth Anything V2 Metric Indoor Small

Depth Anything V2 Metric Indoor Small dipilih karena proyek membutuhkan estimasi kedalaman dari satu gambar RGB, tanpa sensor depth tambahan. Varian Metric Indoor Small sesuai dengan domain penelitian, yaitu citra indoor, dan ukurannya lebih ringan untuk eksekusi lokal.

Alasan teknis:

1. Dirancang untuk monocular depth estimation.
2. Memiliki varian metric indoor yang relevan dengan citra ruangan.
3. Tersedia dalam format ONNX dan sudah ditempatkan di `model_weights/`.
4. Lebih ringan dibanding varian model besar, sehingga cocok untuk prototype web lokal.
5. Output depth map dapat dianalisis menjadi region dan kategori jarak.

Alasan tidak memilih model lain sebagai model utama:

- MiDaS/DPT relevan tetapi lebih tua dan umumnya menghasilkan relative depth, bukan varian metric indoor khusus.
- ZoeDepth kuat untuk metric depth, tetapi Depth Anything V2 lebih baru dan model indoor small tersedia langsung untuk integrasi lokal.
- Sensor RGB-D memberi depth lebih kuat, tetapi membutuhkan perangkat tambahan dan mengubah ruang lingkup skripsi.

Klaim yang aman: Depth Anything V2 digunakan sebagai estimasi kedalaman untuk memperkaya deskripsi, bukan sebagai sensor jarak presisi.

## 11. Permasalahan Penelitian dan Gap

Permasalahan yang diangkat adalah keterbatasan deskripsi gambar biasa dalam menyampaikan informasi spasial. Deskripsi seperti "terdapat meja dan kursi di ruangan" belum cukup jika pengguna membutuhkan informasi area mana yang dekat, objek mana yang mungkin menghalangi, atau bagian mana yang relatif lebih lapang.

Penelitian terkait menunjukkan bahwa scene understanding untuk pengguna dengan gangguan penglihatan mencakup kebutuhan seperti scene description, object finding, object location, obstacle avoidance, dan text reading. Penelitian lain pada spatial reasoning VLM juga menunjukkan bahwa vision-language model masih memiliki tantangan dalam memahami relasi ruang 3D, jarak, dan ukuran objek.

Gap yang diambil proyek:

1. Banyak sistem caption fokus pada isi gambar, bukan konteks kedalaman.
2. Banyak penelitian spatial VLM berfokus pada benchmark/model besar, bukan prototype lokal sederhana yang bisa dievaluasi dalam skripsi.
3. Banyak solusi assistive vision memerlukan sensor tambahan atau perangkat khusus.
4. Belum banyak implementasi lokal yang menggabungkan VLM, monocular depth estimation, dan output Bahasa Indonesia untuk deskripsi indoor.

Maka posisi proyek adalah membangun prototype sederhana tetapi terukur untuk melihat kontribusi depth estimation pada deskripsi gambar indoor.

## 12. Evaluasi dan Data Eksperimen

Evaluasi proyek diarahkan untuk membandingkan mode:

- `gemma_only`: Gemma Baseline, yaitu deskripsi visual dan relasi spasial kualitatif dari gambar saja tanpa metadata depth eksplisit.
- `depth_only`: ringkasan informasi depth tanpa Gemma.
- `gemma_depth`: fusion antara Gemma dan depth.

Dataset lokal:

- Gambar disimpan di `dataset/images/`.
- Anotasi manual disimpan di `dataset/annotations.csv`.
- Format anotasi mengikuti `docs/evaluation_protocol.md`.

Metrik awal:

1. Object mention accuracy.
2. Position accuracy.
3. Distance category accuracy.
4. Obstacle warning accuracy.
5. Description quality heuristic.
6. Average latency.

Interpretasi hasil:

- Distance category dan obstacle warning berlaku untuk mode yang menghasilkan metadata depth. Pada `gemma_only`, metrik depth ditulis sebagai N/A agar absence metadata tidak dibaca sebagai kegagalan Gemma.
- Jika `gemma_depth` atau `gemma_depth_prompted` meningkat pada distance category atau obstacle warning, maka depth memberi kontribusi pada informasi spasial eksplisit.
- Jika object accuracy tidak meningkat, hal itu wajar karena depth module tidak bertugas mengenali objek.
- Jika latency meningkat, pembahasan dapat diarahkan pada trade-off antara kelengkapan informasi dan waktu pemrosesan.

Dataset tidak boleh dimanipulasi untuk mengejar hasil bagus. Semua hasil eksperimen harus berdasarkan gambar aktual, anotasi aktual, dan output aktual dari pipeline.

## 13. Rujukan Utama 2021-2026

Rujukan berikut relevan untuk dasar teori, alasan model, gap penelitian, dan evaluasi. File rujukan sudah disimpan di `docs/pustaka/`.

| Tahun | Rujukan | Relevansi | File Lokal |
|---|---|---|---|
| 2025 | Gemma Team. Gemma 3 Technical Report. | Dasar pemilihan Gemma sebagai model multimodal/open model. | `docs/pustaka/2025-gemma-3-technical-report.pdf` |
| 2024 | Yang et al. Depth Anything V2. | Dasar pemilihan Depth Anything V2 untuk monocular depth estimation. | `docs/pustaka/2024-depth-anything-v2.pdf` |
| 2024 | Depth Anything V2 Metric Indoor Small Model Card. | Dasar pemilihan varian metric indoor small yang digunakan proyek. | `docs/pustaka/2024-depth-anything-v2-metric-indoor-small-model-card.html` |
| 2024 | Valipoor, de Antonio, Cabrera. Analysis and design framework for indoor scene understanding assistive solutions. Multimedia Systems. | Dasar masalah scene understanding indoor dan kebutuhan pengguna dengan visual impairment. | `docs/pustaka/2024-indoor-scene-understanding-assistive-valipoor.pdf` |
| 2024 | Chen et al. SpatialVLM. CVPR. | Bukti bahwa VLM masih perlu ditingkatkan untuk spatial reasoning dan informasi 3D. | `docs/pustaka/2024-spatialvlm-cvpr.pdf` |
| 2024 | Cheng et al. SpatialRGPT. | Rujukan integrasi depth/spatial information ke VLM. | `docs/pustaka/2024-spatialrgpt.pdf` |
| 2024 | Zhang et al. Do Vision-Language Models Represent Space and How? | Rujukan keterbatasan dan evaluasi representasi ruang pada VLM. | `docs/pustaka/2024-vlm-represent-space-comfort.pdf` |
| 2023 | Wang et al. Dense captioning and multidimensional evaluations for indoor robotic scenes. Frontiers in Neurorobotics. | Rujukan RGB-D captioning dan evaluasi deskripsi scene indoor. | `docs/pustaka/2023-rgbd2cap-frontiers.pdf` |
| 2023 | Bhat et al. ZoeDepth. | Alternatif model metric depth dan pembanding alasan memilih Depth Anything V2. | `docs/pustaka/2023-zoedepth.pdf` |
| 2023 | Kamath et al. What's Up with Vision-Language Models? | Rujukan keterbatasan VLM pada relasi spasial. | `docs/pustaka/2023-vlm-spatial-relations-emnlp.pdf` |
| 2026 | WHO. Blindness and visual impairment fact sheet. | Data aktual konteks sosial gangguan penglihatan. | `docs/pustaka/2026-who-blindness-visual-impairment.html` |

Catatan: rujukan WHO adalah sumber institusional untuk konteks sosial, bukan paper akademik. Untuk Bab 2, pisahkan antara "penelitian terdahulu" dan "data pendukung konteks".

## 14. Penelitian Terdahulu dan Perbedaan Proyek

Penelitian terdahulu yang relevan dapat dikelompokkan menjadi empat:

1. Vision-language model dan image captioning.
2. Monocular depth estimation.
3. RGB-D/depth-aware captioning.
4. Assistive indoor scene understanding.

Perbedaan proyek ini:

| Aspek | Penelitian Terdahulu | Proyek Ini |
|---|---|---|
| Model semantik | Banyak memakai captioning/VLM besar atau benchmark publik. | Memakai Gemma lokal via LM Studio. |
| Depth | Beberapa memakai RGB-D sensor atau pendekatan depth khusus. | Memakai monocular depth dari satu gambar RGB dengan Depth Anything V2. |
| Bahasa output | Umumnya Bahasa Inggris. | Output difokuskan ke Bahasa Indonesia. |
| Fokus | Model training, benchmark, atau assistive framework. | Prototype implementatif dan evaluasi sederhana untuk skripsi. |
| Fusion | Banyak pendekatan learned fusion atau benchmark-level. | Rule-based fusion agar transparan dan mudah dibahas. |
| Klaim | Sebagian mengarah ke assistive solution luas. | Dibatasi sebagai prototype depth-aware description, bukan navigasi aman. |

Novelty yang aman untuk skripsi:

> Implementasi pipeline lokal yang menggabungkan Gemma, Depth Anything V2 Metric Indoor Small, analisis region depth, dan rule-based fusion untuk menghasilkan deskripsi gambar indoor Bahasa Indonesia yang lebih sadar ruang.

## 15. Struktur Penulisan Skripsi yang Disarankan

### Bab 1 - Pendahuluan

Isi yang perlu ditekankan:

- Deskripsi gambar biasa belum cukup untuk informasi spasial.
- Lingkungan indoor membutuhkan informasi objek, posisi, jarak, dan potensi hambatan.
- VLM dapat menjelaskan gambar, tetapi masih memiliki keterbatasan pada spatial reasoning.
- Depth estimation dapat memberi informasi tambahan tentang kedalaman.
- Penelitian ini membangun dan mengevaluasi pipeline Gemma + Depth Anything V2.

### Bab 2 - Landasan Teori

Topik teori:

1. Computer vision.
2. Image captioning dan vision-language model.
3. Gemma sebagai model vision-language/open model.
4. Monocular depth estimation.
5. Depth Anything V2.
6. Scene understanding indoor.
7. Assistive technology untuk visual impairment sebagai konteks.
8. Evaluasi deskripsi gambar dan evaluasi sistem.

### Bab 3 - Metodologi

Isi yang perlu dijelaskan:

- Arsitektur sistem.
- Dataset dan format anotasi.
- Preprocessing gambar.
- Prompt Gemma dan schema output JSON.
- Inferensi Depth Anything.
- Region depth analysis.
- Rule-based fusion.
- Skenario evaluasi `gemma_only` vs `gemma_depth`.
- Metrik evaluasi.

### Bab 4 - Implementasi dan Pengujian

Isi yang perlu dijelaskan:

- Implementasi backend.
- Implementasi frontend.
- Integrasi LM Studio.
- Integrasi ONNX Depth Anything.
- Hasil uji per gambar.
- Hasil evaluasi CSV.
- Analisis kualitas output dan latency.

### Bab 5 - Penutup

Isi yang perlu dijelaskan:

- Kesimpulan apakah depth memberi kontribusi.
- Keterbatasan sistem.
- Saran pengembangan: dataset lebih besar, human evaluation, audio output, real-time camera, model pembanding, dan kalibrasi depth.

## 16. Pernyataan Klaim yang Aman

Klaim yang aman dipakai:

- Sistem menghasilkan deskripsi gambar indoor dengan tambahan informasi kedalaman.
- Depth estimation membantu menambahkan konteks jarak relatif dan area terdekat.
- Evaluasi membandingkan deskripsi tanpa depth dan dengan depth.
- Sistem merupakan prototype penelitian, bukan aplikasi navigasi production-ready.

Klaim yang harus dihindari:

- Sistem menjamin keselamatan pengguna.
- Sistem mengukur jarak secara presisi.
- Sistem sudah siap digunakan tunanetra untuk navigasi real-time.
- Gemma atau Depth Anything V2 adalah model terbaik secara mutlak.
- Hasil evaluasi berlaku umum tanpa dataset yang cukup.

## 17. Checklist Kematangan Proyek Skripsi

Checklist akademik:

- [x] Masalah penelitian jelas.
- [x] Ada gap antara caption biasa dan depth-aware description.
- [x] Ada model utama dan alasan pemilihan model.
- [x] Ada pipeline implementasi.
- [x] Ada mode pembanding.
- [x] Ada dataset dan format anotasi.
- [x] Ada metrik evaluasi.
- [x] Ada batasan masalah.
- [x] Ada rujukan 5 tahun terakhir.
- [ ] Dataset eksperimen final perlu diisi dengan gambar aktual.
- [ ] Anotasi manual perlu dilengkapi.
- [ ] Hasil evaluasi final perlu dijalankan setelah dataset siap.
- [ ] Analisis Bab 4 perlu memakai output aktual, bukan contoh mock.

## 18. Catatan Penting untuk Penulisan

Gunakan istilah "estimasi kedalaman" atau "kategori jarak relatif" saat membahas output depth. Hindari menulis "jarak pasti" kecuali ada kalibrasi dan validasi metrik yang kuat.

Saat membahas target pengguna, gunakan framing hati-hati:

> Sistem ini berpotensi dikembangkan sebagai komponen awal assistive scene understanding, khususnya untuk memberikan deskripsi visual-spasial pada lingkungan indoor.

Jangan menulis:

> Sistem ini membantu tunanetra bernavigasi dengan aman.

Untuk hasil eksperimen, pastikan semua tabel berasal dari:

- `dataset/images/`
- `dataset/annotations.csv`
- `results/predictions.csv`
- `results/evaluation.csv`

Sebelum menjalankan inference final, jalankan preflight:

```bash
python scripts\run_batch_evaluation.py --preflight-only
```

Preflight digunakan untuk memastikan dataset, anotasi, konfigurasi mock, model depth, dan runtime Gemma siap sebelum hasil dipakai dalam Bab 4.

Jika hasil kurang bagus, tetap tulis apa adanya. Nilai skripsi tetap kuat jika analisisnya jujur, batasannya jelas, dan rekomendasi pengembangannya matang.

## 19. Kontrak API dan Interface

### 19.1 Endpoint Utama

Endpoint minimal yang menjadi permukaan sistem:

| Endpoint | Method | Fungsi |
|---|---|---|
| `/` | GET | Menampilkan web interface. |
| `/health` | GET | Mengecek status backend, Gemma, dan depth model. |
| `/analyze` | POST | Menerima gambar dan menjalankan pipeline analisis. |

Form data untuk `POST /analyze`:

| Field | Type | Wajib | Keterangan |
|---|---|---|---|
| `image` | file | Ya | JPG, PNG, atau WebP. |
| `mode` | string | Tidak | `gemma_depth_prompted`, `gemma_depth`, `gemma_only`, atau `depth_only`. |
| `save_result` | boolean | Tidak | Menentukan apakah hasil ditulis ke CSV. |

Response utama harus berisi:

- `success`
- `filename`
- `content_type`
- `width`
- `height`
- `mode`
- `description_gemma`
- `gemma_structured`
- `depth_summary`
- `final_description`
- `display`
- `latency`
- `depth_map_url`
- `mock`
- `error`

### 19.2 Frontend Requirements

UI web berfungsi sebagai alat demonstrasi dan pengujian, bukan produk komersial. Komponen minimal yang harus tetap tersedia:

1. Upload gambar.
2. Preview gambar input.
3. Pilihan mode analisis.
4. Tombol analyze.
5. Loading/error state.
6. Panel final description.
7. Panel structured Gemma output.
8. Panel depth summary.
9. Panel latency.
10. Depth map preview jika tersedia.
11. Debug JSON untuk membantu analisis Bab 4.

Desain harus tetap sederhana, responsif, dan fokus pada keterbacaan hasil eksperimen. Hindari dekorasi berlebihan, animasi tidak perlu, atau komponen yang membuat pembahasan skripsi melebar ke ranah desain produk.

## 20. Failure Handling

Skenario gagal harus ditangani secara eksplisit agar hasil eksperimen tidak tercampur dengan error teknis.

Jika Gemma gagal:

- Mode `gemma_only` dan `gemma_depth` dianggap gagal karena deskripsi visual tidak tersedia.
- Response harus berisi error yang menjelaskan LM Studio/model belum siap.
- Depth summary boleh tersedia untuk debugging, tetapi tidak boleh dipakai sebagai hasil final utama mode Gemma.

Jika Depth Anything gagal:

- Mode `gemma_only` tetap dapat berjalan.
- Mode `gemma_depth` dapat fallback ke deskripsi Gemma dengan catatan bahwa depth tidak tersedia.
- Error depth harus dicatat agar tidak dianggap sebagai hasil depth valid.

Jika gambar tidak valid:

- Request ditolak.
- Error harus menyebut format/ukuran gambar yang diterima.

Jika output model berupa mock:

- Field `mock` harus bernilai true.
- Hasil mock tidak boleh dipakai sebagai hasil eksperimen final.

## 21. Acceptance Criteria MVP

MVP dianggap siap untuk demonstrasi skripsi jika memenuhi:

1. Web UI dapat dibuka dari browser.
2. Pengguna dapat upload gambar.
3. Backend menerima dan memvalidasi gambar.
4. Gemma menghasilkan deskripsi visual aktual melalui LM Studio.
5. Depth Anything menghasilkan depth map aktual melalui ONNX Runtime.
6. Depth analysis menghasilkan nearest region, distance category, front area status, warning, dan safer direction.
7. Fusion menghasilkan final description Bahasa Indonesia.
8. UI menampilkan final description, Gemma output, depth summary, latency, dan depth map.
9. Prediction log tersimpan ke `results/predictions.csv`.
10. Batch evaluation script berjalan.
11. Evaluation CSV dibuat.
12. README dan project initialization menjelaskan setup, batasan, dan cara evaluasi.
13. Tidak ada klaim navigasi aman atau jarak presisi.

## 22. Development Phases yang Sudah Menjadi Arah Proyek

Tahapan implementasi yang menjadi acuan:

| Fase | Fokus | Status Saat Ini |
|---|---|---|
| Phase 1 | Project skeleton FastAPI + UI dasar | Selesai |
| Phase 2 | Integrasi Gemma via LM Studio | Selesai secara teknis, perlu evaluasi dataset aktual |
| Phase 3 | Integrasi Depth Anything V2 ONNX | Selesai secara teknis |
| Phase 4 | Depth region analysis | Selesai secara teknis, perlu kalibrasi dataset |
| Phase 5 | Rule-based fusion | Selesai secara teknis, perlu penilaian kualitas output |
| Phase 6 | Logging dan evaluation scripts | Selesai secara teknis, dataset final belum lengkap |
| Phase 7 | Dokumentasi dan batasan proyek | Berjalan dan perlu terus disinkronkan dengan hasil eksperimen |

## 23. Expected Final Deliverables

Deliverables final yang harus tersedia untuk skripsi:

1. Source code prototype web + backend.
2. Pipeline `gemma_only`.
3. Pipeline `depth_only`.
4. Pipeline `gemma_depth`.
5. Dataset gambar indoor aktual.
6. Annotation CSV yang diisi manual.
7. Prediction CSV dari model aktual.
8. Evaluation CSV dari eksperimen final.
9. Depth map visualization.
10. README penggunaan.
11. Dokumentasi inisialisasi proyek.
12. Dokumentasi protokol evaluasi.
13. Analisis hasil untuk Bab 4.

## 24. Keputusan Konsolidasi Dokumen

Dokumen ini dipilih sebagai single source of truth karena lebih matang dibanding `.agents/instructions/global.md`. Alasan pemilihan:

1. Memuat dasar akademik, gap penelitian, dan rujukan 2021-2026.
2. Memuat batas klaim yang aman untuk skripsi.
3. Memuat struktur penulisan Bab 1 sampai Bab 5.
4. Memuat arsitektur dan modul berdasarkan implementasi yang sudah ada.
5. Sudah menggabungkan bagian operasional yang masih berguna dari `global.md`, seperti kontrak API, frontend requirements, failure handling, acceptance criteria, dan deliverables.

`.agents/instructions/global.md` dihapus agar tidak ada dua dokumen yang memberikan arahan mirip tetapi berbeda tingkat kematangan.

## 25. Ringkasan Satu Kalimat

Skripsi ini membahas implementasi dan evaluasi sistem deskripsi gambar indoor yang menggabungkan vision-language model dan estimasi kedalaman monokular untuk menghasilkan deskripsi Bahasa Indonesia yang lebih sadar ruang dibanding deskripsi visual biasa.
