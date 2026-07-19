# Prototype Verdict

Tanggal eksekusi: 14 Juli 2026.

Keputusan: **FAIL — detector tidak boleh dilatih dari hasil prototipe ini.**

## Hasil Gate yang Ditetapkan Sebelum Eksekusi

| Kriteria | Ambang | Hasil | Status |
|---|---:|---:|---|
| Citra dengan respons tervalidasi | 12/12 | 9/12 (75%) | Gagal |
| Mark yang dikembalikan | >=90% | 25/35 (71,43%) | Gagal |
| Identitas objek end-to-end | >=70% | 13/35 (37,14%) | Gagal |
| Mark ID yang dikarang | 0 | 0 | Lulus |

Akurasi jika hanya menghitung mark dari sembilan citra yang responsnya berhasil diparsing adalah 13/27 (48,15%). Angka ini hanya diagnosis tambahan; gate tetap memakai 13/35 agar kegagalan parsing tidak disembunyikan.

Rata-rata latensi Gemma `google/gemma-4-e4b` adalah 162.046 ms/citra. Pada sembilan respons tervalidasi, rentangnya 147.436–170.855 ms dengan median 162.226 ms.

## Audit Visual Per Citra

Audit ini merupakan pemeriksaan plausibilitas visual oleh Codex, bukan ground-truth jarak dan bukan anotasi manusia final. Pengguna tetap perlu memverifikasi citra secara manual.

| Citra | Top-1 depth | Temuan utama |
|---|---|---|
| `living_room_814.jpg` | Plausibel | Box meja tertutup sebagian oleh sofa; Gemma salah menganggapnya kabinet/media. |
| `living_room_1020.jpg` | Plausibel | Box berlabel laptop tampak mengurung ponsel; label sofa dijawab “tempat duduk merah”, tetapi matcher awal tidak menerima istilah generik itu. |
| `living_room_168.jpg` | Plausibel | Label sofa secara visual menyerupai bangku; box lamp hanya berupa potongan sempit di tepi kiri. |
| `living_room_10.jpg` | Plausibel | Ketiga region relatif jelas dan ketiganya cocok. |
| `living_room_1000.jpg` | Plausibel | Wardrobe terpotong di tepi kanan; dua box meja bertumpang tindih tetapi kelas target disebut. |
| `living_room_1008.jpg` | Plausibel | Box tanaman, meja, dan sofa saling bertumpang tindih; dua identitas terakhir salah meski objek masih terlihat. |
| `living_room_1012.jpg` | Plausibel | Badge terlihat, tetapi Gemma hanya mengembalikan satu dari tiga mark. |
| `living_room_1016.jpg` | Plausibel | Tiga badge terlihat; respons tidak dapat diparsing sebagai JSON sesuai skema. |
| `living_room_1024.jpg` | Plausibel | Label wardrobe sebenarnya tampak seperti rak buku built-in; ketiga jawaban gagal terhadap label dataset. |
| `living_room_1028.jpg` | Plausibel | Region meja, kursi, dan lampu terlihat; respons tidak dapat diparsing. |
| `living_room_103.jpg` | Plausibel | Box meja tengah bertumpang tindih dengan kursi sehingga Gemma menjawab kursi. |
| `living_room_1032.jpg` | Ambigu | Meja dan kursi sama-sama berada di foreground; tidak ada ground-truth depth untuk membuktikan urutan fisiknya, dan respons tidak dapat diparsing. |

## Interpretasi yang Dapat Dipertanggungjawabkan

1. Badge besar memperbaiki masalah keterbacaan: respons versi kedua secara eksplisit mengenali `MARK 1`–`MARK 3`. Jadi kegagalan utama bukan lagi nomor yang terlalu kecil.
2. Oracle bounding box tidak otomatis menjadi visual prompt yang bersih. Occlusion, box bertumpang tindih, objek terpotong di tepi, dan label dataset yang terlalu kasar membuat beberapa region ambigu.
3. HomeObjects-3K tidak boleh langsung diperlakukan sebagai ground truth sempurna untuk eksperimen ini. Audit menemukan contoh kuat label `laptop` pada region yang secara visual tampak seperti ponsel dan `wardrobe` pada rak buku built-in.
4. Ranking top-1 terlihat masuk akal pada 11 citra dan ambigu pada satu citra, tetapi ini hanya plausibilitas visual. Tanpa ground-truth depth, eksperimen tidak membuktikan objek yang benar-benar paling dekat.
5. Hasil kelas tidak seimbang. Sembilan respons tervalidasi hanya mencakup bed, chair, lamp, laptop, photo frame, potted plant, sofa, table, dan wardrobe; tidak ada bukti parsed untuk tv, window, atau door.
6. Latensi sekitar 2,7 menit per citra terlalu tinggi untuk alur deskripsi interaktif saat ini.

## Langkah Berikut yang Diizinkan

- Jangan melatih detector.
- Bekukan prototipe ini sebagai hasil negatif yang informatif.
- Jika pendekatan tetap ingin diselamatkan, lakukan annotation QA pada subset kecil, tetapkan aturan penolakan untuk box terpotong/bertumpang tindih, lalu uji ulang oracle-box dengan sampel berimbang dan keluaran JSON yang dipaksa oleh API.
- Training detector baru boleh dipertimbangkan setelah oracle-box rerun memenuhi gate yang sama tanpa mengubah ambang secara post-hoc.
