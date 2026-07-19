# Red-Team Evaluation Review

> Arsip historis. Status metode aktif mengikuti `methodological_upgrade_20260714.md`; mode Depth-to-Spatial Prompting telah dipensiunkan setelah evaluasi image-aware 44 citra.

Tanggal evaluasi: 2026-07-06

## Putusan Singkat

Dataset dan hasil evaluasi saat ini cukup untuk eksperimen pilot, tetapi belum cukup untuk klaim skripsi yang kuat. Bukti paling keras: mode depth-aware late fusion (`gemma_depth`) belum menunjukkan peningkatan kualitas yang meyakinkan dibanding `gemma_only`. Modul depth juga belum selaras dengan anotasi jarak lokal karena mayoritas objek yang dianotasi `dekat` diprediksi sebagai `sedang`.

## Artefak Yang Dihasilkan

- `dataset/annotations.csv`: anotasi diperbaiki untuk 30 gambar.
- `docs/dataset_annotation_review.md`: audit kualitas dataset dan alasan anotasi per gambar.
- `results/predictions_review_20260706.csv`: prediksi gabungan untuk audit, termasuk catatan kegagalan prompted.
- `results/predictions_review_complete_modes_20260706.csv`: prediksi bersih untuk mode lengkap.
- `results/evaluation_review_complete_modes_20260706.csv`: metrik evaluasi bersih.
- `results/per_image_review_20260706.csv`: evaluasi per gambar dan per mode.

## Kelayakan Dataset

Dataset berisi 30 gambar. Ini memenuhi angka minimal eksperimen awal pada protokol proyek, tetapi berada di batas bawah. Secara akademik, 30 gambar dari lingkungan yang sangat mirip tidak cukup untuk klaim generalisasi.

Kelemahan dataset:

1. Lokasi terlalu homogen: mayoritas gambar berasal dari rumah/kamar/kos yang sama.
2. Objek sering berulang: pintu, meja kerja, dapur, kamar mandi, kursi, kipas, galon.
3. Negative cases hanya 7 dari 30 gambar.
4. Label jarak masih estimasi visual, bukan pengukuran aktual.
5. Definisi obstacle masih bergantung pada interpretasi visual, bukan uji pengguna atau sensor.

Kesimpulan: dataset boleh dipakai untuk Bab 4 awal jika disebut sebagai dataset lokal terbatas. Jangan klaim performa umum pada indoor scene luas.

## Metrik Bersih

Evaluasi valid hanya memakai mode yang lengkap untuk 30 gambar: `gemma_only`, `depth_only`, dan `gemma_depth`. Mode `gemma_depth_prompted` tidak valid untuk hasil final karena runtime gagal/timeout.

| Mode | Object Acc. | Position Acc. | Distance Acc. | Obstacle Acc. | Quality | Avg Latency |
|---|---:|---:|---:|---:|---:|---:|
| `gemma_only` | 50.00% | 66.67% | N/A | N/A | 3.61/5 | 106,283.5 ms |
| `depth_only` | 0.00% | 66.67% | 26.67% | 26.67% | 2.20/5 | 1,355.5 ms |
| `gemma_depth` | 50.00% | 86.67% | 26.67% | 26.67% | 2.90/5 | 105,769.8 ms |

Interpretasi keras:

- `gemma_depth` meningkatkan position accuracy dibanding `gemma_only`.
- `gemma_depth` tidak meningkatkan object accuracy.
- `gemma_depth` lebih rendah dari `gemma_only` pada quality heuristic karena depth distance sering salah.
- `depth_only` cepat, tetapi secara semantik tidak mengenali objek dan distance accuracy rendah.
- Latency Gemma sekitar 105-106 detik per gambar, terlalu lambat untuk klaim aplikasi interaktif.

## Status `gemma_depth_prompted`

Mode `gemma_depth_prompted` belum bisa dipakai sebagai hasil eksperimen final. Saat audit, file prediksi hanya memiliki 1 gambar sukses dari run lama dan 1 kegagalan baru:

- `indoor_001.webp | gemma_depth_prompted`: gagal setelah sekitar 242 detik dengan error Gemma inference.

Implikasi: pertanyaan penelitian tentang prompt fusion belum terbukti. Kalau Bab 4 tetap membahas prompt fusion tanpa menyelesaikan runtime dan prediksi 30 gambar, penguji bisa menyerang bahwa klaim metode utama tidak punya data.

## Analisis Berhasil

Kasus yang relatif berhasil pada `gemma_depth`:

- `indoor_005.webp`: kulkas terdeteksi, posisi/label distance cocok, kualitas 5/5.
- `indoor_013.webp`: pintu jauh dan no-obstacle cocok, kualitas 5/5.
- `indoor_015.webp`: koper sedang/no-obstacle cocok, kualitas 5/5.
- `indoor_021.webp`: wastafel dekat/obstacle cocok, kualitas 5/5.
- `indoor_027.webp`: kipas angin sedang/no-obstacle cocok, kualitas 5/5.

Pola keberhasilan: sistem lebih baik saat objek besar, jelas, dan label jaraknya berada pada `sedang` atau `jauh`. Satu kasus `dekat` yang berhasil adalah `indoor_021.webp`.

## Analisis Gagal

Kegagalan utama terjadi pada kategori jarak:

- Dari 21 gambar berlabel `dekat`, hanya 1 yang diprediksi `dekat`.
- 19 gambar berlabel `dekat` diprediksi `sedang`.
- 2 gambar berlabel `sangat_dekat` juga diprediksi `sedang`.

Contoh gagal keras:

- `indoor_001.webp`: anotasi kipas angin kanan dekat, `gemma_depth` memprediksi objek "Sofa" dan depth `sedang`.
- `indoor_002.webp`: anotasi kipas angin kanan dekat, `gemma_depth` fokus ke rak kiri dan depth `sedang`.
- `indoor_006.webp`: anotasi galon air kiri sangat dekat, `gemma_depth` fokus ke kompor dan depth `sedang`.
- `indoor_009.webp`: anotasi ember kiri dekat, depth memprediksi `jauh`.
- `indoor_018.webp`: anotasi kantong belanja kanan dekat, `gemma_depth` fokus ke wastafel dan kualitas hanya 1/5.

Penyebab yang paling mungkin:

1. Threshold depth belum dikalibrasi terhadap dataset lokal.
2. Grid 3x3 memilih region terdekat berdasarkan p10, tetapi objek kecil/foreground bisa kalah oleh permukaan lain.
3. Anotasi memilih objek manusia sebagai halangan, sedangkan depth memilih region numerik terdekat.
4. Evaluator masih berbasis string matching sederhana, sehingga sinonim dan frasa umum dapat dihitung salah.
5. Beberapa gambar terlalu close-up dan bukan skenario jalur indoor yang ideal.

## Celah Yang Akan Digoreng Penguji

1. "Depth membantu" belum terbukti kuat. Distance dan obstacle accuracy baru 26.67%.
2. Prompt fusion belum punya hasil lengkap karena runtime gagal.
3. Dataset terlalu kecil dan homogen.
4. Ground truth jarak subjektif karena tidak diukur dengan meter/sensor.
5. Latency terlalu tinggi untuk aplikasi bantu real-time.
6. Evaluator otomatis terlalu sederhana untuk klaim kualitas deskripsi.
7. `gemma_only` quality heuristic lebih tinggi daripada `gemma_depth`, jadi narasi bahwa depth selalu meningkatkan kualitas tidak aman.

## Rekomendasi Akademik

Prioritas penyelamatan:

1. Kalibrasi ulang threshold depth berdasarkan distribusi depth map dataset lokal.
2. Jalankan ulang `gemma_depth_prompted` sampai 30/30 gambar sukses, atau turunkan mode itu menjadi future work.
3. Tambahkan minimal 20-30 gambar lagi dari lokasi indoor berbeda.
4. Seimbangkan label obstacle/no-obstacle agar tidak bias.
5. Tambahkan penilaian manual deskripsi 1-5 oleh minimal 2 penilai.
6. Tulis Bab 4 dengan jujur: hasil saat ini menunjukkan pipeline berjalan, tetapi kontribusi depth belum konsisten.

## Kesimpulan Keras

Dengan hasil saat ini, penelitian belum bisa mengatakan bahwa depth-aware fusion berhasil meningkatkan kualitas deskripsi secara umum. Yang bisa dikatakan secara aman adalah: pipeline sudah dapat menjalankan baseline Gemma, depth-only, dan late fusion; late fusion meningkatkan position accuracy, tetapi belum memperbaiki object accuracy dan gagal pada mayoritas kategori jarak dekat. Mode prompt fusion belum valid karena runtime belum stabil.

Jika ini dibawa ke dosbing sebagai hasil final, bagian yang paling mudah diserang adalah klaim kontribusi depth. Jika dibawa sebagai hasil sementara dan diikuti kalibrasi depth + evaluasi ulang, proyek masih bisa diselamatkan.
