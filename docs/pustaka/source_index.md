# Indeks Sumber Aktif Bridge-Gap

Indeks ini mengikuti arah Bridge-Gap aktif dan batas klaim pada `../../CONTEXT.md` per 22 Juli 2026. Folder `pustaka/` tetap berfungsi sebagai arsip penelitian; hanya sumber yang selaras dengan rumusan masalah aktif yang masuk daftar di bawah.

## Kelompok sumber aktif

### Gemma dan input multimodal

1. Google DeepMind, *Gemma 4 Model Card* — acuan kemampuan multimodal dan model Gemma 4 E2B: https://ai.google.dev/gemma/docs/core/model_card_4
2. Google, *Gemma multi-image inference example* — acuan pengiriman lebih dari satu gambar: https://ai.google.dev/gemma/docs/core/keras_inference
3. Gemma Team (2025), *Gemma 3 Technical Report* — rujukan lokal pendukung keluarga model Gemma; bukan pengganti dokumentasi Gemma 4. File: `2025-gemma-3-technical-report.pdf`.

### Estimasi kedalaman

4. Yang et al. (2024), *Depth Anything V2*, NeurIPS 2024. File: `2024-depth-anything-v2.pdf`.
5. Depth Anything V2 Metric Indoor Small model card (2024) — acuan checkpoint metric indoor. File: `2024-depth-anything-v2-metric-indoor-small-model-card.html`.
6. Bhat et al. (2023), *ZoeDepth* — penelitian pembanding monocular metric depth. File: `2023-zoedepth.pdf`.

### Deskripsi citra berbasis RGB dan depth

7. Wang et al. (2023), *Dense Captioning and Multidimensional Evaluations for Indoor Robotic Scenes*, Frontiers in Neurorobotics, DOI: 10.3389/fnbot.2023.1280501. File utama: `2023-rgbd2cap-frontiers.pdf`.
8. Baltrušaitis, Ahuja dan Morency (2019), *Multimodal Machine Learning: A Survey and Taxonomy*, IEEE TPAMI, DOI: 10.1109/TPAMI.2018.2798607.
9. Liu, Emerson dan Collier (2023), *Visual Spatial Reasoning*, TACL, DOI: 10.1162/tacl_a_00566. File: `2023-visual-spatial-reasoning-vsr.pdf`.
10. Chen et al. (2024), *SpatialVLM*, CVPR 2024. File: `2024-spatialvlm-cvpr.pdf`.
11. Cheng et al. (2024), *SpatialRGPT*, NeurIPS 2024. File: `2024-spatialrgpt.pdf`.

### Sensor HC-SR04

12. Komarizadehasl et al. (2022), *Low-Cost Sensors Accuracy Study and Enhancement Strategy*, Applied Sciences, DOI: 10.3390/app12063186.
13. Păpară et al. (2024), *Testing of Indoor Obstacle-Detection Prototypes Designed for Visually Impaired Persons*, Applied Sciences, DOI: 10.3390/app14051767. Ini sumber utama untuk indoor satu objek, bentuk target, material, dan posisi objek di dalam cone.
14. Téllez-Garzón et al. (2025), pengujian sensor jarak pada kondisi terkontrol, Ingeniería, DOI: 10.14483/23448393.22458.
15. Hunter (2023), *Analysis of the Measurement Error from a Low-Cost Ultrasonic Sensor*, Edward Waters University Undergraduate Research Journal, DOI: 10.62962/001c.87939.
16. Priadi et al. (2025), pengujian indoor HC-SR04 pada 25–70 cm, TESLA: Jurnal Teknik Elektro, DOI: 10.24912/tesla.v27i1.33372.
17. Estu Broto (2024), pengujian HC-SR04 terhadap dinding hingga 350 cm, Jurnal Sains Fisika: SAINFIS, DOI: 10.24252/sainfis.v4i1.41079. Gunakan sebagai pendukung rentang 120–200 cm pada target ideal, bukan bukti akurasi universal sampai 350 cm.

### Sensor HC-SR04 — sumber proxy dan implementasi

18. Widianto, Ikhsan dan Prasetijo (2021), *Rompi Penyedia Informasi bagi Penyandang Tunanetra Menggunakan Multisensor HC-SR04*, Jurnal Teknik Elektro, DOI: 10.15294/jte.v13i2.31112. Gunakan untuk arsitektur multisensor/sektor, bukan sebagai bukti pemisahan beberapa objek dalam satu cone.
19. Abreu et al. (2021), *Low-Cost Ultrasonic Range Improvements for an Assistive Device*, Sensors, DOI: 10.3390/s21124250. Gunakan untuk risiko interferensi dan sequential triggering; perangkatnya dimodifikasi sehingga hasil jarak minimum tidak langsung berlaku pada modul standar.
20. GaryDyr, *HC-SR04 Beam Tests* — bukti engineering untuk penyusunan variasi jarak dan permukaan: https://github.com/GaryDyr/HC-SR04-beam-tests

Aturan seleksi, kondisi objek tiap paper, batas klaim, dan paragraf siap adaptasi tersedia di `hcsr04_indoor_evidence_context.md`. Dokumen tersebut wajib diperiksa sebelum menulis bagian HC-SR04.

## Pemakaian per bab

- Bab I: masalah deskripsi citra indoor, informasi kedalaman, dan kebutuhan verifikasi jarak.
- Bab II: Gemma, multimodal fusion, Depth Anything V2, RGB-D captioning, dan HC-SR04.
- Bab III: konfigurasi model, input dua gambar, pengolahan raw depth, pengolahan dua sensor, dan metadata Hybrid Fusion.
- Bab IV: pembahasan kesalahan objek terdekat, estimasi jarak, pembacaan sensor, dan kualitas deskripsi.

## Aturan pustaka final

Daftar pustaka skripsi tetap harus dikembangkan menjadi minimum 20 sumber, menggunakan sumber sepuluh tahun terakhir, dan menjaga proporsi sekitar 70% artikel ilmiah serta maksimum 30% sumber lain sesuai pedoman Gunadarma. Dokumentasi resmi, model card, dan repository engineering digunakan sebagai sumber implementasi, bukan pengganti jurnal metodologis.
