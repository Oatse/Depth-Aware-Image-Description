# Sample New Annotation Validation - 2026-07-07

## Tujuan

Validasi ulang dilakukan untuk mengecek apakah anotasi pada `dataset/sample_new_annotations.csv` sesuai dengan isi visual gambar, terutama label `dekat` yang sebelumnya berisiko terlalu dominan.

## Metode Validasi

1. Memastikan jumlah file aktif di `dataset/sample_new`.
2. Membuat contact sheet visual berlabel dari seluruh gambar aktif.
3. Mengecek ulang semua gambar aktif terhadap label:
   - `main_object`
   - `object_position`
   - `distance_category`
   - `has_obstacle`
   - `front_area_status`
4. Membuka ulang gambar borderline secara individual, terutama gambar dengan label `dekat` dan `has_obstacle=yes`.

Contact sheet audit disimpan di:

`results/annotation_audit_sheets/`

## Koreksi yang Dilakukan

| Image | Sebelum | Sesudah | Alasan |
|---|---|---|---|
| `1 (1030).jpg` | `tengah`, `dekat`, `yes`, `terhalang` | `kanan`, `sedang`, `no`, `relatif_lapang` | Mesin cuci berada di sisi kanan-tengah; lantai depan masih relatif terbuka. |
| `1 (8466).jpg` | `kiri`, `dekat`, `yes`, `terhalang` | `kiri`, `sedang`, `no`, `relatif_lapang` | Kabinet dapur berada di sisi kiri; jalur tengah menuju pintu tidak tertutup. |
| `1 (8552).jpg` | posisi `tengah` | posisi `kiri` | Kabinet kayu dominan berada di kiri depan. |
| `1 (8815).jpg` | posisi `tengah` | posisi `kiri` | Kursi terdekat berada di kiri bawah frame, bukan tengah. |

## Distribusi Setelah Validasi

### Distance Category

| Label | Jumlah |
|---|---:|
| dekat | 28 |
| sedang | 10 |
| sangat_dekat | 2 |
| jauh | 4 |

### Has Obstacle

| Label | Jumlah |
|---|---:|
| yes | 30 |
| no | 14 |

### Object Position

| Label | Jumlah |
|---|---:|
| tengah | 26 |
| kiri | 11 |
| kanan | 7 |

## Keputusan Audit

Dataset aktif sudah lebih konsisten dibanding versi sebelumnya. Beberapa label `dekat` memang tetap dominan karena banyak gambar berisi furniture atau objek foreground, tetapi dua kasus yang terlalu agresif sudah diturunkan ke `sedang/no`.

Dataset masih belum seimbang sempurna. Kategori `jauh` masih hanya 4 gambar, sehingga klaim penelitian tetap harus dibatasi sebagai evaluasi pada subset indoor terbatas yang dianotasi manual.

## Validasi Format

- File gambar aktif: 44
- Baris anotasi aktif: 44
- File tanpa anotasi: 0
- Anotasi tanpa file: 0
- Sel kosong: 0
- Skema CSV: valid
