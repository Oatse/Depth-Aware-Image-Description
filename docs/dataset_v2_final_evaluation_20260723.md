# Evaluasi final dataset v2 — paket reanalisis

Sumber angka dan batas klaim utama berada di
`results/captures/dataset_v2_reanalysis_final_report_20260723.md`.

## Status

- Integritas dataset: valid, 18/18 capture.
- Inferensi baseline: 18/18 selesai.
- Inferensi sensor-conditioned: 18/18 selesai.
- Evaluasi visual: 36/36 item selesai dan dikunci sebelum unblinding.
- Unit perbandingan: 18 pasangan citra.
- UAT: tidak dilakukan.

## Keputusan

Tidak ada bukti pada dataset ini bahwa `sensor_assisted` meningkatkan kualitas
deskripsi dibandingkan `gemma_only`. Delta skor keseluruhan adalah -0,0778 dengan
bootstrap 95% CI [-0,2222; 0,0556], sedangkan latency bertambah rata-rata 26,41%.

Hasil tersebut bukan kegagalan tujuan sensor. Tujuan eksperimen adalah mengamati
pengaruh konteks frontal terverifikasi terhadap keluaran, latency, dan provenance,
bukan menetapkan peningkatan kualitas sebagai syarat keberhasilan. Skor kualitas
berfungsi sebagai pengaman non-degradasi dan tetap dilaporkan tanpa seleksi.

Referensi frontal HC-SR04 tetap layak dilaporkan sebagai jalur bukti terpisah.
Ia tidak boleh ditempelkan sebagai jarak ke objek yang disebut Gemma.

## Implikasi untuk skripsi

Framing yang aman adalah evaluasi teknis deskripsi visual-spasial indoor dan
referensi sensor frontal dengan provenance terpisah. Jangan menulis bahwa integrasi
sensor terbukti memperbaiki deskripsi, meningkatkan keselamatan, atau membantu
pengguna tertentu. Temuan negatif dan overhead latency harus dipertahankan.
