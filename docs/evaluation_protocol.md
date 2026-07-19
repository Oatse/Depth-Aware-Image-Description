# Evaluation Protocol

Dokumen ini menjelaskan prosedur evaluasi prototype depth-aware image description untuk kebutuhan skripsi.

## Tujuan Evaluasi

Evaluasi bertujuan membandingkan tiga mode aktif:

1. `gemma_only`: Gemma Baseline, yaitu deskripsi visual dan relasi spasial kualitatif dari Gemma tanpa metadata depth eksplisit.
2. `depth_only`: ringkasan depth tanpa pemahaman semantik Gemma.
3. `gemma_depth`: deskripsi visual Gemma yang digabungkan dengan depth summary melalui fusi regional berbatas bukti.

Pertanyaan yang diuji: apakah informasi depth memberi metadata kedalaman relatif yang cocok dengan label lokal, dan apakah kebijakan fusi berbatas bukti mengurangi klaim visual yang tidak didukung dibanding kebijakan verbose lama. Evaluasi ini tidak mengasumsikan peningkatan dan tidak boleh dibaca sebagai pembuktian bahwa Gemma tidak mampu memahami gambar.

## Dataset

Dataset eksperimen final disimpan di `dataset/final_images/` dan anotasi final di `dataset/final_annotations.csv`. Dataset tersebut berisi 44 citra. Path `dataset/images/` dan `dataset/annotations.csv` tetap tersedia untuk baseline lama/development dan tidak boleh tertukar dengan artefak final ketika menulis Bab 4.

Endpoint `/experiment-status` memakai path `EXPERIMENT_*` dan mengembalikan `artifact_profile` serta `artifact_paths`. Verifikasi field tersebut sebelum menyalin readiness atau metrik ke laporan.

Jumlah minimal untuk eksperimen awal:

- 30 gambar indoor untuk baseline.
- 50-100 gambar untuk hasil yang lebih stabil.

Skenario yang disarankan:

- Objek dekat di area depan.
- Jalur tengah kosong.
- Objek dominan di kiri.
- Objek dominan di kanan.
- Objek kecil di lantai.
- Objek besar seperti kursi, meja, lemari, atau pintu.
- Kondisi terang dan redup.
- Variasi kedekatan visual relatif: objek sangat dominan di foreground, objek dekat di area depan, objek sedang, serta objek atau struktur jauh di latar.

## Format Anotasi

Kolom wajib:

```csv
image_name,main_object,object_position,distance_annotation_basis,annotation_confidence,distance_category,has_obstacle,front_area_status,safer_direction,notes
```

`distance_annotation_basis` diisi `visual_relative` untuk menegaskan bahwa kategori jarak berasal dari anotasi visual relatif terhadap perspektif kamera. Kolom ini bukan hasil pengukuran fisik, bukan output sensor, dan bukan ground truth meter aktual.

`annotation_confidence` berisi `high`, `medium`, atau `low` sesuai tingkat keyakinan anotator. Nilai `low` digunakan ketika objek, area relatif lapang, atau potensi halangan sulit diputuskan dari citra.

Kategori jarak relatif:

- `sangat_dekat`: objek relevan sangat dominan pada foreground atau bagian bawah-depan citra dan tampak sangat dekat dari perspektif kamera.
- `dekat`: objek relevan berada di area depan dan berpotensi menjadi halangan visual.
- `sedang`: objek relevan terlihat jelas, tetapi tidak mendominasi foreground dan masih menyisakan ruang visual di sekitarnya.
- `jauh`: objek atau struktur dominan berada di latar atau tidak menjadi potensi halangan dekat.

## Prosedur Eksperimen

1. Masukkan gambar ke `dataset/images/`.
2. Buat atau lengkapi `dataset/annotations.csv`.
3. Pastikan LM Studio berjalan dan model Gemma loaded.
4. Pastikan `DEPTH_MODEL_PATH` mengarah ke folder ONNX Depth Anything.
5. Jalankan preflight eksperimen:

```bash
python scripts\run_batch_evaluation.py --preflight-only
```

Preflight harus lulus sebelum hasil dipakai untuk Bab 4. Pemeriksaan ini memastikan:

- folder gambar tidak kosong;
- setiap gambar memiliki anotasi;
- setiap baris anotasi memiliki file gambar yang sesuai;
- kolom anotasi wajib tersedia;
- mock runtime tidak aktif untuk eksperimen final;
- model depth tersedia;
- Gemma di LM Studio sudah siap jika mode memakai Gemma.

Untuk dry run development, mock boleh dipakai hanya dengan flag eksplisit:

```bash
python scripts\run_batch_evaluation.py --preflight-only --allow-mock
```

Hasil dry run mock tidak boleh digunakan sebagai hasil eksperimen final.

6. Jalankan batch evaluation:

```bash
python scripts\run_batch_evaluation.py --images-dir dataset\images --annotations dataset\annotations.csv
```

Untuk eksperimen final 44 citra, gunakan path eksplisit dan nama output baru agar artefak lama tidak tertimpa:

```bash
python scripts\run_batch_evaluation.py --images-dir dataset\final_images --annotations dataset\final_annotations.csv --predictions results\final_predictions_<tanggal>.csv --output results\final_evaluation_<tanggal>.csv
```

Secara default, batch evaluation menjalankan `gemma_only`, `depth_only`, dan `gemma_depth`. Untuk evaluasi parsial/resumable, gunakan:

```bash
python scripts\run_resumable_evaluation.py --limit-jobs 2
```

7. Baca output:

- `results/predictions.csv`
- `results/evaluation.csv`
- `results/depth_maps/`

## Metrik

Metrik otomatis awal:

- object accuracy dari field terstruktur `main_object` saja;
- position accuracy dari field terstruktur `object_position` saja;
- object-position joint accuracy, yang benar hanya bila objek dan posisinya sama-sama cocok;
- distance category accuracy, hanya berlaku untuk mode yang menghasilkan metadata depth;
- obstacle warning accuracy, hanya berlaku untuk mode yang menghasilkan metadata depth;
- obstacle precision, recall, F1 positif, serta confusion matrix TP/FP/TN/FN untuk mode depth;
- average latency.

Pada `gemma_only`, distance category accuracy dan obstacle warning accuracy ditulis sebagai N/A karena mode tersebut tidak mengekstrak metadata depth eksplisit. Pada `depth_only`, object accuracy, position accuracy, dan object-position joint accuracy ditulis sebagai N/A karena mode tersebut tidak menghasilkan prediksi semantik objek. Teks bebas `final_description` tidak dipakai untuk mengoreksi field terstruktur; aturan lama itu menyebabkan kebocoran karena kata area yang ditambahkan fusion dapat dikreditkan sebagai posisi objek.

F1 obstacle memakai kelas positif `has_obstacle=yes`. Accuracy tetap dilaporkan karena mudah dipahami, sedangkan precision, recall, dan F1 diperlukan agar ketidakseimbangan kelas dan trade-off false positive/false negative terlihat. Confusion matrix wajib ikut ditampilkan; F1 tunggal tanpa TP/FP/TN/FN mudah disalahartikan.

Dataset final tidak memiliki `reference_description` independen. Karena itu, evaluasi leksikal berbasis reference caption tidak dilaporkan; kolom `notes` tidak boleh dialihfungsikan karena dibuat sebagai catatan anotasi, bukan deskripsi referensi dengan protokol konsisten.

LLM-as-a-Judge dijalankan terpisah memakai `scripts/run_llm_judge.py`. Judge menerima citra sumber yang dinormalisasi ke JPEG dan dibatasi maksimal 768 piksel sebagai bukti visual utama, anotasi terstruktur sebagai pembanding sekunder, dan kandidat deskripsi. Nama mode dibutakan, output memakai JSON schema, model dan versi rubric dicatat, setiap kandidat dinilai tiga kali, simpangan baku dilaporkan, dan respons di-cache. `temperature=0` digunakan untuk mengurangi variasi, bukan menjamin hasil deterministik. Judge tetap bukan ground truth dan tidak menggantikan penilaian manusia.

Tidak ada lagi skor kualitas deskripsi buatan 1-5. Tanpa reference caption atau penilai independen, skor tersebut hanya mengodekan preferensi panjang/format yang ditulis pengembang. Kualitas teks dievaluasi terpisah melalui image-aware judge dan, bila tersedia, penilaian manusia dengan rubric yang ditetapkan sebelum melihat keluaran mode.

## Interpretasi

Perbandingan `gemma_depth` dengan `gemma_only` harus memisahkan metadata depth, semantik objek, dan kualitas bahasa. Evaluator ketat tidak boleh menganggap region depth sebagai posisi objek. Hasil image-aware judge dan kontrol kebijakan fusion dilaporkan sebagai eksperimen tambahan; hasil tersebut tidak boleh ditulis sebagai peningkatan kualitas teks universal tanpa bukti berpasangan yang mendukungnya.

Pada kontrol kebijakan 44 pasangan, fusi berbatas bukti memperoleh overall 3,9015 dibanding verbose lama 3,7045; groundedness 3,9621 dibanding 3,7803; dan clarity 4,4545 dibanding 4,2879. Interval bootstrap snapshot tidak memotong nol untuk tiga metrik tersebut. Hasil ini mendukung pemilihan kebijakan aktif pada dataset dan judge yang dilaporkan, tetapi tidak membuktikan generalisasi atau kesetaraan dengan human rating.

Deskripsi akhir mode depth-aware menyebut area terdekat dan, hanya untuk kategori `dekat` atau `sangat_dekat`, potensi halangan visual pada area tersebut. Ia tidak menyatakan bahwa objek yang disebut Gemma berada pada kedalaman itu. Bahasa tetap guarded, misalnya "area tengah-kiri berpotensi menjadi halangan visual", bukan klaim pasti seperti "kursi itu berjarak dekat", "jalan terhalang", atau "area aman".

Label area seperti `tengah-kiri` dan `bawah-tengah` dibaca dari grid 3x3 aplikasi. Depth model menghasilkan peta kedalaman kontinu; grid 3x3 adalah post-processing untuk membuat region lebih mudah dianalisis dan dibandingkan dengan anotasi.

Post-processing aktif hanya memakai grid 3x3 dengan statistik persentil ke-10 (`grid_p10`). Kandidat adaptive bands tidak dipertahankan: pada pemeriksaan 44 citra, obstacle recall turun dari 0,8519 menjadi 0,6667 dan F1 dari 0,8679 menjadi 0,7826. Hasil tersebut hanya menjadi dasar keputusan penyederhanaan, bukan fitur atau klaim kontribusi penelitian.

Jika mode depth-aware tidak meningkatkan object accuracy, itu wajar karena depth module tidak bertugas mengenali objek. Kontribusi utama depth seharusnya terlihat pada kategori kedalaman relatif, status area depan, area relatif lapang, dan kualitas deskripsi spasial.

## Batasan

- Depth map adalah estimasi monocular depth, bukan sensor jarak.
- Kategori jarak relatif pada anotasi tidak merepresentasikan pengukuran meter aktual.
- Threshold depth model perlu dikalibrasi terhadap kategori visual relatif pada dataset lokal.
- Model yang dipakai adalah varian metric-indoor, tetapi label dataset merupakan kategori visual relatif dan bukan ground truth meter; evaluasi menguji transformasi output model menjadi kategori lokal, bukan akurasi kedalaman metrik.
- Evaluasi otomatis pada label semantik memakai pencocokan field terstruktur yang ketat; ia tidak menggantikan penilaian manual dan tidak menangani sinonim tanpa kamus yang dipraregistrasikan.
- LLM judge telah melihat citra, tetapi tetap bergantung pada provider/model eksternal dan dapat memiliki bias, salah membaca visual, serta variasi antar-pengulangan.
- Endpoint router lokal tidak membuktikan inferensi lokal; citra dapat diteruskan ke provider upstream. Hak pemrosesan dan kebijakan privasi provider harus diverifikasi sebelum run.
- Label rute `cx/gpt-5.5` tidak diperlakukan sebagai snapshot immutable tanpa bukti resolusi model dari provider; tanggal, konfigurasi router, dan label model harus disimpan bersama hasil.
- Dataset final 44 citra adalah proof-of-concept lokal; tidak mendukung generalisasi populasi atau klaim lintas bangunan/perangkat.
- Prototype tidak diklaim sebagai alat navigasi aman.
