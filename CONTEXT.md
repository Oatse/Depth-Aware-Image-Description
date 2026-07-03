# Depth-Aware Image Description Context

Konteks ini mendefinisikan bahasa domain untuk prototype skripsi Depth-Aware Image Description agar output sistem tetap ilmiah, terukur, dan tidak berubah menjadi klaim navigasi aman.

## Language

**Deskripsi visual**:
Ringkasan semantik isi gambar yang berasal dari vision-language model.
_Avoid_: rekomendasi navigasi, instruksi berjalan

**Estimasi kedalaman**:
Sinyal kedalaman monokular dari gambar 2D yang digunakan untuk membaca struktur jarak relatif.
_Avoid_: jarak presisi, pengukuran sensor

**Kategori jarak relatif**:
Kelas dekat, sedang, atau jauh yang menjelaskan kedekatan relatif area pada gambar.
_Avoid_: meter presisi, jarak pasti

**Region terdekat**:
Area grid gambar yang diperkirakan memiliki objek atau permukaan paling dekat berdasarkan depth map.
_Avoid_: objek terdekat pasti

**Potensi halangan visual**:
Indikasi bahwa suatu region perlu diperhatikan karena posisi dan kedekatan relatifnya.
_Avoid_: jalan terhalang pasti, bahaya pasti

**Area relatif lapang**:
Region yang terlihat lebih sedikit objek dekatnya dibanding region lain dalam estimasi kedalaman.
_Avoid_: jalur aman, arah aman

**Deskripsi visual-spasial**:
Deskripsi akhir yang menggabungkan deskripsi visual dengan estimasi kedalaman, kategori jarak relatif, potensi halangan, dan area relatif lapang.
_Avoid_: panduan navigasi aman

## Relationships

- **Deskripsi visual-spasial** menggabungkan satu **Deskripsi visual** dengan satu **Estimasi kedalaman**.
- **Estimasi kedalaman** menghasilkan **Kategori jarak relatif**, **Region terdekat**, **Potensi halangan visual**, dan **Area relatif lapang**.
- **Region terdekat** dapat menunjukkan area/objek terdekat, tetapi tidak membuktikan identitas objek tanpa dukungan **Deskripsi visual**.

## Example dialogue

> **Dev:** "Boleh tulis area tengah sebagai arah aman?"
> **Domain expert:** "Tidak. Tulis sebagai **Area relatif lapang** karena sistem hanya membaca estimasi kedalaman dari gambar 2D, bukan menguji keamanan navigasi."

## Flagged ambiguities

- "Objek terdekat" dapat disalahartikan sebagai identitas objek yang pasti. Resolusi: gunakan **Region terdekat** atau "area/objek pada region terdekat" kecuali ada bukti semantik yang jelas dari deskripsi visual.
- "Arah aman" terlalu kuat untuk prototype ini. Resolusi: gunakan **Area relatif lapang**.
