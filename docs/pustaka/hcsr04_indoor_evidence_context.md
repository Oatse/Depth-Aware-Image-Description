---
status: active
scope: "Pemilihan sumber HC-SR04 yang paling serupa dengan setup indoor Bridge-Gap"
date: "2026-07-22"
use_for: "Bab II, justifikasi Bab III, pembahasan Bab IV, dan pemeriksaan batas klaim"
---

# Konteks bukti HC-SR04 indoor untuk Bridge-Gap

Dokumen ini adalah aturan pemilihan sumber HC-SR04 untuk penulisan Bridge-Gap. Gunakan dokumen ini bersama `CONTEXT.md` dan `docs/evaluation_protocol.md`. Jika sumber HC-SR04 lain tidak menjelaskan lingkungan, susunan objek, sensor, serta prosedur pengujiannya, jangan menyebutnya mempunyai kondisi yang sama dengan proyek.

## 1. Kondisi kanonik proyek

Kondisi yang harus dipakai ketika menilai kemiripan penelitian terdahulu adalah:

- lingkungan **indoor**;
- dua HC-SR04 standar pada dudukan tetap, menghadap frontal dan kira-kira sejajar dengan kamera belakang;
- kedua sensor dipicu bergantian untuk mengurangi interferensi;
- rentang evaluasi penelitian 20–200 cm;
- base case evaluasi memakai satu target planar yang besar, frontal, dan mempunyai `ground_truth_cm` eksternal;
- `ground_truth_cm` diukur dari bidang referensi kamera; muka HC-SR04 berada 3 cm lebih maju akibat ketebalan kerangka prototipe dan dudukan/kerangka sensor;
- setiap sensor tetap menghasilkan satu nilai jarak untuk cone-nya, bukan identitas objek;
- scene kamera dapat memuat beberapa objek, tetapi tidak tersedia pengikatan yang membuktikan objek mana yang menghasilkan echo;
- rata-rata pasangan hanya sah ketika kedua sensor valid, segar, searah, dan tidak konflik.

Konvensi titik nol proyek:

```text
camera_sensor_offset_cm = 3.0
sensor_face_ground_truth_cm = ground_truth_cm - camera_sensor_offset_cm
```

Jadi, jarak 50 cm dari bidang referensi kamera setara dengan 47 cm dari muka sensor. Offset tetap ini merupakan kondisi mekanis prototipe, bukan temuan universal dari literatur HC-SR04. Profil kalibrasi aktif sudah dipasang terhadap `ground_truth_cm` beracuan kamera; jangan menambahkan 3 cm lagi pada nilai terkoreksi.

## Keputusan sintesis yang dikunci: 20–200 cm

Untuk kebutuhan Bridge-Gap, **20–200 cm ditetapkan sebagai rentang evaluasi operasional konservatif HC-SR04 pada kondisi indoor**. Angka ini bukan hasil menghitung rata-rata aritmetika dari batas minimum dan maksimum setiap paper. Desain, target, metrik, jumlah pengulangan, serta kualitas paper berbeda sehingga perhitungan mean antar-rentang tidak valid secara metodologis.

Rentang tersebut diperoleh melalui **triangulasi bukti berbobot**:

1. memilih studi HC-SR04 yang benar-benar melakukan eksperimen indoor/laboratorium;
2. memeriksa bagian rentang 20–200 cm yang benar-benar dicakup setiap studi;
3. memberi bobot lebih besar pada studi dengan target, jarak, pengulangan, dan keterbatasan yang jelas;
4. mencari tumpang tindih hasil pada jarak dekat, menengah, dan mendekati 200 cm;
5. menurunkan klaim ketika hasil hanya berlaku pada dinding atau bidang besar yang frontal.

Interpretasi internalnya tetap bertingkat:

- **20–120 cm:** zona utama dengan dukungan paling rapat untuk pengukuran akurasi;
- **120–200 cm:** perluasan operasional untuk target cukup besar dan frontal, dengan keyakinan lebih rendah serta wajib verifikasi lokal;
- `<20 cm` dan `>200 cm`: tidak masuk klaim utama penelitian ini.

### Korpus inti untuk mendukung rentang 20–200 cm

| Sumber | Cakupan eksperimen yang relevan | Peran dalam sintesis | Batas utama |
|---|---|---|---|
| Komarizadehasl et al. (2022) | Laboratorium, 25 HC-SR04, target bidang bersama, sekitar 29–114 cm | Jangkar rentang dekat–menengah, variasi antarunit, dan dua sensor pada target bersama | Target sangat besar dan frontal |
| Hunter (2023) | Satu dinding indoor, sekitar 21,6–365,8 cm | Menutup bagian bawah 20 cm dan menunjukkan bias berubah bersama jarak | Satu sensor dan satu dinding |
| Păpară et al. (2024) | Ruang indoor, satu objek per pengujian, 50–230/250 cm | Jangkar terkuat untuk objek indoor, bentuk target, posisi cone, serta bagian atas hingga sekitar 200 cm | Ruang kosong; bukan multiobjek simultan |
| Téllez-Garzón et al. (2025) | Laboratorium, satu target, 0–460 cm, frontal dan lateral | Menunjukkan bahwa pembacaan frontal dapat melampaui 200 cm tetapi posisi lateral menurunkan keterandalan | Target planar; konfigurasi catu perlu dicermati |
| Priadi et al. (2025) | Indoor, 25–70 cm | Bukti nasional untuk bagian bawah rentang | Lima pengulangan dan terminologi metrik tidak standar |
| Estu Broto (2024) | Target dinding hingga 350 cm, 20 pembacaan per jarak | Bukti nasional pendukung bahwa bagian 120–200 cm masih dapat diukur pada target ideal | Hanya dinding frontal; hasil agregat |

Keenam sumber tersebut tidak membuktikan bahwa setiap objek dan sudut akan akurat sepanjang 20–200 cm. Mereka cukup untuk **membenarkan pemilihan rentang uji**, sedangkan klaim performa akhir harus berasal dari data verifikasi Bridge-Gap pada 40, 80, 125, dan 175 cm.

## 2. Kriteria pemilihan sumber

Sumber masuk kelompok utama bila memenuhi seluruh syarat berikut:

1. terbit dalam rentang 2016–2026;
2. menggunakan HC-SR04, bukan hanya sensor ultrasonik generik;
3. pengujian dilakukan di ruang indoor atau laboratorium terkontrol;
4. susunan target/objek dapat diketahui;
5. melaporkan jarak, galat, repeatability, sudut, bentuk, material, atau status deteksi;
6. DOI atau laman penerbit dapat diverifikasi.

Kemiripan tidak ditentukan oleh kesamaan tema aplikasi saja. Penelitian alat bantu tunanetra yang tidak menjelaskan kondisi uji tidak otomatis lebih kuat daripada penelitian laboratorium yang menjelaskan target, jarak, sudut, dan pengulangannya.

## 3. Sumber utama yang dipilih

### 3.1 Păpară et al. (2024) — kecocokan tertinggi untuk indoor satu objek

**Sitasi:** Păpară, R., Grec, L., Potarniche, I.-A. and Gălătuș Voichița, R. (2024) ‘Testing of indoor obstacle-detection prototypes designed for visually impaired persons’, *Applied Sciences*, 14(5), 1767. https://doi.org/10.3390/app14051767.

**Kondisi eksperimen:**

- ruang kosong tanpa perabot agar tidak ada interferensi objek lain;
- satu HC-SR04 pada prototipe;
- **satu objek diuji pada satu waktu**;
- objek kotak 40 cm, silinder diameter 38 cm, pipa PVC 2 cm, kotak korek, dan berbagai material;
- jarak 50, 70, 100, 140, 180, 210, dan 230/250 cm;
- posisi objek mencakup penuh, setengah, dan seperempat cone sensor;
- pengujian tiap konfigurasi dilakukan selama 30 menit; material diuji pada 50 cm selama 10 menit.

**Pemakaian yang sah:** landasan utama bahwa bentuk objek dan penempatan di dalam cone memengaruhi hasil pada kondisi indoor. Sumber ini juga mendukung pemakaian target tunggal terkontrol pada eksperimen utama Bridge-Gap.

**Batas:** ruang sengaja dikosongkan dan tidak menguji beberapa objek sekaligus. Metrik utamanya menilai keluaran kategori/peringatan prototipe, bukan hanya MAE jarak mentah. Klaim keselamatan atau manfaat pengguna dari paper tidak diadopsi oleh Bridge-Gap.

### 3.2 Komarizadehasl et al. (2022) — kecocokan tertinggi untuk dua sensor pada target yang sama

**Sitasi:** Komarizadehasl, S., Mobaraki, B., Ma, H., Lozano-Galant, J.-A. and Turmo, J. (2022) ‘Low-cost sensors accuracy study and enhancement strategy’, *Applied Sciences*, 12(6), 3186. https://doi.org/10.3390/app12063186.

**Kondisi eksperimen:**

- eksperimen laboratorium;
- 25 unit HC-SR04 sebagai bagian dari 75 sensor jarak;
- sensor diarahkan pada **satu bidang target besar yang sama**, bukan beberapa objek;
- target lebih besar dari 0,5 m²;
- jarak acuan HC-SR04 sekitar 29–114 cm;
- 80 siklus per kondisi.

**Pemakaian yang sah:** landasan untuk variasi antarunit, evaluasi tiap sensor secara individual, dan penggunaan ringkasan beberapa sensor hanya ketika semuanya mengamati target/permukaan yang sama.

**Batas:** banyak sensor tidak berarti banyak objek. Hasil averaging pada satu bidang besar tidak membenarkan merata-ratakan dua sensor yang mengenai objek berbeda.

### 3.3 Hunter (2023) — baseline satu sensor dan satu dinding indoor

**Sitasi:** Hunter, D. (2023) ‘Analysis of the measurement error from a low-cost ultrasonic sensor’, *Edward Waters University Undergraduate Research Journal*, 1(1). https://doi.org/10.62962/001c.87939.

**Kondisi eksperimen:**

- satu HC-SR04 menghadap **satu dinding**;
- suhu ruang sekitar 21,1 °C;
- 30 titik jarak sekitar 21,6–365,8 cm;
- 16 pembacaan dirata-ratakan pada setiap jarak.

**Pemakaian yang sah:** bukti pendukung bahwa bias dapat berubah bersama jarak walaupun targetnya ideal dan frontal.

**Batas:** satu unit, satu dinding, dan kualitas venue lebih rendah daripada jurnal instrumentasi utama. Jangan memakai hasilnya untuk scene multiobjek.

### 3.4 Téllez-Garzón et al. (2025) — satu objek pada variasi jarak dan posisi lateral

**Sitasi:** Téllez-Garzón, J.L., Fandiño-Pelayo, J.S., Bernard, A. and Mazzini, G. (2025) ‘Study comparing empirical data on sensors used to measure obstacle distance’, *Ingeniería*, 30(1), e22458. https://doi.org/10.14483/23448393.22458.

**Kondisi eksperimen:**

- laboratorium berukuran 6 × 6 m;
- satu target planar berukuran 22 × 27 cm;
- target dipindahkan pada 93 posisi dari 0–460 cm dengan interval 5 cm;
- pengujian frontal dan lateral;
- sepuluh pembacaan dirata-ratakan pada setiap posisi.

**Pemakaian yang sah:** landasan bahwa kondisi frontal lebih mudah daripada target lateral dan bahwa jarak nominal tidak sama dengan rentang presisi universal.

**Batas:** hanya satu target planar. Paper melaporkan catu 3 V untuk HC-SR04 walaupun spesifikasi umum modul menggunakan 5 V, sehingga hasil tidak boleh dianggap identik dengan perangkat Bridge-Gap.

### 3.5 Priadi et al. (2025) — bukti Indonesia untuk pengujian indoor jarak dekat

**Sitasi:** Priadi, A.R., Safitri, R.A., Pratama, T.B. and Latifa, U. (2025) ‘Comparison of accuracy and precision of distance readings on HC-SR04, JSN-SR04T, and A02YYUW ultrasonic sensors’, *TESLA: Jurnal Teknik Elektro*, 27(1), pp. 19–29. https://doi.org/10.24912/tesla.v27i1.33372.

**Kondisi eksperimen:**

- pengujian indoor;
- HC-SR04 dibandingkan dengan dua tipe sensor ultrasonik lain;
- target/jarak diuji satu per satu pada 25–70 cm;
- lima pengulangan per titik.

**Pemakaian yang sah:** sumber nasional pendukung untuk rentang dekat indoor dan pembandingan karakter sensor murah.

**Batas:** jumlah pengulangan kecil dan istilah akurasi/presisi pada rumus paper tidak mengikuti penggunaan metrologi yang lazim. Ambil data eksperimennya dengan catatan, jangan menyalin terminologinya tanpa kritik.

### 3.6 Estu Broto (2024) — bukti Indonesia untuk rentang atas pada target ideal

**Sitasi:** Estu Broto, P. (2024) ‘Perbandingan persentase kesalahan sensor sonar pengukur jarak berbasis HC-SR04 dan HY-SRF05’, *Jurnal Sains Fisika: SAINFIS*, 4(1), pp. 1–10. https://doi.org/10.24252/sainfis.v4i1.41079.

**Kondisi eksperimen:** target dinding diuji setiap 10 cm hingga 350 cm dengan 20 pembacaan per jarak. Rata-rata persentase error HC-SR04 dilaporkan sebesar 1,107579%.

**Pemakaian yang sah:** bukti nasional pendukung bahwa HC-SR04 masih dapat menghasilkan pembacaan pada bagian 120–200 cm ketika targetnya berupa dinding besar dan frontal.

**Batas:** hasil agregat terhadap satu dinding tidak mewakili objek kecil, miring, melengkung, atau lunak. Paper ini mendukung batas evaluasi 200 cm, tetapi bukan bukti akurasi universal sampai 350 cm.

## 4. Sumber proxy multisensor, bukan bukti multiobjek langsung

### Widianto, Ikhsan dan Prasetijo (2021)

**Sitasi:** Widianto, E.D., Ikhsan, M. and Prasetijo, A.B. (2021) ‘Rompi penyedia informasi bagi penyandang tunanetra menggunakan multisensor HC-SR04’, *Jurnal Teknik Elektro*, 13(2), pp. 42–47. https://doi.org/10.15294/jte.v13i2.31112.

Paper menggunakan lima HC-SR04 yang menghadap sektor depan, kanan, kiri, atas, dan bawah serta menganalisis cakupan dan daerah buta hingga sekitar 150 cm. Ini adalah sumber Indonesia yang paling dekat untuk membahas **arsitektur multisensor dan cone berbeda**.

Namun, paper tidak menjadi bukti bahwa satu HC-SR04 dapat memisahkan beberapa objek di dalam cone yang sama. Jumlah sensor lebih dari satu juga tidak membuktikan bahwa pengujian menempatkan beberapa objek secara simultan atau bahwa dua sensor boleh dirata-ratakan ketika melihat permukaan berbeda. Gunakan paper ini untuk latar belakang multisensor, bukan untuk validasi `frontal_reference_cm`.

### Abreu et al. (2021)

**Sitasi:** Abreu, D., Toledo, J., Codina, B. and Suárez, A. (2021) ‘Low-cost ultrasonic range improvements for an assistive device’, *Sensors*, 21(12), 4250. https://doi.org/10.3390/s21124250.

Paper memakai dua HC-SR04 untuk level rintangan berbeda dan menguji interferensi ketika dua perangkat ultrasonik memancar pada area yang sama. Gunakan hanya untuk menjelaskan risiko cross-talk dan alasan sensor Bridge-Gap dipicu bergantian.

Sebagian rangkaian dan pemrosesan HC-SR04 dimodifikasi. Angka blind zone 28 cm pada sistem termodulasi tidak boleh dipindahkan ke modul standar Bridge-Gap.

## 5. Status bukti beberapa objek sekaligus

**Tidak ditemukan bukti langsung yang cukup serupa** dalam korpus terpilih untuk kondisi berikut secara bersamaan:

1. ruang indoor;
2. HC-SR04 standar;
3. beberapa objek fisik berada serentak di dalam cone sensor yang sama;
4. ground truth setiap objek diketahui;
5. penelitian memverifikasi objek mana yang menghasilkan pembacaan HC-SR04.

Konsekuensinya:

- Păpară et al. menguji banyak bentuk/material, tetapi satu per satu;
- Komarizadehasl et al. memakai banyak sensor, tetapi semuanya mengamati satu target bersama;
- Widianto et al. memakai banyak sensor untuk sektor berbeda, bukan pemisahan beberapa echo oleh satu sensor;
- Abreu et al. menguji interferensi beberapa pemancar, bukan beberapa objek;
- studi array ultrasonik yang dapat mengestimasi beberapa obstacle memakai hardware dan pemrosesan yang berbeda dari HC-SR04 standar sehingga tidak dipakai sebagai bukti langsung.

Scene multiobjek harus diposisikan sebagai **gap validitas eksternal** dan diuji lokal bila ingin dibahas. Nilai HC-SR04 pada scene tersebut tetap disebut “referensi jarak pada cone/sektor sensor”, bukan “jarak objek X”.

## 6. Aturan pemakaian dalam penulisan

### Bab II — penelitian terdahulu

- gunakan Păpară et al. sebagai sumber utama pengujian HC-SR04 indoor terhadap bentuk, posisi cone, material, dan jarak;
- gunakan Komarizadehasl et al. untuk akurasi, variasi antarunit, dan kombinasi beberapa sensor pada satu target;
- gunakan Téllez-Garzón et al. untuk pengaruh posisi frontal/lateral;
- gunakan Priadi et al. sebagai bukti nasional indoor dengan kritik pada metrik;
- gunakan Widianto et al. untuk desain multisensor Indonesia, bukan sebagai bukti pemisahan multiobjek;
- gunakan Abreu et al. untuk interferensi ultrasonik dan kebutuhan sequential triggering.
- untuk justifikasi rentang 20–200 cm, gunakan korpus inti enam sumber dan sebut metode **sintesis konservatif/triangulasi bukti**, bukan “rata-rata jarak dari jurnal”.

### Bab III — metode

Literatur utama mendukung eksperimen dasar dengan **satu target planar terkendali**. Karena itu, hasil kalibrasi/verifikasi 20–200 cm hanya berlaku pada target dan kondisi yang diuji. Jika ditambahkan eksperimen multiobjek, jadikan eksperimen terpisah dan jangan mencampurnya dengan data kalibrasi.

### Bab IV — hasil dan pembahasan

Bandingkan hasil lokal dengan penelitian yang susunan targetnya sama. Jangan membandingkan MAE target planar Bridge-Gap secara langsung dengan accuracy kategori peringatan Păpară et al. tanpa menjelaskan perbedaan metrik. Laporkan `pair_conflict`, timeout, atau perubahan echo sebagai hasil, bukan dibuang sebagai noise.

## 7. Kalimat yang boleh dan tidak boleh digunakan

### Boleh

> Penelitian indoor terdahulu menunjukkan bahwa performa HC-SR04 dipengaruhi bentuk dan posisi objek dalam cone sensor; sebagian besar pengujian dilakukan terhadap satu objek atau satu permukaan dominan pada satu waktu.

> Penggabungan pembacaan beberapa HC-SR04 memiliki dukungan empiris ketika sensor mengamati target bidang yang sama, tetapi tidak membuktikan bahwa averaging sah ketika sensor menerima pantulan dari objek berbeda.

> Literatur yang ditelaah belum memberikan validasi langsung untuk identifikasi beberapa objek simultan menggunakan HC-SR04 standar dalam satu cone.

> Berdasarkan triangulasi eksperimen indoor nasional dan internasional, rentang 20–200 cm dipilih sebagai rentang evaluasi operasional konservatif; bagian 20–120 cm memiliki dukungan paling kuat, sedangkan 120–200 cm memerlukan target frontal dan verifikasi lokal.

### Tidak boleh

- “Semua jurnal menggunakan kondisi yang sama dengan Bridge-Gap.”
- “HC-SR04 dapat menentukan jarak setiap objek dalam gambar.”
- “Dua sensor menjamin objek yang diukur sama.”
- “Penelitian multisensor membuktikan akurasi pada scene multiobjek.”
- “Rentang 2–400 cm seluruhnya akurat untuk indoor.”
- “Hasil teknis membuktikan keamanan navigasi atau manfaat pengguna.”
- “Rentang 20–200 cm diperoleh dengan merata-ratakan batas jarak seluruh jurnal.”

## 8. Paragraf siap adaptasi untuk Bab II

> Păpară, Grec, Potarniche dan Gălătuș Voichița (2024) menguji prototipe berbasis HC-SR04 dalam ruang indoor kosong menggunakan objek kotak, silinder, objek kecil, serta berbagai material pada beberapa jarak dan posisi terhadap cone sensor. Hasil penelitian tersebut memperlihatkan bahwa bentuk permukaan dan penempatan objek terhadap arah sensor memengaruhi keluaran sistem. Meskipun relevan dengan konteks indoor, eksperimen dilakukan terhadap satu objek pada satu waktu sehingga belum mewakili scene dengan beberapa objek yang menghasilkan pantulan secara bersamaan.

> Komarizadehasl, Mobaraki, Ma, Lozano-Galant dan Turmo (2022) menguji 25 unit HC-SR04 terhadap satu bidang target besar dalam kondisi laboratorium. Penelitian tersebut mendukung perlunya mengevaluasi variasi antarunit dan mempertahankan hasil setiap sensor sebelum membentuk nilai agregat. Namun, keberhasilan kombinasi beberapa sensor pada satu target tidak dapat digunakan untuk menyimpulkan bahwa rata-rata dua sensor tetap valid ketika keduanya menerima pantulan dari objek yang berbeda.

> Dalam konteks nasional, Widianto, Ikhsan dan Prasetijo (2021) mengembangkan rompi dengan lima HC-SR04 untuk memperluas cakupan deteksi pada beberapa arah. Penelitian tersebut relevan sebagai contoh arsitektur multisensor, tetapi tidak membuktikan bahwa satu HC-SR04 dapat memisahkan beberapa objek dalam cone yang sama. Oleh karena itu, Bridge-Gap mempertahankan pembacaan sensor sebagai referensi frontal tanpa identitas objek dan menahan rata-rata ketika pasangan sensor berkonflik.

Paragraf ini adalah bahan awal. Sesuaikan dengan struktur Bab II, hindari kutipan verbatim panjang, dan pastikan semua sumber yang benar-benar dikutip masuk daftar pustaka final bergaya Harvard.
