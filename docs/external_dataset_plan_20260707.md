# External Dataset Plan - IndoorOutdoorNet-20K

## Keputusan

Dataset eksternal seperti IndoorOutdoorNet-20K boleh digunakan sebagai penambah variasi gambar, tetapi tidak boleh langsung dipakai sebagai ground truth utama penelitian ini.

Alasannya: label bawaan dataset tersebut hanya membedakan `Indoor` dan `Outdoor`, sedangkan skema penelitian ini membutuhkan anotasi yang lebih spesifik:

- `main_object`
- `object_position`
- `distance_category`
- `has_obstacle`

Dengan demikian, gambar eksternal hanya aman dipakai setelah dipilih, difilter, dan dianotasi ulang mengikuti `dataset/annotations.csv`.

## Status Sumber

Berdasarkan halaman dataset publik yang ditemukan:

- Nama dataset: IndoorOutdoorNet-20K.
- Tugas asal: klasifikasi scene indoor/outdoor.
- Jumlah gambar: 19,998.
- Label asal: Indoor dan Outdoor.
- Ukuran: sekitar 451 MB.
- Lisensi yang tertera pada mirror Hugging Face/ModelScope: Apache-2.0.

Halaman Kaggle dapat digunakan sebagai sumber unduhan jika akses akun tersedia, tetapi metadata yang lebih terbaca publik tersedia pada mirror Hugging Face dan ModelScope.

## Cara Pakai yang Aman

1. Ambil hanya subset `Indoor`, bukan seluruh dataset.
2. Pilih gambar yang relevan dengan skenario proyek: ruangan rumah/kos, lorong, dapur, kamar, area dengan objek dekat.
3. Hindari gambar yang terlalu generik, stock-like, blur, terlalu jauh, outdoor, atau tidak punya potensi objek spasial.
4. Anotasi ulang satu per satu memakai skema proyek.
5. Pisahkan data menjadi dua fungsi:
   - data kalibrasi threshold depth;
   - data uji akhir.
6. Laporkan bahwa dataset eksternal digunakan sebagai tambahan variasi visual, bukan sebagai benchmark resmi indoor navigation.

## Rekomendasi Jumlah

Untuk skripsi, target realistis:

- Tambah 30-50 gambar indoor eksternal yang dianotasi ulang.
- Gabungkan dengan 30 gambar lokal saat ini.
- Gunakan minimal split sederhana:
  - 20-30 gambar untuk kalibrasi/penentuan threshold;
  - sisanya untuk evaluasi akhir.

Jika waktu terbatas, lebih baik menambah 20 gambar yang benar-benar dianotasi rapi daripada 100 gambar yang labelnya longgar.

## Risiko Sidang

Jika dataset eksternal dipakai tanpa anotasi ulang, dosen dapat menyerang:

- label dataset asal tidak sesuai variabel penelitian;
- tidak ada ground truth jarak relatif;
- tidak ada ground truth obstacle;
- data eksternal hanya membuktikan scene indoor/outdoor, bukan kualitas deskripsi visual-spasial.

Jika dataset eksternal dipakai setelah anotasi ulang, argumennya jauh lebih kuat:

- variasi visual meningkat;
- evaluasi tidak hanya bergantung pada satu lokasi lokal;
- klaim penelitian tetap sesuai skema anotasi sendiri.

## Kalimat Metodologi yang Aman

Sebagian citra tambahan diambil dari dataset eksternal IndoorOutdoorNet-20K pada kelas indoor. Citra tersebut tidak digunakan dengan label bawaan dataset, melainkan diseleksi dan dianotasi ulang secara manual mengikuti skema penelitian yang mencakup objek utama, posisi relatif objek, kategori jarak relatif, dan potensi halangan visual.
