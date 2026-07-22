# Project Initialization Bridge-Gap

## 1. Judul kerja

**Sistem Deskripsi Gambar Indoor Berbahasa Indonesia Menggunakan Gemma 4 E2B dengan Referensi Jarak Frontal dari Dua Sensor HC-SR04**

Judul final harus disetujui dosen pembimbing. Frasa “referensi jarak frontal” dipertahankan untuk mencegah klaim bahwa sensor mengukur objek yang disebut model.

## 2. Posisi penelitian

Penelitian ini berbentuk perancangan dan evaluasi prototipe teknis. Sistem menerima satu citra indoor, menghasilkan deskripsi Bahasa Indonesia melalui Gemma 4 E2B, dan menyertakan referensi sensor frontal yang dikumpulkan dekat dengan waktu capture. Jalur visual dan jalur sensor dievaluasi secara terpisah karena tidak tersedia pengikatan spasial yang membuktikan bahwa echo sensor berasal dari objek yang dinamai Gemma.

Kontribusi yang realistis:

1. implementasi lokal deskripsi citra indoor berbahasa Indonesia;
2. pencocokan waktu capture dengan dua sensor frontal serta status evidence yang dapat diaudit;
3. evaluasi teknis terpisah untuk kualitas deskripsi dan akurasi sensor pada setup terkendali.

Kontribusi tidak diposisikan sebagai metode fusion baru, sistem navigasi, atau pembuktian manfaat pengguna.

## 3. Rumusan masalah

1. Bagaimana merancang prototipe yang menghasilkan deskripsi gambar indoor berbahasa Indonesia menggunakan Gemma 4 E2B?
2. Bagaimana mengintegrasikan dua HC-SR04 sebagai referensi jarak frontal dengan mempertahankan nilai, waktu, identitas sensor, arah kamera, dan status evidence?
3. Bagaimana mengevaluasi kualitas deskripsi Gemma dan akurasi pembacaan HC-SR04 secara terpisah pada skenario pengujian yang terkendali?

## 4. Tujuan penelitian

1. Mengimplementasikan pipeline deskripsi satu citra indoor menggunakan Gemma 4 E2B.
2. Mengimplementasikan akuisisi dan klasifikasi evidence dari dua HC-SR04 yang sinkron dengan capture.
3. Mengukur kualitas deskripsi dengan rubrik yang ditetapkan serta error tiap sensor pada target planar setelah titik nol sensor diselaraskan dengan `ground_truth_cm` eksternal beracuan kamera.

Tujuan tidak mencakup estimasi metrik objek dari citra, navigasi, deteksi rintangan keselamatan, atau UAT pengguna tunanetra.

## 5. Ruang lingkup

### Termasuk

- satu citra RGB indoor per analisis;
- Bahasa Indonesia sebagai bahasa keluaran;
- `google/gemma-4-e2b` melalui LM Studio;
- dua HC-SR04 dan ESP32-WROOM-32;
- kamera belakang untuk capture yang memakai evidence sensor;
- pencocokan waktu capture-sensor;
- klasifikasi `paired`, `partial`, `pair_conflict`, `stale`, `direction_mismatch`, dan `unavailable`;
- pencatatan nilai sensor individual, age/timestamp, disagreement, status, dan alasan status;
- rata-rata aritmetika dua sensor hanya pada base case `paired`;
- evaluasi black-box, integrasi, performa, dan pengukuran fisik terkendali.

### Tidak termasuk

- jarak ke objek bernama atau piksel tertentu;
- peta ruang tiga dimensi;
- pelokalan objek berdasarkan cone sensor;
- perintah navigasi atau jaminan keselamatan;
- klaim manfaat pengguna akhir tanpa UAT;
- inference real-time sebagai klaim tanpa pengukuran latency yang relevan;
- novelty algoritmik dari penambahan teks sensor.

## 6. Dasar perhitungan sensor

Prinsip HC-SR04 adalah pengukuran waktu tempuh pulang-pergi:

```text
d = v * t / 2
```

Firmware menghasilkan `distance_cm`. Backend tidak boleh menciptakan koreksi baru tanpa prosedur kalibrasi dan bukti residual terhadap alat ukur eksternal.

Bidang referensi kamera berada 3 cm di belakang muka akustik HC-SR04 akibat gabungan ketebalan kerangka prototipe dan dudukan/kerangka sensor. Gunakan definisi berikut:

```text
camera_sensor_offset_cm = 3.0
sensor_face_ground_truth_cm = ground_truth_cm - camera_sensor_offset_cm
camera_reference_from_raw_cm = sensor_raw_cm + camera_sensor_offset_cm
```

`ground_truth_cm` diukur dari bidang referensi kamera. Karena itu, jarak aktual 50 cm dari kamera secara geometris setara dengan 47 cm dari muka sensor, dan bacaan mentah ideal HC-SR04 adalah sekitar 47 cm. Offset 3 cm adalah perbedaan titik nol fisik, bukan error intrinsik sensor; selisih tambahan tetap dianalisis sebagai error pengukuran.

Profil kalibrasi aktif dipasang terhadap `ground_truth_cm` beracuan kamera. Nilai `sensor_1_corrected_cm` dan `sensor_2_corrected_cm` sudah berada pada acuan kamera, sehingga offset 3 cm tidak boleh ditambahkan lagi setelah koreksi.

Untuk pasangan yang valid, segar, searah, dan konsisten:

```text
pair_disagreement_cm = abs(sensor_1_cm - sensor_2_cm)
sensor_1_corrected_cm = intercept_1 + slope_1 * sensor_1_cm
sensor_2_corrected_cm = intercept_2 + slope_2 * sensor_2_cm
frontal_reference_cm = (sensor_1_corrected_cm + sensor_2_corrected_cm) / 2
```

Rata-rata tersebut adalah ringkasan dua cone frontal. Nilai mentah dan terkoreksi tiap sensor tetap menjadi sumber utama audit. `partial` tidak dirata-ratakan; `stale`, `pair_conflict`, `direction_mismatch`, dan `unavailable` ditahan dari kontribusi angka pada deskripsi.

Rentang evaluasi sensor ditetapkan pada 20–200 cm sebagai sintesis konservatif dari beberapa eksperimen indoor, bukan mean aritmetika batas jarak paper. Zona 20–120 cm menjadi bagian dengan dukungan paling kuat, sedangkan 120–200 cm merupakan perluasan operasional yang memerlukan target cukup besar, frontal, dan verifikasi lokal. Verifikasi koreksi menggunakan 40, 80, 125, dan 175 cm dengan 30 pembacaan berpasangan per titik. Titik verifikasi disimpan terpisah dan tidak mengubah profil kalibrasi. Klaim kinerja sampai 200 cm hanya dibuat jika seluruh titik verifikasi lengkap dan memenuhi kriteria evaluasi.

## 7. Arsitektur logis

```text
Citra RGB -> validasi/preprocess -> Gemma -> deskripsi visual
Capture metadata -----------------------> sinkronisasi
HC-SR04 1 -> ESP32 -> sensor bridge ------^
HC-SR04 2 -> ESP32 -> sensor bridge ------^
                         |
                         -> klasifikasi evidence
                         -> kontribusi sensor deterministik
Deskripsi visual + kontribusi sensor -> API/UI/log
```

Gemma tidak bertanggung jawab menghitung atau menebak jarak. Backend mempertahankan pemisahan sumber agar angka sensor tidak berubah menjadi klaim visual.

## 8. Metode pengembangan

Metode pengembangan dapat ditulis sebagai prototyping iteratif:

1. analisis kebutuhan dan batas klaim;
2. perancangan pipeline visual dan sensor;
3. implementasi antarmuka dan API;
4. integrasi capture-sensor;
5. pengujian unit, integrasi, dan black-box;
6. pengukuran fisik serta evaluasi deskripsi;
7. revisi berdasarkan temuan.

Setiap iterasi harus mempertahankan raw log; kegagalan tidak boleh dibuang dari rekap.

## 9. Metode penelitian dan evaluasi

Evaluasi dibagi menjadi dua eksperimen.

### Eksperimen A — sensor

- target planar dengan ukuran dan material tetap;
- jarak diukur dari bidang referensi kamera menggunakan alat ukur eksternal dan disimpan sebagai `ground_truth_cm`, sedangkan acuan muka sensor diturunkan sebagai `sensor_face_ground_truth_cm = ground_truth_cm - 3.0`;
- posisi kamera/sensor, sudut target, dan kondisi ruangan dikendalikan;
- alat ukur dipakai untuk menetapkan posisi target lalu dikeluarkan dari bidang pandang sebelum capture, tanpa mengubah zoom atau framing antar-titik;
- tiap sensor dinilai sendiri menggunakan absolute error, MAE, bias, RMSE, dan valid-read rate;
- pasangan dinilai berdasarkan disagreement dan proporsi status evidence;
- kalibrasi, bila dilakukan, dibangun pada subset kalibrasi dan diuji pada subset berbeda.

### Eksperimen B — deskripsi

- dataset citra indoor dan kriteria inklusi ditetapkan sebelum penilaian;
- output Gemma dinilai terhadap anotasi/rubrik visual tanpa memakai angka HC-SR04 sebagai label objek;
- aspek minimum: kesesuaian objek, posisi relatif yang tampak, kejelasan Bahasa Indonesia, kelengkapan scene, dan klaim tidak didukung;
- penilai, skala, serta aturan agregasi skor dilaporkan.

Hasil dua eksperimen tidak digabung menjadi satu skor “akurasi sistem”.

## 10. Kontrak API

Alur kamera menggunakan penyimpanan tertunda:

- sebelum capture kamera, operator memasukkan `ground_truth_cm` beracuan kamera pada rentang 20–200 cm;
- `POST /captures` menyimpan citra, metadata capture, offset 3 cm, `sensor_face_ground_truth_cm`, `repeat_index` otomatis, dan sensor evidence ke folder lokal tanpa menjalankan Gemma;
- `GET /captures` dan `GET /captures/count` dipakai backend serta penghitung UI;
- `POST /captures/{capture_id}/analysis-jobs` membuat satu job untuk satu capture dan memakai snapshot sensor tersimpan;
- runner backend menunggu job selesai sebelum mengirim capture berikutnya.

`POST /analyze` tetap tersedia untuk analisis langsung satu file upload. Response sukses minimum memuat:

- deskripsi Gemma;
- deskripsi akhir;
- `sensor_evidence` dengan sampel individual dan provenance;
- `sensor_contribution` dengan status, alasan, dan `frontal_reference_cm` hanya bila paired;
- latency dan identitas run untuk audit.

`GET /sensor-status` menampilkan status bridge dan sampel terakhir. `GET /health` dan `GET /readiness` digunakan untuk pemeriksaan runtime.

## 11. Kontrak UI

Pada tab kamera, UI hanya menyediakan capture dan jumlah capture tersimpan. UI tidak menampilkan daftar dataset atau tombol analisis semua; analisis capture tersimpan dijalankan dari backend. Tab upload tetap menyediakan analisis langsung satu file. Prioritas tampilan hasil analisis:

1. deskripsi gambar;
2. status referensi sensor frontal;
3. nilai sensor 1 dan sensor 2;
4. rata-rata paired bila tersedia;
5. detail provenance dan error.

Tidak ada label yang mengaitkan angka sensor dengan objek bernama.

## 12. Struktur skripsi

### Bab I — Pendahuluan

Memuat latar belakang, rumusan masalah, ruang lingkup, tujuan, dan sistematika penulisan. Kebutuhan sensor dijelaskan sebagai referensi frontal tambahan, bukan pengganti persepsi visual.

### Bab II — Tinjauan Pustaka

Memuat image description, VLM, Gemma, sensor ultrasonik, prinsip ToF, sinkronisasi data multimodal, evaluasi caption, dan penelitian terdahulu yang relevan. Hanya sumber yang benar-benar dipakai dalam argumen yang masuk daftar pustaka final.

Untuk bagian HC-SR04, ikuti seleksi dan batas klaim pada `docs/pustaka/hcsr04_indoor_evidence_context.md`. Tuliskan secara eksplisit apakah setiap penelitian menguji satu objek, satu target bersama untuk beberapa sensor, atau beberapa sektor sensor. Jangan menyebut bukti multiobjek simultan jika paper hanya memakai banyak sensor atau menguji banyak objek secara bergantian.

### Bab III — Metode Penelitian

Memuat perangkat, rancangan prototipe, preprocessing citra, prompt Gemma, akuisisi dua sensor, klasifikasi evidence, logging, ground truth eksternal, rubrik deskripsi, dan teknik analisis.

### Bab IV — Hasil dan Pembahasan

Urutan pembahasan mengikuti tujuan:

1. hasil implementasi deskripsi;
2. hasil integrasi dan status evidence sensor;
3. hasil evaluasi sensor dan deskripsi pada subbagian terpisah.

### Bab V — Penutup

Kesimpulan menjawab rumusan masalah berdasarkan data. Saran berangkat dari keterbatasan yang ditemukan, bukan janji fitur di luar scope.

## 13. Acceptance criteria

1. Satu citra indoor menghasilkan satu deskripsi Bahasa Indonesia.
2. Capture dapat dicocokkan dengan evidence sensor dan menyimpan provenance.
3. Nilai kedua sensor tetap dapat diaudit secara individual.
4. Rata-rata hanya muncul pada status paired yang memenuhi gate.
5. Tidak ada angka sensor yang dilekatkan pada objek bernama.
6. Status konflik, stale, mismatch, partial, dan unavailable ditangani eksplisit.
7. UI, API, log, dan dokumentasi memakai istilah yang konsisten.
8. Evaluasi sensor memakai `ground_truth_cm` eksternal; evaluasi deskripsi dilakukan terpisah.
9. Hasil gagal dan missing data tetap dilaporkan.

## 14. Ringkasan satu kalimat

Bridge-Gap adalah prototipe deskripsi gambar indoor berbahasa Indonesia berbasis Gemma 4 E2B yang menyertakan referensi jarak frontal dari dua HC-SR04 tanpa mengaitkan angka sensor dengan objek bernama.
