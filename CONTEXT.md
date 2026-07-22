# Context Bridge-Gap

Dokumen ini adalah kamus domain kanonik Bridge-Gap. Jika dokumen aktif lain bertentangan, gunakan batas istilah dan klaim pada dokumen ini lalu selaraskan `instructions/PROJECT_INITIALIZATION.md`.

## Arah utama

Bridge-Gap menghasilkan satu deskripsi gambar indoor berbahasa Indonesia dari citra RGB menggunakan Gemma 4 E2B. Dua HC-SR04 memberi referensi jarak frontal berbasis pantulan ultrasonik pada cone masing-masing. Kedua jalur dipertahankan provenance-nya:

- citra menjadi sumber deskripsi visual;
- sensor menjadi sumber pembacaan jarak frontal;
- teks sensor ditambahkan sebagai bagian terpisah dari deskripsi visual;
- pembacaan sensor tidak dilekatkan pada objek yang dinamai Gemma.

## Istilah kanonik

**Deskripsi visual-spasial indoor**

Teks Bahasa Indonesia yang menjelaskan objek, posisi relatif yang tampak, dan konteks scene dari satu citra. Istilah ini tidak menyatakan sistem navigasi atau keselamatan mobilitas.

**Referensi sensor frontal**

Informasi jarak ke permukaan pantul di dalam cone dua HC-SR04 yang menghadap searah kamera belakang. Referensi ini tidak mempunyai identitas objek, koordinat piksel, atau cakupan seluruh citra.

**Sampel valid**

Sampel yang mempunyai nilai numerik non-negatif, status pembacaan baik, dan metadata waktu yang dapat diperiksa.

**Sampel segar**

Sampel valid yang umurnya tidak melewati `SENSOR_FRESHNESS_MAX_AGE_MS` pada waktu pencocokan capture.

**Paired**

Dua sampel valid dan segar, arah kamera sesuai dengan sensor, dan selisih nilai tidak melewati `SENSOR_PAIR_DISAGREEMENT_CM`. Hanya status ini yang boleh menghasilkan rata-rata pasangan.

**Offset geometri kamera–sensor**

Bidang referensi kamera berada 3 cm di belakang muka akustik HC-SR04 karena gabungan ketebalan kerangka prototipe dan dudukan/kerangka sensor. Tetapkan `camera_sensor_offset_cm = 3.0`. `ground_truth_cm` adalah jarak dari bidang referensi kamera ke bidang target, sedangkan jarak ekuivalen dari muka sensor adalah:

```text
sensor_face_ground_truth_cm = ground_truth_cm - camera_sensor_offset_cm
camera_reference_from_raw_cm = sensor_raw_cm + camera_sensor_offset_cm
```

Contoh: ketika target berjarak aktual 50 cm dari bidang referensi kamera, jarak geometris dari muka sensor adalah 47 cm sehingga pembacaan mentah ideal HC-SR04 adalah sekitar 47 cm. Selisih tetap 3 cm ini adalah transformasi titik acuan fisik, bukan error intrinsik sensor. Penyimpangan tambahan dari 47 cm tetap diperlakukan sebagai error pengukuran.

Profil kalibrasi aktif dibentuk langsung terhadap `ground_truth_cm` yang beracuan pada kamera. Karena itu, keluaran `sensor_1_corrected_cm` dan `sensor_2_corrected_cm` sudah berada pada acuan kamera dan telah menyerap offset geometri bersama bias hasil fitting. **Jangan menambahkan 3 cm lagi pada nilai terkoreksi.**

```text
sensor_1_corrected_cm = intercept_1 + slope_1 * sensor_1_cm
sensor_2_corrected_cm = intercept_2 + slope_2 * sensor_2_cm
frontal_reference_cm = (sensor_1_corrected_cm + sensor_2_corrected_cm) / 2
```

Rata-rata dibulatkan untuk penyajian, tetapi nilai mentah dan terkoreksi kedua sensor tetap disimpan. Kalimat yang diizinkan: “Referensi sensor frontal sekitar X cm pada bidang pandang sensor.”

**Batas operasional penelitian**

Rentang evaluasi sensor ditetapkan pada 20–200 cm. Rentang ini adalah sintesis konservatif dari tumpang tindih bukti eksperimen indoor nasional dan internasional, **bukan rata-rata aritmetika batas jarak antarjurnal**. Dukungan paling rapat berada pada 20–120 cm; bagian 120–200 cm diperlakukan sebagai perluasan operasional untuk target cukup besar dan frontal. Verifikasi koreksi memakai titik baru 40, 80, 125, dan 175 cm dengan 30 pembacaan berpasangan per titik. Seluruh titik verifikasi disimpan terpisah dari data kalibrasi dan tidak mengubah profil koreksi yang telah dibekukan. Klaim kinerja sampai 200 cm hanya boleh dibuat setelah keempat titik verifikasi lengkap dan hasilnya memenuhi kriteria evaluasi.

**Partial**

Hanya satu sampel valid/tersedia. Nilai sensor yang ada boleh tampil dengan identitasnya, tetapi tidak boleh disebut rata-rata dua sensor.

**Pair conflict**

Dua sampel valid memiliki selisih di atas ambang konfigurasi. Kedua nilai dapat ditampilkan untuk audit, tetapi kontribusi rata-rata ditahan.

**Stale**

Satu atau lebih sampel terlalu lama untuk dipasangkan dengan capture. Nilai tidak digunakan pada deskripsi akhir.

**Direction mismatch**

Frame berasal dari kamera yang tidak menghadap searah sensor. Nilai sensor tidak diterapkan pada hasil capture tersebut.

**Unavailable**

Bridge sensor tidak terhubung atau tidak ada sampel valid yang dapat digunakan.

## Prinsip fisik sensor

Prinsip waktu tempuh (*time of flight*) HC-SR04:

```text
d = v * t / 2
```

- `d`: jarak sensor ke permukaan pantul;
- `v`: cepat rambat suara;
- `t`: waktu echo pulang-pergi.

Rumus tersebut menjelaskan cara sensor memperoleh jarak. Ia bukan rumus pengikatan sensor ke objek dalam gambar. Variasi suhu, sudut permukaan, material, ukuran target, interferensi antarsensor, dan geometri pemasangan dapat memengaruhi pembacaan.

## Konteks bukti HC-SR04 untuk penulisan

Gunakan `docs/pustaka/hcsr04_indoor_evidence_context.md` sebagai rute sumber kanonik ketika menulis landasan teori, penelitian terdahulu, metode, atau pembahasan HC-SR04. Dokumen tersebut memisahkan:

- bukti langsung indoor dengan satu objek/permukaan dominan;
- bukti beberapa sensor yang mengamati satu target bersama;
- proxy multisensor dengan cone/sektor berbeda;
- gap beberapa objek simultan dalam cone yang sama.

Mayoritas sumber yang paling serupa memakai satu objek pada satu waktu. Sampai ada bukti lokal atau literatur yang lebih kuat, scene multiobjek tidak boleh diperlakukan sebagai kondisi yang sudah tervalidasi oleh penelitian terdahulu. Setiap tulisan harus menyebut susunan objek dan tidak boleh menyamakan “banyak sensor” dengan “banyak objek yang terpisah secara terukur”.

## Kontrak provenance sensor

Evidence minimum per capture menyimpan:

```json
{
  "capture_id": "cap_001",
  "status": "paired",
  "match_time_ms": 0,
  "match_time_source": "client_capture",
  "camera_facing_mode": "environment",
  "pair_disagreement_cm": 1.2,
  "samples": {
    "sensor_1": {
      "distance_cm": 60.1,
      "received_time_ms": 0,
      "age_ms": 35,
      "status": "ok"
    },
    "sensor_2": {
      "distance_cm": 61.3,
      "received_time_ms": 0,
      "age_ms": 41,
      "status": "ok"
    }
  }
}
```

Nilai nol pada contoh adalah placeholder bentuk data, bukan hasil pengujian. Log aktual harus menyimpan timestamp sebenarnya.

## Kontrak capture tertunda

Capture kamera dan analisis Gemma adalah dua tahap terpisah. Sebelum capture kamera, operator wajib mengisi `ground_truth_cm`, yaitu jarak aktual dari bidang referensi kamera ke target. Saat tombol capture ditekan, backend langsung menyimpan gambar, `capture_id`, `batch_id`, waktu capture, arah kamera, offset kamera–sensor, `ground_truth_cm`, `sensor_face_ground_truth_cm = ground_truth_cm - 3.0`, nomor pengulangan, serta snapshot evidence sensor ke folder lokal `results/captures/`. Tahap ini tidak menjalankan Gemma. Nilai jarak pada UI dipertahankan agar beberapa pengulangan pada jarak yang sama dapat dilakukan tanpa mengetik ulang; backend menaikkan `repeat_index` secara otomatis untuk kombinasi batch, jarak, dan target yang sama.

Untuk seri capture terkendali, alat ukur digunakan menetapkan jarak lalu dikeluarkan dari bidang pandang kamera sebelum gambar disimpan. Kontrol ini mencegah alat ukur menjadi objek visual tambahan, tetapi **bukan** perubahan tujuan penelitian menjadi uji konsistensi identitas objek pada berbagai jarak. Citra tetap dinilai sebagai deskripsi visual-spasial atas apa yang terlihat, sedangkan jarak fisik tetap menjadi ground truth eksperimen sensor. Jangan mengubah zoom atau framing per titik hanya untuk memaksa target selalu terlihat utuh.

Analisis dilakukan kemudian dari backend dengan aturan **satu capture menjadi satu job**. Job wajib memakai gambar dan sensor evidence yang tersimpan pada waktu capture; sensor tidak boleh dibaca ulang pada waktu analisis. Hanya satu job yang boleh aktif untuk satu capture, dan runner backend memproses capture secara berurutan agar kegagalan dapat diisolasi. UI kamera hanya menampilkan jumlah capture tersimpan dan tidak menyediakan daftar dataset atau tombol analisis batch.

## Kontrak prompt dan deskripsi

Prompt Gemma harus:

1. menggunakan citra RGB sebagai bukti visual;
2. meminta deskripsi indoor berbahasa Indonesia yang jelas dan natural;
3. melarang klaim objek atau posisi yang tidak terlihat;
4. tidak meminta Gemma menebak angka jarak;
5. tidak mengaitkan angka sensor dengan objek yang dinamai model.

Kontribusi sensor dibentuk deterministik oleh backend sesudah deskripsi Gemma. Status paired menghasilkan referensi frontal; status conflict, stale, direction mismatch, dan unavailable menghasilkan penjelasan status tanpa angka rata-rata.

## Kontrak UI

UI final menampilkan:

- citra sumber;
- satu deskripsi gambar;
- status referensi sensor frontal;
- nilai sensor 1 dan sensor 2;
- rata-rata pasangan hanya bila `paired`;
- disagreement, umur/timestamp, dan alasan status pada detail teknis;
- waktu proses dan pesan error yang relevan.

UI tidak menampilkan angka sensor sebagai atribut objek bernama, peta jarak visual, atau klaim keamanan navigasi.

## Kontrak akses runtime

```text
Browser/HP
  -> https://api.mbridgegap.my.id
  -> Cloudflare Tunnel Windows service
  -> http://127.0.0.1:8000
  -> FastAPI
```

Origin FastAPI menggunakan HTTP dan bind ke `127.0.0.1:8000`. Akses eksternal memakai hostname tunnel, bukan alamat LAN langsung.

## Batas klaim akademik

Yang dapat diuji dan dilaporkan:

- kemampuan prototipe menghasilkan deskripsi Bahasa Indonesia pada dataset indoor yang ditetapkan;
- kesesuaian, kejelasan, dan kelengkapan deskripsi berdasarkan rubrik;
- error mentah tiap sensor terhadap `sensor_face_ground_truth_cm` serta error nilai terkoreksi terhadap `ground_truth_cm` beracuan kamera pada target planar terkendali;
- status sinkronisasi dan ketersediaan evidence sensor.

Yang tidak boleh diklaim dari evidence ini:

- angka sensor mengukur objek yang disebut Gemma;
- sensor merepresentasikan seluruh scene atau menghasilkan peta ruang;
- sistem aman untuk navigasi;
- deskripsi meningkatkan keselamatan atau kemandirian pengguna tertentu;
- prototipe terbukti unggul tanpa baseline dan desain evaluasi yang sesuai.

## Hirarki dokumen aktif

1. `CONTEXT.md` — istilah dan batas klaim;
2. `instructions/PROJECT_INITIALIZATION.md` — scope akademik dan implementasi;
3. `docs/architecture.md` — arsitektur dan kontrak data;
4. `docs/evaluation_protocol.md` — protokol pengujian;
5. `docs/DESIGN.md` — aturan UI;
6. `README.md` — setup dan penggunaan.
