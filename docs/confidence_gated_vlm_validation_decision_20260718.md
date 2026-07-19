# Keputusan Validasi VLM Alternatif 1

Tanggal: 18 Juli 2026  
Protocol: `cgsp-final-candidate-vlm-20260718-v1`

## Putusan

**Controlled VLM evaluation belum dapat diselesaikan pada runtime saat ini.** Depth calibration, held-out evaluation, dan kontrak fusion tetap tervalidasi; validasi kualitas deskripsi VLM tidak boleh dianggap selesai.

## Yang Dijalankan

1. Protocol VLM baru dibekukan sebelum inference.
2. Endpoint LM Studio menjawab HTTP 200 dan mendaftarkan `google/gemma-4-e4b`.
3. Controlled runner memulai 20 held-out images dengan satu panggilan VLM per image.
4. Dua panggilan pertama selesai, masing-masing membutuhkan kira-kira tiga menit.
5. Proses dihentikan sebelum image ketiga karena proyeksi total sekitar satu jam.
6. Probe terpisah pada `google/gemma-4-e2b` untuk satu image menghasilkan error setelah 20,7 detik dalam batas 90 detik.

## Mengapa Tidak Dianggap Hasil Final

Runner hanya menulis CSV dan summary setelah seluruh loop selesai. Karena run dihentikan, tidak ada artefak VLM 20-image yang sah. Dua respons parsial tidak dijadikan dataset evaluasi.

Mengubah model, prompt, `max_tokens`, atau jumlah image setelah melihat latency akan menjadi protocol baru. Saya tidak melakukan perubahan tersebut pada run ini.

## Dampak terhadap Validasi Alternatif 1

### Sudah tervalidasi

- Depth gate berjalan pada 200/200 call.
- Calibration dan held-out dipisahkan.
- Gate menghasilkan coverage 60% dan risk held-out 66,67% versus always-fuse 75%.
- 83 test suite lulus setelah penambahan runner dan kontrak.
- Fusion menggunakan output VLM yang sama secara desain ketika VLM tersedia.

### Belum tervalidasi

- VLM success rate pada 20 image.
- Structured JSON rate final.
- Repeat variation final.
- Latency p50/p95 VLM pada seluruh held-out set.
- Kualitas bahasa baseline versus gated.
- Dampak depth claim terhadap deskripsi VLM secara statistik.

## Keputusan Penelitian

Alternatif 1 belum dapat dipromosikan sebagai sistem image-description lengkap. Bukti yang ada hanya mendukung klaim lebih sempit:

> Mekanisme regional depth gate dapat dioperasionalkan dan diuji terhadap ground-truth depth, tetapi integrasi VLM lokal belum feasible untuk controlled evaluation 20 image pada konfigurasi Gemma yang tersedia.

Untuk melanjutkan VLM secara sah, perlu salah satu perubahan eksternal yang dipreregistrasikan baru: serving stack yang lebih cepat, model yang benar-benar dapat dipanggil, atau desain sample size yang lebih kecil untuk smoke validation. Tidak boleh mengubah parameter lalu memakai hasilnya sebagai bukti yang sama.

## Artefak

- [Candidate final protocol](D:/Tugas/SKRIPSI/Bride-Gap/Program/docs/final_protocol_confidence_gated_v1_20260718.md)
- [Frozen protocol JSON](D:/Tugas/SKRIPSI/Bride-Gap/Program/prototypes/confidence_gated_spatial_pilot/final_vlm_protocol.json)
- [VLM runner](D:/Tugas/SKRIPSI/Bride-Gap/Program/prototypes/confidence_gated_spatial_pilot/run_final_vlm_validation.py)
- [E2B runtime probe](D:/Tugas/SKRIPSI/Bride-Gap/Program/results/prototypes/confidence_gated_vlm_validation_20260718/runtime_probe_e2b.json)
- [Runtime blocker report](D:/Tugas/SKRIPSI/Bride-Gap/Program/docs/confidence_gated_vlm_runtime_blocker_20260718.md)

