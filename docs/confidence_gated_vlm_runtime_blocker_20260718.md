# VLM Runtime Gate Audit

Tanggal: 18 Juli 2026  
Protocol: `cgsp-final-candidate-vlm-20260718-v1`

## Temuan

LM Studio endpoint merespons HTTP 200 dan mendaftarkan `google/gemma-4-e4b`. Controlled VLM runner memulai evaluasi 20 held-out images dengan satu panggilan per image. Dua panggilan pertama selesai, tetapi masing-masing membutuhkan kira-kira tiga menit. Proses dihentikan sebelum image ketiga karena estimasi waktu total sekitar satu jam.

Tidak ada CSV final yang diterbitkan oleh runner karena artefak ditulis setelah seluruh loop selesai. Dua respons parsial tidak diperlakukan sebagai hasil evaluasi.

## Makna

Ini adalah kegagalan feasibility runtime untuk konfigurasi `gemma-4-e4b` dan protocol tersebut. Ini bukan bukti bahwa confidence-gated spatial claim tidak valid. Namun, konfigurasi tersebut tidak cocok untuk controlled VLM evaluation lokal pada 20 image tanpa perubahan serving/model.

Mengganti model, max tokens, prompt, atau jumlah sampel setelah melihat latency harus diperlakukan sebagai protokol baru. Probe model `gemma-4-e2b` dijalankan terpisah sebagai audit resource, bukan sebagai data final `gemma-4-e4b`.

## Batas Klaim

- Depth calibration dan held-out depth result tetap valid karena tidak bergantung pada VLM.
- VLM quality, structured JSON rate, dan repeat variation belum tervalidasi pada 20 image.
- Tidak boleh menulis bahwa baseline dan gated caption sudah dibandingkan secara final.

