# Design System Bridge-Gap

## 1. Prinsip antarmuka

UI menyediakan satu alur capture kandidat dan satu hasil deskripsi. Referensi sensor tampil sebagai evidence tambahan yang provenance-nya dapat diperiksa.

- deskripsi gambar menjadi elemen utama;
- tidak ada pemilih metode atau hasil paralel;
- angka sensor tidak dikaitkan dengan objek bernama;
- hanya evidence `applied` yang dapat mengondisikan prompt;
- capture baru tidak ditulis ke dataset evaluasi v2 yang telah dibekukan;
- status tidak tersedia atau konflik terlihat jelas;
- detail teknis tidak mengganggu alur utama.

## 2. Tata letak

### Sebelum analisis

1. header ringkas;
2. area kamera atau upload;
3. preview citra;
4. status backend, Gemma, dan sensor;
5. tombol **Analisis Gambar**.

### Setelah analisis

1. deskripsi gambar;
2. citra sumber;
3. kartu referensi sensor frontal;
4. ringkasan latency;
5. detail teknis dalam accordion.

## 3. Komponen

### Capture/Upload

- menerima JPG, PNG, atau WebP;
- kamera belakang menjadi arah capture yang sesuai dengan sensor;
- preview harus sama dengan frame yang dikirim;
- loading mencegah request ganda.
- operator mengisi `target_id` dan `ground_truth_cm`;
- backend menyimpan capture ke `results/captures/incoming/`;
- UI tidak menawarkan path atau batch yang dapat menunjuk ke dataset v2 final.

### System Status

Menampilkan status Backend, Gemma, dan Sensor. Rincian koneksi dibuka melalui popover atau panel detail.

### Deskripsi Gambar

- menjadi panel utama setelah analisis;
- menggunakan Bahasa Indonesia yang jelas;
- menjelaskan objek dan konteks scene berdasarkan citra;
- dapat dipengaruhi konteks frontal terverifikasi pada mode sensor-assisted;
- tidak menyisipkan angka sensor ke objek bernama.

### Referensi Sensor Frontal

Base case `paired` menampilkan:

- Sensor 1;
- Sensor 2;
- Referensi frontal berupa rata-rata kedua nilai;
- status “Paired”.

Keterangan wajib menggunakan bentuk “Referensi sensor frontal sekitar X cm”. Pada `partial`, tampilkan hanya sensor yang tersedia tanpa rata-rata. Pada `pair_conflict`, `stale`, `direction_mismatch`, atau `unavailable`, tampilkan status dan alasan tanpa angka rata-rata pada narasi hasil.

### Detail Teknis

Accordion tertutup secara default dapat menampilkan:

- `capture_id`;
- nilai setiap sensor;
- `received_time_ms` dan `age_ms`;
- `pair_disagreement_cm`;
- `match_time_source`;
- arah kamera;
- status dan `reason_code`;
- latency serta respons mentah Gemma;
- error teknis.

## 4. Visual tokens

| Role | Token | Value |
|---|---|---|
| Canvas | `--canvas` | `#fbfaf8` |
| Surface | `--surface` | `#ffffff` |
| Surface soft | `--surface-soft` | `#f4f2ef` |
| Ink | `--ink` | `#18151f` |
| Ink soft | `--ink-soft` | `#595664` |
| Line | `--line` | `#e9e5df` |
| Accent | `--accent` | `#6f3cc3` |
| Accent dark | `--accent-dark` | `#4a238d` |
| Result panel | `--panel` | `#191622` |
| Ready | `--status-ready` | `#4f8b63` |
| Warning | `--status-warning` | `#b9843a` |
| Error | `--error` | `#a23a32` |

## 5. Tipografi dan spacing

- font utama: Plus Jakarta Sans, Geist, Segoe UI, atau system sans-serif;
- font angka/metadata: JetBrains Mono, Consolas, atau monospace;
- lebar konten maksimum: 1168 px;
- radius panel utama: 14 px;
- mobile satu kolom tanpa horizontal scroll.

## 6. Interaksi dan aksesibilitas

- animasi memakai opacity dan transform;
- loading menjelaskan tahap upload, analisis Gemma, dan pencocokan sensor;
- `prefers-reduced-motion` mematikan animasi dekoratif;
- tombol mempunyai nama, focus state, dan status disabled yang jelas;
- error muncul dekat tindakan yang gagal;
- status tidak dibedakan hanya dengan warna.

## 7. Copy kanonik

- **Analisis Gambar**
- **Citra Sumber**
- **Deskripsi Gambar**
- **Referensi Sensor Frontal**
- **Sensor 1**
- **Sensor 2**
- **Status Evidence**
- **Detail Teknis**

Copy yang dilarang: “objek terdekat X cm”, “aman dilalui”, atau klaim lain yang mengikat cone sensor ke isi citra.
