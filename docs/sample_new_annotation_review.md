# Sample New Annotation Review

## Ringkasan

Folder `dataset/sample_new` berisi 44 file `.jpg` aktif. Sebanyak 10 gambar dekat yang repetitif dipindahkan ke `dataset/sample_new_excluded_close` agar distribusi dataset tidak terlalu berat ke objek dekat di tengah frame. Sepuluh gambar tambahan terbaru dari dataset indoor eksternal sudah masuk sebagai pengganti sebagian sampel sebelumnya.

Semua file aktif sudah dianotasi pada:

`dataset/sample_new_annotations.csv`

Validasi format:

- Jumlah file gambar aktif: 44
- Jumlah baris anotasi aktif: 44
- File tanpa anotasi: 0
- Anotasi tanpa file gambar: 0

## Distribusi Label

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

## Sampel Terbaru yang Ditambahkan

Sampel berikut aktif di dataset dan sudah dianotasi. Kelompok ini membantu menambah contoh lorong/ruang memanjang, meskipun sebagian tetap berasal dari konteks publik seperti sekolah, ruang ganti, dan kantor.

- `1 (7248).jpg`
- `1 (6083).jpg`
- `1 (6082).jpg`
- `1 (6845).jpg`
- `1 (7258).jpg`
- `1 (7254).jpg`
- `1 (7252).jpg`
- `1 (9887).jpg`
- `1 (6169).jpg`
- `1 (7245).jpg`

## Sampel yang Dikeluarkan

Sampel berikut dikeluarkan dari dataset aktif karena relatif repetitif: furniture/sofa/meja/kursi sangat dekat dan dominan di tengah frame.

- `1 (8478).jpg`
- `1 (8481).jpg`
- `1 (8482).jpg`
- `1 (8487).jpg`
- `1 (8505).jpg`
- `1 (8530).jpg`
- `1 (8537).jpg`
- `1 (8547).jpg`
- `1 (8548).jpg`
- `1 (8550).jpg`

## Penilaian Kualitas

Dataset tambahan ini layak dipakai sebagai variasi indoor eksternal. Setelah pengurangan 10 gambar dekat yang repetitif dan masuknya 10 sampel lorong/ruang memanjang, distribusi dataset menjadi lebih baik karena contoh `jauh`, `sedang`, dan `no obstacle` tetap tersedia.

Secara akademik, dataset ini membantu memperluas variasi visual dari dataset lokal sebelumnya. Namun, distribusi masih dominan pada `dekat`, `tengah`, dan `has_obstacle=yes`, sehingga klaim hasil tetap harus ditulis sebagai evaluasi pada dataset indoor terbatas yang telah dianotasi manual.

## Risiko Jika Langsung Digabung

1. Model/evaluator masih dapat terlihat bagus pada obstacle karena mayoritas ground truth adalah `yes`.
2. Metrik distance masih bisa bias karena kategori `dekat` tetap paling dominan.
3. Posisi `tengah` terlalu dominan, sehingga position accuracy bisa tampak naik tanpa benar-benar membuktikan pemahaman spasial.
4. Beberapa gambar berasal dari konteks kantor atau interior real estate, bukan rumah/kos lokal, sehingga klaim domain perlu ditulis sebagai indoor umum.

## Rekomendasi

Dataset ini boleh digabung sebagai tambahan. Jika masih ada waktu, sebaiknya ditambah lagi dengan gambar yang memiliki:

- area depan lapang tanpa halangan;
- objek utama di kanan;
- objek utama di kiri;
- objek sedang atau jauh;
- lorong atau ruangan dengan depth yang lebih panjang.

Untuk skripsi, gunakan dataset ini sebagai **external indoor subset yang dianotasi ulang manual**, bukan sebagai dataset benchmark asli dari Kaggle.
