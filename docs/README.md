# Indeks Dokumentasi Bridge-Gap

## Dokumen aktif

Dokumen berikut menentukan scope dan implementasi saat ini:

1. [`../CONTEXT.md`](../CONTEXT.md) — kamus istilah dan batas klaim.
2. [`../instructions/PROJECT_INITIALIZATION.md`](../instructions/PROJECT_INITIALIZATION.md) — judul kerja, rumusan masalah, tujuan, metode, dan acceptance criteria.
3. [`architecture.md`](architecture.md) — alur sistem, state evidence, serta kontrak API dan logging.
4. [`evaluation_protocol.md`](evaluation_protocol.md) — evaluasi sensor dan deskripsi yang dipisahkan.
5. [`DESIGN.md`](DESIGN.md) — aturan UI satu alur.
6. [`sensor_evaluation_template.csv`](sensor_evaluation_template.csv) — template data pengujian fisik HC-SR04.
7. [`../README.md`](../README.md) — setup dan penggunaan workspace.

Urutan acuan jika terjadi konflik mengikuti `../CONTEXT.md`.

## Pustaka penelitian

Folder [`pustaka/`](pustaka/) menyimpan salinan sumber dan indeks sitasi. Keberadaan file di folder tersebut tidak otomatis menjadikannya komponen sistem, variabel penelitian, atau sumber yang harus masuk daftar pustaka final. Hanya sumber yang dipakai dan diverifikasi yang boleh disitasi.

## Dokumen historis

Dokumen di folder `archive/`, laporan eksperimen lama, log, dan artefak hasil sebelumnya adalah bukti historis. Mereka tidak menentukan scope runtime aktif. Jangan menghapus atau menulis ulang bukti historis untuk menyamakan istilah baru; beri label tanggal dan status bila dirujuk.

Dokumen aktif tidak boleh mengambil klaim runtime hanya dari nama file historis atau hasil tes lama. Perilaku saat ini harus diverifikasi dari kode, konfigurasi, dan pengujian yang berjalan.

## Scope saat ini

Bridge-Gap menggunakan Gemma 4 E2B untuk deskripsi gambar indoor berbahasa Indonesia. Dua HC-SR04 menyediakan referensi jarak frontal berbasis cone. Rata-rata hanya dibentuk untuk pasangan valid, segar, searah, dan konsisten; nilai tidak diikat pada objek bernama. Evaluasi sensor memakai `ground_truth_cm` eksternal, sedangkan kualitas deskripsi dinilai pada jalur terpisah.
