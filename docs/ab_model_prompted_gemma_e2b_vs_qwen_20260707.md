# A/B Test Prompt Fusion - Gemma e2b vs Qwen - 2026-07-07

## Tujuan

Eksperimen ini membandingkan `google/gemma-4-e2b` dan `qwen3.5-4b` pada mode Depth-to-Spatial Prompting (`gemma_depth_prompted`).

Pengujian dilakukan secara serial satu gambar per job menggunakan:

`--resume --limit-jobs 1`

Tujuannya adalah menghindari batch inference besar yang dapat menyebabkan timeout atau beban berlebih di LM Studio.

## Model yang Diuji

| Model | Max Tokens | Catatan |
|---|---:|---|
| `google/gemma-4-e2b` | 1200 | Kandidat Gemma lebih ringan dari e4b Q6_K. |
| `qwen3.5-4b` | 4096 | Qwen membutuhkan token lebih besar karena uji 1200 sebelumnya membuat JSON terpotong. |

## Subset Uji

Subset sama dengan A/B test sebelumnya agar hasil dapat dibandingkan:

| Image | Distance GT | Obstacle GT | Position GT |
|---|---|---|---|
| `1 (5).jpg` | dekat | yes | tengah |
| `1 (31).jpg` | dekat | yes | kanan |
| `1 (8390).jpg` | dekat | yes | kiri |
| `1 (40).jpg` | dekat | yes | tengah |
| `1 (34).jpg` | sedang | no | tengah |
| `1 (6083).jpg` | sedang | no | kanan |
| `1 (6082).jpg` | sedang | no | kanan |
| `1 (6845).jpg` | sedang | no | tengah |
| `1 (7248).jpg` | jauh | no | tengah |
| `1 (7254).jpg` | jauh | no | tengah |

## Hasil Utama

| Model | Success Unique | Error Row | Object | Position | Distance | Obstacle | Quality | Avg Latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Gemma e2b | 10/10 | 1 transient | 10.00% | 100.00% | 40.00% | 70.00% | 3.20/5 | 58,794.9 ms |
| Qwen | 10/10 | 0 | 0.00% | 100.00% | 40.00% | 70.00% | 3.10/5 | 89,394.3 ms |

## Runtime

### Gemma e2b

Gemma e2b sempat gagal sekali pada `1 (31).jpg`, tetapi retry serial berikutnya berhasil. Karena `--resume` hanya melewati job sukses, job yang gagal dapat dicoba ulang tanpa mengulang gambar yang sudah berhasil.

Latency sukses:

| Image | Latency |
|---|---:|
| `1 (31).jpg` | 67,277 ms |
| `1 (34).jpg` | 65,096 ms |
| `1 (40).jpg` | 62,263 ms |
| `1 (5).jpg` | 48,201 ms |
| `1 (6082).jpg` | 58,727 ms |
| `1 (6083).jpg` | 60,954 ms |
| `1 (6845).jpg` | 51,408 ms |
| `1 (7248).jpg` | 52,951 ms |
| `1 (7254).jpg` | 61,097 ms |
| `1 (8390).jpg` | 59,975 ms |

### Qwen

Qwen menyelesaikan semua gambar tanpa error runtime, tetapi lebih lambat dari Gemma e2b pada rata-rata subset ini.

Latency sukses:

| Image | Latency |
|---|---:|
| `1 (31).jpg` | 112,338 ms |
| `1 (34).jpg` | 66,941 ms |
| `1 (40).jpg` | 78,090 ms |
| `1 (5).jpg` | 62,963 ms |
| `1 (6082).jpg` | 117,087 ms |
| `1 (6083).jpg` | 105,928 ms |
| `1 (6845).jpg` | 87,894 ms |
| `1 (7248).jpg` | 115,564 ms |
| `1 (7254).jpg` | 85,416 ms |
| `1 (8390).jpg` | 61,722 ms |

## Temuan Kritis

1. Gemma e2b lebih cepat daripada Qwen pada subset ini.
2. Qwen lebih bersih dari sisi runtime karena tidak memiliki error row, tetapi kualitas semantik objek tetap lemah.
3. Kedua model sama-sama lemah pada object accuracy, tetapi Gemma e2b masih mendapat 10.00%, sedangkan Qwen 0.00%.
4. Distance accuracy sama-sama 40.00%, sehingga masalah distance lebih mungkin berasal dari depth pipeline/definisi label, bukan hanya VLM.
5. Obstacle accuracy sama-sama 70.00%.

## Keputusan Sementara

Gemma e2b lebih layak menjadi kandidat model utama dibanding Qwen untuk eksperimen ini.

Alasannya:

- lebih cepat;
- kualitas deskripsi sedikit lebih tinggi;
- object accuracy tidak nol;
- tetap dapat menyelesaikan 10 gambar setelah retry serial;
- masih berada dalam keluarga Gemma sehingga transisi dari baseline lama lebih mudah dijelaskan.

Namun, Gemma e2b belum sempurna. Ada satu error transient dan object accuracy masih rendah, sehingga perlu uji lanjutan pada dataset final yang lebih besar sebelum keputusan final skripsi.

## Rekomendasi

1. Gunakan `google/gemma-4-e2b` sebagai kandidat utama berikutnya.
2. Jangan gunakan `qwen3.5-4b` sebagai model utama kecuali sudah dipastikan varian tersebut benar-benar vision-capable dan hasil object recognition membaik.
3. Jika tersedia, uji juga `google/gemma-4-e4b Q4_K_M` karena itu membandingkan kapasitas model yang sama dengan quantization lebih ringan.
4. Untuk evaluasi final, jalankan semua mode pada dataset final dengan model yang dipilih, bukan mencampur hasil dari model berbeda.
