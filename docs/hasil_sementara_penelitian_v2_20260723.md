# Dokumen Sementara Hasil Penelitian Dataset v2

> Status: **dokumen penampung hasil sementara**. Dokumen ini bukan Bab IV final dan belum mengikuti struktur penulisan skripsi. Isinya disimpan sebagai sumber faktual ketika penulisan dimulai kembali dari Bab I.

Tanggal pembekuan hasil: 23 Juli 2026
Dataset: `hcsr04-indoor-distance-v2-clean`
Batch: `0c9d8d8e-a646-4302-9e1c-696423ebf689`

## A. Ringkasan pekerjaan yang telah selesai

Dataset v2 bersih terdiri dari 18 capture pada enam jarak kamera, masing-masing dengan tiga pengulangan: 30, 50, 75, 100, 150, dan 200 cm. Tidak dilakukan capture ulang setelah dataset dinyatakan bersih.

Seluruh capture mempunyai:

- `capture_id`, gambar, dan metadata eksperimen;
- `ground_truth_cm` dari bidang referensi kamera;
- `sensor_face_ground_truth_cm = ground_truth_cm - 3 cm`;
- snapshot Sensor 1 dan Sensor 2 pada waktu capture;
- status evidence `paired` serta status kedua sensor `ok`;
- checksum SHA-256 gambar dan input metadata.

Manifest input telah diverifikasi dengan hasil:

| Pemeriksaan | Hasil |
|---|---:|
| Total capture | 18 |
| Capture ID unik | 18 |
| Path gambar unik | 18 |
| Checksum gambar unik | 18 |
| Checksum gambar cocok | 18/18 |
| Evidence `paired` | 18/18 |
| Sensor 1 `ok` | 18/18 |
| Sensor 2 `ok` | 18/18 |

## B. Hasil eksekusi analisis

Analisis dijalankan berurutan berdasarkan manifest. Satu capture menjadi satu job dan runner menunggu job tersebut selesai atau gagal sebelum mengirim capture berikutnya.

| Indikator | Hasil |
|---|---:|
| Job disubmit | 18 |
| Job selesai | 18 |
| Job gagal | 0 |
| Capture dengan satu attempt | 18 |
| Mismatch capture–run | 0 |
| Mismatch nilai snapshot sensor | 0 |

Sensor live tidak dibaca ulang pada tahap analisis. Setiap job memakai gambar dan `sensor_evidence` yang sudah tersimpan pada record capture. Nilai mentah Sensor 1 dan Sensor 2 pada output telah dibandingkan dengan manifest dan seluruhnya cocok.

Model menghasilkan deskripsi visual menggunakan citra RGB. Kontribusi sensor ditambahkan secara deterministik setelah deskripsi Gemma dan tetap dipisahkan sebagai referensi sensor frontal. Angka sensor tidak dimasukkan ke dalam deskripsi visual Gemma dan tidak dilekatkan pada objek yang disebut model.

Rata-rata waktu total analisis adalah **40.995,5 ms per capture** atau sekitar **41,0 detik**. Nilai ini adalah latency pada perangkat dan konfigurasi runtime yang digunakan, bukan klaim real-time universal.

## C. Hasil sementara deskripsi Gemma

Penilaian dilakukan secara visual oleh satu evaluator teknis dengan skala 1–4:

- 4: tepat, jelas, dan mencakup unsur utama yang terlihat;
- 3: didukung gambar tetapi generik atau mempunyai kekurangan kecil;
- 2: sebagian didukung tetapi ambigu atau mempunyai kesalahan penting;
- 1: tidak didukung atau tidak memadai.

Penilaian ini bukan UAT dan tidak melibatkan klaim manfaat pengguna.

### C.1 Ringkasan keseluruhan

| Aspek | Hasil |
|---|---:|
| Identitas utama tepat sebagai koper | 9/18 (50,00%) |
| Konsistensi objek | 3,4444/4 |
| Konsistensi posisi | 3,4444/4 |
| Kejelasan | 3,9444/4 |
| Naturalness | 3,9444/4 |
| Kelengkapan scene | 3,5556/4 |
| Unsupported claims | 0 pada 18 capture |

### C.2 Hasil per jarak

| Jarak kamera | Identitas koper tepat | Objek | Posisi | Kejelasan | Kelengkapan | Unsupported claims |
|---:|---:|---:|---:|---:|---:|---:|
| 30 cm | 0/3 | 3,0000 | 3,6667 | 4,0000 | 4,0000 | 0 |
| 50 cm | 0/3 | 3,0000 | 3,6667 | 4,0000 | 3,0000 | 0 |
| 75 cm | 0/3 | 2,6667 | 3,6667 | 4,0000 | 3,0000 | 0 |
| 100 cm | 3/3 | 4,0000 | 3,6667 | 4,0000 | 3,6667 | 0 |
| 150 cm | 3/3 | 4,0000 | 3,0000 | 3,6667 | 4,0000 | 0 |
| 200 cm | 3/3 | 4,0000 | 3,0000 | 4,0000 | 3,6667 | 0 |

### C.3 Temuan deskriptif

1. Pada 30 cm, gambar didominasi permukaan koper. Model konsisten menjelaskan permukaan gelap, pola lingkaran, dan benda terang di bagian atas, tetapi tidak mengenali keseluruhan objek sebagai koper.
2. Pada 50 cm, model menyebut objek besar atau persegi panjang gelap dengan dinding sebagai latar belakang. Identitas koper belum muncul.
3. Pada 75 cm, identitas masih generik. Satu keluaran menyebut objek sebagai “wadah atau kotak”, sehingga skor konsistensi objek pada jarak ini paling rendah.
4. Pada 100, 150, dan 200 cm, seluruh keluaran mengenali objek utama sebagai koper.
5. Tidak ditemukan klaim posisi kiri/kanan yang bertentangan dengan citra.
6. Satu keluaran 150 cm mempunyai repetisi frasa “lantai ruangan dalam ruangan”. Ini merupakan masalah kejelasan/naturalness, bukan hallucination faktual.
7. Tidak ditemukan tebakan angka jarak oleh Gemma dan tidak ditemukan pengikatan angka sensor ke koper.

## D. Hasil sementara HC-SR04

Hasil sensor dilaporkan terpisah dari hasil deskripsi Gemma.

- Error mentah dihitung terhadap `sensor_face_ground_truth_cm`.
- Error nilai terkoreksi dihitung terhadap `ground_truth_cm` kamera.
- Nilai terkoreksi tidak ditambah offset 3 cm lagi karena profil aktif sudah menghasilkan acuan kamera.

### D.1 Ringkasan error keseluruhan

| Jalur | Bias (cm) | MAE (cm) | RMSE (cm) | Maks. absolut (cm) |
|---|---:|---:|---:|---:|
| Sensor 1 mentah vs muka sensor | -0,9183 | 0,9439 | 1,0028 | 1,60 |
| Sensor 2 mentah vs muka sensor | -0,6922 | 0,7733 | 0,8357 | 1,20 |
| Sensor 1 terkoreksi vs kamera | -0,3639 | 1,0561 | 1,2057 | 1,98 |
| Sensor 2 terkoreksi vs kamera | -0,3061 | 0,8806 | 0,9995 | 1,70 |
| Referensi frontal terkoreksi vs kamera | -0,3339 | 0,9672 | 1,0691 | 1,83 |

Valid-read rate adalah 100%, missing read berjumlah 0, dan rata-rata disagreement Sensor 1–Sensor 2 adalah 0,3839 cm.

### D.2 Referensi frontal per jarak

| Jarak kamera | Rata-rata referensi frontal (cm) | Bias (cm) | MAE (cm) | Maks. absolut (cm) |
|---:|---:|---:|---:|---:|
| 30 | 28,8667 | -1,1333 | 1,1333 | 1,38 |
| 50 | 48,8867 | -1,1133 | 1,1133 | 1,37 |
| 75 | 73,9633 | -1,0367 | 1,0367 | 1,13 |
| 100 | 99,3800 | -0,6200 | 0,6200 | 0,73 |
| 150 | 150,2833 | +0,2833 | 0,2833 | 0,48 |
| 200 | 201,6167 | +1,6167 | 1,6167 | 1,83 |

### D.3 Temuan sensor

1. Error referensi frontal paling kecil ditemukan pada 150 cm dan paling besar pada 200 cm.
2. Koreksi menurunkan besar bias rata-rata kedua sensor.
3. Namun, pada 18 capture ini, koreksi menaikkan MAE Sensor 1 sebesar 0,1122 cm dan Sensor 2 sebesar 0,1073 cm dibanding pembacaan mentah yang sudah disejajarkan ke muka sensor.
4. Hasil ini tidak mendukung klaim bahwa koreksi selalu memperbaiki seluruh metrik pada setiap dataset.
5. Dataset v2 tidak boleh dipakai untuk memfit ulang profil kalibrasi kemudian dinilai kembali pada data yang sama.
6. Keputusan tentang keberhasilan profil kalibrasi harus tetap mengacu pada dataset verifikasi terpisah 40, 80, 125, dan 175 cm.

## E. Batas provenance hasil yang tersedia

Run menyimpan `analysis_run_id`, `capture_id`, gambar sumber, snapshot sensor, output terstruktur, deskripsi visual, deskripsi final, latency, versi kalibrasi, dan status mock. Namun terdapat tiga keterbatasan pencatatan:

1. raw response provider Gemma tidak disimpan dalam `analysis_runs.jsonl`;
2. model ID tidak disimpan di setiap run;
3. teks atau versi prompt tidak disimpan di setiap run.

Model `google/gemma-4-e2b` dan hash prompt yang akan dicantumkan dalam evaluation manifest berasal dari konfigurasi serta source code aktif. Informasi tersebut merupakan **derived provenance**, bukan bukti kriptografis bahwa payload historis setiap request identik dengan source saat ini. Tidak dilakukan inferensi ulang untuk menutupi kekurangan pencatatan ini.

## F. Batas klaim untuk penulisan nanti

Hasil saat ini dapat dipakai untuk membahas:

- implementasi pipeline capture dan analisis tertunda;
- deskripsi visual-spasial pada dataset indoor terkendali;
- konsistensi objek, posisi, kejelasan, kelengkapan, dan unsupported claim;
- error HC-SR04 terhadap ground truth pada setup tersebut;
- keberhasilan provenance snapshot serta isolasi job.

Hasil saat ini tidak membuktikan:

- jarak sensor adalah jarak ke objek yang dinamai Gemma;
- kemampuan pada scene multiobjek atau material/sudut lain;
- manfaat bagi pengguna tertentu;
- peningkatan aksesibilitas, kemandirian, atau keselamatan navigasi;
- performa real-time universal;
- keunggulan sistem tanpa baseline dan desain pembanding yang sesuai.

## G. Rute artefak sumber

- `results/captures/dataset_manifest_v2.json` — input dataset beku;
- `results/captures/dataset_manifest_v2_validation.json` — validasi input;
- `results/captures/dataset_analysis_rows_v2.csv` — hasil per capture;
- `results/captures/dataset_analysis_summary_v2.json` — rekap sensor dan latency;
- `results/captures/dataset_visual_scores_v2.csv` — skor visual per capture;
- `results/captures/dataset_visual_summary_v2.json` — rekap Gemma;
- `results/analysis_runs.jsonl` — run terpilih berdasarkan `analysis_run_id` record;
- `results/captures/evaluation_manifest_v2.json` — paket pembekuan output setelah dibuat;
- `docs/dataset_v2_final_evaluation_20260723.md` — laporan teknis rinci pendamping.

Ketika penulisan skripsi dimulai dari Bab I, dokumen ini dipakai sebagai gudang fakta hasil. Narasi Bab IV baru disusun setelah rumusan masalah, tujuan, batasan, landasan teori, dan metode pada Bab I–III sudah konsisten dengan bukti ini.
