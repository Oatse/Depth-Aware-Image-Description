# Analisis Perbandingan Project Skripsi: Bridge-Gap vs MBG

Tanggal analisis: 2026-07-03  
Basis analisis: pembacaan dokumentasi utama, struktur proyek, kode inti, testing, dataset/evaluasi, naskah MBG, dan verifikasi runtime lokal.

## 1. Ringkasan Eksekutif

Rekomendasi tegas: **pilih Bridge-Gap sebagai skripsi utama**.

Bridge-Gap lebih aman karena fokusnya lebih sempit, metodologinya lebih jelas, objek penelitiannya lebih mudah dikendalikan, dan Bab 4 dapat dibangun dari dataset gambar indoor tanpa wajib melibatkan responden tunanetra. Kelemahan terbesarnya serius tetapi terukur: dataset aktual dan hasil evaluasi belum siap. Masalah ini bisa diselesaikan dengan kerja disiplin: kumpulkan 30-50 gambar indoor, anotasi manual, jalankan evaluasi `gemma_only` vs `gemma_depth`, lalu bahas trade-off kualitas deskripsi dan latensi.

MBG lebih matang sebagai aplikasi dan lebih menarik saat demo, tetapi lebih berisiko sebagai skripsi dalam waktu terbatas. Ia membawa klaim "navigasi asistif untuk penyandang tunanetra", mobile camera, voice trigger, STT, TTS, backend, Cloudflare Tunnel, stabilisasi temporal, Gemma, depth estimation, dan safety guidance sekaligus. Itu impresif sebagai engineering, tetapi berat secara akademis karena dosen penguji akan menuntut validasi pengguna, etika pengujian, UAT, keselamatan navigasi, dan bukti bahwa sistem aman dipakai oleh target pengguna. Jika UAT tunanetra tidak kuat, klaim MBG mudah diserang.

Skor keseluruhan saat ini:

| Project | Kesiapan Software | Kesiapan Skripsi | Risiko Sidang | Rekomendasi |
|---|---:|---:|---:|---|
| Bridge-Gap | 8/10 | 7/10 jika dataset segera diisi; 5/10 jika tidak | Sedang | Utama |
| MBG | 8.5/10 | 5.5/10 tanpa UAT kuat; 7/10 jika scope dipersempit | Tinggi | Backup / inspirasi teknis |

Keputusan paling aman: jadikan Bridge-Gap sebagai penelitian implementasi dan evaluasi pipeline depth-aware image description. Ambil kekuatan MBG berupa fusion safety-first, response stabilization, dan bahasa asistif sebagai inspirasi terbatas, bukan memindahkan seluruh scope aplikasi mobile.

## 2. Deskripsi Singkat Masing-Masing Project

### Bridge-Gap

Bridge-Gap adalah prototype penelitian untuk menghasilkan deskripsi citra indoor yang sadar kedalaman. Sistem menerima gambar indoor, menghasilkan deskripsi visual dengan Gemma melalui LM Studio, menghitung estimasi kedalaman dengan Depth Anything V2 Metric Indoor Small, lalu menggabungkan hasil keduanya melalui fusion rule. Mode eksperimen yang tersedia adalah `gemma_only`, `depth_only`, dan `gemma_depth`.

Fokus akademisnya jelas: apakah informasi kedalaman dapat memperkaya kualitas deskripsi gambar indoor, terutama pada posisi objek, jarak, dan peringatan halangan. Ini cocok sebagai penelitian implementasi dan evaluasi pipeline.

Bukti proyek:

- Dokumen utama: `instructions/PROJECT_INITIALIZATION.md`.
- Protokol evaluasi: `docs/evaluation_protocol.md`.
- Audit maturity: `docs/project_maturity_audit.md`.
- Pipeline inti: `services/pipeline.py`.
- Evaluasi batch: `scripts/run_batch_evaluation.py`.
- Dataset: `dataset/images/`, `dataset/annotations.csv`.
- Hasil evaluasi: `results/evaluation.csv`.
- Verifikasi terbaru: `python -m pytest -q` menghasilkan 15 test passed.

Kelemahan paling besar: `dataset/images` belum berisi gambar aktual, `dataset/annotations.csv` baru contoh satu baris, dan `results/evaluation.csv` masih bernilai nol karena belum ada eksperimen final.

### MBG

MBG Assistive Vision adalah sistem mobile assistive vision berbasis React Native/Expo dan backend Bun/ElysiaJS. Pengguna mengucapkan trigger `MBG`, aplikasi mengambil gambar dari kamera, backend menjalankan Gemma via LM Studio dan Depth Anything V2 ONNX secara paralel, lalu hasilnya difusikan menjadi narasi keselamatan yang dibacakan dengan TTS.

Fokus engineering-nya kuat: voice-first mobile flow, kamera, API upload multipart, health check, retry, fusion, depth, stabilisasi temporal, dan output bahasa Indonesia. Namun fokus akademisnya lebih berat karena menyentuh navigasi asistif untuk penyandang tunanetra. Klaim itu tidak cukup dibuktikan dengan unit test dan demo; perlu validasi pengguna atau minimal evaluasi skenario yang sangat hati-hati.

Bukti proyek:

- Dokumen utama: `DOCUMENTATION.md`.
- Naskah skripsi: `Penulisan/main.tex`, `bab2.tex`, `bab2_part2.tex`.
- Backend utama: `backend/src/routes/describe.ts`.
- Fusion: `backend/src/services/depth/responseFusion.ts`.
- Mobile flow: `mobile/App.tsx`, `mobile/services/api.ts`.
- Benchmark depth: `backend/scripts/benchmark-results.json`.
- Kalibrasi depth: `backend/scripts/calibration-results.json`.
- Verifikasi terbaru: backend `bun test` menghasilkan 94 pass; mobile `npm test -- --runInBand` menghasilkan 25 passed; backend dan mobile `tsc --noEmit` bersih.

Kelemahan paling besar: klaim navigasi asistif dan target tunanetra membutuhkan beban validasi yang jauh lebih mahal daripada proyek berbasis dataset gambar indoor.

## 3. Perbandingan Kesiapan Project

Skala: 1 sangat lemah, 10 sangat kuat.

| Aspek | Bridge-Gap | MBG | Catatan Kritis |
|---|---:|---:|---|
| Selesai secara implementasi | 8 | 8.5 | Keduanya sudah punya pipeline inti. MBG lebih lengkap sebagai aplikasi end-to-end. |
| Fitur utama berjalan | 7.5 | 8.5 | Bridge-Gap bergantung pada dataset final; MBG punya alur mobile-backend yang lebih nyata. |
| Alur input-proses-output | 8.5 | 9 | Keduanya jelas. Bridge-Gap lebih cocok untuk eksperimen, MBG lebih cocok untuk demo produk. |
| Stabilitas demo | 7 | 6.5 | Bridge-Gap demo web lebih sederhana. MBG rawan jaringan mobile, izin kamera/mic, backend, LM Studio, dan device. |
| Bagian masih rencana | 5 | 6.5 | Bridge-Gap masih kosong pada data hasil eksperimen. MBG masih punya placeholder dokumentasi deployment/CI/model detail dan UAT. |
| Struktur mendukung skripsi | 8.5 | 7 | Bridge-Gap punya dokumen metodologi/evaluasi khusus. MBG punya naskah Bab 1/2, tetapi scope terlalu luas. |
| Over-engineering | 6 | 7.5 | Bridge-Gap cukup modular. MBG punya banyak lapisan yang bagus secara teknis tetapi memperluas serangan sidang. |
| Terlalu dangkal | 4 | 3 | Keduanya tidak dangkal secara teknik. Risiko dangkal muncul jika evaluasi hanya demo tanpa angka. |
| Risiko dependency/model/service | 7 | 8.5 | MBG lebih banyak titik gagal: mobile, Expo speech, kamera, network, tunnel, backend, LM Studio, ONNX. |
| Mudah dijalankan ulang penguji | 7.5 | 5.5 | Bridge-Gap bisa dijalankan lokal sebagai web/CLI. MBG perlu mobile environment dan koneksi perangkat. |

Kesimpulan kesiapan: **MBG unggul sebagai aplikasi**, tetapi **Bridge-Gap unggul sebagai skripsi yang bisa dikendalikan**.

## 4. Perbandingan Kesulitan Teknis

| Area Teknis | Bridge-Gap | MBG | Risiko vs Nilai Akademis |
|---|---|---|---|
| Integrasi Gemma | Sedang | Sedang-tinggi | Keduanya memakai LM Studio. Nilai akademis muncul jika output dievaluasi, bukan sekadar dipakai. |
| Depth Anything V2 | Sedang | Sedang-tinggi | Keduanya kuat. MBG lebih kompleks karena depth dipakai untuk navigasi real-time. |
| Pipeline inference | Jelas, mode eksperimen | Kompleks, paralel, request-response mobile | Bridge-Gap lebih mudah dijelaskan sebagai eksperimen. |
| Frontend/backend | Web sederhana | Mobile + backend | MBG lebih sulit dan lebih rawan demo. |
| Kamera/mobile integration | Tidak dominan | Sangat dominan | Nilai praktis tinggi, tetapi memperluas scope skripsi. |
| Deployment/local execution | Lokal sederhana | Lokal/tunnel/mobile | MBG lebih banyak konfigurasi. |
| Latency/performa | Bisa diukur per mode | Harus cukup cepat untuk navigasi | Klaim navigasi membuat latency MBG lebih kritis. |
| Error handling | Cukup | Lebih matang | MBG punya retry dan health check, tetapi makin banyak mode gagal. |
| Reproducibility | Lebih mudah | Lebih sulit | Dataset + CLI Bridge-Gap lebih mudah direplikasi. |
| Maintainability | Baik | Baik tetapi lebih besar | MBG lebih banyak modul dan state lintas device. |
| Debugging demo | Sedang | Sulit | MBG bisa gagal di mic, camera permission, device network, API token, tunnel, LM Studio, ONNX. |

Project yang lebih sulit secara teknis: **MBG**.

Apakah kesulitan MBG memberi nilai akademis? Sebagian iya, terutama pada fusion dan voice-first accessibility. Tetapi sebagian besar kesulitannya adalah risiko engineering dan demo, bukan kontribusi ilmiah langsung. Dosen tidak selalu memberi nilai lebih karena aplikasi lebih kompleks; mereka akan bertanya apakah kompleksitas itu dievaluasi dengan benar.

## 5. Perbandingan Kesulitan Penulisan Skripsi

| Bab | Bridge-Gap | MBG | Pemenang |
|---|---|---|---|
| Bab 1 | Mudah: masalah spesifik deskripsi indoor kurang sadar kedalaman | Menarik tetapi luas: tunanetra, navigasi, mobile, AI lokal, bahasa Indonesia | Bridge-Gap |
| Rumusan masalah | Bisa dibuat 2-3 pertanyaan eksperimen | Rentan terlalu banyak: mobile, STT/TTS, VLM, depth, navigasi, UAT | Bridge-Gap |
| Batasan masalah | Mudah dibatasi ke citra indoor statis | Sulit karena kata "navigasi" memancing ekspektasi real-world safety | Bridge-Gap |
| Bab 2 | Teori VLM, image captioning, monocular depth, fusion, evaluasi caption | Lebih banyak teori: tunanetra, navigasi, mobile, STT, TTS, VLM, depth, SDLC, UAT | Bridge-Gap |
| Bab 3 | Pipeline eksperimen jelas | Metodologi campuran aplikasi + pengujian pengguna lebih rumit | Bridge-Gap |
| Bab 4 | Butuh dataset dan metrik; realistis | Butuh functional test, latency, model output, mungkin UAT; lebih berat | Bridge-Gap |
| Bab 5 | Kesimpulan bisa berbasis peningkatan metrik | Kesimpulan rawan overclaim jika UAT lemah | Bridge-Gap |

Bridge-Gap lebih mudah dipertanggungjawabkan secara akademis karena klaimnya dapat dibuat sempit: "mengimplementasikan dan mengevaluasi pipeline", bukan "membuat alat navigasi aman".

## 6. Perbandingan Metodologi Penelitian

### Bridge-Gap

Metodologi paling cocok: **implementasi dan evaluasi eksperimental prototype**.

Formulasi aman:

- Jenis penelitian: penelitian implementatif dengan evaluasi kuantitatif dan analisis deskriptif.
- Objek penelitian: citra lingkungan indoor.
- Variabel bebas: mode deskripsi (`gemma_only`, `gemma_depth`).
- Variabel terikat: akurasi kategori jarak, deteksi halangan, kesesuaian posisi objek, kualitas deskripsi, dan latensi.
- Baseline: `gemma_only`.
- Perlakuan: `gemma_depth`.
- Ground truth: anotasi manual pada `dataset/annotations.csv`.
- Output dievaluasi: deskripsi akhir, kategori jarak, posisi objek, obstacle warning, latency.

Kritik keras:

- Judul menyebut "Evaluasi", tetapi evaluasi final belum ada.
- Depth akan dianggap tempelan jika metrik tidak membuktikan kontribusi depth dibanding Gemma-only.
- Ground truth manual harus jelas: siapa anotator, aturan anotasi, resolusi konflik, dan format CSV.
- Jika dataset hanya 5-10 gambar, Bab 4 akan terlihat lemah.

### MBG

Metodologi paling cocok: **pengembangan prototype aplikasi dan evaluasi fungsional**, bukan eksperimen model murni.

Formulasi aman jika tetap dipilih:

- Jenis penelitian: pengembangan aplikasi menggunakan SDLC, dengan pengujian fungsional dan evaluasi skenario terbatas.
- Objek penelitian: prototype sistem navigasi asistif berbasis mobile.
- Variabel diuji: keberhasilan capture, upload, inference, fusion, TTS, latency, stabilitas respons.
- Output dievaluasi: keberhasilan fungsi dan kualitas narasi pada skenario indoor.
- UAT: opsional jika tidak mengklaim efektivitas bagi penyandang tunanetra.

Kritik keras:

- Judul "navigasi asistif untuk penyandang tunanetra" mengundang kewajiban validasi pada target pengguna. Jika tidak ada responden tunanetra, klaim harus diturunkan.
- "Aman untuk navigasi" adalah klaim sensitif. Sistem berbasis VLM dan monocular depth bisa hallucinate atau salah estimasi jarak.
- Functional testing tidak cukup untuk membuktikan efektivitas penggunaan oleh tunanetra.
- UAT non-tunanetra tidak membuktikan kebutuhan pengguna tunanetra; paling jauh membuktikan usability umum atau expert review.

## 7. Perbandingan Testing dan Evaluasi

### Bukti Testing Saat Ini

| Bukti | Bridge-Gap | MBG |
|---|---|---|
| Unit/backend test | 15 passed | Backend 94 pass |
| Mobile test | Tidak relevan | 25 passed |
| Typecheck | Python compileall bersih | Backend dan mobile `tsc --noEmit` bersih |
| Dataset aktual | 0 gambar aktual | Tidak terlihat dataset penelitian terstruktur |
| Evaluasi model | Script ada, hasil belum bermakna | Benchmark dan calibration depth ada, tetapi bukan evaluasi skripsi penuh |
| Human/UAT | Belum ada | Dibahas di naskah, tetapi bukti responden belum terlihat |

### Testing yang Dibutuhkan Bridge-Gap

- Functional test upload dan mode inference.
- Batch evaluation `gemma_only` vs `gemma_depth`.
- Evaluasi distance category.
- Evaluasi obstacle warning.
- Evaluasi posisi objek.
- Evaluasi kualitas deskripsi manual dengan rubrik.
- Latency per mode.
- Analisis kegagalan depth map.
- Minimal 30 gambar indoor aktual, lebih baik 50 jika waktu cukup.

Bridge-Gap tidak wajib melibatkan tunanetra jika judul dan batasan dibuat sebagai evaluasi deskripsi gambar indoor, bukan alat navigasi pengguna akhir.

### Testing yang Dibutuhkan MBG

- Functional test backend dan mobile.
- Test kamera, izin mic, STT, TTS, API upload, retry, timeout.
- Test depth inference dan fusion.
- Test latency end-to-end mobile sampai TTS.
- Test skenario indoor nyata.
- UAT atau expert review.
- Jika tetap menyebut "penyandang tunanetra", perlu pertimbangan izin, etika, keamanan skenario, dan jumlah responden.

Risiko responden tunanetra:

- Sulit mencari responden dalam waktu terbatas.
- Ada isu etika dan keselamatan jika diuji sebagai alat navigasi.
- Jumlah responden kecil membuat validitas dipertanyakan.
- UAT tunanetra tidak selalu wajib jika scope diturunkan menjadi prototype fungsional, tetapi kalau klaimnya "untuk penyandang tunanetra", penguji dapat menuntutnya.
- Expert review atau evaluator non-tunanetra bisa dipakai sebagai alternatif, tetapi harus ditulis jujur sebagai evaluasi awal, bukan validasi efektivitas pengguna akhir.

Project yang lebih mudah diuji realistis: **Bridge-Gap**.

## 8. Grill dari Perspektif Dosen Penguji

### Bridge-Gap

| Pertanyaan Penguji | Risiko | Jawaban Defensif Aman | Yang Harus Disiapkan | Kekuatan |
|---|---|---|---|---|
| Kenapa memakai Depth Anything V2? | Jika hanya ikut tren, lemah. | Karena varian Metric Indoor Small cocok untuk estimasi kedalaman monocular pada citra indoor tanpa sensor tambahan. | Sitasi Depth Anything V2, model card indoor, batasan akurasi. | Kuat jika ada evaluasi jarak. |
| Kenapa memakai Gemma? | Penguji bisa tanya kenapa bukan LLaVA/Qwen. | Gemma dipilih sebagai VLM lokal yang bisa dijalankan melalui LM Studio untuk eksperimen yang dapat direplikasi tanpa cloud. | Alasan pemilihan dan batasan model. | Cukup. |
| Apa kontribusi penelitian? | Jika jawab "membuat aplikasi", lemah. | Kontribusinya pipeline lokal dan evaluasi perbandingan deskripsi Gemma-only vs Gemma+Depth pada citra indoor. | Tabel metrik dan analisis per mode. | Kuat jika Bab 4 selesai. |
| Apa bedanya dengan image captioning biasa? | Ini pertanyaan inti. | Captioning biasa hanya semantik; sistem ini menambahkan estimasi kedalaman untuk jarak, posisi, dan obstacle warning. | Contoh output pasangan sebelum/sesudah. | Kuat. |
| Bagaimana membuktikan depth membantu? | Tanpa data, jatuh. | Dibuktikan dengan perbandingan metrik antara mode `gemma_only` dan `gemma_depth`. | Dataset, anotasi, confusion/error analysis. | Saat ini lemah, bisa diperbaiki. |
| Apa ground truth-nya? | Ground truth manual bisa dianggap subjektif. | Ground truth berupa anotasi manual terstruktur: objek utama, posisi, kategori jarak, status halangan, arah aman. | Protokol anotasi, contoh data, aturan kategori. | Sedang. |
| Apakah depth map akurat? | Depth monocular tidak presisi. | Tidak diklaim sebagai sensor presisi; digunakan sebagai sinyal pendukung kategori kedekatan. | Batasan dan contoh kesalahan. | Aman jika klaim dibatasi. |
| Apakah output LLM hallucination? | VLM bisa salah. | Karena itu ada evaluasi manual dan baseline; sistem tidak dipakai untuk navigasi real-time. | Error cases dan batasan. | Aman. |
| Apakah dataset cukup? | Jika kurang dari 30, lemah. | Dataset minimum 30 gambar indoor untuk baseline awal, dengan saran perluasan pada penelitian lanjut. | Minimal 30-50 gambar. | Bergantung data. |
| Apakah ini aplikasi atau penelitian? | Jika UI terlalu dominan, bisa diserang. | Ini prototype eksperimen pipeline; UI hanya alat uji. | Tekankan mode eksperimen dan metrik. | Kuat. |

### MBG

| Pertanyaan Penguji | Risiko | Jawaban Defensif Aman | Yang Harus Disiapkan | Kekuatan |
|---|---|---|---|---|
| Kenapa disebut navigasi asistif? | Sangat tinggi. | Sistem adalah prototype bantuan deskripsi lingkungan, bukan alat navigasi final atau pengganti tongkat. | Revisi klaim dan batasan keselamatan. | Lemah jika judul tetap besar. |
| Kenapa tidak diuji langsung ke tunanetra? | Tinggi. | Penelitian tahap awal berfokus pada validasi fungsional dan skenario terkontrol; uji pengguna akhir menjadi pengembangan lanjut. | Justifikasi etika, keterbatasan, expert review. | Sedang-lemah. |
| Apakah sistem aman untuk navigasi? | Sangat tinggi. | Tidak diklaim aman untuk navigasi mandiri; output hanya informasi pendukung. | Disclaimer dan batasan keras. | Lemah jika klaim safety besar. |
| Bagaimana validasi STT/TTS? | Sedang. | Diuji melalui skenario trigger, command parsing, dan keberhasilan feedback audio. | Test cases dan log demo. | Cukup. |
| Bagaimana membuktikan fusion meningkatkan navigasi? | Tinggi. | Dibandingkan output Gemma-only dengan output fused pada skenario halangan. | Dataset/skenario dan rubrik. | Belum cukup. |
| Bagaimana jika depth salah? | Tinggi. | Sistem memakai warning sebagai estimasi, bukan ukuran presisi; fallback dan batasan dijelaskan. | Error analysis depth. | Sedang. |
| Bagaimana jika Gemma hallucination? | Tinggi. | Output disanitasi dan difusi dengan sinyal depth, tetapi tetap ada batasan. | Contoh failure dan mitigasi. | Sedang. |
| Kenapa Cloudflare Tunnel? | Scope melebar. | Untuk akses backend dari perangkat mobile saat pengujian, bukan fokus penelitian. | Jangan jadikan kontribusi utama. | Netral. |
| Apakah UAT non-tunanetra valid? | Tinggi. | Valid hanya untuk usability umum atau expert review, bukan klaim efektivitas tunanetra. | Instrumen dan batasan. | Lemah jika salah klaim. |
| Apa kontribusi ilmiah? | Tinggi. | Prototype integrasi VLM lokal, monocular depth, voice-first, dan stabilisasi temporal untuk narasi asistif bahasa Indonesia. | Pembatasan kontribusi sebagai prototype. | Cukup tetapi rawan. |

## 9. Celah Akademik dan Teknis

### Bridge-Gap

Celah akademik:

- Evaluasi final belum tersedia.
- Dataset aktual belum ada.
- Hasil `results/evaluation.csv` masih nol dan belum bisa dipakai sebagai Bab 4.
- Ground truth manual perlu aturan anotasi yang ketat.
- Jika tidak ada baseline `gemma_only`, kontribusi depth tidak terbukti.
- Jika hanya menampilkan depth map, depth terlihat sebagai tempelan.
- Jumlah gambar harus cukup agar evaluasi tidak terlihat main-main.

Celah teknis:

- LM Studio harus berjalan dan model Gemma harus loaded.
- Depth threshold perlu kalibrasi dengan dataset lokal.
- Output VLM dapat hallucinate.
- Estimasi depth monocular tidak boleh diklaim presisi meter.
- UI web layak sebagai console eksperimen, bukan produk final.

### MBG

Celah akademik:

- Klaim "untuk penyandang tunanetra" dan "navigasi asistif" terlalu besar jika tanpa UAT target pengguna.
- Functional testing tidak membuktikan efektivitas pengguna akhir.
- Bab 4 berisiko melebar menjadi daftar fitur, bukan evaluasi penelitian.
- Jika responden tunanetra tidak ada, penguji bisa mempertanyakan relevansi target pengguna.
- Jika ada responden tunanetra, muncul beban etika dan keselamatan.
- SDLC waterfall menjelaskan pengembangan, tetapi belum otomatis menjadi kontribusi ilmiah.

Celah teknis:

- Banyak titik gagal saat demo: kamera, mic, permission, speech recognition, TTS, jaringan, API token, backend, tunnel, LM Studio, ONNX.
- Latency end-to-end harus cukup rendah karena output dipakai untuk konteks navigasi.
- Mobile local HTTP bisa bermasalah pada Android jika cleartext traffic tidak cocok.
- Respons AI untuk navigasi dapat berbahaya jika salah.
- Stabilisasi temporal bagus, tetapi sulit dibuktikan manfaatnya tanpa skenario multi-frame.

## 10. Tabel Perbandingan Final

| Aspek | Bridge-Gap | MBG | Project yang Lebih Unggul | Catatan Kritis |
|---|---|---|---|---|
| Kejelasan fokus penelitian | Tinggi | Sedang | Bridge-Gap | Bridge-Gap fokus pada depth-aware description. MBG terlalu luas. |
| Kesesuaian dengan judul skripsi | Tinggi jika evaluasi selesai | Sedang | Bridge-Gap | Judul MBG memicu tuntutan validasi tunanetra. |
| Kesiapan implementasi | Baik | Sangat baik | MBG | MBG lebih lengkap sebagai aplikasi. |
| Kesiapan dokumentasi | Baik | Baik | Seri | Bridge-Gap lebih metodologis; MBG lebih teknis-aplikatif. |
| Kemudahan Bab 1 | Tinggi | Sedang | Bridge-Gap | MBG menarik tetapi rawan overclaim. |
| Kemudahan Bab 2 | Tinggi | Sedang | Bridge-Gap | MBG butuh lebih banyak teori. |
| Kemudahan Bab 3 | Tinggi | Sedang | Bridge-Gap | Bridge-Gap punya alur eksperimen sederhana. |
| Kemudahan Bab 4 | Sedang | Rendah-sedang | Bridge-Gap | Bridge-Gap butuh dataset; MBG butuh UAT/skenario lebih kompleks. |
| Kemudahan testing | Tinggi | Sedang-rendah | Bridge-Gap | Dataset gambar lebih mudah daripada mobile UAT. |
| Kebutuhan responden | Opsional | Tinggi jika klaim tunanetra | Bridge-Gap | Ini faktor penentu. |
| Risiko sidang | Sedang | Tinggi | Bridge-Gap | MBG diserang dari safety dan validasi pengguna. |
| Risiko teknis | Sedang | Tinggi | Bridge-Gap | MBG banyak dependency runtime. |
| Risiko akademis | Sedang | Tinggi | Bridge-Gap | MBG harus hati-hati dengan klaim navigasi. |
| Kekuatan kontribusi | Baik jika evaluasi membuktikan depth | Baik sebagai prototype integrasi | Seri | Bridge-Gap lebih mudah dibuktikan. |
| Kekuatan evaluasi | Belum siap tetapi jalurnya jelas | Belum cukup untuk klaim pengguna | Bridge-Gap | Bridge-Gap tinggal isi data. |
| Relevansi dengan tunanetra | Tidak langsung | Tinggi | MBG | Relevansi tinggi sekaligus risiko tinggi. |
| Kesesuaian penelitian implementasi | Tinggi | Sedang | Bridge-Gap | MBG lebih cocok pengembangan aplikasi. |
| Kesesuaian produk/aplikasi | Sedang | Tinggi | MBG | MBG lebih demoable. |
| Kelayakan selesai cepat | Tinggi jika fokus dataset | Sedang-rendah | Bridge-Gap | MBG bisa terjebak debugging device dan UAT. |
| Kemudahan demo | Tinggi | Sedang | Bridge-Gap | MBG lebih impresif tetapi lebih rawan. |
| Kemudahan jawab penguji | Tinggi jika data siap | Sedang-rendah | Bridge-Gap | Bridge-Gap punya jawaban metodologis lebih bersih. |

## 11. Rekomendasi Project yang Paling Aman

## Rekomendasi Utama

Pilih **Bridge-Gap** sebagai project skripsi utama.

## Alasan

Bridge-Gap paling aman karena masalah penelitiannya spesifik, metodologinya bisa dirapikan, baseline-nya jelas, evaluasinya bisa dilakukan tanpa responden khusus, dan klaimnya dapat dibatasi secara akademis. Dosen penguji masih akan menyerang dataset dan evaluasi, tetapi serangan itu bisa dijawab dengan bukti eksperimen.

MBG secara teknis lebih keren, tetapi skripsi bukan lomba fitur. Skripsi membutuhkan pertanyaan penelitian yang bisa dijawab dengan data yang sah. MBG menuntut pembuktian lebih berat: apakah benar membantu tunanetra, apakah aman, apakah latency cukup, apakah narasi tidak membahayakan, dan apakah UAT valid.

## Risiko Jika Tetap Memilih Bridge-Gap

- Jika dataset tidak selesai, Bab 4 kosong.
- Jika tidak ada baseline `gemma_only`, depth tidak terbukti berguna.
- Jika anotasi manual tidak rapi, evaluasi dianggap subjektif.
- Jika klaim depth terlalu presisi, penguji akan menyerang validitas jarak.

Risiko ini masih realistis diperbaiki dalam waktu terbatas.

## Risiko Jika Tetap Memilih MBG

- Wajib menjawab isu tunanetra, UAT, etika, dan keselamatan.
- Demo lebih rawan gagal karena banyak komponen runtime.
- Penguji bisa menilai project terlalu aplikatif dan kurang evaluasi ilmiah.
- Jika hanya functional testing, klaim "navigasi asistif" terlalu besar.
- Jika tidak ada responden tunanetra, judul harus diturunkan atau dibatasi keras.

Risiko ini lebih berat karena bukan hanya masalah coding, tetapi masalah metodologi dan validitas penelitian.

## Strategi Aman

Gunakan Bridge-Gap sebagai skripsi utama dengan framing:

> Implementasi dan Evaluasi Depth-Aware Image Description Menggunakan Gemma dan Depth Anything V2 pada Citra Lingkungan Indoor.

Jangan framing sebagai alat navigasi untuk tunanetra. Jangan klaim aman untuk mobilitas. Sebut sebagai prototype eksperimen deskripsi visual-spasial indoor.

MBG dijadikan backup teknis atau sumber inspirasi untuk:

- bahasa output yang ringkas dan safety-aware;
- fusion rule yang lebih kuat;
- contoh future work mobile/voice/TTS;
- ide stabilisasi respons, jika benar-benar dibutuhkan dan tidak memperluas scope.

## 12. Roadmap Perbaikan Project Terpilih

Project terpilih: **Bridge-Gap**.

## Prioritas 1 - Wajib Sebelum Penulisan Bab 4

- [ ] Isi `dataset/images/` dengan minimal 30 gambar indoor aktual; 50 lebih baik jika waktu cukup.
- [ ] Pastikan setiap file gambar punya nama stabil dan tidak berubah.
- [ ] Lengkapi `dataset/annotations.csv` sesuai semua gambar.
- [ ] Gunakan kategori anotasi yang konsisten: objek utama, posisi, kategori jarak, status halangan, arah aman.
- [ ] Jalankan batch evaluation untuk `gemma_only` dan `gemma_depth`.
- [ ] Simpan hasil final ke `results/predictions.csv` dan `results/evaluation.csv`.
- [ ] Buat tabel perbandingan metrik per mode.
- [ ] Buat contoh 5-10 kasus sukses dan gagal.
- [ ] Pastikan filename prediction dan annotation sinkron.

## Prioritas 2 - Wajib Sebelum Sidang

- [ ] Tulis batasan penelitian dengan tegas: bukan alat navigasi, bukan sensor jarak presisi, bukan sistem real-time safety-critical.
- [ ] Siapkan jawaban kenapa Gemma dan Depth Anything V2 dipilih.
- [ ] Siapkan diagram pipeline input-proses-output.
- [ ] Siapkan rubrik evaluasi kualitas deskripsi.
- [ ] Tambahkan analisis latency `gemma_only` vs `gemma_depth`.
- [ ] Tambahkan error analysis: depth salah, Gemma hallucination, fusion tidak membantu.
- [ ] Siapkan slide contoh gambar, output Gemma-only, output Gemma+Depth, dan ground truth.

## Prioritas 3 - Tambahan Jika Ada Waktu

- [ ] Tambahkan 1 baseline model lain hanya jika setup sangat mudah; jangan wajib.
- [ ] Tambahkan expert review non-tunanetra untuk menilai kejelasan deskripsi, bukan klaim navigasi.
- [ ] Tambahkan visualisasi depth map pada laporan sebagai pendukung.
- [ ] Tambahkan analisis per jenis ruangan atau per kategori objek.
- [ ] Rapikan UI web hanya sebagai console eksperimen, bukan produk final.

## 13. Strategi Penulisan Skripsi

Strategi aman untuk Bridge-Gap:

1. Bab 1 harus membatasi masalah pada deskripsi gambar indoor yang kurang informasi spasial.
2. Rumusan masalah jangan terlalu banyak. Cukup:
   - bagaimana merancang pipeline Gemma + Depth Anything V2;
   - bagaimana mengevaluasi perbedaan output Gemma-only dan Gemma+Depth;
   - bagaimana pengaruh depth terhadap informasi posisi, jarak, dan halangan.
3. Bab 2 fokus pada VLM, image captioning, monocular depth estimation, Depth Anything V2, Gemma, fusion rule, dan evaluasi deskripsi.
4. Bab 3 jelaskan dataset, anotasi manual, mode eksperimen, metrik, dan alur evaluasi.
5. Bab 4 jangan menjadi demo aplikasi. Bab 4 harus berisi tabel angka, contoh output, analisis failure, dan trade-off latency.
6. Bab 5 jangan klaim sistem aman untuk navigasi. Klaim yang aman: depth membantu memperkaya aspek spasial pada deskripsi indoor dalam skenario dataset yang diuji.

Kalimat klaim aman:

> Sistem yang dikembangkan menunjukkan bahwa integrasi estimasi kedalaman dapat menambahkan informasi spasial pada deskripsi citra indoor, terutama terkait kategori jarak dan peringatan halangan, dengan konsekuensi peningkatan waktu pemrosesan.

Kalimat yang harus dihindari:

> Sistem ini aman digunakan tunanetra untuk navigasi.

> Depth Anything V2 memberikan jarak akurat.

> Gemma memahami semua objek dengan benar.

## 14. Kerangka Jawaban Sidang

### 1. Kenapa memilih project ini?

Karena project ini memiliki masalah yang spesifik dan dapat diuji: deskripsi gambar indoor dari VLM sering menjelaskan objek, tetapi belum selalu memberikan informasi spasial seperti jarak dan potensi halangan. Dengan menggabungkan Gemma dan Depth Anything V2, penelitian dapat mengevaluasi apakah informasi kedalaman membuat deskripsi lebih berguna secara spasial.

### 2. Apa kontribusi utama penelitian?

Kontribusinya adalah implementasi dan evaluasi pipeline lokal depth-aware image description yang membandingkan output Gemma-only dengan output Gemma+Depth pada citra indoor menggunakan anotasi manual dan metrik evaluasi terstruktur.

### 3. Apa peran Depth Anything V2?

Depth Anything V2 digunakan untuk memperkirakan informasi kedalaman dari satu citra RGB. Output depth dipakai sebagai sinyal pendukung untuk menentukan kategori jarak, area terdekat, dan potensi halangan. Model ini tidak diklaim sebagai alat ukur presisi.

### 4. Apa peran Gemma?

Gemma berperan sebagai vision-language model yang menghasilkan deskripsi semantik gambar. Gemma menjawab "apa yang terlihat", sedangkan Depth Anything membantu menambahkan konteks "seberapa dekat" dan "di area mana".

### 5. Apa perbedaan dengan image captioning biasa?

Image captioning biasa cenderung menghasilkan deskripsi semantik. Sistem ini menambahkan informasi spasial dari estimasi kedalaman, sehingga output dapat menyebutkan kedekatan objek, status area depan, atau peringatan halangan jika terdeteksi.

### 6. Bagaimana metode evaluasi?

Evaluasi dilakukan dengan dataset gambar indoor yang dianotasi manual. Mode `gemma_only` digunakan sebagai baseline dan `gemma_depth` sebagai mode usulan. Metrik mencakup akurasi objek/posisi, kategori jarak, obstacle warning, kualitas deskripsi, dan latency.

### 7. Bagaimana membuktikan depth-aware benar-benar berguna?

Dengan membandingkan hasil `gemma_only` dan `gemma_depth` pada gambar yang sama. Jika mode `gemma_depth` lebih baik pada kategori jarak atau obstacle warning, berarti depth memberikan kontribusi. Jika tidak meningkat pada semua aspek, hasil itu tetap dilaporkan sebagai batasan.

### 8. Kenapa tidak membuat aplikasi final?

Karena fokus penelitian adalah pipeline dan evaluasi depth-aware description, bukan pengembangan produk akhir. UI hanya digunakan sebagai alat demonstrasi dan pengujian. Membuat aplikasi final akan memperluas scope dan mengaburkan kontribusi penelitian.

### 9. Kenapa tidak diuji langsung sebagai alat navigasi?

Karena sistem belum dirancang sebagai alat navigasi safety-critical. Pengujian langsung untuk navigasi membutuhkan desain etika, kontrol keselamatan, dan validasi pengguna yang berbeda. Penelitian ini dibatasi pada evaluasi deskripsi citra indoor.

### 10. Apa batasan penelitian?

Batasannya: dataset terbatas pada citra indoor, depth berasal dari estimasi monocular, jarak tidak diklaim presisi, output VLM dapat salah, sistem tidak diuji sebagai alat navigasi real-time, dan hasil berlaku pada dataset yang diuji.

### 11. Apa kelemahan sistem?

Kelemahannya adalah ketergantungan pada kualitas output Gemma, potensi kesalahan depth estimation, threshold depth yang perlu kalibrasi, dan evaluasi yang bergantung pada anotasi manual.

### 12. Apa saran pengembangan?

Pengembangan berikutnya dapat menambah dataset lebih besar, melibatkan evaluator manusia lebih banyak, membandingkan model VLM lain, melakukan kalibrasi depth lebih kuat, menambahkan audio output, dan mengembangkan versi mobile setelah pipeline terbukti.

## 15. Kesimpulan Tegas

**Bridge-Gap adalah pilihan skripsi yang lebih aman, lebih realistis, dan lebih mudah dipertahankan saat sidang.**

MBG lebih menarik sebagai produk dan lebih mengesankan saat demo, tetapi beban akademiknya lebih berbahaya. Ia membawa klaim tunanetra dan navigasi yang memerlukan validasi pengguna, etika, dan bukti keselamatan. Tanpa itu, project yang terlihat canggih justru dapat menjadi sasaran empuk saat sidang.

Bridge-Gap tidak sempurna. Saat ini ia masih lemah pada dataset dan evaluasi. Tetapi kelemahan itu jelas, terbatas, dan bisa diperbaiki dengan pekerjaan yang langsung menghasilkan Bab 4. Dengan dataset 30-50 gambar, anotasi rapi, baseline `gemma_only`, mode `gemma_depth`, metrik yang jujur, dan klaim yang tidak berlebihan, Bridge-Gap punya jalur skripsi yang jauh lebih bersih.

Keputusan praktis:

- Project utama: **Bridge-Gap**.
- Project backup: **MBG**, hanya jika scope direvisi menjadi prototype fungsional dan klaim tunanetra/navigasi diturunkan.
- Fokus 7 hari berikutnya: **dataset, anotasi, batch evaluation, tabel Bab 4**.

