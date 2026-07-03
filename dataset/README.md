# Dataset Indoor

Folder ini menyimpan gambar dan anotasi untuk evaluasi prototype depth-aware image description.

## Pengambilan Gambar

- Simpan gambar indoor di `dataset/images/`.
- Gunakan variasi objek seperti kursi, meja, pintu, lemari, tas, dan benda kecil di lantai.
- Ambil variasi posisi: kiri, kanan, tengah, depan, dan bawah.
- Ambil variasi jarak perkiraan: kurang dari 0.5 m, 0.5-1 m, 1-2 m, dan lebih dari 2 m.
- Target awal minimal 30 gambar; target lebih baik 50-100 gambar.

## Format Anotasi

File `dataset/annotations.csv` memakai kolom:

```csv
image_name,main_object,object_position,distance_meter,distance_category,has_obstacle,front_area_status,safer_direction,notes
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
