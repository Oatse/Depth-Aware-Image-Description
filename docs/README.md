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
8. [`dataset_v2_final_evaluation_20260723.md`](dataset_v2_final_evaluation_20260723.md) — keputusan hasil evaluasi final.
9. [`project_maturity_report_20260724.md`](project_maturity_report_20260724.md) — status penyelesaian terbaru.
10. [`diverse_capture_decision_20260724.md`](diverse_capture_decision_20260724.md) — dampak dan gate dataset ekstensi beragam.

Urutan acuan jika terjadi konflik mengikuti `../CONTEXT.md`.

## Pustaka penelitian

Folder [`pustaka/`](pustaka/) menyimpan salinan sumber dan indeks sitasi. Keberadaan file di folder tersebut tidak otomatis menjadikannya komponen sistem, variabel penelitian, atau sumber yang harus masuk daftar pustaka final. Hanya sumber yang dipakai dan diverifikasi yang boleh disitasi.

## Artefak hasil

Hanya paket evaluasi final dataset v2 di `../results/captures/` yang menjadi hasil
aktif. Log runtime, eksperimen depth lama, perbandingan model yang dihentikan, dan
hasil evaluasi sebelum reanalisis tidak menjadi bagian baseline penelitian. Riwayat
perubahan tetap tersedia melalui Git; workspace aktif tidak menyimpan duplikat
artefak lama.

## Scope saat ini

Bridge-Gap menggunakan Gemma 4 E2B untuk deskripsi gambar indoor berbahasa Indonesia. Dua HC-SR04 menyediakan referensi jarak frontal berbasis cone. Rata-rata hanya dibentuk untuk pasangan valid, segar, searah, dan konsisten; nilai tidak diikat pada objek bernama. Contribution `applied` dapat mengondisikan prompt, sedangkan backend tetap menambahkan bagian sensor berprovenance. Evaluasi mengamati pengaruh konteks tanpa mengasumsikan peningkatan kualitas; metrik sensor tetap dilaporkan terpisah.
