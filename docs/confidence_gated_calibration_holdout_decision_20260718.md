# Keputusan Calibration dan Held-Out Alternatif 1

Tanggal: 18 Juli 2026  
Run ID: `cgsp-calibration-holdout-20260718-v1`

## Putusan Singkat

**Lanjut hanya ke desain protokol final; jangan mempromosikan Alternatif 1 sebagai metode yang sudah terbukti efektif.**

Run ini menunjukkan bahwa mekanisme confidence-gated spatial description dapat dikalibrasi tanpa melihat held-out label, berjalan pada resource lokal, dan menghasilkan coverage-risk trade-off yang tidak degeneratif. Namun, interval bootstrap masih memotong nol, akurasi joint tetap rendah, dan data tidak scene-stratified.

## Pemisahan Data

- Calibration: 20 indeks sistematis.
- Held-out: 20 indeks berbeda yang ditentukan sebelum run.
- Sampel pilot sebelumnya, indeks 0-5, dikeluarkan.
- Source shard: `sayakpaul/nyu_depth_v2`, revision `67602a2e747bf4f55f90ff2e724173fc10302843`.
- Schema source tidak memiliki scene ID. Karena itu sampling disebut systematic spread, bukan scene-stratified.

## Pemilihan Gate

Grid 27 konfigurasi ditetapkan sebelum inferensi:

- nearest-region agreement: 0,60; 0,80; 1,00;
- distance-category agreement: 0,60; 0,80; 1,00;
- relative-MAD: 0,05; 0,12; 0,20.

Objective calibration: selective risk minimum dengan coverage 0,50-0,90. Tie-breaker: coverage lebih tinggi, agreement lebih tinggi, lalu relative-MAD lebih rendah.

Konfigurasi yang dipilih:

```json
{
  "minimum_nearest_region_agreement": 1.0,
  "minimum_distance_category_agreement": 0.6,
  "maximum_relative_mad": 0.05
}
```

Calibration coverage 0,60 dan selective risk 0,4167.

## Hasil Held-Out

| Metrik | Always-fuse | Confidence-gated |
|---|---:|---:|
| Coverage | 1,00 | 0,60 |
| Joint accuracy | 0,25 | 0,3333 pada klaim terbit |
| Selective risk | 0,75 | 0,6667 |
| Error capture | N/A | 7/15 = 0,4667 |
| False rejection | N/A | 1/5 = 0,20 |

Risk difference gated minus always-fuse adalah `-0,0833`. Bootstrap snapshot 95% interval adalah `[-0,25; 0,0667]`, sehingga belum mendukung pernyataan penurunan risiko yang konsisten.

Seluruh 200 panggilan depth berhasil. Total waktu inferensi depth 156,292 detik dan total wall time 346,225 detik, termasuk pembacaan shard remote.

## Interpretasi

### Positif

1. Pemilihan threshold tidak menggunakan held-out labels.
2. Gate menghasilkan coverage 60%, bukan abstain total atau menerbitkan semuanya.
3. Gate menangkap 7 dari 15 joint error always-fuse.
4. False rejection pada held-out adalah 20%.
5. Sistem dapat berjalan tanpa training pada checkpoint lokal.

### Negatif

1. Always-fuse joint accuracy hanya 25% pada held-out.
2. Gated joint accuracy pada klaim yang lolos hanya 33,33%.
3. Risk reduction hanya 8,33 poin persentase dan intervalnya melewati nol.
4. Gate lebih banyak menjadi abstention policy daripada verifier kebenaran.
5. Kesalahan regional yang konsisten tetap dapat lolos.
6. Tidak ada VLM, sehingga belum ada bukti bahwa gating memperbaiki deskripsi bahasa.
7. Sampling tidak scene-stratified dan threshold near/mid/far tidak dikalibrasi ulang.

## Keputusan terhadap Alternatif 1

Alternatif 1 **layak sebagai arah eksperimen**, tetapi belum layak sebagai klaim utama skripsi. Bukti saat ini cukup untuk membenarkan desain final yang lebih disiplin, bukan untuk menyimpulkan bahwa confidence-gated depth meningkatkan image description.

Jika dipilih sebagai skripsi, protokol final wajib:

1. memakai split scene atau sequence yang benar-benar independen;
2. menyediakan metadata scene, perangkat, dan provenance;
3. menguji threshold kategori pada calibration split terpisah;
4. mempertahankan held-out test yang tidak disentuh;
5. menambahkan evaluasi output VLM setelah gate;
6. melaporkan coverage, selective risk, false rejection, error capture, latency, dan failure case systematic;
7. tetap membatasi klaim pada region depth, bukan jarak objek atau navigasi aman.

Jika final test kembali menunjukkan risk reduction kecil dengan interval yang melintasi nol, Alternatif 1 sebaiknya diposisikan sebagai studi evaluasi trade-off atau dihentikan sebagai topik utama.

## Artefak

- [Protokol calibration-holdout](D:/Tugas/SKRIPSI/Bride-Gap/Program/prototypes/confidence_gated_spatial_pilot/calibration_holdout_protocol.json)
- [Frozen gate](D:/Tugas/SKRIPSI/Bride-Gap/Program/results/prototypes/confidence_gated_spatial_calibration_holdout_20260718/frozen_holdout_gate.json)
- [Calibration candidates](D:/Tugas/SKRIPSI/Bride-Gap/Program/results/prototypes/confidence_gated_spatial_calibration_holdout_20260718/calibration_candidates.csv)
- [Held-out decisions](D:/Tugas/SKRIPSI/Bride-Gap/Program/results/prototypes/confidence_gated_spatial_calibration_holdout_20260718/holdout_decisions.csv)
- [Summary JSON](D:/Tugas/SKRIPSI/Bride-Gap/Program/results/prototypes/confidence_gated_spatial_calibration_holdout_20260718/summary.json)
- [Pilot report](D:/Tugas/SKRIPSI/Bride-Gap/Program/results/prototypes/confidence_gated_spatial_calibration_holdout_20260718/REPORT.md)

