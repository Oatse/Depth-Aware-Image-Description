# Indeks Sumber Aktif Bridge-Gap

Indeks ini mengikuti arah kanonik pada `../../CONTEXT.md` per 23 Juli 2026: deskripsi gambar indoor berbahasa Indonesia menggunakan Gemma 4 E2B dan referensi jarak frontal terpisah dari dua HC-SR04. Folder `pustaka/` tetap merupakan arsip penelitian; keberadaan file tidak otomatis menjadikannya sumber aktif atau komponen sistem.

## Sumber aktif

### Gemma dan deskripsi citra

1. Google DeepMind, *Gemma 4 Model Card* — sumber resmi kemampuan dan batas model Gemma 4: https://ai.google.dev/gemma/docs/core/model_card_4
2. Google, *Gemma multi-image inference example* — referensi implementasi input multimodal: https://ai.google.dev/gemma/docs/core/keras_inference
3. Gemma Team (2025), *Gemma 3 Technical Report* — konteks ilmiah keluarga model, bukan pengganti dokumentasi Gemma 4. File: `2025-gemma-3-technical-report.pdf`.
4. Gurari et al. (2018), *VizWiz Grand Challenge* — konteks evaluasi visual question answering untuk pengguna tunanetra. File: `2018-vizwiz-grand-challenge-blind-vqa.pdf`.
5. Liu, Emerson, dan Collier (2023), *Visual Spatial Reasoning* — landasan hubungan spasial visual. File: `2023-visual-spatial-reasoning-vsr.pdf`.

### HC-SR04 dan evaluasi jarak frontal

6. Komarizadehasl et al. (2022), *Low-Cost Sensors Accuracy Study and Enhancement Strategy*, Applied Sciences, DOI: 10.3390/app12063186.
7. Hunter (2023), *Analysis of the Measurement Error from a Low-Cost Ultrasonic Sensor*, Edward Waters University Undergraduate Research Journal, DOI: 10.62962/001c.87939.
8. Păpară et al. (2024), *Testing of Indoor Obstacle-Detection Prototypes Designed for Visually Impaired Persons*, Applied Sciences, DOI: 10.3390/app14051767.
9. Estu Broto (2024), pengujian HC-SR04 terhadap dinding hingga 350 cm, Jurnal Sains Fisika: SAINFIS, DOI: 10.24252/sainfis.v4i1.41079. Gunakan hanya sebagai bukti target ideal frontal, bukan akurasi universal.
10. Téllez-Garzón et al. (2025), pengujian sensor jarak pada kondisi terkontrol, Ingeniería, DOI: 10.14483/23448393.22458.
11. Priadi et al. (2025), pengujian indoor HC-SR04 pada 25–70 cm, TESLA: Jurnal Teknik Elektro, DOI: 10.24912/tesla.v27i1.33372.
12. Widianto, Ikhsan, dan Prasetijo (2021), *Rompi Penyedia Informasi bagi Penyandang Tunanetra Menggunakan Multisensor HC-SR04*, Jurnal Teknik Elektro, DOI: 10.15294/jte.v13i2.31112. Gunakan untuk arsitektur multisensor/sektor, bukan pemisahan beberapa objek dalam satu cone.
13. Abreu et al. (2021), *Low-Cost Ultrasonic Range Improvements for an Assistive Device*, Sensors, DOI: 10.3390/s21124250. Gunakan untuk risiko interferensi dan sequential triggering.

Aturan seleksi, kondisi objek, batas interpretasi, dan daftar sumber yang lebih lengkap tersedia di `hcsr04_indoor_evidence_context.md`. Dokumen tersebut wajib diperiksa sebelum menulis bagian HC-SR04.

## Sumber arsip, bukan arah aktif

File tentang Depth Anything V2, ZoeDepth, RGB-D captioning, SpatialRGPT, SpatialVLM, COMFORT, dan sistem navigasi tetap disimpan sebagai jejak kajian terdahulu. Mereka tidak menentukan pipeline aktif, variabel penelitian, atau klaim Bridge-Gap saat ini.

Secara khusus:

- Depth Anything V2 tidak lagi menjadi komponen runtime;
- depth map tidak menjadi ground truth HC-SR04;
- referensi sensor tidak diikat ke objek yang dinamai Gemma;
- tidak ada klaim navigasi atau keselamatan mobilitas.

## Pemakaian per bab

- Bab I: masalah deskripsi citra indoor dan kebutuhan informasi frontal tambahan dengan batas klaim eksplisit.
- Bab II: image description, Gemma, hubungan spasial visual, HC-SR04, time of flight, serta penelitian terdahulu yang benar-benar dipakai.
- Bab III: citra RGB ke Gemma, akuisisi dua sensor, pencocokan waktu, kalibrasi terhadap ground truth eksternal, dan pemisahan provenance.
- Bab IV: kualitas deskripsi dan akurasi sensor dilaporkan sebagai dua evaluasi terpisah.

## Aturan pustaka final

Daftar pustaka final harus memenuhi ketentuan Gunadarma yang telah diverifikasi pada dokumen pedoman yang berlaku. Sumber resmi, model card, datasheet, dan repository engineering dipakai untuk keputusan implementasi, bukan menggantikan artikel ilmiah metodologis. Hanya sumber yang benar-benar dibaca dan mendukung argumen naskah yang masuk daftar pustaka final.
