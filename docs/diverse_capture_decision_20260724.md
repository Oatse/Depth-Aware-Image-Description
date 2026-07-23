# Keputusan Capture Dataset Beragam

Tanggal keputusan: 24 Juli 2026

## Rekomendasi

**Disarankan melakukan capture tambahan**, tetapi tidak dengan menambah atau
mengubah dataset v2. Dataset v2 dipertahankan sebagai seri jarak terkendali satu
objek. Capture baru menjadi dataset ekstensi, misalnya `dataset_v3_diverse`, setelah
protokolnya dikunci sebelum gambar pertama diambil.

Rekomendasi ini diperlukan jika judul dan rumusan masalah tetap membahas deskripsi
gambar indoor secara umum. Jika skripsi secara eksplisit dibatasi pada evaluasi
terkendali satu objek, capture tambahan tidak wajib, tetapi risiko pertanyaan penguji
tentang generalisasi tetap tinggi.

## Apa yang berubah

Capture tambahan mengubah unit bukti dari variasi jarak satu objek menjadi variasi
scene. Kalibrasi sensor tidak perlu diulang selama geometri kamera, dudukan sensor,
firmware, dan profil kalibrasi tidak berubah.

Dataset ekstensi harus:

- disimpan di area `results/captures/incoming/` selama pengumpulan;
- mempunyai ID scene/target eksplisit;
- memakai satu capture, satu snapshot sensor, dan satu job;
- menjalankan pasangan `gemma_only` dan `sensor_assisted`;
- memasukkan failed, conflict, stale, atau unavailable ke denominator;
- dibekukan ke folder, capture list, manifest, dan checksum baru;
- dinilai blind tanpa melihat mode, jarak, prompt, atau run ID.

## Desain minimum yang realistis

- 12 konfigurasi scene indoor unik;
- 2 pengulangan per konfigurasi;
- total 24 citra independen dan 48 run model;
- 2–5 objek tampak per scene;
- empat keluarga kondisi: ruang kerja, ruang santai, area penyimpanan, dan
  koridor/area transisi;
- variasi layout dan pencahayaan dicatat, bukan diubah setelah melihat output;
- rig kamera-sensor, resolusi, dan prompt tetap sama.

`ground_truth_cm` tetap mengacu pada bidang referensi kamera ke permukaan frontal
yang ditetapkan secara fisik, bukan ke objek yang disebut Gemma. Pada scene
multiobjek, susunan objek dan permukaan yang berada di cone sensor wajib dicatat.

Estimasi inferensi berdasarkan latency dataset v2 adalah sekitar 31 menit untuk 24
pasangan mode, belum termasuk capture, pemeriksaan provenance, dan scoring blind.

## Dampak terhadap nilai proyek

### Dampak positif

- mengurangi kelemahan eksternal-validity dari satu koper;
- memberi bukti bahwa pipeline bekerja pada komposisi visual yang lebih beragam;
- menguji apakah gate sensor tetap aman ketika cone menghadapi scene kompleks;
- memperkuat alasan penggunaan istilah “gambar indoor” pada judul;
- menyediakan contoh keberhasilan dan kegagalan yang lebih bermakna untuk Bab IV.

### Dampak dan risiko

- menambah 24 capture, 48 inferensi, scoring, dan validasi manifest;
- hasil dapat lebih buruk atau menghasilkan lebih banyak conflict; seluruhnya harus
  dilaporkan;
- karena keputusan dibuat setelah melihat dataset v2, analisis harus diberi label
  ekstensi konfirmatori/validasi tambahan, bukan seolah sudah direncanakan sejak awal;
- penggabungan skor v2 dan v3 tanpa stratifikasi akan mencampur dua desain berbeda.

## Dampak terhadap penulisan

Bab III perlu menambahkan subbagian protokol dataset ekstensi, kriteria scene, dan
kontrol bias. Bab IV harus memisahkan:

1. dataset v2 sebagai evaluasi jarak terkendali;
2. dataset beragam sebagai evaluasi eksternal-validity;
3. metrik sensor sebagai jalur terpisah.

Kesimpulan tetap tidak boleh menyatakan peningkatan kualitas oleh sensor. Capture
tambahan memperkuat cakupan pengujian sistem, bukan mengubah tujuan sensor
conditioning.

## Gate sebelum capture

Jangan mulai capture sampai daftar 12 scene, aturan inklusi/eksklusi, penamaan
target, kondisi pencahayaan, evaluator, rubrik, dan acceptance rule telah ditulis dan
dibekukan. Setelah capture dimulai, prompt dan rubrik tidak diubah berdasarkan hasil.
