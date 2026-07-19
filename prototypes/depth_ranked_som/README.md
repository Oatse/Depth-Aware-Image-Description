# PROTOTYPE — Oracle-Box Depth-Ranked Set-of-Mark

## Pertanyaan

Apakah Gemma lokal dapat mengenali objek pada visual mark yang berasal dari bounding box ground truth, setelah kandidat box diperingkat memakai relative depth map? Prototipe ini harus menjawab pertanyaan tersebut sebelum detector dilatih.

## Bukan Klaim

- Tidak mengevaluasi detector.
- Tidak membuktikan objek terdekat secara fisik.
- Tidak menghasilkan ground-truth depth.
- Tidak menjadi fitur runtime FastAPI.
- Tidak boleh dilaporkan sebagai hasil final skripsi.

## Gate Sebelum Training Detector

- 12/12 gambar selesai diproses.
- Minimal 90% mark yang diminta dikembalikan Gemma.
- Minimal 70% identitas objek bertanda sesuai label HomeObjects-3K.
- Tidak ada mark ID yang dikarang.
- Overlay box dan plausibilitas top-1 depth harus lolos audit visual per gambar.

Jika gate otomatis gagal, detector tidak dilatih. Jika gate otomatis lolos tetapi audit visual depth gagal, detector juga tidak dilatih.

## Menjalankan

Dari folder `Program`:

```powershell
python prototypes\depth_ranked_som\run_oracle_som_prototype.py
```

Default dataset: `D:\Tugas\DUMP\homeobjects-3K`.

Artefak disimpan di `results/prototypes/depth_ranked_som_20260714/` dan meliputi marked images, depth maps, respons mentah, CSV per mark, checkpoint per gambar, contact sheet, dan ringkasan gate.
