# Riset Pemilihan Sensor Indoor: HC-SR04 vs Infrared untuk Ekstensi ESP32

Tanggal: 18 Juli 2026  
Konteks: prototype *depth-aware image description* Bride-Gap

## Ringkasan keputusan

Untuk kebutuhan Bride-Gap yang paling masuk akal—menambahkan satu atau beberapa referensi jarak fisik indoor ke pipeline kamera dan depth monocular—**HC-SR04 adalah pilihan utama di antara dua opsi yang dibandingkan**. Alasannya bukan karena HC-SR04 selalu paling akurat, tetapi karena ia memberi rentang lebih panjang, relatif tidak sensitif terhadap warna dan cahaya, murah, dan bukti penelitian indoor/robotics-nya lebih konsisten.

Sensor infrared perlu dibedakan menjadi dua kelas:

1. **IR obstacle module** seperti KY-032, FC-51, atau TCRT5000: umumnya keluaran digital ada/tidak ada objek pada jarak pendek. Ini bukan pengganti sensor jarak kuantitatif dan tidak cocok sebagai acuan depth map.
2. **IR triangulation analog** seperti Sharp GP2Y0A21YK0F/GP2Y0A710K0F: menghasilkan estimasi jarak kontinu, tetapi rentangnya pendek dan dipengaruhi reflektansi, warna/tekstur permukaan, sudut, dan cahaya.

Jika yang dimaksud “infrared merah” adalah modul obstacle digital, maka perbandingan yang adil bukan “HC-SR04 vs sensor jarak IR”, melainkan “sensor jarak vs sakelar proximity”. Modul itu hanya layak sebagai *near-field trigger* tambahan.

## Paper paling relevan

| Sumber | Desain uji | Temuan yang relevan | Kekuatan/batasan |
|---|---|---|---|
| Téllez-Garzón et al. (2025), *Ingeniería*, DOI 10.14483/23448393.22458 | HC-SR04 vs GP2Y0A21YK0F; indoor lab 6×6 m; frontal/lateral; 10 pembacaan per titik; 0–460 cm untuk US dan 0–92 cm untuk IR | US sangat linear (Pearson/Spearman 0,999; Kendall 0,998), error umumnya <1% pada frontal; IR hanya efektif sekitar 10–60 cm pada uji mereka, dengan error dapat mendekati 15%; IR lebih baik pada jarak pendek dan obstacle miring | Paper peer-reviewed, langsung membandingkan dua sensor; hanya satu obstacle putih/flat dan lingkungan terkontrol |
| Zieliński (2021), *International Journal of Electronics and Telecommunications*, DOI 10.24425/ijet.2021.135976 | HC-SR04 vs Sharp GP2Y0A02YK0F; pengujian indoor 30–150 cm dan uji warna, permukaan, cahaya; 1.000 pengukuran per kondisi | Pada uji indoor, jarak tidak mengubah akurasi secara berarti. US sekitar 99% hasil “exact” pada warna hitam/abu/merah/putih; IR turun dari ~90% (70 cm) menjadi ~85% (130 cm). Permukaan mengilap menurunkan IR; cahaya kuat menurunkan akurasi IR sekitar 20%, sedangkan US hampir tidak berubah | Pengujian kondisi lingkungan sangat lengkap; target utama rangefinder sepeda, bukan citra indoor |
| Adarsh et al. (2016), IOP Conf. Ser. MSE 149 012141, DOI 10.1088/1757-899X/149/1/012141 | Kendaraan robot bergerak menuju cardboard, paper, sponge, wood, plastic, rubber, tile; US vs Sharp GP2Y0A21YK0F | US lebih stabil untuk cardboard, wood, plastic, rubber; IR lebih baik untuk paper dan sponge; tile relatif bisa keduanya dengan keunggulan kecil pada US | Menunjukkan material adalah variabel penting; hasil tidak boleh digeneralisasi menjadi satu sensor selalu menang |
| Irawan, Rinaldi & Priyadi (2023), skripsi Universitas Bengkulu | HC-SR04 vs Sharp GP2Y0A710K0F; ruang tertutup; variasi cahaya 1.000/2.670 lux dan suhu 20–40°C | IR lebih terpengaruh cahaya; jarak optimal IR sampai ~250 cm dari uji 400 cm, sedangkan US sampai ~400 cm pada cahaya uji. Keduanya terpengaruh pada 37–40°C, IR lebih besar | Sangat dekat dengan pertanyaan indoor Indonesia; statusnya skripsi repositori, bukan artikel jurnal peer-reviewed |
| Potarniche et al. (2024), *Applied Sciences* 14(5):1767, DOI 10.3390/app14051767 | Prototype indoor assistive berbasis HC-SR04; obstacle berbagai material pada 50 cm, variasi bentuk dan posisi | Material umum bangunan tidak menghilangkan echo 40 kHz; bentuk, ukuran, dan posisi obstacle lebih berpengaruh. Prototype mempertahankan keberhasilan >80% dan >90% pada jarak kritis setelah kalibrasi | Relevan untuk indoor dan assistive; menguji sistem prototype, bukan perbandingan langsung dengan IR |
| Mustapha, Zayegh & Begg (2013), IEEE AIMS, DOI 10.1109/AIMS.2013.89 | Sistem obstacle wireless dengan US + IR untuk lansia/pengguna low vision | Relevan sebagai bukti desain komplementer: dua sensor dipakai untuk menutup kelemahan masing-masing setelah kalibrasi/linearisasi | Paper IEEE langsung relevan, tetapi akses hasil numerik rinci terbatas |
| Mohammad (2009), WASET vol. 51 | Metode IR berbasis reflektansi permukaan, dengan US untuk memperoleh parameter awal | Besaran pantulan IR bergantung pada sifat permukaan; perubahan sudut kecil dapat mengubah estimasi jarak; US dapat menjadi referensi awal | Menjelaskan mengapa IR membutuhkan kalibrasi berbasis material; venue lebih lemah daripada jurnal/IEEE |
| Komarizadehasl et al. (2022), *Applied Sciences* 12:3186, DOI 10.3390/app12063186 | 25 HC-SR04, 25 VL53L0X, 25 VL53L1X; eksperimen laboratorium dan kombinasi sensor | HC-SR04 punya rentang 2–400 cm, 40 Hz, murah, dan tidak dipengaruhi cahaya; satu HC-SR04 menghasilkan error sekitar 2,40% pada eksperimen, dua sensor sekitar 1,85% setelah penggabungan | Bukan eksperimen HC-SR04 vs Sharp IR langsung; berguna untuk strategi averaging dan justifikasi biaya |
| Rahman (2025), *JITE* 8(2):219–226, DOI 10.31289/jite.v8i2.13406 | Ultrasonic vs **infrared laser ToF**, bukan Sharp analog/IR obstacle module | IR ToF lebih akurat/precise pada setup mereka; US lebih baik pada jarak pendek tetapi turun setelah 40 cm | Penting sebagai peringatan klasifikasi: hasil IR ToF tidak boleh dipakai untuk mengklaim modul KY-032 atau Sharp analog pasti lebih baik |

## Sintesis teknis

### HC-SR04

- Prinsip time-of-flight suara; keluaran berupa lebar pulsa ECHO.
- Datasheet umumnya menyatakan 2–400 cm, sekitar 40 kHz, dan sudut nominal sekitar 15°.
- Kelebihan indoor: tidak bergantung pada warna/warna cat dan cahaya tampak; cukup baik untuk dinding, kayu, plastik, kardus, dan obstacle besar.
- Risiko: echo lemah/keliru pada permukaan kecil, tipis, menyerap, atau sangat miring; kecepatan suara berubah dengan suhu; cone beam dapat mengukur permukaan terdekat yang bukan objek yang diasumsikan.
- Untuk dua atau lebih sensor, trigger harus dijadwalkan bergantian untuk menghindari *cross-talk*.

### Sharp IR analog

- Prinsip triangulasi pantulan IR; keluaran analog nonlinear yang harus dikalibrasi menjadi jarak.
- GP2Y0A21YK0F resmi hanya 10–80 cm dan membutuhkan 4,5–5,5 V; hasil datasheet bergantung pada target kertas putih reflektansi 90%.
- Kelebihan: beam lebih sempit, respons dekat cepat, dapat menangani beberapa obstacle miring yang tidak ideal untuk echo ultrasonik.
- Risiko: permukaan gelap, mengilap, transparan, bertekstur, variasi sudut, dan cahaya lingkungan mengubah hasil; rentang praktis bisa lebih pendek daripada datasheet.

### IR obstacle module digital

- Keluaran comparator digital; jarak ambang diatur potensiometer dan tidak memberikan meter/cm yang stabil.
- Cocok untuk pertanyaan “ada obstacle sangat dekat?” atau deteksi tepi/jurang, bukan untuk menguji akurasi depth map.
- Jika dipakai dalam penelitian, definisikan sebagai sensor klasifikasi biner dan evaluasi precision/recall, bukan MAE jarak.

## Kecocokan dengan Bride-Gap

Arsitektur aktif Bride-Gap menerima satu gambar, menghasilkan depth map monocular, lalu meringkasnya sebagai kategori relatif per region. ESP32 tidak akan menjadi pengganti Depth Anything; sensor hanya memberi **satu atau beberapa pengukuran sparse pada sumbu pemasangan**.

Kontribusi yang defensible:

1. **Sparse metric reference**: bandingkan jarak fisik HC-SR04 dengan nilai depth pada region kamera yang sudah dikalibrasi.
2. **Device-aware correction/evaluation**: uji apakah sinyal sensor meningkatkan ketepatan kategori dekat/sedang/jauh pada region tertentu.
3. **Confidence/guardrail**: jika sensor fisik mendeteksi obstacle sangat dekat tetapi depth monocular tidak, sistem menandai konflik bukti—bukan langsung menyatakan navigasi aman/bahaya.

Klaim yang tidak boleh dibuat:

- Satu HC-SR04 menghasilkan depth map penuh.
- Jarak sensor otomatis melekat pada objek yang disebut Gemma tanpa kalibrasi kamera-sensor dan lokalisasi objek.
- Sensor menjadi ground truth universal; ia sendiri memiliki error, cone beam, dan kondisi gagal.
- Sistem menjadi alat navigasi aman atau siap produksi.

## Rekomendasi keputusan

### Pilihan utama: HC-SR04

Pilih HC-SR04 bila target penelitian adalah rentang indoor sekitar 20 cm–3 m, referensi obstacle frontal, biaya rendah, dan pembandingan terhadap kategori depth relatif. Ini adalah keputusan paling mudah dipertanggungjawabkan dari literatur yang ditemukan.

### Pilihan khusus: Sharp IR analog

Pilih Sharp GP2Y0A21YK0F/GP2Y0A710K0F hanya bila target dibatasi pada 10–80 cm atau 20–250 cm sesuai model, sensor harus sangat directional, dan penelitian memang ingin menguji pengaruh warna/reflektansi/cahaya. Ia bukan pilihan default untuk coverage ruangan.

### Jangan pilih sebagai sensor jarak utama: KY-032/FC-51/TCRT5000 module

Gunakan hanya sebagai kanal biner near-field/edge detection. Untuk angka jarak dan korelasi dengan depth map, modul ini terlalu terbatas.

### Catatan opsi yang lebih modern

Jika pembelian baru masih terbuka, VL53L1X/VL53L0X (IR ToF) lebih mudah diintegrasikan pada logika 3,3 V dan beam-nya lebih sempit, tetapi harus diuji terhadap cahaya, permukaan, dan biaya. Ia tidak boleh dicampur secara terminologis dengan “IR merah” analog atau modul obstacle.

## Integrasi ESP32 yang wajib diperhatikan

1. HC-SR04 biasanya diberi 5 V. Pin ECHO 5 V **tidak boleh langsung** ke GPIO ESP32; gunakan pembagi tegangan atau level shifter. Datasheet ESP32 menetapkan batas input/IO sekitar 3,6 V.
2. TRIG dari ESP32 3,3 V biasanya perlu diverifikasi pada modul yang dipakai; jangan mengasumsikan semua clone identik.
3. Sharp IR analog umumnya juga diberi 5 V. Ukur output maksimum aktual; bila melewati rentang ADC board, gunakan pembagi tegangan.
4. Gunakan ADC1 bila Wi-Fi aktif pada ESP32 klasik karena ADC2 berbagi sumber daya dengan Wi-Fi. Aktifkan kalibrasi ADC dan averaging/median.
5. Kirim payload terukur, bukan hanya label: `sensor_id`, `timestamp_ms`, `distance_cm`, `valid`, `temperature_c`, `battery_v`, dan `sample_count`.
6. Trigger sensor dan capture foto harus memiliki timestamp yang sama. Tanpa sinkronisasi, jarak yang dikaitkan ke gambar dapat berasal dari pose berbeda.

## Protokol eksperimen yang disarankan

### Faktor uji

- Jarak: 20, 40, 60, 80, 100, 150, 200, 300 cm; tambahkan 10–80 cm untuk Sharp IR.
- Sudut obstacle: 0°, 10°, 20°, 30°.
- Material/permukaan: matte putih, hitam/gelap, mengilap, kaca/transparan, kardus, kayu, kain/foam, plastik, silinder kecil.
- Cahaya indoor: redup, normal, terang; catat lux jika tersedia.
- Suhu: catat suhu ruang; lakukan subset uji pada kondisi panas jika relevan.
- Replikasi: minimal 30 pembacaan valid per kombinasi untuk prototipe awal; gunakan 50–100 bila ingin membangun distribusi error.

### Metrik

- MAE, RMSE, bias signed, standard deviation, valid-read rate, latency, dan outlier rate.
- Untuk mode obstacle: precision, recall, F1, false alarm, missed detection.
- Untuk Bride-Gap: agreement kategori dekat/sedang/jauh, error region depan/bawah, konflik sensor-vs-depth, tambahan latency end-to-end, dan kehilangan paket Wi-Fi.

### Baseline dan kontrol

- Gunakan laser distance meter atau jig mekanik + pengukuran pita sebagai referensi, bukan depth monocular.
- Kunci posisi kamera dan sensor pada bracket yang sama; dokumentasikan tinggi, offset, orientasi, dan field of view.
- Uji `gemma_only`, `depth_only`, `gemma_depth`, dan `gemma_depth + sensor` pada gambar/scene yang sama.
- Pisahkan evaluasi sensor dari evaluasi kualitas teks Gemma agar korelasi palsu tidak terjadi.

## Verdict akhir

**Untuk ekstensi ESP32 pada proyek sekarang: mulai dari satu HC-SR04 di arah depan/bawah, dengan level shifting ECHO, timestamp bersama kamera, dan evaluasi terbatas sebagai sparse metric reference.** Tambahkan Sharp IR analog hanya sebagai eksperimen pembanding near-field jika memang ingin membahas pengaruh material/cahaya. Jangan menggunakan modul IR digital sebagai pengukur jarak kontinu dan jangan menyebut hasil sensor sebagai ground truth penuh.

Urutan implementasi yang paling aman:

1. Bangun logger ESP32 + HC-SR04 dan validasi MAE/latency pada target matte indoor.
2. Kalibrasi transformasi sensor-to-camera dan definisikan region kamera yang sesuai.
3. Jalankan paired evaluation terhadap 44 citra/scene baru yang memiliki pengukuran fisik, bukan mengubah anotasi lama menjadi “ground truth sensor”.
4. Baru setelah data menunjukkan manfaat, uji fusi dengan depth map sebagai kanal konflik/kepercayaan terbatas.

## Tautan sumber utama

- [Téllez-Garzón et al. (2025), Ingeniería, DOI 10.14483/23448393.22458](https://doi.org/10.14483/23448393.22458)
- [Zieliński (2021), IJET, DOI 10.24425/ijet.2021.135976](https://doi.org/10.24425/ijet.2021.135976)
- [Adarsh et al. (2016), IOP MSE, DOI 10.1088/1757-899X/149/1/012141](https://doi.org/10.1088/1757-899X/149/1/012141)
- [Irawan, Rinaldi & Priyadi (2023), repositori Universitas Bengkulu](https://repository.unib.ac.id/id/eprint/17264/)
- [Potarniche et al. (2024), Applied Sciences, DOI 10.3390/app14051767](https://doi.org/10.3390/app14051767)
- [Mustapha, Zayegh & Begg (2013), IEEE AIMS, DOI 10.1109/AIMS.2013.89](https://doi.org/10.1109/AIMS.2013.89)
- [Mohammad (2009), Using Ultrasonic and Infrared Sensors for Distance Measurement](https://publications.waset.org/6833/using-ultrasonic-and-infrared-sensors-for-distance-measurement)
- [Komarizadehasl et al. (2022), Applied Sciences, DOI 10.3390/app12063186](https://doi.org/10.3390/app12063186)
- [Rahman (2025), JITE, DOI 10.31289/jite.v8i2.13406](https://doi.org/10.31289/jite.v8i2.13406)
- [Sharp GP2Y0A21YK0F official datasheet](https://global.sharp/products/device/lineup/data/pdf/datasheet/gp2y0a21yk_e.pdf)
- [Espressif ESP32 datasheet](https://documentation.espressif.com/esp32_datasheet_en.html)
- [Espressif ESP32 ADC documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/adc.html)
