# Dataset Annotation Review

Tanggal audit: 2026-07-06

## Putusan Akademik

Dataset berisi 30 gambar indoor. Jumlah ini memenuhi batas minimal eksperimen awal pada protokol proyek, tetapi belum cukup kuat untuk klaim generalisasi. Hampir semua gambar berasal dari lingkungan rumah/kamar yang sama, sehingga variasi lokasi, bentuk ruangan, material lantai, warna dinding, dan kondisi pencahayaan masih sempit.

Dataset tetap dapat dipakai untuk pilot Bab 4 jika klaim dibatasi menjadi evaluasi awal pada citra indoor lokal. Dataset belum layak untuk klaim bahwa sistem bekerja baik pada lingkungan indoor secara umum.

## Prinsip Anotasi

Anotasi diperbaiki dengan prinsip berikut:

- `main_object` dipilih sebagai objek atau struktur paling relevan untuk deskripsi visual-spasial, diprioritaskan sebagai potensi halangan jika objek tersebut dekat.
- `object_position` memakai posisi kasar pada bidang gambar: kiri, tengah, atau kanan.
- `distance_meter` adalah estimasi visual, bukan pengukuran sensor.
- `distance_category` mengikuti protokol proyek: `sangat_dekat`, `dekat`, `sedang`, atau `jauh`.
- `has_obstacle` bernilai `yes` jika objek dekat secara visual dan perlu diperlakukan sebagai potensi halangan; bukan klaim bahaya navigasi pasti.
- `safer_direction` dibaca sebagai area relatif lebih lapang, bukan arah aman.

## Review Per Gambar

| Image | Kualitas | Anotasi Revisi | Catatan Kritis |
|---|---|---|---|
| indoor_001.webp | Layak | kipas angin, kanan, dekat, obstacle yes | Adegan padat dan informatif, tetapi objek kiri/kanan banyak sehingga label bisa diperdebatkan. |
| indoor_002.webp | Cukup | kipas angin, kanan, dekat, obstacle yes | Label lama lemari plastik tidak konsisten karena kipas kanan lebih dekat dan dominan sebagai halangan. |
| indoor_003.webp | Cukup | meja kerja, tengah, dekat, obstacle yes | Scene jelas, tetapi objek terlalu dekat sehingga depth lebih mudah daripada scene lorong. |
| indoor_004.webp | Layak | tumpukan barang, kanan, dekat, obstacle yes | Baik untuk kasus clutter kanan. |
| indoor_005.webp | Layak | kulkas, kanan, sedang, obstacle no | Baik sebagai kasus sisi kanan terisi tetapi jalur kiri-tengah relatif lapang. |
| indoor_006.webp | Layak | galon air, kiri, sangat_dekat, obstacle yes | Baik untuk objek sangat dekat. |
| indoor_007.webp | Cukup | kantong belanja, kanan, dekat, obstacle yes | Objek kecil dekat dapat menguji sensitivitas deskripsi, tetapi semantik mudah terlewat. |
| indoor_008.webp | Cukup | ember, kiri, dekat, obstacle yes | Ruang kecil membuat `safer_direction` sulit, sehingga ditandai tidak diketahui. |
| indoor_009.webp | Cukup | ember, kiri, dekat, obstacle yes | Mirip indoor_008; variasi rendah. |
| indoor_010.webp | Layak | wastafel, tengah, dekat, obstacle yes | Objek jelas, tetapi lebih merupakan close-up area dapur daripada jalur indoor. |
| indoor_011.webp | Cukup | galon air, kanan, dekat, obstacle yes | Area tengah cukup terbuka, tetapi galon dekat tetap relevan sebagai potensi halangan. |
| indoor_012.webp | Layak | magic com, kiri, dekat, obstacle yes | Baik untuk objek kiri dekat pada lorong. |
| indoor_013.webp | Layak | pintu, tengah, jauh, obstacle no | Negative case yang penting; lantai depan relatif kosong. |
| indoor_014.webp | Cukup | bantal lantai, kiri, dekat, obstacle yes | Label lama kasur terlalu umum; objek lantai dekat lebih relevan. |
| indoor_015.webp | Layak | koper, kiri, sedang, obstacle no | Negative/side-object case; berguna untuk menguji bahwa objek samping tidak selalu obstacle. |
| indoor_016.webp | Cukup | lemari plastik, kanan, dekat, obstacle yes | Ruang sempit, tetapi posisi objek dominan kanan cukup jelas. |
| indoor_017.webp | Layak | meja kerja, kanan, dekat, obstacle yes | Objek dekat dan jelas. |
| indoor_018.webp | Cukup | kantong belanja, kanan, dekat, obstacle yes | Mirip indoor_007, variasi terbatas. |
| indoor_019.webp | Layak | kulkas, kanan, sedang, obstacle no | Baik sebagai kasus lorong samping relatif lapang. |
| indoor_020.webp | Cukup | kompor, tengah, dekat, obstacle yes | Close-up dapur; kurang ideal jika klaimnya jalur indoor. |
| indoor_021.webp | Cukup | wastafel, kiri, dekat, obstacle yes | Scene jelas, tetapi masih bagian area dapur/kamar mandi yang sama. |
| indoor_022.webp | Cukup | pintu, kiri, dekat, obstacle yes | Pintu terbuka dekat dapat dianggap halangan, namun koridor kanan masih terbuka. |
| indoor_023.webp | Layak | pintu, tengah, jauh, obstacle no | Negative case kuat untuk jalur kosong. |
| indoor_024.webp | Cukup | pintu, kiri, dekat, obstacle yes | Pintu dekat dominan, tetapi label dapat diperdebatkan karena jalur kanan masih terbuka. |
| indoor_025.webp | Layak | kursi, kanan, dekat, obstacle yes | Objek dekat sangat jelas. |
| indoor_026.webp | Layak | rak sepatu, kanan, sedang, obstacle no | Side-object case; bagus untuk menguji perbedaan dekat-samping versus jalur lapang. |
| indoor_027.webp | Layak | kipas angin, kanan, sedang, obstacle no | Side-object case; tidak boleh otomatis dianggap obstacle. |
| indoor_028.webp | Layak | meja komputer, tengah, dekat, obstacle yes | Objek dekat dan jelas, tetapi sangat mirip indoor_017/025. |
| indoor_029.webp | Layak | kursi, tengah, sangat_dekat, obstacle yes | Kasus sangat dekat paling jelas. |
| indoor_030.webp | Cukup | pintu, kiri, dekat, obstacle yes | Pintu dominan dekat, tetapi label arah lapang bergantung interpretasi. |

## Risiko Dataset

1. Dataset terlalu homogen: mayoritas gambar dari area rumah/kamar/kos yang sama.
2. Banyak gambar bertema berulang: pintu, meja kerja, dapur, kamar mandi, kursi, kipas.
3. Negative cases masih sedikit dibanding obstacle-positive cases.
4. Jarak masih estimasi visual, bukan pengukuran meter aktual.
5. Beberapa label tetap dapat diperdebatkan karena definisi "halangan" belum berbasis user study atau sensor nyata.

## Implikasi Untuk Skripsi

Dataset ini boleh dipakai untuk evaluasi awal, tetapi harus ditulis sebagai dataset lokal terbatas. Jika hasil metrik bagus, hasil itu tidak boleh dijual sebagai bukti sistem general untuk semua indoor scene. Jika hasil metrik buruk, penyebabnya bisa berasal dari model, dari depth estimation, atau dari ambiguitas anotasi.
