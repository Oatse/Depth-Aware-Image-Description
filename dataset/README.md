# Dataset Indoor

Folder ini menyimpan gambar dan anotasi untuk evaluasi prototype depth-aware image description.

## Pengambilan Gambar

- Simpan gambar indoor di `dataset/images/`.
- Gunakan variasi objek seperti kursi, meja, pintu, lemari, tas, dan benda kecil di lantai.
- Ambil variasi posisi: kiri, kanan, tengah, depan, dan bawah.
- Ambil variasi kedekatan visual relatif: objek sangat dominan di foreground, objek dekat di area depan, objek sedang, dan objek/struktur jauh di latar.
- Target awal minimal 30 gambar; target lebih baik 50-100 gambar.

## Format Anotasi

File `dataset/annotations.csv` memakai kolom:

```csv
image_name,main_object,object_position,distance_annotation_basis,annotation_confidence,distance_category,has_obstacle,front_area_status,safer_direction,notes
```

Kategori `distance_category`:

- `sangat_dekat`
- `dekat`
- `sedang`
- `jauh`

Nilai `has_obstacle`:

- `yes`
- `no`

Nilai `safer_direction`:

- `kiri`
- `kanan`
- `tengah`
- `tidak_diketahui`

Catatan jarak adalah estimasi kategori untuk evaluasi penelitian, bukan pengukuran navigasi presisi.

`distance_annotation_basis` diisi `visual_relative` untuk menegaskan bahwa kategori jarak berasal dari anotasi visual relatif terhadap perspektif kamera, bukan hasil pengukuran meter aktual. `annotation_confidence` berisi `high`, `medium`, atau `low` sesuai tingkat keyakinan anotator terhadap kategori visual tersebut.
