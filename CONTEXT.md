# Depth-Aware Image Description Context

Konteks ini mendefinisikan bahasa domain untuk prototype skripsi Depth-Aware Image Description agar output sistem tetap ilmiah, terukur, dan tidak berubah menjadi klaim navigasi aman.

## Language

**Deskripsi visual**:
Ringkasan semantik isi gambar yang berasal dari vision-language model.
_Avoid_: rekomendasi navigasi, instruksi berjalan

**Gemma Baseline**:
Mode Gemma tanpa metadata depth eksplisit. Mode ini boleh membaca relasi spasial visual secara kualitatif dari gambar, tetapi tidak boleh diklaim mengukur jarak atau menghasilkan peta kedalaman.
_Avoid_: menulis N/A depth sebagai bukti Gemma tidak mampu memahami visual

**Estimasi kedalaman**:
Sinyal kedalaman monokular dari gambar 2D yang digunakan untuk membaca struktur jarak relatif.
_Avoid_: jarak presisi, pengukuran sensor

**Kategori jarak relatif**:
Kelas dekat, sedang, atau jauh yang menjelaskan kedekatan relatif area pada gambar.
_Avoid_: meter presisi, jarak pasti

**Region terdekat**:
Area grid gambar yang diperkirakan memiliki objek atau permukaan paling dekat berdasarkan depth map.
_Avoid_: objek terdekat pasti

**Grid area 3x3**:
Skema ringkasan aplikasi yang membagi peta kedalaman menjadi sembilan area: atas-kiri, atas-tengah, atas-kanan, tengah-kiri, tengah, tengah-kanan, bawah-kiri, bawah-tengah, dan bawah-kanan. Ini bukan keluaran asli model, melainkan post-processing untuk membuat depth map lebih mudah dibaca.
_Avoid_: menyebut grid sebagai arsitektur internal Depth Anything

**Potensi halangan visual**:
Indikasi bahwa suatu region perlu diperhatikan karena posisi dan kedekatan relatifnya.
_Avoid_: jalan terhalang pasti, bahaya pasti

**Area relatif lapang**:
Region yang terlihat lebih sedikit objek dekatnya dibanding region lain dalam estimasi kedalaman.
_Avoid_: jalur aman, arah aman

**Deskripsi visual-spasial**:
Deskripsi akhir yang menggabungkan deskripsi visual dengan estimasi kedalaman, kategori jarak relatif, potensi halangan, dan area relatif lapang.
_Avoid_: panduan navigasi aman

**Late fusion berbasis aturan**:
Strategi fusi yang membuat deskripsi visual Gemma dan ringkasan kedalaman secara terpisah, lalu menyusun deskripsi akhir lewat aturan/template setelah kedua hasil tersedia.
_Avoid_: menyebutnya sebagai depth-to-spatial prompting

**Depth-to-Spatial Prompting**:
Strategi fusi yang menjalankan estimasi kedalaman lebih dulu, lalu memasukkan metadata region dan kategori kedalaman relatif ke prompt Gemma sebelum deskripsi akhir dibuat.
_Avoid_: mengklaim depth sebagai sensor jarak atau pengganti pemahaman visual Gemma

**Provenance highlighting**:
Penanda warna pada teks deskripsi untuk memperlihatkan sumber informasi, seperti Gemma, depth, inferensi, template, atau guardrail.
_Avoid_: menyebutnya tokenisasi model jika warna tidak berasal dari tokenizer asli

## Relationships

- **Deskripsi visual-spasial** menggabungkan satu **Deskripsi visual** dengan satu **Estimasi kedalaman**.
- **Gemma Baseline** menghasilkan deskripsi visual-spasial kualitatif dari gambar saja, tanpa metadata depth eksplisit.
- **Estimasi kedalaman** menghasilkan **Kategori jarak relatif**, **Region terdekat**, **Potensi halangan visual**, dan **Area relatif lapang**.
- **Grid area 3x3** adalah cara UI dan evaluator menjelaskan region depth kepada manusia; model depth tetap menghasilkan peta kedalaman kontinu.
- **Region terdekat** dapat menunjukkan area/objek terdekat, tetapi tidak membuktikan identitas objek tanpa dukungan **Deskripsi visual**.
- **Late fusion berbasis aturan** dan **Depth-to-Spatial Prompting** adalah strategi fusi berbeda yang boleh dibandingkan, bukan istilah yang saling menggantikan.
- **Provenance highlighting** menjelaskan sumber teks pada UI, bukan jumlah token atau segmentasi tokenizer.

## Example dialogue

> **Dev:** "Boleh tulis area tengah sebagai arah aman?"
> **Domain expert:** "Tidak. Tulis sebagai **Area relatif lapang** karena sistem hanya membaca estimasi kedalaman dari gambar 2D, bukan menguji keamanan navigasi."

## Flagged ambiguities

- "Objek terdekat" dapat disalahartikan sebagai identitas objek yang pasti. Resolusi: gunakan **Region terdekat** atau "area/objek pada region terdekat" kecuali ada bukti semantik yang jelas dari deskripsi visual.
- "Arah aman" terlalu kuat untuk prototype ini. Resolusi: gunakan **Area relatif lapang**.
- "Fusion" terlalu umum. Resolusi: tulis **Late fusion berbasis aturan** untuk metode post-processing dan **Depth-to-Spatial Prompting** untuk metode prompt-level.
- "Tidak tersedia" pada kolom Gemma dapat dibaca sebagai kelemahan model. Resolusi: gunakan "tidak diekstrak sebagai metadata depth" untuk field depth yang bukan output mode Gemma Baseline.
