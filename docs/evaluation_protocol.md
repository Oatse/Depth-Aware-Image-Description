# Protokol Pengujian Bridge-Gap

Protokol ini memisahkan evaluasi deskripsi Gemma dari evaluasi HC-SR04. Pemisahan diperlukan karena cone sensor tidak mempunyai pengikatan spasial ke objek atau piksel dalam citra.

## 1. Pertanyaan evaluasi

1. Apakah prototipe menghasilkan deskripsi indoor berbahasa Indonesia yang sesuai dan jelas?
2. Berapa error pembacaan setiap HC-SR04 terhadap jarak fisik eksternal pada target planar terkendali?
3. Apakah pipeline mempertahankan provenance serta menerapkan status evidence dan gate pasangan secara benar?

Tidak ada pertanyaan evaluasi tentang akurasi metrik objek yang disebut Gemma.

## 2. Eksperimen sensor

### 2.1 Setup

- pasang dua HC-SR04 pada dudukan tetap dan sejajar;
- gunakan pembagi tegangan atau level shifter pada pin ECHO ke ESP32;
- picu sensor bergantian untuk mengurangi interferensi;
- gunakan target planar dengan ukuran, material, dan orientasi yang dicatat;
- ukur jarak referensi menggunakan meteran/alat ukur eksternal dari bidang referensi kamera ke bidang target;
- simpan nilai tersebut sebagai `ground_truth_cm`;
- tandai bidang referensi kamera dan muka akustik sensor pada dudukan;
- catat offset tetap `camera_sensor_offset_cm = 3.0`, yaitu jarak antara bidang referensi kamera dan muka sensor akibat ketebalan kerangka prototipe serta dudukan/kerangka sensor;
- jaga sudut target, tinggi, pencahayaan, dan posisi perangkat selama satu seri.
- gunakan alat ukur untuk menetapkan jarak, lalu keluarkan alat ukur dari bidang pandang sebelum capture tanpa mengubah zoom atau framing.

`ground_truth_cm` dan bacaan mentah sensor mempunyai titik nol berbeda. Selaraskan keduanya dengan:

```text
sensor_face_ground_truth_cm = ground_truth_cm - 3.0
camera_reference_from_raw_cm = sensor_raw_cm + 3.0
```

Contoh: target pada 50 cm dari bidang referensi kamera berada 47 cm dari muka sensor, sehingga pembacaan mentah ideal adalah sekitar 47 cm. Offset 3 cm merupakan transformasi geometri, bukan error intrinsik sensor. Pembacaan sensor lain tidak boleh dipakai sebagai ground truth.

Profil kalibrasi aktif dibentuk langsung terhadap `ground_truth_cm` beracuan kamera. Dengan demikian, nilai terkoreksi sudah berada pada acuan kamera dan **tidak boleh** ditambah 3 cm lagi. Jika pada masa depan profil dibentuk terhadap titik nol muka sensor, metadata profil wajib menyatakannya dan konversi ke acuan kamera dilakukan tepat satu kali.

### 2.2 Titik dan ulangan

Tetapkan titik jarak sebelum pengambilan data. Protokol aktif menggunakan:

- kalibrasi pada 20, 60, 100, 150, dan 200 cm;
- 30 pembacaan berpasangan pada setiap jarak kalibrasi (150 pasangan);
- verifikasi pada 40, 80, 125, dan 175 cm sebagai titik baru dalam rentang evaluasi penelitian sampai 200 cm;
- 30 pembacaan berpasangan pada setiap jarak verifikasi (120 pasangan).

Data kalibrasi membentuk koreksi linear terpisah untuk Sensor 1 dan Sensor 2. Data verifikasi disimpan terpisah, memakai versi profil yang sudah dibekukan, dan tidak boleh mengubah koefisien koreksi.

Titik kalibrasi 150 dan 200 cm tetap menjadi bagian pembentukan profil, sedangkan bukti generalisasi pada rentang atas diperoleh dari titik verifikasi baru 125 dan 175 cm. Klaim kinerja sampai 200 cm hanya dibuat jika keempat titik verifikasi lengkap dan memenuhi kriteria evaluasi.

Jangan melaporkan residual pada data kalibrasi saja sebagai bukti generalisasi.

### 2.3 Data yang dicatat

- `capture_id`;
- `target_id`, material, ukuran, dan sudut;
- `ground_truth_cm` beracuan pada kamera;
- `camera_sensor_offset_cm` dan `sensor_face_ground_truth_cm`;
- `sensor_1_cm` dan `sensor_2_cm`;
- nilai terkoreksi Sensor 1 dan Sensor 2 serta versi profil kalibrasi;
- status tiap sampel;
- received time, age, dan match time;
- `pair_disagreement_cm`;
- status evidence dan reason code;
- `frontal_reference_cm` hanya bila paired;
- suhu ruangan bila diukur;
- error/kegagalan teknis.

### 2.4 Metrik

Untuk tiap sensor `s` dan observasi `i`, bedakan error mentah yang sudah disejajarkan titik nolnya dari error nilai terkoreksi:

```text
sensor_face_ground_truth_i = ground_truth_i - camera_sensor_offset_cm
raw_error_i,s = sensor_i,s - sensor_face_ground_truth_i
corrected_error_i,s = sensor_corrected_i,s - ground_truth_i
raw_MAE_s = mean(abs(raw_error_i,s))
raw_Bias_s = mean(raw_error_i,s)
raw_RMSE_s = sqrt(mean(raw_error_i,s^2))
corrected_MAE_s = mean(abs(corrected_error_i,s))
corrected_Bias_s = mean(corrected_error_i,s)
corrected_RMSE_s = sqrt(mean(corrected_error_i,s^2))
```

Hitung dan beri label metrik mentah menggunakan `raw_error_i,s`, lalu metrik terkoreksi menggunakan `corrected_error_i,s`. Perbandingan langsung `sensor_i,s - ground_truth_i` mencampurkan error sensor dengan offset geometri 3 cm dan hanya boleh dilaporkan sebagai selisih terhadap acuan kamera, bukan sebagai error intrinsik HC-SR04.

Laporkan pula median absolute error, simpangan baku bila jumlah sampel memadai, valid-read rate, jumlah missing, serta hasil per titik jarak. Untuk pasangan, laporkan distribusi `pair_disagreement_cm` dan proporsi setiap status evidence.

Metrik `frontal_reference_cm` boleh dilaporkan sebagai ringkasan pipeline paired, tetapi tidak menggantikan hasil individual dua sensor.

### 2.5 Interpretasi

- error mengukur perbedaan sensor terhadap target planar pada setup tersebut;
- hasil tidak otomatis berlaku pada material, sudut, atau ukuran target lain;
- rata-rata pasangan tidak dikaitkan dengan objek pada citra;
- threshold disagreement adalah gate kualitas aplikasi, bukan hukum fisik universal;
- koreksi hanya dipakai jika residual validasi menunjukkan perbaikan dan batas penggunaannya dicatat.

## 3. Eksperimen deskripsi Gemma

### 3.1 Unit uji

Satu unit uji memuat citra sumber, prompt, respons mentah, deskripsi yang ditampilkan, latency, dan error. Dataset, kriteria inklusi/eksklusi, serta versi model dikunci sebelum penilaian utama.

### 3.2 Rubrik

| Aspek | Pertanyaan penilaian |
|---|---|
| Kesesuaian objek | Apakah objek yang disebut terlihat pada citra? |
| Posisi relatif | Apakah hubungan kiri/kanan/depan/belakang yang disebut didukung citra? |
| Kejelasan | Apakah kalimat mudah dipahami? |
| Naturalness | Apakah Bahasa Indonesia terdengar wajar? |
| Kelengkapan scene | Apakah unsur penting scene dijelaskan? |
| Klaim tidak didukung | Apakah deskripsi menambahkan fakta yang tidak tampak? |

Definisi setiap skala ditulis sebelum scoring. Jika memakai lebih dari satu penilai, laporkan prosedur penyelesaian perbedaan dan ukuran agreement yang sesuai. Jika tidak ada penilai manusia independen, nyatakan keterbatasan tersebut.

### 3.3 Larangan pencampuran label

- `ground_truth_cm` sensor tidak menjadi label metrik objek Gemma;
- angka sensor tidak digunakan untuk menilai kesesuaian nama objek;
- skor deskripsi tidak digabung dengan MAE sensor menjadi satu skor akurasi;
- teks kontribusi sensor dinilai sebagai kepatuhan format/provenance, bukan pemahaman visual Gemma.

## 4. Pengujian integrasi

Skenario minimum:

1. paired valid dan konsisten menghasilkan rata-rata serta kalimat referensi frontal;
2. partial menyimpan satu nilai tanpa rata-rata pasangan;
3. pair conflict menyimpan dua nilai dan menahan rata-rata;
4. stale menahan kontribusi angka;
5. kamera depan menghasilkan direction mismatch;
6. sensor unavailable tidak menggagalkan deskripsi visual;
7. Gemma gagal menghasilkan error eksplisit;
8. capture ID, timestamp, status, dan reason code tersimpan pada log.

Untuk base case paired, verifikasi:

```text
camera_sensor_offset_cm == 3.0
sensor_face_ground_truth_cm == ground_truth_cm - camera_sensor_offset_cm
sensor_1_corrected_cm = intercept_1 + slope_1 * sensor_1_cm
sensor_2_corrected_cm = intercept_2 + slope_2 * sensor_2_cm
frontal_reference_cm == round((sensor_1_corrected_cm + sensor_2_corrected_cm) / 2, presisi_aplikasi)
pair_disagreement_cm == abs(sensor_1_cm - sensor_2_cm)
```

Jangan menerapkan `frontal_reference_cm + 3.0` karena profil aktif sudah menghasilkan nilai beracuan kamera.

Keberhasilan koreksi dinilai pada data verifikasi: MAE koreksi harus lebih kecil daripada MAE mentah dan residual maksimum koreksi tidak melewati gate 10 cm. Nilai training pada data kalibrasi tidak boleh dilaporkan sebagai hasil verifikasi.

## 5. Format pencatatan

Gunakan `sensor_evaluation_template.csv` untuk eksperimen fisik. Untuk evaluasi deskripsi, kolom minimum:

```csv
capture_id,image_name,prompt_version,model_id,raw_response,description,object_consistency,spatial_consistency,clarity,naturalness,scene_completeness,unsupported_claims,total_latency_ms,error
```

Nilai mentah tidak boleh diubah untuk memperbaiki tampilan hasil. Baris gagal tetap disimpan.

## 6. Analisis Bab IV

Urutan yang disarankan:

1. hasil implementasi dan black-box alur utama;
2. hasil deskripsi Gemma beserta contoh keberhasilan/kegagalan;
3. hasil sensor 1 dan sensor 2 terhadap ground truth;
4. hasil klasifikasi evidence dan sinkronisasi;
5. keterbatasan cone sensor, setup, dataset, penilai, dan perangkat.

Setiap tabel dijelaskan dengan jumlah sampel, missing data, satuan, dan batas interpretasi.

## 7. Kriteria kelengkapan

Pengujian siap dilaporkan ketika:

1. protokol, titik jarak, target, dan alat ukur dicatat;
2. setiap baris sensor mempunyai `ground_truth_cm` eksternal atau alasan missing;
3. nilai kedua sensor tidak diganti oleh rata-rata saja;
4. seluruh status evidence diuji;
5. dataset serta rubrik deskripsi tersedia;
6. raw response, error, dan kegagalan dipertahankan;
7. hasil sensor dan hasil deskripsi disajikan terpisah;
8. kesimpulan tidak melewati data yang tersedia.
