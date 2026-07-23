# Pembekuan dan Evaluasi Dataset v2 Bersih

Tanggal eksekusi: 23 Juli 2026
Dataset: `hcsr04-indoor-distance-v2-clean`
Batch: `0c9d8d8e-a646-4302-9e1c-696423ebf689`

## 1. Status akhir

Dataset v2 bersih telah dibekukan dan dianalisis tanpa capture ulang.

- 18 capture: 6 jarak (30, 50, 75, 100, 150, dan 200 cm) × 3 pengulangan;
- 18 `capture_id` unik;
- 18 path gambar unik dan 18 checksum SHA-256 gambar unik;
- seluruh checksum gambar dan metadata cocok dengan sumber;
- seluruh evidence berstatus `paired`;
- status Sensor 1 dan Sensor 2 adalah `ok` pada seluruh capture;
- 18 job Gemma selesai, 0 gagal;
- urutan job mengikuti urutan manifest;
- nilai sensor pada setiap output cocok dengan snapshot capture terkait.

Manifest final berada di `results/captures/dataset_manifest_v2.json`. Hasil validasi independen berada di `results/captures/dataset_manifest_v2_validation.json`.

## 2. Kontrak eksekusi analisis

Setiap capture disubmit sebagai satu job dan runner menunggu status terminal sebelum mengirim capture berikutnya. Route stored-capture memuat gambar serta `sensor_evidence` dari record capture; sensor live tidak dibaca ulang. Saat eksekusi, readiness sensor live berstatus `unavailable`, tetapi seluruh output tetap menggunakan snapshot `paired` yang telah disimpan.

Rekap pasca-analisis memeriksa dua kondisi provenance untuk setiap capture:

1. `capture_id` pada snapshot sensor di run sama dengan `capture_id` manifest;
2. nilai mentah Sensor 1 dan Sensor 2 pada kontribusi output sama dengan nilai snapshot manifest.

Rekap 18 capture berhasil tanpa mismatch. Isolasi kegagalan juga diuji pada unit test: kegagalan submit satu capture dicatat sebagai `failed`, kemudian runner tetap memproses capture berikutnya.

## 3. Evaluasi deskripsi Gemma

Evaluasi ini adalah penilaian visual oleh satu evaluator teknis, bukan UAT. Skor positif memakai skala 1–4: 4 tepat dan lengkap; 3 didukung tetapi generik atau memiliki kekurangan kecil; 2 sebagian didukung dengan kesalahan penting; 1 tidak didukung atau tidak memadai. `unsupported_claims` dihitung sebagai jumlah klaim yang tidak dapat didukung citra.

### 3.1 Ringkasan keseluruhan

| Aspek | Hasil |
|---|---:|
| Identitas utama tepat sebagai koper | 9/18 (50,00%) |
| Konsistensi objek | 3,4444/4 |
| Konsistensi posisi | 3,4444/4 |
| Kejelasan | 3,9444/4 |
| Naturalness | 3,9444/4 |
| Kelengkapan scene | 3,5556/4 |
| Unsupported claims | 0 pada 18 capture |

### 3.2 Hasil per jarak

| Jarak kamera | Identitas koper tepat | Objek | Posisi | Kejelasan | Kelengkapan | Unsupported claims |
|---:|---:|---:|---:|---:|---:|---:|
| 30 cm | 0/3 | 3,0000 | 3,6667 | 4,0000 | 4,0000 | 0 |
| 50 cm | 0/3 | 3,0000 | 3,6667 | 4,0000 | 3,0000 | 0 |
| 75 cm | 0/3 | 2,6667 | 3,6667 | 4,0000 | 3,0000 | 0 |
| 100 cm | 3/3 | 4,0000 | 3,6667 | 4,0000 | 3,6667 | 0 |
| 150 cm | 3/3 | 4,0000 | 3,0000 | 3,6667 | 4,0000 | 0 |
| 200 cm | 3/3 | 4,0000 | 3,0000 | 4,0000 | 3,6667 | 0 |

### 3.3 Temuan Gemma

- Pada 30 cm, citra hanya menampilkan permukaan koper secara sangat dekat. Gemma konsisten menjelaskan tekstur gelap dan benda terang di bagian atas, tetapi tidak mengidentifikasi koper.
- Pada 50 cm, model konsisten menyebut objek besar/persegi panjang gelap dan dinding, tetapi identitas koper belum muncul.
- Pada 75 cm, model masih memakai label generik; satu capture menyebut objek sebagai “wadah atau kotak”, sehingga skor objek paling rendah berada pada jarak ini.
- Pada 100, 150, dan 200 cm, seluruh deskripsi mengenali objek sebagai koper dan tidak mengubah identitas antarulangan.
- Posisi yang disebut tidak bertentangan dengan citra. Kekurangan utama pada jarak 150–200 cm adalah beberapa deskripsi tidak menyebut posisi tengah secara eksplisit.
- Tidak ditemukan angka sensor di dalam deskripsi visual Gemma dan tidak ditemukan pengikatan angka sensor ke objek bernama.
- Satu keluaran 150 cm mempunyai repetisi frasa “lantai ruangan dalam ruangan”; ini menurunkan kejelasan dan naturalness, bukan unsupported claim.

Skor rinci dan catatan per capture berada di `results/captures/dataset_visual_scores_v2.csv`; rekapnya berada di `results/captures/dataset_visual_summary_v2.json`.

## 4. Evaluasi HC-SR04

Hasil sensor dilaporkan terpisah dari skor Gemma. Error mentah dihitung terhadap `sensor_face_ground_truth_cm = ground_truth_cm - 3 cm`. Error terkoreksi dan error referensi frontal dihitung terhadap `ground_truth_cm` beracuan kamera. Nilai terkoreksi tidak ditambah offset 3 cm lagi.

### 4.1 Ringkasan keseluruhan

| Jalur | Bias (cm) | MAE (cm) | RMSE (cm) | Maks. absolut (cm) |
|---|---:|---:|---:|---:|
| Sensor 1 mentah vs muka sensor | -0,9183 | 0,9439 | 1,0028 | 1,60 |
| Sensor 2 mentah vs muka sensor | -0,6922 | 0,7733 | 0,8357 | 1,20 |
| Sensor 1 terkoreksi vs kamera | -0,3639 | 1,0561 | 1,2057 | 1,98 |
| Sensor 2 terkoreksi vs kamera | -0,3061 | 0,8806 | 0,9995 | 1,70 |
| Rata-rata frontal terkoreksi vs kamera | -0,3339 | 0,9672 | 1,0691 | 1,83 |

Valid-read rate adalah 100%, missing read 0, dan rata-rata disagreement antarsensor 0,3839 cm. Rata-rata total latency analisis adalah 40.995,5 ms per capture.

### 4.2 Referensi frontal per jarak

| Jarak kamera | Rata-rata referensi frontal (cm) | Bias (cm) | MAE (cm) | Maks. absolut (cm) |
|---:|---:|---:|---:|---:|
| 30 | 28,8667 | -1,1333 | 1,1333 | 1,38 |
| 50 | 48,8867 | -1,1133 | 1,1133 | 1,37 |
| 75 | 73,9633 | -1,0367 | 1,0367 | 1,13 |
| 100 | 99,3800 | -0,6200 | 0,6200 | 0,73 |
| 150 | 150,2833 | +0,2833 | 0,2833 | 0,48 |
| 200 | 201,6167 | +1,6167 | 1,6167 | 1,83 |

### 4.3 Interpretasi sensor

- Pada dataset ini, pembacaan mentah yang sudah disejajarkan ke muka sensor mempunyai MAE lebih kecil daripada nilai terkoreksi untuk kedua sensor. Selisih MAE adalah +0,1122 cm pada Sensor 1 dan +0,1073 cm pada Sensor 2 setelah koreksi.
- Koreksi mengurangi bias rata-rata, tetapi meningkatkan MAE dan RMSE pada 18 capture ini. Jadi hasil ini tidak mendukung klaim bahwa koreksi selalu meningkatkan setiap metrik pada setiap dataset.
- Referensi frontal terbaik pada titik 150 cm dan error terbesar terjadi pada titik 200 cm.
- Dataset v2 tidak boleh dipakai untuk memfit ulang profil kalibrasi lalu dinilai kembali pada data yang sama. Profil tetap dibekukan; keputusan koreksi utama harus mengacu pada dataset verifikasi terpisah 40, 80, 125, dan 175 cm.
- Angka sensor hanya merupakan referensi permukaan frontal pada cone sensor, bukan jarak ke objek yang dinamai Gemma.

## 5. Batas klaim

Hasil ini mendukung laporan teknis tentang deskripsi visual pada 18 citra terkendali, error dua HC-SR04 terhadap ground truth setup tersebut, provenance snapshot, dan isolasi job. Hasil ini tidak membuktikan generalisasi ke scene multiobjek, manfaat pengguna, peningkatan aksesibilitas, keselamatan navigasi, atau jarak ke objek yang disebut model.

## 6. Artefak final

- `results/captures/dataset_manifest_v2.json` — manifest final dan checksum;
- `results/captures/dataset_manifest_v2_validation.json` — validasi manifest;
- `results/captures/dataset_analysis_rows_v2.csv` — hasil per capture dan error sensor;
- `results/captures/dataset_analysis_summary_v2.json` — rekap numerik HC-SR04 dan latency;
- `results/captures/dataset_visual_scores_v2.csv` — skor serta catatan visual per capture;
- `results/captures/dataset_visual_summary_v2.json` — rekap evaluasi Gemma;
- `results/analysis_runs.jsonl` — raw run dan output model yang dipertahankan.
