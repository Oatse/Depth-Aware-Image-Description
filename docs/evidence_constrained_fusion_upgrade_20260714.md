# Implementasi Fusi Regional Berbatas Bukti

Tanggal: 14 Juli 2026. Status: implementasi aktif dan evaluasi terkontrol selesai.

## Putusan

Mode `gemma_depth` kini memakai **evidence-constrained regional late fusion**. Deskripsi Gemma dan ringkasan depth tetap diproses sebagai dua sumber bukti berbeda. Fusion hanya menambahkan kategori kedalaman relatif pada region grid 3x3 dan, untuk kategori `dekat` atau `sangat_dekat`, peringatan potensi halangan pada region tersebut.

Sistem tidak menyatakan bahwa depth suatu region adalah jarak objek yang disebut Gemma. Pipeline belum menghasilkan bounding box, mask, atau korespondensi objek-piksel, sehingga object-depth binding belum dapat dibuktikan. Kebijakan verbose lama dipertahankan hanya sebagai kontrol eksperimen dan bukan default runtime.

Keputusan ini memperbaiki validitas klaim, tetapi bukan novelty algoritmik umum. Kontribusi yang dapat dipertahankan adalah desain kontrak bukti, kontrol pasangan, evaluator yang tidak bocor, dan analisis kegagalan pada PoC lokal.

## Dasar Riset

- [SpatialRGPT](https://papers.neurips.cc/paper_files/paper/2024/file/f38cb4cf9a5eaa92b3cfa481832719c6-Paper-Conference.pdf) memakai box/mask dan representasi 3D untuk grounded spatial reasoning. Ini mendukung kebutuhan lokalisasi eksplisit sebelum mengikat objek ke depth.
- [SD-VLM](https://papers.neurips.cc/paper_files/paper/2025/file/30bc3a3a44c9d2e3f32e6dd1cd18f552-Paper-Conference.pdf) meneliti beberapa mekanisme integrasi depth ke VLM. Paper tersebut menunjukkan bahwa "memberi konteks depth" bukan satu operasi tunggal; cara representasi dan integrasinya harus diuji.
- [SpatialVLM](https://openaccess.thecvf.com/content/CVPR2024/papers/Chen_SpatialVLM_Endowing_Vision-Language_Models_with_Spatial_Reasoning_Capabilities_CVPR_2024_paper.pdf) memperoleh kemampuan spasial melalui data dan training khusus. Proyek ini tidak melakukan training tersebut dan tidak boleh mengklaim kemampuan setara.
- [Shi et al., ICML 2023](https://proceedings.mlr.press/v202/shi23a.html) menunjukkan bahwa konteks tambahan yang tidak relevan dapat menurunkan performa reasoning. Ini konsisten dengan hasil prompting lama yang tidak otomatis membaik ketika metadata depth dimasukkan ke prompt.
- [Selective Classification](https://papers.neurips.cc/paper_files/paper/2017/hash/4a8423d5e91fda00bb7e46540e2b0cf1-Abstract.html) dan [calibration of neural networks](https://proceedings.mlr.press/v70/guo17a.html) menjadi alasan untuk tidak menyebut skor heuristik internal sebagai `confidence` tanpa evaluasi kalibrasi.
- [Depth Anything V2](https://arxiv.org/abs/2406.09414) menyediakan dasar model depth. Dataset proyek tidak memiliki sensor depth atau parameter kamera, sehingga checkpoint metric-indoor tetap dievaluasi sebagai kategori visual relatif, bukan ground truth meter.

## Bukti Lokal Sebelum Implementasi

### Tidak Ada Grounding Objek-Depth

- Posisi terstruktur Gemma selaras dengan region depth global hanya pada 1 dari 44 citra.
- Bahkan bila posisi anotasi dipakai sebagai oracle, posisi objek utama hanya selaras dengan region depth global pada 21 dari 44 citra (47,73%).
- Karena itu, region terdekat global tidak dapat dianggap sebagai jarak objek utama.

Arsitektur object-grounded baru baru layak jika proyek menambahkan detector/segmenter, mendefinisikan pemetaan mask ke depth, membuat label grounding, dan mengevaluasi kegagalan lokalisasi secara terpisah. Menambahkan aturan baru tanpa komponen tersebut hanya memindahkan asumsi ke kode.

### Evaluator Lama Bocor

Evaluator lama menerima kata posisi dari `final_description`. Fusion sendiri menambahkan nama region, sehingga output dapat mendapat kredit posisi objek walau field `object_position` salah. Setelah evaluator hanya memakai field terstruktur:

| Artefak `gemma_depth` | Object | Position | Object-position joint |
|---|---:|---:|---:|
| Evaluator lama | 52,27% | 90,91% | tidak tersedia |
| Evaluator ketat | 34,09% | 31,82% | 11,36% |

Penurunan ini bukan regresi model. Ia adalah penghapusan kredit yang tidak sah. Metrik depth tidak berubah: distance accuracy 68,18%, obstacle accuracy 84,09%, precision 88,46%, recall 85,19%, dan F1 86,79%.

## Perubahan Implementasi

1. `FusionPolicy.EVIDENCE_CONSTRAINED` menjadi default `gemma_depth`; `LEGACY_VERBOSE` hanya untuk kontrol.
2. Final description dibatasi maksimal tiga kalimat dan tidak menambahkan klaim area lapang ke teks utama.
3. Provenance `fusion_policy` dan `fusion_strategy` disimpan pada hasil dan ditampilkan di UI.
4. Parser Gemma mengubah posisi compound/out-of-schema menjadi `tidak_diketahui`, bukan memilih salah satu arah secara arbitrer.
5. Object dan position hanya dinilai dari field terstruktur; object-position joint accuracy ditambahkan.
6. Metrik semantik `depth_only` ditulis N/A. Skor kualitas teks heuristik 1-5 dihapus.
7. Evaluator menghasilkan scope keseluruhan dan subgroup `source_subset`.
8. Preflight mewajibkan `distance_annotation_basis=visual_relative`, memvalidasi `annotation_confidence`, dan menolak kolom jarak fisik seperti `distance_cm` atau `distance_meters`.
9. Script kontrol membuat dua teks dari cabang Gemma dan depth yang sama. Tidak ada pemanggilan Gemma kedua yang dapat mengacaukan perbandingan.
10. UI menamai mode aktif `Fusi Regional Berbatas Bukti` dan menjelaskan bahwa depth tidak diikat ke objek tertentu.

## Keputusan Anotasi

Anotasi distance tidak diubah. Tidak tersedia sensor depth, kalibrasi kamera, pengukuran meter, atau anotator independen yang dapat membuktikan label baru lebih benar. Mengubah label setelah melihat prediksi juga berisiko menjadi outcome-driven relabeling.

Dataset tetap memakai `distance_annotation_basis=visual_relative`. Distribusi confidence adalah 40 `medium`, 4 `low`, dan 0 `high`. Nilai confidence adalah self-rating anotator, bukan probabilitas terkalibrasi. Tidak ada estimasi jarak spesifik yang ditambahkan.

Pemeriksaan temporal menunjukkan distance accuracy 76,67% pada `original_30` dan 50,00% pada 14 citra tambahan; obstacle accuracy masing-masing 86,67% dan 78,57%. Penurunan ini dipertahankan sebagai bukti sensitivitas distribusi, bukan diperbaiki dengan menala ulang label atau threshold pada seluruh data.

## Eksperimen Kontrol Kebijakan Fusion

Kedua kebijakan memakai 44 deskripsi Gemma historis yang sama dan satu hasil depth bersama per citra. Karena metadata terstruktur identik, seluruh metrik object/depth dan component-sum latency juga identik. Variabel yang diuji hanya kebijakan penyusunan teks.

Kebijakan verbose menghasilkan rata-rata 532,6 karakter, 71,1 kata, dan 5 kalimat. Kebijakan berbatas bukti menghasilkan 329,9 karakter, 45,0 kata, dan 3 kalimat: pengurangan panjang karakter sekitar 38,1% tanpa membuang deskripsi visual Gemma atau fakta kategori depth regional.

### Image-aware Judge 9router

Judge memakai label rute `cx/gpt-5.5`, rubric `spatial-description-judge-v2-image-aware`, citra asli sebagai bukti utama, anotasi sebagai pembanding sekunder, nama mode dibutakan, dan tiga pengulangan per citra. Label rute tidak dianggap sebagai snapshot upstream immutable. Hasil berpasangan:

| Metrik | Verbose lama | Berbatas bukti | Selisih | Bootstrap 95% snapshot |
|---|---:|---:|---:|---:|
| Semantic correctness | 3,9167 | 3,9773 | +0,0606 | [-0,0379; 0,1667] |
| Spatial accuracy | 3,3485 | 3,4621 | +0,1136 | [-0,0985; 0,3258] |
| Groundedness | 3,7803 | 3,9621 | +0,1818 | [0,0530; 0,3182] |
| Clarity | 4,2879 | 4,4545 | +0,1667 | [0,0530; 0,2879] |
| Overall | 3,7045 | 3,9015 | +0,1970 | [0,0682; 0,3258] |

Interpretasi yang diizinkan: pada snapshot 44 citra dan judge tersebut, kebijakan berbatas bukti mempunyai rata-rata groundedness, clarity, dan overall lebih tinggi; interval bootstrap pasangan tidak memotong nol untuk tiga metrik itu. Semantic correctness dan spatial accuracy arahnya positif tetapi interval masih memotong nol.

Interpretasi yang dilarang: hasil ini tidak membuktikan superioritas pada populasi, tidak menghilangkan bias judge, dan bukan pengganti human rating. Bootstrap merangkum stabilitas perbedaan pada 44 pasangan yang tersedia, bukan confidence interval generalisasi global.

## Trade-off Setelah Perubahan

### Keuntungan

- Klaim akhir sesuai bukti yang benar-benar dihasilkan pipeline.
- Teks lebih pendek dan, pada judge yang sama, lebih jelas serta lebih grounded.
- Evaluasi tidak lagi memberi kredit posisi objek dari kata region yang ditambahkan fusion.
- Kebijakan lama tetap dapat direplikasi sebagai kontrol tanpa menjadi fitur pengguna.
- Preflight mencegah jarak fisik palsu masuk ke anotasi final.

### Kerugian dan Batas

- Sistem belum dapat menjawab jarak relatif objek tertentu.
- Grid 3x3 masih post-processing kasar atas depth map kontinu.
- Object-position joint accuracy rendah; masalah semantik Gemma tidak diselesaikan oleh fusion.
- Kategori depth sensitif terhadap distribusi data tambahan.
- Kebijakan baru memperbaiki penyajian bukti, bukan akurasi depth atau novelty learned fusion.
- Image-aware judge bergantung pada router/provider eksternal, mempunyai risiko privasi, biaya, bias visual, dan variasi keluaran.
- Request sinkron inferensi nyata masih dapat melampaui 90 detik. Polling menjaga UI responsif, tetapi tidak mengurangi waktu komputasi model.

## Artefak Audit

- `results/final_evaluation_strict_20260714.csv`
- `results/controlled_fusion_predictions_20260714.csv`
- `results/controlled_fusion_evaluation_20260714.csv`
- `results/llm_judge_9router_controlled_legacy_20260714.csv`
- `results/llm_judge_9router_controlled_constrained_20260714.csv`
- `results/llm_judge_9router_controlled_pairwise_20260714.csv`

Perintah reproduksi tersedia di `docs/reproducibility_runbook_20260714.md`.
