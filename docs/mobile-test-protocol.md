# Protokol uji HP

1. Hubungkan HP dan PC ke Wi-Fi yang sama.
2. Tempatkan certificate lokal yang dipercaya HP di `certs/`, lalu jalankan `scripts/start_mobile.ps1`.
3. Buka URL HTTPS LAN yang ditampilkan script. Jangan gunakan URL HTTP untuk kamera.
4. Pastikan system status dan `/readiness` menampilkan model LM Studio loaded, depth ready, dua sensor paired, secure context, dan profile kalibrasi validated.
5. Izinkan kamera, pilih Kamera, gunakan kamera belakang, lalu pastikan dua nilai sensor tampil dan state berubah menjadi `Dua sensor paired`.
6. Ambil frame. Untuk kamera depan, mode IoT harus disabled dengan alasan direction mismatch.
7. Jalankan analisis tunggal atau Bandingkan mode. Pastikan tiga mode comparison memakai capture ID yang sama dan kolom IoT menjelaskan evidence atau reason code.
8. Cabut serial sebentar, pastikan UI menampilkan unavailable/reconnect tanpa restart backend; sambungkan kembali dan ulangi capture.

Catat tanggal, device/browser, facing mode, capture ID, status sensor, latency, analysis run ID, dan error. Jangan masukkan private key, raw image, atau PII ke repository.
