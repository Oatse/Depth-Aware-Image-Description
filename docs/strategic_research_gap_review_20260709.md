# Strategic Research Gap Review - Bride-Gap - 2026-07-09

> Arsip strategi 9 Juli 2026. Keputusan aktif terbaru mengikuti `methodological_upgrade_20260714.md`; Prompt Fusion telah dipensiunkan, bukan dipertahankan sebagai mode pembanding.

Dokumen ini merangkum evaluasi kritis historis setelah rerun Prompt Fusion tweak 44 gambar dan penelusuran literatur eksternal.

## Putusan Singkat

Proyek ini sebaiknya tidak diposisikan sebagai sistem navigasi tunanetra siap pakai. Posisi yang paling aman dan kuat adalah:

> Evaluasi fusi metadata kedalaman relatif untuk meningkatkan deskripsi citra indoor berbahasa Indonesia pada skenario bantuan visual terbatas.

Mode utama untuk Bab 4 tetap `gemma_depth` atau Late Fusion. Prompt Fusion kini hanya menjadi bukti keputusan negatif yang diringkas dalam audit 14 Juli 2026; implementasi dan artefak redundannya telah dihapus.

## Temuan Internal Terbaru

Sumber internal utama:

- `docs/methodological_upgrade_20260714.md`
- `docs/final_experiment_report_20260708.md`
- `docs/final_annotation_revalidation_20260708.md`
- `dataset/final_annotations.csv`
- `results/retired_prompted_decision_evidence_20260714.csv`

Ringkasan hasil:

| Mode | Coverage | Object | Position | Distance | Obstacle | Quality | Latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| Late Fusion | 100.00% | 52.27% | 90.91% | 68.18% | 84.09% | 3.95/5 | 11,794.9 ms |
| Prompt Fusion tweak | 100.00% | 38.64% | 68.18% | 68.18% | 84.09% | 3.59/5 | 14,274.0 ms |

Distribusi dataset final 44 gambar:

| Aspek | Distribusi |
|---|---|
| Source | 30 original, 14 balancing medium/far |
| Distance | 25 dekat, 10 sedang, 7 jauh, 2 sangat dekat |
| Obstacle | 27 yes, 17 no |
| Object position | 18 kanan, 15 tengah, 11 kiri |
| Safer direction | 20 tengah, 13 kiri, 7 kanan, 4 tidak diketahui |

## Kritik Paling Berbahaya Saat Sidang

### 1. Klaim navigasi terlalu besar untuk bukti yang ada

Literatur assistive navigation menekankan kebutuhan sistem yang reliabel, real-time, user-centered, dan aman. Proyek ini baru melakukan evaluasi citra statis indoor. Tidak ada uji pengguna tunanetra, tidak ada video egosentris, tidak ada jalur dinamis, dan tidak ada sensor ground-truth selain anotasi manual.

Risiko pertanyaan penguji:

- "Kalau ini untuk tunanetra, mengapa tidak diuji pada pengguna tunanetra?"
- "Apa jaminan sistem tidak memberi instruksi berbahaya?"
- "Mengapa hasil latency 11-14 detik masih disebut asistif?"

Jawaban defensible:

- Jangan klaim navigasi real-time.
- Klaim sebagai prototype evaluasi deskripsi visual-spasial indoor.
- Nyatakan sistem belum direkomendasikan untuk keputusan keselamatan.

### 2. Dataset 44 gambar masih kecil

Dataset 44 gambar cukup untuk pilot experiment skripsi, tetapi tidak cukup untuk klaim general. Distribusinya juga belum sepenuhnya seimbang: kategori `dekat` dominan, `sangat_dekat` hanya 2 gambar, dan safer direction masih berat ke `tengah`.

Risiko pertanyaan penguji:

- "Mengapa hanya 44 gambar?"
- "Apakah hasil 84.09% obstacle warning tetap valid kalau kategori jauh atau sangat dekat ditambah?"
- "Bagaimana memastikan anotasi tidak subjektif?"

Jawaban defensible:

- Sebut sebagai dataset final pilot lokal terbatas.
- Tambahkan dataset card, annotation protocol, dan audit sheet.
- Tambahkan inter-annotator check kecil pada 10-15 gambar, walau hanya satu putaran.

### 3. Object accuracy rendah

Late Fusion terbaik hanya 52.27% object accuracy. Ini celah serius jika proyek diklaim mengenali objek. Depth membantu posisi dan obstacle, tetapi tidak memperbaiki semantik objek karena depth tidak mengenali kelas objek.

Risiko pertanyaan penguji:

- "Kalau objek utamanya sering salah, apa manfaat sistem?"
- "Mengapa tidak memakai object detector seperti YOLO?"

Jawaban defensible:

- Fokus kontribusi bukan object detection, melainkan fusi depth untuk informasi spasial.
- Tambahkan opsi nilai tambah: lightweight object vocabulary normalization atau YOLO-lite sebagai post-check terbatas untuk objek indoor umum.

### 4. Prompt Fusion kalah, tetapi justru bisa menjadi temuan ilmiah

Prompt Fusion tweak menurunkan position accuracy dan quality karena membersihkan sinyal posisi internal yang sebelumnya membantu evaluator. Ini bukan kegagalan total jika dibahas dengan jujur.

Interpretasi ilmiah:

- Prompt Fusion lebih natural tetapi kurang stabil secara metrik.
- Late Fusion lebih konsisten karena depth dipakai sebagai struktur deterministik.
- Untuk dataset kecil dan model lokal, fusi post-processing lebih aman daripada membiarkan VLM mengolah depth dalam prompt.

### 5. Evaluator masih heuristik

Metrik object, position, distance, obstacle, dan quality bersifat rule-based. Ini sah untuk skripsi prototype, tetapi harus dijelaskan sebagai evaluasi terstruktur berbasis anotasi, bukan standar industri.

Perbaikan minimum:

- Tambahkan confusion matrix per mode.
- Tambahkan bootstrap confidence interval.
- Tambahkan error taxonomy per gambar.
- Tambahkan contoh 5 sukses dan 5 gagal paling representatif.

## Riset Eksternal Yang Menguatkan Arah Proyek

### Kebutuhan domain

WHO mencatat beban global gangguan penglihatan sangat besar dan memerlukan pendekatan yang mendukung kemandirian. Literatur indoor assistive navigation juga menegaskan bahwa lingkungan indoor sulit karena GPS tidak bekerja, layout kompleks, dan kebutuhan pengguna bukan hanya objek, tetapi orientasi, obstacle, dan instruksi yang aman.

Implikasi untuk proyek:

- Bab 1 harus menekankan indoor scene understanding, bukan sekadar image captioning umum.
- Output sistem harus singkat, hati-hati, dan actionable.

### VLM belum kuat pada spatial reasoning

SpatialVLM, SpatialRGPT, VSR, COMFORT, dan SPINBench/AxisBench sama-sama menunjukkan bahwa reasoning spasial pada VLM masih menjadi masalah terbuka. Ini sangat menguntungkan proyek karena alasan penggunaan depth menjadi jelas.

Implikasi untuk proyek:

- Novelty lokal bukan "membuat VLM baru", tetapi menguji apakah metadata depth eksplisit membantu deskripsi spasial indoor.
- Bab 2 bisa membangun argumen: VLM kuat secara semantik, tetapi spatial reasoning masih lemah; depth estimation dapat menjadi sinyal bantu.

### RGB-D dan depth-based captioning sudah menjadi arah sah

RGBD2Cap dan SpatialRGPT menunjukkan bahwa depth bukan aksesori kosmetik; depth dapat dipakai untuk meningkatkan scene description dan reasoning spasial. Depth Anything V2 memberi dasar teknis untuk monocular depth estimation yang praktis tanpa RGB-D camera fisik.

Implikasi untuk proyek:

- Penggunaan Depth Anything V2 harus dijustifikasi sebagai pendekatan monocular yang murah dan praktis.
- Batasannya harus jelas: depth relatif dari satu gambar bukan ground-truth jarak keselamatan.

### BLV/VizWiz literature menuntut reliability dan abstention

VizWiz dan VizWiz-LF menunjukkan kebutuhan nyata pengguna blind/low vision berbeda dari VQA akademik biasa: gambar bisa blur, pertanyaan natural, jawaban panjang bisa membantu, tetapi hallucination sangat berbahaya terutama untuk gambar yang tidak answerable.

Implikasi untuk proyek:

- Tambahkan mekanisme "tidak cukup yakin" atau "informasi visual belum cukup".
- Hindari kalimat absolut seperti "jalur aman"; pakai "area relatif lebih lapang menurut estimasi depth".

## Rekomendasi Perbaikan Prioritas

### Prioritas 1 - Perkuat Bab 4 tanpa menambah scope berbahaya

1. Buat confusion matrix untuk `distance_category` dan `has_obstacle`.
2. Buat error taxonomy per mode:
   - object semantic error
   - left/right/center mismatch
   - near/medium/far mismatch
   - obstacle false positive
   - obstacle false negative
   - over-warning medium depth
   - hallucinated spatial claim
3. Tambahkan bootstrap 95% confidence interval untuk metrik utama.
4. Tambahkan 10 contoh kualitatif: 5 keberhasilan dan 5 kegagalan.

Nilai sidang: membuat proyek terlihat sebagai eksperimen, bukan demo.

### Prioritas 2 - Tambahkan dataset card dan annotation protocol

Buat `docs/dataset_card_final_44.md` yang memuat:

- sumber gambar;
- jumlah gambar;
- distribusi kategori;
- aturan anotasi;
- contoh ambigu;
- batasan dataset;
- alasan 44 gambar cukup sebagai pilot;
- larangan klaim generalisasi.

Tambahkan `docs/annotation_protocol.md` atau perluas dokumen yang ada:

- definisi `dekat`, `sedang`, `jauh`, `sangat_dekat`;
- cara memilih `main_object`;
- cara menentukan `safer_direction`;
- aturan jika ruang sempit atau tidak ada area lapang.

Nilai sidang: mengurangi serangan "anotasinya subjektif".

### Prioritas 3 - Tambahkan statistical guardrail

Implementasi yang masih masuk scope:

- bootstrap CI untuk accuracy dan quality;
- paired comparison Late Fusion vs Prompt Fusion;
- latency summary: mean, median, p95;
- per-class metrics untuk distance dan obstacle.

Nilai sidang: penguji lebih sulit menganggap hasil sebagai angka mentah tanpa analisis.

### Prioritas 4 - Tambahkan safety language dan abstention policy

Di output dan naskah:

- jangan sebut "aman";
- gunakan "relatif lebih lapang menurut estimasi depth";
- tampilkan disclaimer saat `distance_category=sedang` atau `tidak_diketahui`;
- jika Gemma gagal/timeout, jangan memaksa deskripsi visual;
- jika objek tidak teridentifikasi, tetap boleh melaporkan depth tetapi dengan catatan.

Nilai sidang: proyek terlihat matang secara etika dan keselamatan.

### Prioritas 5 - Tambahkan nilai teknis kecil tetapi cerdas

Fitur kecil yang bernilai tinggi dan masih scope:

1. Object synonym normalization
   - Contoh: "mesin cuci/pengering pakaian", "mesin cuci", "laundry machine" dinormalisasi.
   - Tujuan: object accuracy lebih adil tanpa menambah model baru.

2. Spatial confidence label
   - Output: `confidence = high/medium/low` berdasarkan konsistensi depth, object, dan position.
   - Tujuan: memperlihatkan awareness terhadap risiko hallucination.

3. Report generator otomatis
   - Input: predictions + annotations.
   - Output: tabel Bab 4, confusion matrix, contoh gagal.
   - Tujuan: reproducibility dan siap tulis.

4. External validation mini-set
   - 10-15 gambar indoor dari sumber berbeda, dianotasi ulang dengan schema yang sama.
   - Tujuan: bukan untuk mengganti dataset utama, tetapi sanity check generalisasi.

## Ide Out of the Box Yang Masih Realistis

### Depth-Aware Safety Narrator

Bukan navigasi penuh, tetapi "narator keselamatan visual" yang mengubah hasil menjadi tiga level:

- Visual: objek utama dan posisi.
- Spatial: region terdekat dan kategori jarak relatif.
- Safety wording: peringatan hati-hati, bukan instruksi mutlak.

Ini membuat proyek punya value praktis tanpa berbohong soal keselamatan.

### Failure-First Evaluation

Daripada hanya mengejar akurasi, jadikan kontribusi sebagai evaluasi failure mode:

- kapan VLM salah posisi;
- kapan Prompt Fusion over-trust depth;
- kapan Late Fusion lebih stabil;
- kapan depth tidak membantu karena masalahnya semantik objek.

Ini kuat untuk skripsi karena menunjukkan berpikir ilmiah.

### Human-Centered Output Rubric Tanpa Uji Pengguna Penuh

Jika tidak sempat UAT dengan tunanetra, buat expert heuristic rubric berbasis literatur:

- ringkas;
- tidak overclaim;
- menyebut obstacle hanya jika dekat;
- menyebut ketidakpastian;
- tidak memberi instruksi arah absolut.

Gunakan rubrik ini sebagai evaluasi kualitatif tambahan, bukan klaim usability final.

## Roadmap Pengerjaan

### 1-2 hari

- Tulis dataset card final 44.
- Buat confusion matrix dan failure taxonomy.
- Tambahkan CI bootstrap.
- Perbarui Bab 4 dengan tabel hasil terbaru.

### 3-5 hari

- Tambahkan external validation mini-set 10-15 gambar.
- Buat comparison report Late Fusion vs Prompt Fusion vs baseline lama.
- Tambahkan 10 contoh visual kualitatif.

### 1 minggu

- Rapikan Bab 1: klaim, ruang lingkup, kontribusi.
- Rapikan Bab 2: VLM spatial reasoning, monocular depth, assistive indoor scene understanding.
- Rapikan Bab 3: annotation protocol, evaluation protocol, model/runtime.
- Rapikan Bab 4: hasil, interpretasi, kegagalan, batasan.

## Final Recommendation

Jangan menambah fitur besar seperti full navigation, SLAM, voice assistant lengkap, atau mobile app baru. Itu akan memperbesar beban validasi dan membuka celah sidang.

Tambahan terbaik adalah:

1. dataset card;
2. annotation protocol;
3. statistical confidence interval;
4. failure taxonomy;
5. safety-aware wording;
6. optional external mini-validation.

Dengan enam hal itu, proyek berubah dari "demo Gemma + depth" menjadi "eksperimen terkontrol tentang fusi kedalaman untuk deskripsi visual-spasial indoor". Itu jauh lebih sulit diremehkan.
