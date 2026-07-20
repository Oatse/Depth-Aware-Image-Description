# Protokol uji HP

1. Hubungkan HP dan PC ke Wi-Fi yang sama.
2. Tempatkan certificate lokal yang dipercaya HP di `certs/`, lalu jalankan `scripts/start_mobile.ps1`.
3. Buka URL HTTPS LAN yang ditampilkan script. Jangan gunakan URL HTTP untuk kamera.
4. Izinkan kamera, pilih Kamera, gunakan kamera belakang, lalu pastikan dua nilai sensor tampil dan state berubah menjadi `Dua sensor paired`.
5. Buka **Kalibrasi jarak sensor**. Hadapkan kedua sensor ke bidang datar dan catat minimal tiga jarak fisik berbeda, misalnya 30, 60, dan 90 cm. Jangan memasukkan angka sensor sebagai jarak referensi; ukur dengan penggaris atau meteran terpisah.
6. Pastikan status kalibrasi menjadi `Valid` dengan residual maksimum tidak lebih dari 10 cm. Jika gagal, reset lalu periksa posisi target, sudut sensor, dan pengukuran referensi.
7. Pastikan system status dan `/readiness` menampilkan Gemma `google/gemma-4-e2b`, depth ready, dua sensor paired, secure context, serta profil kalibrasi validated.
8. Ambil frame. Untuk kamera depan, mode IoT harus disabled dengan alasan direction mismatch.
9. Jalankan analisis tunggal atau Bandingkan mode. Pastikan tiga mode comparison memakai capture ID yang sama dan kolom IoT menjelaskan evidence atau reason code.
10. Cabut serial sebentar, pastikan UI menampilkan unavailable/reconnect tanpa restart backend; sambungkan kembali dan ulangi capture.

Catat tanggal, device/browser, facing mode, capture ID, status sensor, latency, analysis run ID, dan error. Jangan masukkan private key, raw image, atau PII ke repository.
