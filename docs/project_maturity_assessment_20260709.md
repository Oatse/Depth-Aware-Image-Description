# Project Maturity Assessment - Bride-Gap - 2026-07-09

> Arsip snapshot 9 Juli 2026. Status metode aktif mengikuti `methodological_upgrade_20260714.md`; Depth-to-Spatial Prompting telah dipensiunkan.

Dokumen ini menilai kematangan codebase, eksperimen, dan kesiapan akademik skripsi berdasarkan pembacaan `instructions/PROJECT_INITIALIZATION.md`, `CONTEXT.md`, `README.md`, dokumen evaluasi, dataset final, dan implementasi program.

## Ringkasan Eksekutif

Status proyek saat ini: **layak sebagai prototype eksperimen skripsi, belum layak diklaim sebagai sistem navigasi atau assistive safety system**.

Estimasi kematangan:

| Aspek | Nilai | Interpretasi |
|---|---:|---|
| Kematangan implementasi software | 82% | Struktur kode, test, dan pipeline cukup baik; runtime Gemma lokal masih tidak stabil saat audit. |
| Kematangan eksperimen | 76% | Dataset final 44 gambar dan evaluasi sudah ada; analisis statistik, confidence interval, dan failure taxonomy belum lengkap. |
| Kematangan akademik skripsi | 70% | Arah kontribusi sudah defensible; Bab 4 masih perlu diperkuat agar tidak terlihat sebagai demo model. |
| Kesiapan sidang | 68% | Bisa dipertahankan jika klaim dibatasi; masih rawan diserang pada dataset kecil, object accuracy rendah, dan runtime reproducibility. |
| Kematangan keseluruhan | 74% | Sudah melewati fase prototype awal, tetapi belum final thesis package. |

Putusan utama:

> Gunakan `gemma_depth` atau Late Fusion sebagai mode utama. Posisikan penelitian sebagai evaluasi depth-aware image description pada citra indoor, bukan sistem navigasi tunanetra siap pakai.

## Bukti Audit

### Verifikasi yang dijalankan

| Pemeriksaan | Hasil |
|---|---|
| `python -m pytest -q` | 43 passed |
| `python -m compileall -q app models services scripts tests` | Lolos |
| Preflight `depth_only` pada dataset final | Lolos: 44 images, 44 annotations, depth model ready |
| Preflight `gemma_depth` pada dataset final | Gagal: `Gemma runtime belum ready: error` |
| Jumlah file Python | 39 |
| Jumlah file test | 11 |
| Jumlah dokumen Markdown di `docs/` | 19 |
| Jumlah file pustaka di `docs/pustaka/` | 27 |

### Dataset final

| Aspek | Distribusi |
|---|---|
| Total gambar/anotasi | 44 gambar, 44 anotasi |
| Source subset | 30 original, 14 balancing medium/far |
| Distance category | 25 dekat, 10 sedang, 7 jauh, 2 sangat dekat |
| Obstacle | 27 yes, 17 no |
| Object position | 18 kanan, 15 tengah, 11 kiri |
| Safer direction | 20 tengah, 13 kiri, 7 kanan, 4 tidak diketahui |

### Hasil evaluasi terakhir

Berdasarkan artefak aktif `results/final_evaluation_metrics_20260714.csv`:

| Mode | Coverage | Object | Position | Distance | Obstacle | Quality | Latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| Late Fusion (`gemma_depth`) | 100.00% | 52.27% | 90.91% | 68.18% | 84.09% | 3.95/5 | 11,794.9 ms |

Interpretasi:

- Late Fusion unggul pada object, position, quality, dan latency.
- Prompt Fusion tidak mendukung klaim sebagai mode utama dan telah dihapus dari sistem aktif pada audit 14 Juli 2026.
- Depth membantu metadata spasial dan obstacle warning, tetapi tidak memperbaiki object semantics.
- Latency 11-14 detik tidak mendukung klaim real-time.

## Temuan Kritis

### KRITIS-1: Klaim tujuan harus dibatasi

`CONTEXT.md` sudah benar menahan bahasa domain: gunakan "potensi halangan visual" dan "area relatif lapang", bukan "jalur aman" atau "arah aman". Namun dari sisi sidang, risiko klaim tetap tinggi karena domain proyek bersinggungan dengan bantuan pengguna tunanetra.

Risiko:

- Penguji dapat meminta validasi pengguna tunanetra, uji keselamatan, atau uji real-time.
- Proyek belum punya bukti untuk menjawab klaim navigasi.

Rekomendasi:

- Rumusan judul dan tujuan harus memakai frasa **depth-aware image description** atau **deskripsi visual-spasial indoor**.
- Jangan memakai klaim "navigasi aman", "sistem pemandu", atau "jalur aman".
- Di Bab 1 dan Bab 5, tulis eksplisit bahwa sistem adalah prototype evaluasi citra statis.

### KRITIS-2: Reproducibility runtime Gemma belum stabil

Saat audit, preflight mode `gemma_depth` gagal karena runtime Gemma tidak ready. Ini berbeda dengan preflight depth-only yang lolos.

Risiko:

- Hasil final sulit direproduksi jika LM Studio/model tidak sedang loaded.
- Sidang atau demonstrasi bisa gagal jika hanya mengandalkan runtime lokal.
- Default config saat ini memakai `google/gemma-4-e4b`, sementara hasil final utama menggunakan artefak `gemma_e2b`.

Rekomendasi:

- Tambahkan dokumen `docs/reproducibility_runbook.md`.
- Kunci model eksperimen final: nama model, versi/quantization jika ada, endpoint LM Studio, timeout, max tokens.
- Simpan command final yang benar untuk e2b dan jelaskan perbedaan dengan default config.
- Untuk sidang, gunakan artefak CSV final sebagai bukti utama, demo runtime sebagai tambahan.

### KRITIS-3: Endpoint `/experiment-status` belum merepresentasikan dataset final

`app/main.py` membaca `dataset/annotations.csv`, `dataset/images`, dan `results/evaluation.csv`. Sementara eksperimen final berada di `dataset/final_annotations.csv`, `dataset/final_images`, dan file `results/final_*` / `results/rerun_*`.

Risiko:

- Dashboard status dapat memberi gambaran readiness yang salah.
- Penguji atau pembimbing yang membuka endpoint bisa melihat data yang bukan final.

Rekomendasi:

- Tambahkan konfigurasi path dataset/evaluation final.
- Atau ubah `/experiment-status` agar menampilkan dataset default dan dataset final secara terpisah.
- Minimal dokumentasikan bahwa endpoint status adalah status eksperimen default, bukan final thesis run.

### KRITIS-4: Evaluator masih heuristik dan perlu diposisikan sebagai metric proxy

`services/evaluator.py` memakai pencocokan string untuk object, position, distance, obstacle, dan description quality. Ini cukup untuk skripsi prototype, tetapi belum kuat sebagai metric akademik tanpa penjelasan batasan.

Risiko:

- Object accuracy bisa undercount karena sinonim terbatas.
- Position accuracy bisa berubah jika kalimat final menyebut/menghapus kata "kiri", "kanan", "tengah".
- Description quality bukan human evaluation, melainkan skor turunan dari aturan.

Rekomendasi:

- Bab 3 harus menyebut metrik sebagai **evaluasi berbasis anotasi dan rule-based proxy**.
- Tambahkan daftar alias object yang lebih lengkap atau normalisasi istilah.
- Tambahkan confusion matrix dan contoh kualitatif agar angka tidak berdiri sendiri.

## Kelemahan Program

### 1. Default path eksperimen belum sinkron dengan final dataset

README dan script default masih mengarah ke `dataset/images`, `dataset/annotations.csv`, dan `results/evaluation.csv`, sedangkan hasil final memakai path khusus. Ini normal untuk proses eksplorasi, tetapi buruk untuk reproducibility akhir.

Perbaikan:

- Tambahkan preset command `final` pada README.
- Tambahkan `scripts/run_final_evaluation.py` atau dokumentasi final command.
- Pastikan endpoint status bisa membaca hasil final.

### 2. Runtime VLM terlalu bergantung pada LM Studio lokal

Codebase sudah punya preflight, timeout, dan error handling. Namun state eksternal LM Studio tetap menjadi single point of failure.

Perbaikan:

- Tambahkan smoke check khusus `/v1/models` dan `/chat/completions` teks pendek.
- Tambahkan catatan fallback: jika demo runtime gagal, tampilkan hasil final dari CSV.
- Simpan satu contoh JSON response yang valid sebagai artefak lampiran.

### 3. Late Fusion bisa sukses walau Gemma error

Dalam `services/pipeline.py`, mode `gemma_depth` tetap dapat menghasilkan `success=True` ketika Gemma error, selama depth tersedia. Ini berguna untuk robustness, tetapi berisiko membingungkan evaluasi jika tidak dipisahkan.

Perbaikan:

- Tambahkan flag `partial_success` atau `gemma_available`.
- Pada evaluasi final, laporkan jumlah baris dengan `error` per mode.
- Untuk Bab 4, pastikan metrik utama hanya memakai prediksi tanpa error.

### 4. Tidak ada confidence interval

Dataset 44 gambar membuat angka akurasi sensitif terhadap beberapa gambar. Tanpa confidence interval, klaim peningkatan terlihat lebih pasti daripada kenyataannya.

Perbaikan:

- Tambahkan bootstrap 95% confidence interval untuk object, position, distance, obstacle, dan quality.
- Tambahkan paired comparison Late Fusion vs Prompt Fusion.

### 5. Tidak ada failure taxonomy final yang langsung siap Bab 4

Sudah ada beberapa artefak failure summary, tetapi laporan final masih perlu taxonomy yang langsung menjawab:

- salah objek;
- salah posisi;
- salah kategori jarak;
- obstacle false positive;
- obstacle false negative;
- over-warning pada jarak sedang;
- hallucinated spatial claim;
- timeout/runtime failure.

## Kekuatan Program

### 1. Struktur codebase cukup rapi

Pemisahan modul sudah jelas:

- `app/`: FastAPI dan endpoint.
- `models/`: Gemma, Depth Anything, fusion.
- `services/`: pipeline, evaluator, preflight, validation, logging.
- `scripts/`: batch/resumable/single-image evaluation.
- `tests/`: unit dan API tests.

Ini sudah lebih matang daripada prototype satu-file.

### 2. Test suite sudah signifikan

`43 passed` menunjukkan ada perhatian pada regression safety. Test mencakup API, fusion, evaluator, preflight, result logger, depth analysis, depth prompting, dan Gemma client.

Kekurangan: belum terlihat CI, belum ada coverage report, dan belum ada integration test dengan runtime LM Studio nyata.

### 3. Dataset final sudah lebih matang daripada baseline awal

Dataset final 44 gambar dengan anotasi revalidated jauh lebih layak daripada kondisi awal proyek yang hanya punya data minimal. Ini memperbaiki kesiapan Bab 4 secara signifikan.

Kekurangan: ukuran tetap kecil dan distribusi kategori belum seimbang.

### 4. Bahasa domain sudah aman

`CONTEXT.md` adalah aset penting. Dokumen itu mencegah proyek berubah menjadi klaim navigasi yang tidak terbukti. Ini harus dijadikan dasar penulisan Bab 1, Bab 3, Bab 4, dan Bab 5.

## Analisis Kematangan Akademik

### Bab 1

Kondisi: cukup siap, tetapi harus disiplin pada klaim.

Yang harus ditulis:

- masalah: VLM dapat mendeskripsikan visual, tetapi informasi spasial/kedalaman masih terbatas;
- tujuan: menguji kontribusi estimasi kedalaman pada deskripsi visual-spasial indoor;
- ruang lingkup: citra indoor statis, dataset lokal terbatas, depth relatif, bukan navigasi real-time.

Yang harus dihindari:

- klaim sistem pemandu tunanetra;
- klaim jalur aman;
- klaim jarak akurat berbasis sensor.

### Bab 2

Kondisi: sumber sudah cukup untuk mulai penulisan.

`docs/pustaka/source_index_20260709.md` berisi 23 sumber inti, melebihi minimum 20 sumber. Namun daftar pustaka final tetap perlu dicek Harvard, DOI, dan rasio 70% artikel ilmiah.

Struktur Bab 2 yang disarankan:

1. Gangguan penglihatan dan kebutuhan assistive visual description.
2. Vision-language model untuk image description.
3. Keterbatasan spatial reasoning pada VLM.
4. Monocular depth estimation.
5. RGB-D/depth-aware captioning.
6. Fusion strategy: Late Fusion vs Depth-to-Spatial Prompting.
7. Evaluasi deskripsi visual-spasial.

### Bab 3

Kondisi: cukup kuat untuk metode penelitian, tetapi perlu ditulis lebih formal.

Yang harus ada:

- arsitektur pipeline;
- dataset final dan annotation schema;
- preprocessing gambar;
- model Gemma dan Depth Anything V2;
- grid area 3x3;
- strategi fusion;
- evaluator dan metrik;
- preflight dan reproducibility protocol.

Kekurangan saat ini:

- belum ada dataset card formal;
- belum ada runbook reproducibility;
- belum ada confidence interval method.

### Bab 4

Kondisi: ada hasil, tetapi pembahasan belum cukup kuat untuk sidang jika hanya menampilkan tabel akurasi.

Yang harus ditambahkan:

- confusion matrix distance dan obstacle;
- per-class analysis;
- failure taxonomy;
- contoh visual sukses/gagal;
- interpretasi kenapa Prompt Fusion kalah;
- diskusi object accuracy rendah;
- diskusi latency dan batas real-time.

### Bab 5

Kondisi: harus diarahkan agar tidak overclaim.

Kesimpulan harus berbunyi kira-kira:

- Late Fusion memberi hasil paling stabil pada dataset final.
- Depth membantu aspek position/distance/obstacle secara terbatas.
- Prompt Fusion tidak terbukti lebih baik pada dataset ini.
- Sistem belum dapat diklaim sebagai sistem navigasi atau keselamatan.

## Risiko Sidang

| Risiko | Tingkat | Alasan | Mitigasi |
|---|---|---|---|
| Klaim navigasi terlalu kuat | Tinggi | Tidak ada UAT tunanetra, video, atau safety validation | Batasi sebagai deskripsi visual-spasial citra statis |
| Runtime demo gagal | Tinggi | Preflight Gemma gagal saat audit | Siapkan artefak CSV final dan runbook |
| Dataset dianggap kecil | Sedang-Tinggi | 44 gambar pilot, kategori belum seimbang | Jelaskan pilot scope, tambah dataset card, tambah mini validation jika sempat |
| Object accuracy rendah | Sedang-Tinggi | Late Fusion hanya 52.27% | Tegaskan kontribusi depth bukan object detection |
| Evaluator dianggap subjektif | Sedang | Rule-based proxy dan anotasi manual | Jelaskan metrik, tambah contoh kualitatif dan confidence interval |
| Prompt Fusion kalah | Sedang | Mode yang lebih kompleks tidak menang | Jadikan temuan: late fusion lebih stabil untuk prototype lokal |

## Rekomendasi Prioritas

### P0 - Wajib sebelum penulisan final

1. Buat `docs/dataset_card_final_44.md`.
2. Buat `docs/reproducibility_runbook.md`.
3. Tambahkan Bab 4-ready report: confusion matrix, failure taxonomy, contoh sukses/gagal.
4. Selaraskan README dengan dataset/evaluasi final.
5. Jelaskan model final e2b vs default config e4b.

### P1 - Sangat disarankan

1. Tambahkan bootstrap confidence interval.
2. Tambahkan object alias normalization yang lebih luas.
3. Tambahkan endpoint `/experiment-status/final` atau konfigurasi path final.
4. Tambahkan smoke test runtime LM Studio yang eksplisit.

### P2 - Nilai tambah jika waktu cukup

1. Mini external validation 10-15 gambar.
2. Coverage report test.
3. CI sederhana untuk test non-runtime.
4. Export otomatis tabel Bab 4 ke Markdown/CSV.

## Kesimpulan Penilaian

Bride-Gap sudah cukup matang sebagai **prototype eksperimen terkontrol**. Nilai kuatnya ada pada pipeline yang terpisah jelas, test yang berjalan, dataset final 44 gambar, dan evaluasi mode fusion yang menghasilkan temuan nyata: Late Fusion lebih stabil daripada Prompt Fusion.

Kelemahan utamanya bukan lagi "program belum jadi", tetapi:

1. reproducibility runtime Gemma;
2. penyelarasan path final dengan app/README;
3. kekuatan analisis Bab 4;
4. batas klaim akademik;
5. ukuran dan distribusi dataset.

Jika lima area itu dibereskan, proyek ini dapat dipertahankan sebagai skripsi informatika yang cukup kuat. Jika tidak, proyek tetap terlihat sebagai demo AI lokal yang menarik, tetapi rawan dianggap belum cukup ilmiah saat sidang.
