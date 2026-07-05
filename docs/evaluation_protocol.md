# Evaluation Protocol

Dokumen ini menjelaskan prosedur evaluasi prototype depth-aware image description untuk kebutuhan skripsi.

## Tujuan Evaluasi

Evaluasi bertujuan membandingkan empat mode utama:

1. `gemma_only`: Gemma Baseline, yaitu deskripsi visual dan relasi spasial kualitatif dari Gemma tanpa metadata depth eksplisit.
2. `depth_only`: ringkasan depth tanpa pemahaman semantik Gemma.
3. `gemma_depth`: deskripsi visual Gemma yang digabungkan dengan depth summary melalui late/rule-based fusion.
4. `gemma_depth_prompted`: Depth-to-Spatial Prompting, yaitu metadata depth dimasukkan ke prompt Gemma sebelum deskripsi akhir dibuat.

Pertanyaan yang diuji: apakah informasi depth membuat deskripsi lingkungan indoor lebih informatif untuk metadata kedalaman relatif, area terdekat, potensi halangan visual, dan area relatif lapang; serta apakah prompt-level fusion lebih baik daripada late fusion. Evaluasi ini tidak boleh dibaca sebagai pembuktian bahwa Gemma tidak mampu memahami gambar.

## Dataset

Dataset disimpan di `dataset/images/` dan anotasi di `dataset/annotations.csv`.

Jumlah minimal untuk eksperimen awal:

- 30 gambar indoor untuk baseline.
- 50-100 gambar untuk hasil yang lebih stabil.

Skenario yang disarankan:

- Objek dekat di area depan.
- Jalur tengah kosong.
- Objek dominan di kiri.
- Objek dominan di kanan.
- Objek kecil di lantai.
- Objek besar seperti kursi, meja, lemari, atau pintu.
- Kondisi terang dan redup.
- Variasi jarak 0.5 m, 1 m, dan 2 m.

## Format Anotasi

Kolom wajib:

```csv
image_name,main_object,object_position,distance_meter,distance_category,has_obstacle,front_area_status,safer_direction,notes
```

Kategori jarak:

- `sangat_dekat`: kurang dari 0.5 meter.
- `dekat`: 0.5 sampai kurang dari 1.0 meter.
- `sedang`: 1.0 sampai kurang dari 2.0 meter.
- `jauh`: 2.0 meter atau lebih.

## Prosedur Eksperimen

1. Masukkan gambar ke `dataset/images/`.
2. Buat atau lengkapi `dataset/annotations.csv`.
3. Pastikan LM Studio berjalan dan model Gemma loaded.
4. Pastikan `DEPTH_MODEL_PATH` mengarah ke folder ONNX Depth Anything.
5. Jalankan preflight eksperimen:

```bash
python scripts\run_batch_evaluation.py --preflight-only
```

Preflight harus lulus sebelum hasil dipakai untuk Bab 4. Pemeriksaan ini memastikan:

- folder gambar tidak kosong;
- setiap gambar memiliki anotasi;
- setiap baris anotasi memiliki file gambar yang sesuai;
- kolom anotasi wajib tersedia;
- mock runtime tidak aktif untuk eksperimen final;
- model depth tersedia;
- Gemma di LM Studio sudah siap jika mode memakai Gemma.

Untuk dry run development, mock boleh dipakai hanya dengan flag eksplisit:

```bash
python scripts\run_batch_evaluation.py --preflight-only --allow-mock
```

Hasil dry run mock tidak boleh digunakan sebagai hasil eksperimen final.

6. Jalankan batch evaluation:

```bash
python scripts\run_batch_evaluation.py --images-dir dataset\images --annotations dataset\annotations.csv
```

Secara default, batch evaluation menjalankan `gemma_only`, `depth_only`, `gemma_depth`, dan `gemma_depth_prompted`. Untuk evaluasi parsial/resumable setelah mode baru ditambahkan, gunakan:

```bash
python scripts\run_resumable_evaluation.py --limit-jobs 2
```

7. Baca output:

- `results/predictions.csv`
- `results/evaluation.csv`
- `results/depth_maps/`

## Metrik

Metrik otomatis awal:

- object accuracy;
- position accuracy;
- distance category accuracy, hanya berlaku untuk mode yang menghasilkan metadata depth;
- obstacle warning accuracy, hanya berlaku untuk mode yang menghasilkan metadata depth;
- description quality heuristic 1-5;
- average latency.

Pada `gemma_only`, distance category accuracy dan obstacle warning accuracy ditulis sebagai N/A karena mode tersebut tidak mengekstrak metadata depth eksplisit. Gemma Baseline tetap dievaluasi pada object accuracy, position accuracy, dan kualitas deskripsi visual-spasial kualitatif.

Metrik kualitas deskripsi otomatis masih bersifat heuristik. Untuk laporan skripsi, tambahkan penilaian manual 1-5 pada sampel output, terutama untuk aspek kelengkapan, relevansi, dan kehati-hatian bahasa.

## Interpretasi

Jika `gemma_depth_prompted` meningkat pada distance category, obstacle warning, atau description quality dibanding `gemma_depth`, hasil tersebut dapat dibahas sebagai bukti bahwa depth lebih bermanfaat ketika menjadi konteks prompt generatif, bukan hanya ditempel pada tahap post-processing. Perbandingan dengan `gemma_only` harus dibaca sebagai perbedaan ketersediaan metadata depth eksplisit, bukan sebagai bukti Gemma tidak powerful.

Deskripsi akhir mode depth-aware harus memuat potensi halangan visual jika metadata depth menandainya. Bahasa yang dipakai tetap guarded, misalnya "area tengah-kiri berpotensi menjadi halangan visual", bukan klaim pasti seperti "jalan terhalang" atau "area aman".

Label area seperti `tengah-kiri` dan `bawah-tengah` dibaca dari grid 3x3 aplikasi. Depth model menghasilkan peta kedalaman kontinu; grid 3x3 adalah post-processing untuk membuat region lebih mudah dianalisis dan dibandingkan dengan anotasi.

Jika mode depth-aware tidak meningkatkan object accuracy, itu wajar karena depth module tidak bertugas mengenali objek. Kontribusi utama depth seharusnya terlihat pada kategori kedalaman relatif, status area depan, area relatif lapang, dan kualitas deskripsi spasial.

## Batasan

- Depth map adalah estimasi monocular depth, bukan sensor jarak.
- Threshold kategori perlu dikalibrasi terhadap dataset lokal.
- Evaluasi otomatis berbasis string matching tidak menggantikan penilaian manual.
- Prototype tidak diklaim sebagai alat navigasi aman.
