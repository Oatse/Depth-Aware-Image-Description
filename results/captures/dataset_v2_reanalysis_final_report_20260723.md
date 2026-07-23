# Laporan analisis ulang dataset v2

Tanggal: 23 Juli 2026
Dataset: `hcsr04-indoor-distance-v2-clean-latest-50cm-20260723`
Model: `google/gemma-4-e2b`
Kalibrasi: `frontal-distance-v2-be9838c5e410`

## Tujuan analisis

Analisis ini menguji tiga hal yang berbeda:

1. kemampuan prototipe menghasilkan deskripsi visual-spasial indoor berbahasa Indonesia;
2. perbedaan keluaran dan latency antara `gemma_only` dan `sensor_assisted`;
3. error dua HC-SR04 dan referensi frontal terkoreksi terhadap acuan fisik yang benar.

Perbandingan mode bertujuan mengamati pengaruh konteks sensor terverifikasi, bukan
membuktikan bahwa `sensor_assisted` harus lebih benar atau lebih baik. Skor kualitas
dipertahankan sebagai pengaman non-degradasi.

Analisis ini tidak menguji keselamatan navigasi, manfaat bagi pengguna tunanetra,
jarak ke objek yang dinamai Gemma, atau kemampuan generalisasi ke scene multiobjek.

## Pembersihan dan pembekuan hasil

Artefak evaluasi sebelum reanalisis, eksperimen depth historis, log runtime
campuran, dan 18 record nonfinal telah dikeluarkan dari workspace aktif. Paket final
mempertahankan 18 citra sumber, 18 record capture, 36 run terpilih, hasil evaluasi
blind, dan manifest checksum.

Run final disalin dari log runtime ke
`dataset_selected_analysis_runs_v2_fresh.jsonl`. Manifest evaluasi mengunci checksum
seluruh snapshot tersebut sehingga validasi tidak bergantung pada log runtime yang
dapat terus berubah.

## Integritas input dan inferensi

- 18 capture: enam jarak × tiga sampel;
- 18 capture ID, path gambar, dan checksum gambar unik;
- seluruh evidence sensor `paired`;
- Sensor 1 dan Sensor 2 berstatus `ok` pada 18/18 capture;
- 18/18 run `gemma_only` selesai tanpa gagal;
- 18/18 run `sensor_assisted` selesai tanpa gagal;
- analisis dilakukan serial, satu capture satu job;
- run menggunakan gambar dan snapshot sensor tersimpan, bukan pembacaan sensor live.

Checksum input sempat gagal karena field `mode` yang berubah saat reanalisis ikut
dihitung sebagai input immutable. Kontrak manifest diperbaiki agar field analisis
mutable tidak mengubah identitas input, lalu manifest dibekukan dan divalidasi ulang.

Audit run juga menemukan `display.system_note` pada keluaran baseline lama salah
menyatakan bahwa Gemma menerima konteks sensor. Provenance prompt menunjukkan
baseline benar-benar memakai prompt visual default dan `sensor_contribution` bernilai
null; note tersebut dibentuk setelah inferensi dan tidak tampil pada template blind.
Implementasi note telah diperbaiki tanpa mengulang inferensi karena prompt, output
Gemma, dan skor evaluasi tidak terpengaruh.

## Mengapa `dataset_v2_clean` dan `visual_evaluation_blind_v2` terpisah

`dataset_v2_clean` adalah dataset sumber: 18 citra asli dengan nama capture dan
provenance lengkap. `visual_evaluation_blind_v2` bukan dataset baru. Folder itu
berisi salinan citra dengan nama netral `VE-*` agar evaluator tidak melihat
capture ID, jarak, repeat, mode, model, atau run ID.

Folder blind memuat 36 file karena setiap citra sumber memiliki dua keluaran yang
dinilai, satu per mode. Secara statistik tetap ada 18 citra independen dan 18
pasangan repeated-measures, bukan 36 citra independen. Pemisahan folder diperlukan
untuk blinding; kesamaan kontennya memang disengaja.

## Kontrol bias

- hasil lama dikeluarkan dan run final dipilih eksplisit;
- identitas target tidak digunakan sebagai aturan keberhasilan otomatis;
- urutan 36 item dibuat pseudorandom deterministik;
- template evaluator menyembunyikan mode, jarak, capture ID, run ID, model, dan prompt;
- nama citra diganti menjadi `VE-*`;
- skor 36 item dikunci dengan SHA-256 sebelum key mode dibuka;
- ringkasan memakai 18 pasangan capture, bukan memperlakukan 36 item sebagai sampel independen;
- interval bootstrap memakai unit resampling pasangan capture.

Kontrol tersebut mengurangi bias, tetapi tidak membuat evaluasi bebas bias secara
absolut. Penilaian hanya dilakukan oleh satu evaluator teknis; inter-rater
agreement belum tersedia.

## Hasil teknis

| Mode | Selesai | Gagal | Rata-rata latency |
|---|---:|---:|---:|
| `gemma_only` | 18/18 | 0 | 34.475,06 ms |
| `sensor_assisted` | 18/18 | 0 | 43.581,17 ms |

Sensor conditioning menambah rata-rata 9.106,11 ms atau 26,41% terhadap baseline.
Teks `main_object` berubah pada 12/18 pasangan dan teks deskripsi berubah pada
18/18 pasangan. Perubahan teks tidak membuktikan peningkatan kualitas.

## Hasil evaluasi visual blind

Skala kualitas menggunakan 1–5. Delta dihitung sebagai
`sensor_assisted - gemma_only`.

| Metrik | Gemma only | Sensor assisted | Delta | Bootstrap 95% CI |
|---|---:|---:|---:|---:|
| Konsistensi objek | 4,7778 | 4,6667 | -0,1111 | [-0,3333; 0,0000] |
| Konsistensi spasial | 4,4444 | 4,3333 | -0,1111 | [-0,5000; 0,2778] |
| Kejelasan | 4,6667 | 4,6667 | 0,0000 | [-0,1667; 0,1667] |
| Naturalness | 4,6667 | 4,6111 | -0,0556 | [-0,2222; 0,1111] |
| Kelengkapan scene | 3,7778 | 3,6667 | -0,1111 | [-0,2778; 0,0000] |
| Rata-rata keseluruhan | 4,4667 | 4,3889 | -0,0778 | [-0,2222; 0,0556] |

Pada rata-rata keseluruhan per pasangan, `sensor_assisted` lebih tinggi pada 5
citra, seri pada 7 citra, dan `gemma_only` lebih tinggi pada 6 citra. Klaim tidak
didukung tercatat 0 pada kedua mode berdasarkan rubrik evaluator.

Verdik: dataset ini tidak memberikan bukti bahwa sensor conditioning meningkatkan
kualitas deskripsi. Estimasi keseluruhan sedikit lebih rendah dan interval
bootstrap melintasi nol. Hasil yang dapat dipertahankan adalah sensor context
mengubah keluaran dan menambah latency, bukan bahwa ia memperbaiki deskripsi.

## Hasil HC-SR04

Error sensor mentah dibandingkan dengan bidang muka sensor
`ground_truth_cm - 3,0`. Error referensi frontal terkoreksi dibandingkan langsung
dengan ground truth kamera; nilai terkoreksi tidak ditambah 3 cm lagi.

| Metrik | Bias | MAE | RMSE | Maks. absolut |
|---|---:|---:|---:|---:|
| Sensor 1 mentah | -0,8528 cm | 0,8783 cm | 0,9618 cm | 1,6000 cm |
| Sensor 2 mentah | -0,5533 cm | 0,6089 cm | 0,6931 cm | 1,1700 cm |
| Referensi frontal terkoreksi | -0,2289 cm | 0,8622 cm | 0,9827 cm | 1,8300 cm |

Rata-rata disagreement pasangan adalah 0,3550 cm dan maksimum 1,2400 cm.
Kalibrasi mengurangi magnitude bias referensi frontal, tetapi MAE hasil terkoreksi
masih lebih tinggi daripada MAE mentah Sensor 2. Temuan negatif ini harus
dipertahankan dalam penulisan.

## Batas kesimpulan

- hanya satu koper dan satu setup indoor terkendali;
- hanya 18 citra independen;
- hanya satu evaluator teknis dan tanpa inter-rater agreement;
- bukan UAT;
- inferensi tidak memakai seed;
- tidak ada dasar untuk klaim superioritas, keselamatan navigasi, manfaat pengguna,
  scene multiobjek, atau pengikatan jarak sensor ke objek yang disebut Gemma.

## Artefak utama

- `dataset_manifest_v2.json`;
- `dataset_manifest_v2_fresh_validation.json`;
- `dataset_selected_analysis_runs_v2_fresh.jsonl`;
- `fresh_run_selection_gemma_only_v2.json`;
- `fresh_run_selection_sensor_assisted_v2.json`;
- `dataset_analysis_rows_v2_fresh.csv`;
- `dataset_analysis_summary_v2_fresh.json`;
- `dataset_visual_evaluation_v2_fresh.csv`;
- `dataset_visual_evaluation_score_lock_v2_fresh.json`;
- `dataset_visual_summary_v2_fresh.json`;
- `dataset_visual_paired_comparison_v2_fresh.csv`;
- `evaluation_manifest_v2_fresh.json`;
- `evaluation_manifest_v2_fresh_validation.json`.
