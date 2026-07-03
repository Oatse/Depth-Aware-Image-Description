# Evaluation Protocol

Dokumen ini menjelaskan prosedur evaluasi prototype depth-aware image description untuk kebutuhan skripsi.

## Tujuan Evaluasi

Evaluasi bertujuan membandingkan dua mode utama:

1. `gemma_only`: deskripsi visual dari Gemma tanpa informasi kedalaman.
2. `gemma_depth`: deskripsi visual Gemma yang digabungkan dengan depth summary melalui rule-based fusion.

Pertanyaan yang diuji: apakah informasi depth membuat deskripsi lingkungan indoor lebih informatif untuk objek, posisi, kategori jarak, dan potensi hambatan.

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
5. Jalankan batch evaluation:

```bash
python scripts\run_batch_evaluation.py --images-dir dataset\images --annotations dataset\annotations.csv
```

6. Baca output:

- `results/predictions.csv`
- `results/evaluation.csv`
- `results/depth_maps/`

## Metrik

Metrik otomatis awal:

- object accuracy;
- position accuracy;
- distance category accuracy;
- obstacle warning accuracy;
- description quality heuristic 1-5;
- average latency.

Metrik kualitas deskripsi otomatis masih bersifat heuristik. Untuk laporan skripsi, tambahkan penilaian manual 1-5 pada sampel output, terutama untuk aspek kelengkapan, relevansi, dan kehati-hatian bahasa.

## Interpretasi

Jika `gemma_depth` meningkat pada distance category dan obstacle warning, tetapi latency lebih tinggi, hasil tersebut dapat dibahas sebagai trade-off antara kelengkapan informasi dan waktu inferensi.

Jika `gemma_depth` tidak meningkatkan object accuracy, itu wajar karena depth module tidak bertugas mengenali objek. Kontribusi utama depth seharusnya terlihat pada kategori jarak, status area depan, dan arah yang relatif lebih lapang.

## Batasan

- Depth map adalah estimasi monocular depth, bukan sensor jarak.
- Threshold kategori perlu dikalibrasi terhadap dataset lokal.
- Evaluasi otomatis berbasis string matching tidak menggantikan penilaian manual.
- Prototype tidak diklaim sebagai alat navigasi aman.
