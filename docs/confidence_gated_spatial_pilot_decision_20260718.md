# Keputusan Pilot Confidence-Gated Spatial Description

Tanggal run: 18 Juli 2026  
Pilot ID: `cgsp-nyuv2-20260718-v1`  
Putusan: **lanjut hanya ke calibration pilot; belum layak menjadi eksperimen skripsi final**.

## Pertanyaan Pilot

Apakah confidence proxy berbasis konsistensi transformasi dapat dioperasionalkan, menghasilkan coverage yang tidak degeneratif, dan menurunkan selective risk klaim region-kedalaman dibanding kebijakan yang selalu menerbitkan klaim?

Pilot tidak menguji kualitas caption VLM, jarak objek, navigasi, keselamatan, atau pengguna tertentu. Cabang deskripsi citra sengaja tidak dipanggil karena identik untuk semua kebijakan. Unit yang diuji adalah izin menerbitkan metadata spasial regional.

## Protokol Beku

- Data: enam pasangan RGB-depth pertama dari shard validasi konversi NYU Depth V2 `sayakpaul/nyu_depth_v2`, revision `67602a2e747bf4f55f90ff2e724173fc10302843`.
- Model: checkpoint lokal Depth Anything V2 Metric Indoor Small, ONNX Runtime CPU.
- Transformasi: original, brightness 0,60, brightness 1,40, Gaussian blur radius 2,0, dan JPEG quality 40.
- Gate: nearest-region agreement minimal 0,80; distance-category agreement minimal 0,80; relative-MAD maksimal 0,12.
- Kebijakan: `no_depth`, `always_fuse`, dan `confidence_gated`.
- Ground truth: peta depth sejajar dari dataset, diringkas dengan grid dan fungsi kategori yang sama.
- Tidak ada training atau fine-tuning.

Hash protokol: `995e39ea9c873afee2adeaf3baf14a448fbe35b2e956ab265c46d8f16df2224d`.

## Hasil Mekanis

| Ukuran | Hasil |
|---|---:|
| Sampel lengkap | 6/6 |
| Inferensi depth berhasil | 30/30 |
| Total latency depth | 24,254 detik |
| Rerata per panggilan depth | 0,808 detik |
| Approximate depth cost per image untuk 5 transformasi | 4,042 detik |
| Always-fuse nearest-region accuracy | 5/6 = 0,8333 |
| Always-fuse distance-category accuracy | 5/6 = 0,8333 |
| Always-fuse joint accuracy | 4/6 = 0,6667 |
| Always-fuse selective risk | 2/6 = 0,3333 |
| Confidence-gated coverage | 4/6 = 0,6667 |
| Confidence-gated joint accuracy pada klaim terbit | 3/4 = 0,7500 |
| Confidence-gated selective risk | 1/4 = 0,2500 |

Seluruh feasibility gate yang ditetapkan sebelum inferensi lulus: semua panggilan berhasil, coverage berada dalam rentang 0,20-0,90, gated risk tidak lebih buruk daripada always-fuse, dan latency berada di bawah batas pilot 180 detik.

## Audit Perilaku Gate

- Sampel 3: klaim always-fuse salah dan ditolak karena kategori berubah pada transformasi. Ini merupakan error capture yang diharapkan.
- Sampel 4: klaim original benar, tetapi ditolak karena kategori tidak stabil. Ini false rejection dan menjadi harga coverage.
- Sampel 5: klaim salah tetapi stabil pada semua transformasi sehingga tetap diterbitkan. Ini membuktikan bahwa konsistensi tidak sama dengan kebenaran.

Gate menangkap satu dari dua joint error, menolak satu dari empat klaim original yang benar, dan melewatkan satu systematic error. Penurunan risk sebesar 0,0833 hanya berasal dari satu perubahan keputusan pada enam sampel. Angka tersebut tidak mempunyai kekuatan untuk mendukung superiority claim.

## Keputusan Akademik

### Yang sudah terbukti

1. Dataset RGB-depth dapat diakses dan inputnya sejajar.
2. Model lokal dapat menjalankan 30 inferensi tanpa error pada resource saat ini.
3. Confidence proxy, coverage, dan selective risk dapat dihitung secara reproducible.
4. Gate tidak menerima atau menolak seluruh sampel.
5. Ada satu contoh nyata ketika instability signal menahan klaim yang salah.

### Yang belum terbukti

1. Gate secara statistik menurunkan risiko.
2. Threshold berlaku lintas scene atau perangkat.
3. Transformasi sintetis mewakili gangguan kamera nyata.
4. Kategori threshold yang diwarisi dari proyek cocok untuk distribusi NYU Depth V2.
5. Gate memperbaiki kualitas deskripsi bahasa.
6. Sistem dapat mendeteksi systematic depth bias.
7. Metadata region dapat diatribusikan kepada objek tertentu.

## Kekurangan Metodologis

- Enam sampel pertama berurutan bukan sampel representatif atau scene-stratified.
- Sumber yang dipakai merupakan konversi Hugging Face tidak resmi dari NYU Depth V2; eksperimen final perlu mengunci provenance dan memvalidasi skala depth terhadap sumber resmi.
- Threshold kategori belum dikalibrasi pada split NYU yang terpisah.
- Ground-truth depth dan prediction diringkas dengan p10 yang sama. Ini konsisten untuk perbandingan, tetapi belum membuktikan bahwa p10 adalah statistik terbaik untuk bahasa spasial.
- Lima kali inferensi depth menambah biaya sekitar lima kali dibanding satu depth pass.
- Gate berbasis konsistensi hanya sensitif terhadap instability. Kesalahan yang konsisten tetap dapat lolos.
- Tidak ada VLM pada pilot ini. Penelitian final tetap perlu menunjukkan bagaimana accepted/rejected spatial claims memengaruhi keluaran deskripsi tanpa menjadikan LLM judge sebagai bukti primer.

## Syarat Melanjutkan

Langkah berikutnya bukan eksperimen final, melainkan calibration pilot baru dengan identitas protokol baru:

1. Ambil 30-50 sampel yang scene-stratified, bukan baris berurutan.
2. Pisahkan calibration dan held-out test sebelum melihat hasil.
3. Tentukan threshold kategori dan gate hanya pada calibration split.
4. Bekukan transformasi, threshold, prompt, model hash, dan exclusion criteria sebelum test.
5. Laporkan coverage-risk curve, joint claim accuracy, latency p50/p95, false rejection, error capture, dan failure case sistematis.
6. Pertahankan klaim pada region depth; jangan mengubahnya menjadi jarak objek tanpa box/mask dan object-depth correspondence.
7. Bandingkan biaya tiga transformasi versus lima transformasi pada calibration split, kemudian pilih satu konfigurasi sebelum held-out test.

Jika calibration pilot menunjukkan coverage selalu mendekati 0 atau 1, gated risk tidak lebih baik, atau systematic error tetap dominan, Alternatif 1 harus dihentikan. Jika sinyal bertahan pada held-out test dengan interval ketidakpastian yang layak, barulah alternatif ini dapat dipertimbangkan sebagai inti penelitian.

## Artefak

- Protokol sumber: `prototypes/confidence_gated_spatial_pilot/protocol.json`
- Runner: `prototypes/confidence_gated_spatial_pilot/run_pilot.py`
- Unit test: `tests/test_confidence_gated_spatial_pilot.py`
- Hasil: `results/prototypes/confidence_gated_spatial_pilot_20260718/`
- Test suite setelah implementasi: `79 passed`.

