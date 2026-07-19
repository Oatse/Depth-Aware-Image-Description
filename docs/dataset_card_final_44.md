# Dataset Card: Final Indoor 44

Status: artefak proof-of-concept lokal, snapshot 14 Juli 2026.

## Identitas

- Citra: `dataset/final_images/` (44 file).
- Anotasi: `dataset/final_annotations.csv` (44 baris).
- Manifest: `dataset/final_manifest.csv` (path asal, path final, SHA-256, kategori jarak, dan label obstacle).
- Komposisi: 30 citra `original_30` dan 14 citra `sample_new_balancing_medium_far`.
- Unit analisis: satu citra indoor statis.
- Tujuan: evaluasi proof-of-concept deskripsi visual-spasial dan post-processing kedalaman; bukan train set dan bukan benchmark publik.

## Distribusi Label

| Label | Jumlah |
|---|---:|
| `sangat_dekat` | 2 |
| `dekat` | 25 |
| `sedang` | 10 |
| `jauh` | 7 |
| `has_obstacle=yes` | 27 |
| `has_obstacle=no` | 17 |
| confidence `medium` | 40 |
| confidence `low` | 4 |
| confidence `high` | 0 |

Distribusi tersebut tidak seimbang. Karena itu obstacle accuracy harus dibaca bersama precision, recall, F1, dan confusion matrix. `annotation_confidence` adalah penilaian subjektif anotator saat membuat label, bukan probabilitas terkalibrasi atau bukti reliabilitas. Ketiadaan confidence `high` memperkuat alasan untuk tidak memosisikan label sebagai pengukuran fisik.

## Skema dan Makna Ground Truth

`distance_annotation_basis=visual_relative` berarti kategori jarak ditentukan dari dominasi foreground, perspektif kamera, dan posisi relatif dalam citra. Tidak ada pengukuran meter, kamera terkalibrasi, sensor RGB-D, ToF, atau LiDAR. Kolom `notes` mendokumentasikan keputusan anotasi dan bukan reference caption.

Checkpoint Depth Anything yang dipakai bertipe metric-indoor, tetapi eksperimen hanya mengevaluasi kategori visual relatif. Dengan demikian, penelitian tidak membuktikan akurasi kedalaman metrik checkpoint dan tidak boleh melaporkan threshold internal sebagai meter ground truth.

## Provenance dan Integritas

Manifest menyimpan SHA-256 untuk setiap citra final agar perubahan file dapat dideteksi. Namun, metadata izin redistribusi, consent, perangkat kamera, lokasi/bangunan, tinggi kamera, focal length, dan kondisi pencahayaan belum dicatat secara konsisten. Dataset sebaiknya tidak dipublikasikan keluar repo sebelum hak penggunaan dan privasi diverifikasi.

## Risiko Bias dan Validitas

- Dataset lokal kecil dan tidak mewakili populasi bangunan indoor secara umum.
- Penambahan 14 citra memang menyeimbangkan kategori sedang/jauh, tetapi proses seleksi terarah dapat menimbulkan selection bias.
- Belum ada train/validation/test split karena model tidak dilatih pada dataset ini; seluruh 44 citra dipakai sebagai evaluation set PoC.
- Belum ada anotator kedua atau inter-annotator agreement, sehingga variasi subjektif label belum terukur.
- Kategori `dekat` dominan, sedangkan `sangat_dekat` hanya dua citra.
- Tidak ada `reference_description` independen, sehingga dataset ini tidak mendukung evaluasi leksikal berbasis reference caption.
- Dataset yang sama pernah dipakai untuk memeriksa kandidat adaptive bands; hasilnya hanya menjadi dasar menghapus kandidat yang memburuk, bukan untuk memilih parameter baru atau mengklaim peningkatan.

## Pemeriksaan Subgroup Temporal

Threshold kategori depth ditetapkan pada 30 citra awal sebelum 14 citra tambahan tersedia. Karena itu `sample_new_balancing_medium_far` dapat dibaca sebagai subgroup temporal yang belum terlihat saat kalibrasi, tetapi bukan test set independen murni karena proses seleksinya terarah dan seluruh analisis berlangsung dalam proyek yang sama.

| Subgroup | n | Distance accuracy | Obstacle accuracy |
|---|---:|---:|---:|
| `original_30` | 30 | 76,67% | 86,67% |
| `sample_new_balancing_medium_far` | 14 | 50,00% | 78,57% |
| Keseluruhan | 44 | 68,18% | 84,09% |

Penurunan pada 14 citra tambahan menunjukkan sensitivitas threshold terhadap distribusi data. Hasil ini adalah bukti keterbatasan generalisasi internal, bukan alasan untuk mengubah label atau menala ulang threshold pada seluruh 44 citra.

## Penggunaan yang Diizinkan Secara Metodologis

Dataset dapat dipakai untuk membandingkan mode pipeline pada gambar yang sama, menghitung metrik kategori spasial, menganalisis failure case, dan mendemonstrasikan integrasi software. Dataset tidak cukup untuk klaim generalisasi global, keselamatan navigasi, performa real-time universal, atau akurasi jarak absolut.

## Pekerjaan Wajib Sebelum Klaim Lebih Kuat

1. Tambahkan protokol anotasi dan anotator independen kedua.
2. Ukur agreement per label, bukan hanya diskusi informal.
3. Tambahkan reference caption Bahasa Indonesia yang ditulis terpisah dari output model.
4. Catat provenance, perangkat, scene, pencahayaan, dan hak penggunaan.
5. Lakukan external validation pada bangunan/perangkat berbeda.
6. Gunakan RGB-D/ToF/LiDAR terkalibrasi jika penelitian beralih ke klaim metrik.
