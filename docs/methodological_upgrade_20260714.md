# Audit dan Peningkatan Metodologis Bride-Gap

Tanggal audit: 14 Juli 2026. Sasaran: standar pembimbing dengan fokus computer vision, software engineering, keterukuran eksperimen, dan batas klaim yang dapat dipertahankan.

## Putusan Utama

Proyek ini sudah lebih dari demo API, tetapi belum boleh dijual sebagai metode baru yang unggul atau sistem navigasi. Kontribusi yang paling defensible adalah rekayasa dan evaluasi pipeline fusi visual-spasial indoor: membandingkan baseline VLM, depth-only, dan late fusion berbasis aturan pada data lokal yang sama, dengan provenance output serta batas klaim eksplisit.

> **Koreksi 14 Juli 2026:** evaluator lama mengizinkan `object_position` cocok dari kata arah apa pun di `final_description`. Karena fusion sendiri menambahkan nama region, position accuracy 90,91% pada laporan lama mengandung kebocoran evaluasi dan tidak boleh lagi dipakai. Evaluator aktif hanya membandingkan field terstruktur, menambahkan object-position joint accuracy, dan menulis metrik semantik sebagai N/A untuk `depth_only`. Skor kualitas teks heuristik 1-5 juga dihapus karena tidak mempunyai reference atau penilai independen.

| Usulan | Putusan | Alasan dan trade-off |
|---|---|---|
| Dynamic depth banding + variance filter | Dihapus dari sistem aktif | Pada 44 citra, recall obstacle turun 18,52 poin persentase dan F1 turun 8,53 poin. Mempertahankannya menambah parameter dan beban pembuktian tanpa manfaat empiris. |
| Async/polling FastAPI | Dipakai untuk UI | HTTP 202 dan polling mencegah browser menggantung pada satu request panjang. Depth inference blocking dipindahkan ke worker thread. Antrean masih single-process, non-durable, dan bukan pengganti Celery/Redis. |
| F1 obstacle | Dipakai bersama accuracy dan confusion matrix | F1 lebih informatif untuk kelas positif obstacle, tetapi tetap menyembunyikan TN jika berdiri sendiri. Karena itu TP/FP/TN/FN, precision, recall, F1, dan coverage dilaporkan bersama. |
| ROUGE-L | Dihapus dari evaluasi aktif | Dataset final tidak memiliki reference description independen. Nilai N/A tidak memberi bukti, sedangkan memakai `notes` sebagai referensi akan mengubah fungsi anotasi secara tidak sah. |
| LLM-as-a-Judge | Dipakai sebagai evaluasi tambahan image-aware | Judge dibutakan dari nama mode, menerima citra sumber yang dinormalisasi dan dibatasi 768 piksel sebagai bukti utama serta anotasi sebagai pembanding sekunder, memakai structured output, tiga repeat, standard deviation, dan cache. Ia tetap bias/provider-dependent dan bukan pengganti manusia. |
| Depth-to-Spatial Prompting | Dihapus dari sistem aktif | Judge image-aware lama dan latensi tidak menunjukkan keuntungan yang menutup kompleksitas tambahan. Perbandingan object/position dari evaluator lama tidak lagi dipakai sebagai dasar karena terdampak kebocoran evaluasi. |

## Keputusan Arsitektur Setelah Koreksi Evaluator

Menaikkan kompleksitas menjadi object-grounded fusion ditolak untuk implementasi saat ini. Pipeline tidak menghasilkan object box, mask, track, atau korespondensi piksel antara objek Gemma dan depth. Pada 44 citra, posisi terstruktur Gemma hanya selaras dengan region depth global pada 1 citra; bahkan posisi anotasi objek utama hanya selaras dengan region depth global pada 21 citra (47,73%). Jadi menyebut depth region terdekat sebagai jarak objek utama akan membuat klaim yang tidak dapat dibuktikan.

Mode `gemma_depth` kini memakai **evidence-constrained regional late fusion**. Gemma tetap menyatakan isi visual; depth hanya menyatakan region grid 3x3, kategori relatif, dan potensi halangan regional untuk `dekat`/`sangat_dekat`. Kebijakan verbose lama dipertahankan hanya untuk kontrol pasangan dengan cabang Gemma dan depth yang identik. Ini adalah keputusan arsitektur proyek, bukan klaim novelty algoritmik umum.

Evaluator ketat pada artefak aktif lama menghasilkan object accuracy 34,09%, position accuracy 31,82%, dan object-position joint accuracy 11,36% untuk `gemma_depth`; hasil depth tetap distance accuracy 68,18%, obstacle accuracy 84,09%, dan F1 86,79%. Perubahan besar dari position 90,91% menjadi 31,82% bukan regresi model, melainkan penghapusan kredit palsu dari teks fusion.

Pada kontrol 44 pasangan dengan cabang Gemma/depth identik, kebijakan berbatas bukti menaikkan judge overall dari 3,7045 menjadi 3,9015, groundedness dari 3,7803 menjadi 3,9621, dan clarity dari 4,2879 menjadi 4,4545. Interval bootstrap snapshot pasangan tidak memotong nol untuk tiga metrik tersebut, tetapi hasil tetap provider-dependent dan bukan bukti generalisasi. Rincian ada di `docs/evidence_constrained_fusion_upgrade_20260714.md`.

## Temuan yang Membatalkan Sebagian Saran Awal

### Tidak Ada LLM Embeddings atau Korelasi

Implementasi saat ini tidak menghitung embedding LLM dan tidak melakukan correlation analysis antara depth map dengan embedding. Menulis “evaluasi korelasi relative depth map dengan LLM embeddings” pada Bab 1 adalah salah secara faktual dan mudah dipatahkan saat sidang.

Istilah yang benar adalah integrasi metadata kedalaman hasil post-processing dengan deskripsi visual VLM, lalu evaluasi output pipeline terhadap anotasi spasial terstruktur.

### Checkpoint Depth Bertipe Metric-Indoor, Bukan Murni Relative

Model lokal adalah `Depth-Anything-V2-Metric-Indoor-Small-hf`. Paper Depth Anything V2 dan model card resminya memang menyediakan fine-tuned metric depth model untuk indoor. Namun, keluaran monocular metric tetap sensitif terhadap domain, intrinsics, focal length, dan kondisi scene. Dataset ini tidak menyediakan ground truth meter atau kalibrasi kamera, sehingga penelitian memperlakukan output sebagai bukti untuk kategori relatif, bukan pengukuran sensor-grade.

Konsekuensinya, dua klaim ekstrem sama-sama salah:

- “Model hanya menghasilkan relative depth” mengabaikan tipe checkpoint.
- “Model mengukur jarak absolut dengan akurat” tidak didukung desain eksperimen.

### Fine-Tuning LLM Tidak Otomatis Mengurangi Latensi

Fine-tuning dapat mengubah perilaku dan kepatuhan output, tetapi tidak otomatis membuat inferensi lebih cepat. Latensi dipengaruhi ukuran model, quantization, hardware, panjang prompt/output, dan serving stack. Saran Bab 5 yang menghubungkan fine-tuning langsung dengan pengurangan latensi late fusion harus diganti dengan eksperimen distillation, model lebih kecil, quantization, prompt compression, parallelism yang aman, atau caching.

### Temperature Nol Bukan Determinisme

`temperature=0` mengurangi sampling variation, tetapi provider/model/runtime tetap dapat menghasilkan variasi. Reproducibility yang lebih jujur membutuhkan snapshot model, rubric version, input hash, repeat, standard deviation, caching, dan penyimpanan raw result. Istilah “menjaga konsistensi” masih dapat dipakai; istilah “menjamin deterministik” tidak boleh dipakai.

## Dasar Penghapusan Adaptive Bands

Pemeriksaan internal memakai depth map hasil inferensi yang sama per citra agar perbedaan hanya berasal dari post-processing. Hasil berikut dicatat sebagai jejak keputusan desain, bukan sebagai fitur atau kontribusi aktif.

| Metrik | `grid_p10` | `adaptive_bands_v1` | Selisih adaptif |
|---|---:|---:|---:|
| Position accuracy | 0,4773 | 0,5000 | +0,0227 |
| Distance category accuracy | 0,6818 | 0,5682 | -0,1136 |
| Obstacle accuracy | 0,8409 | 0,7727 | -0,0682 |
| Precision obstacle | 0,8846 | 0,9474 | +0,0628 |
| Recall obstacle | 0,8519 | 0,6667 | -0,1852 |
| F1 obstacle | 0,8679 | 0,7826 | -0,0853 |
| TP / FP / TN / FN | 23 / 3 / 14 / 4 | 18 / 1 / 16 / 9 | recall adaptif memburuk |

Interpretasi: variance filter membuat metode adaptif lebih konservatif, sehingga false positive turun dari 3 menjadi 1. Harga yang dibayar terlalu besar: false negative naik dari 4 menjadi 9. Karena recall turun 18,52 poin persentase dan F1 turun 8,53 poin, implementasi, konfigurasi, script, dan artefak aktif adaptive bands dihapus. Sistem hanya mempertahankan `grid_p10`.

Dynamic quantile juga memiliki kelemahan konseptual: setiap citra cenderung dipaksa memiliki band near/middle/far relatif terhadap distribusinya sendiri. Ini membantu membaca struktur intra-image tetapi mengurangi keterbandingan kategori antar-image. Fixed threshold mempunyai masalah kalibrasi, tetapi kategorinya lebih stabil lintas citra. Solusi ilmiah bukan memilih salah satu secara dogmatis; solusinya adalah dataset calibration terpisah atau sensor ground truth.

## Dasar Penghapusan Depth-to-Spatial Prompting

Semua mode lama dinilai pada 44 citra yang sama. Skor judge berasal dari `cx/gpt-5.5` melalui 9router dengan citra, tiga pengulangan, dan rubric `spatial-description-judge-v2-image-aware`. Judge overall prompted 3,5682 lebih rendah daripada Gemma baseline 3,8636 dan late fusion lama 3,7348, sementara latensinya 14.274 ms dibanding 10.569 ms dan 11.795 ms. Selisih judge prompted terhadap Gemma baseline -0,2955 mempunyai interval bootstrap snapshot [-0,5227; -0,0606]. Hasil ini, ditambah jalur inferensi ekstra, cukup untuk memensiunkan mode; object/position dan heuristic quality lama tidak dipakai lagi sebagai bukti karena evaluator tersebut sudah dibatalkan.

Implementasi, opsi UI/API, prompt builder, dan test khusus prompting dihapus. Baris penilaian disimpan sebagai `results/retired_prompted_decision_evidence_20260714.csv` agar keputusan negatif tetap dapat diaudit. Perbandingan baru yang sah adalah kebijakan verbose lama versus kebijakan berbatas bukti pada cabang Gemma dan depth yang sama; hasilnya didokumentasikan di `docs/evidence_constrained_fusion_upgrade_20260714.md`.

## Arsitektur Async yang Sebenarnya

Alur UI sekarang:

```text
Browser -> POST /analysis-jobs -> HTTP 202 + job_id
        -> GET /analysis-jobs/{job_id}
        -> queued -> running -> completed/failed
```

Antrean AnyIO mempunyai kapasitas 8 dan menyimpan maksimal 100 record secara default. Depth ONNX yang synchronous dijalankan melalui worker thread agar event loop tetap dapat melayani health check dan polling. Implementasi ini cukup untuk demonstrasi single-process lokal.

Keterbatasan yang harus disebutkan:

- tidak persisten; restart menghapus job;
- tidak aman untuk koordinasi multi-worker;
- hanya satu consumer, sehingga throughput tidak otomatis meningkat;
- HTTP polling mengubah user experience, bukan mempercepat model;
- job yang sedang berjalan tetap memakai CPU/memori;
- deployment production membutuhkan queue eksternal, persistence, retry policy, idempotency, authentication, rate limiting, dan observability.

Dengan redaksi tersebut, klaim “backend tidak nge-hang” diubah menjadi klaim teknis yang dapat diuji: request diterima cepat dengan 202 dan status dapat dipoll, sementara pekerjaan inference tetap membutuhkan waktu komputasi.

## Evaluasi yang Dapat Dipertahankan

### Spasial

Gunakan distance accuracy, obstacle accuracy, precision, recall, positive-class F1, dan confusion matrix. Pada artefak final lama untuk mode depth, confusion matrix 23 TP, 3 FP, 14 TN, dan 4 FN menghasilkan precision 0,8846, recall 0,8519, dan F1 0,8679. Jangan menyebut F1 sebagai bukti generalisasi; ia hanya merangkum performa pada 44 citra lokal.

### Teks

Evaluasi leksikal berbasis reference caption tidak digunakan karena dataset final belum memiliki reference description independen. Menghasilkan skor dari `notes` atau dari output model sendiri akan menciptakan reference yang tidak sah. Jika kelak reference caption dibuat, protokol serta metriknya harus ditetapkan sebelum melihat hasil model.

LLM judge diposisikan sebagai evaluasi tambahan, bukan pengganti manusia. Citra menjadi bukti visual utama agar judge dapat memeriksa fakta yang tidak tercakup anotasi; anotasi terstruktur hanya pembanding sekunder. Report minimal harus memuat model, provider/router, rubric version, temperature, repeat count, mean, standard deviation, cache policy, jumlah failure, dan biaya. Kemampuan menerima gambar tidak menghilangkan risiko salah persepsi, bias rubric, atau bias model.

Konsekuensi privasi tidak boleh disembunyikan: localhost hanya alamat 9router, bukan bukti bahwa inferensi model berlangsung lokal. Citra dapat diteruskan ke provider upstream sesuai konfigurasi router. Selain itu, `cx/gpt-5.5` adalah label rute yang berhasil dipakai pada run ini; tanpa metadata resolusi upstream, label tersebut tidak boleh disebut snapshot provider immutable.

### Software

Unit/API tests menutup kontrak depth analysis, evaluator, queue/polling, fusion, validation, preflight, logging, dan Gemma client. Passing tests membuktikan konsistensi implementasi terhadap kontrak test, bukan kebenaran ilmiah model.

## Redaksi Bab 1 yang Disarankan

### Batasan Masalah

> Penelitian berfokus pada implementasi dan evaluasi pipeline perangkat lunak yang menggabungkan deskripsi visual dari vision-language model dengan metadata spasial hasil post-processing peta kedalaman monokular. Penelitian tidak menghitung korelasi embedding dan tidak mengevaluasi akurasi jarak absolut seperti sistem berbasis sensor RGB-D, ToF, atau LiDAR.

> Checkpoint kedalaman yang digunakan merupakan varian metric-indoor Depth Anything V2, tetapi keluarannya ditransformasikan dan dievaluasi sebagai kategori kedalaman visual relatif karena dataset tidak memiliki ground truth meter, parameter intrinsik kamera, maupun sensor kedalaman terkalibrasi.

> Evaluasi dilakukan pada dataset lokal sebanyak 44 citra indoor sebagai proof-of-concept. Hasil hanya berlaku pada snapshot dataset, konfigurasi model, dan lingkungan runtime yang dilaporkan serta tidak ditujukan untuk generalisasi global, navigasi nyata, atau klaim keselamatan.

> Evaluasi deskripsi memakai LLM-as-a-Judge image-aware sebagai bukti tambahan karena dataset belum memiliki reference description independen. Judge menerima citra sebagai bukti utama dan anotasi terstruktur sebagai pembanding sekunder. Model, provider/router, rubric version, temperature 0, pengulangan, pelaporan variasi, dan cache dicatat; konfigurasi tersebut mengurangi variasi tetapi tidak menjamin determinisme atau kesetaraan dengan penilaian manusia.

> Post-processing kedalaman mengasumsikan bahwa statistik region pada peta kedalaman cukup representatif untuk kategori visual relatif. Hasil dapat dipengaruhi domain shift, intrinsics/focal length, perspektif kamera, objek reflektif atau transparan, area textureless, clutter, occlusion, serta distribusi kedalaman yang berbeda antar-citra.

Redaksi “permukaan lantai relatif seragam” tidak dipakai karena implementasi tidak melakukan segmentasi lantai atau memilih floor ROI secara eksplisit. Menuliskan asumsi tersebut akan menciptakan komponen metode yang sebenarnya tidak ada.

## Redaksi Bab 5 yang Disarankan

> Penelitian selanjutnya disarankan menggunakan kamera RGB-D, ToF, atau LiDAR terkalibrasi untuk menyediakan ground truth kedalaman metrik, sehingga pengaruh scale ambiguity, parameter kamera, dan domain shift dapat dievaluasi secara langsung.

> Dataset perlu diperluas secara stratified pada bangunan, perangkat kamera, pencahayaan, tingkat clutter, dan kategori kedalaman yang berbeda. Anotasi sebaiknya melibatkan lebih dari satu anotator, mengukur inter-annotator agreement, serta menyediakan reference description Bahasa Indonesia yang ditulis independen dari output model.

> Pengembangan post-processing baru perlu ditetapkan dan dikalibrasi pada calibration/validation set yang terpisah sebelum diuji sekali pada test set. Kandidat dapat mencakup uncertainty estimation yang terkalibrasi dan evaluasi failure case pada permukaan reflektif, transparan, atau textureless.

> Pengurangan latensi sebaiknya diuji melalui model yang lebih kecil, quantization, distillation, prompt compression, caching, atau serving hardware yang berbeda. Fine-tuning hanya disarankan jika tujuannya adalah memperbaiki kepatuhan dan kualitas output, bukan diasumsikan otomatis mengurangi latensi.

> Evaluasi bahasa Indonesia dapat dikembangkan melalui benchmark spasial dengan reference caption jamak dan human rating. Metrik leksikal baru boleh ditambahkan setelah reference dan protokolnya tersedia; evaluator semantik perlu diuji agreement dan biasnya terhadap penilaian manusia.

## Jawaban terhadap Serangan “Hanya Model Glue”

Jawaban yang defensible bukan menyangkal integrasi. Akui bahwa model dasar tidak dilatih ulang. Nilai penelitian berada pada:

1. definisi kontrak metadata spasial dari depth map kontinu ke region/kategori yang dapat diaudit;
2. perbandingan strategi integrasi pada input yang sama;
3. evaluasi mode-specific agar Gemma baseline tidak dihukum untuk metadata yang memang tidak diekstrak;
4. failure analysis, provenance, dan batas klaim;
5. arsitektur inference lokal yang tidak memblokir request browser dan mempunyai kontrak status yang teruji.

Jika dosen menuntut novelty algoritmik, proyek ini masih lemah: tidak ada learned fusion dan tidak ada ground truth kedalaman metrik. Jangan mengubah kelemahan itu menjadi jargon. Pilihan aman adalah memosisikan kontribusi sebagai implementasi dan evaluasi sistem fusion PoC yang transparan. Keputusan menghapus kandidat yang memburuk menunjukkan disiplin desain, bukan novelty metode.

## Readiness Realistis

| Aspek | Status berbasis bukti | Gap yang masih terbuka |
|---|---|---|
| Software engineering | Kontrak API, queue bounded, offloading blocking work, preflight, logging, dan test suite tersedia. | Belum ada queue persisten multi-worker, observability produksi, atau uji beban. |
| Instrumentasi evaluasi | F1/confusion, image-aware judge, repeat/cache, dan artifact paths tersedia. | Judge belum diuji agreement terhadap manusia dan label rute model belum membuktikan snapshot upstream immutable. |
| Validitas dataset | Terdapat 44 citra lokal dengan anotasi terstruktur dan manifest. | Ukuran kecil, label tidak seimbang, confidence didominasi medium, tanpa sensor ground truth, multi-annotator, atau external validation. |
| Bukti kualitas teks | Judge image-aware telah dioperasionalkan dan output per citra disimpan. | Belum ada human rating, reference caption independen, atau inter-rater agreement. |
| Kesiapan klaim sidang | Bukti cukup untuk PoC implementasi dan evaluasi lokal jika batas klaim dinyatakan. | Tidak cukup untuk novelty algoritmik, generalisasi lintas domain, akurasi jarak absolut, atau keselamatan navigasi. |

Status tersebut sengaja tidak diberi skor numerik karena proyek tidak memiliki rubric kesiapan tervalidasi. Target peningkatan paling bernilai bukan menambah jargon, melainkan menyelesaikan human rating/agreement, reference caption independen bila metrik leksikal memang diperlukan, dan external/calibrated validation.

## Sumber Primer dan Dokumentasi Resmi

- [Depth Anything V2 paper](https://arxiv.org/abs/2406.09414)
- [Depth Anything V2 Metric Indoor Small model card](https://huggingface.co/depth-anything/Depth-Anything-V2-Metric-Indoor-Small-hf)
- [Transformers Depth Anything V2 documentation](https://huggingface.co/docs/transformers/model_doc/depth_anything_v2)
- [SpatialRGPT paper](https://arxiv.org/abs/2406.01584)
- [Learning to Evaluate Image Captioning](https://openaccess.thecvf.com/content_cvpr_2018/html/Cui_Learning_to_Evaluate_CVPR_2018_paper.html)
- [scikit-learn F1 definition](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html)
- [Position bias in LLM-as-a-Judge](https://aclanthology.org/2025.ijcnlp-long.18/)
- [Human and LLM bias in language-model evaluation](https://aclanthology.org/2024.emnlp-main.474/)
- [OpenAI GPT-4o mini model snapshot](https://developers.openai.com/api/docs/models/gpt-4o-mini)
- [FastAPI background task caveat for heavier computation](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [AnyIO memory object streams](https://anyio.readthedocs.io/en/stable/streams.html#memory-object-streams)
