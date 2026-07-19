# Laporan Kesimpulan dan Pertanggungjawaban Proyek Bride-Gap

Tanggal audit: 15 Juli 2026. Sudut pandang: kesiapan skripsi S1 Informatika, pembimbing berstandar tinggi, dan penguji yang bersikap devil's advocate.

## 1. Putusan Singkat

Bride-Gap layak dipertahankan sebagai skripsi S1 **implementatif-evaluatif berskala proof-of-concept**, dengan syarat tidak dijual sebagai novelty algoritmik, sistem navigasi, atau metode yang terbukti mengungguli baseline. Secara software proyek lebih kuat daripada demo API sederhana. Secara penelitian, kontribusinya terbatas pada integrasi, kontrak bukti, evaluasi trade-off, dan analisis kegagalan pada 44 citra lokal.

Jika pembimbing mensyaratkan model baru, learned fusion, ground truth depth, atau bukti efektivitas untuk tunanetra, proyek ini tidak memenuhi standar tersebut. Jika standar yang diterapkan adalah kemampuan mahasiswa S1 merancang sistem AI, membuat pembanding yang sah, mengoreksi evaluator yang bocor, melaporkan hasil negatif, dan menjaga reproduktibilitas, proyek ini dapat dipertanggungjawabkan.

## 2. Proyek Ini Akhirnya Menjadi Apa

Judul kerja yang paling sesuai:

> Implementasi dan Evaluasi Depth-Aware Image Description Menggunakan Gemma dan Depth Anything V2 pada Citra Lingkungan Indoor

Sistem menerima citra indoor, menjalankan Gemma untuk deskripsi visual, menjalankan Depth Anything V2 Metric Indoor Small untuk estimasi depth monokular, meringkas depth map menggunakan grid 3x3 dan statistik persentil ke-10, lalu menambahkan satu pernyataan depth regional melalui evidence-constrained late fusion.

Pertanyaan penelitian yang dapat dijawab bukan "apakah sistem lebih pintar?" melainkan:

> Bagaimana penambahan metadata depth regional memengaruhi informasi spasial terstruktur, kualitas deskripsi, latensi, dan failure case dibanding deskripsi berbasis citra saja?

Mode final:

- `gemma_only`: baseline deskripsi visual;
- `depth_only`: ablasi untuk mengukur cabang depth, bukan pesaing kualitas bahasa;
- `gemma_depth`: evidence-constrained regional late fusion.

## 3. Perubahan Penting dari Versi Awal

| Sebelumnya | Keputusan final | Dasar |
|---|---|---|
| Depth-to-Spatial Prompting aktif | Dipensiunkan | Overall judge 3,5682, di bawah baseline 3,8636, dengan latensi lebih tinggi 14.274 ms. |
| Dynamic/adaptive depth bands | Dihapus | Recall obstacle turun 18,52 poin dan F1 turun 8,53 poin dibanding `grid_p10`. |
| Fusion verbose lima-enam kalimat | Diganti evidence-constrained fusion maksimal tiga kalimat | Pada kontrol cabang identik, groundedness, clarity, dan overall lebih baik daripada versi verbose. |
| Evaluator membaca kata posisi dari teks fusion | Dihapus | Aturan lama memberi kredit posisi palsu; position accuracy historis 90,91% turun menjadi 31,82% setelah kebocoran dihilangkan. |
| Skor kualitas heuristik 1-5 | Dihapus | Tidak memiliki reference caption atau penilai independen. |
| ROUGE-L direncanakan | Dihapus | Dataset tidak memiliki reference description independen. |
| Judge hanya membaca anotasi | Diganti image-aware judge | Judge menerima citra sebagai bukti utama dan anotasi sebagai pembanding sekunder. |
| Request inference sinkron untuk UI | UI memakai HTTP 202 dan polling | Browser tetap responsif; waktu komputasi model tidak menjadi lebih cepat. |
| SoM/Depth-Guided ROI dan detector | Dihentikan pada prototipe | Prototipe tidak melewati ambang kelayakan; melatih detector memperluas scope tanpa bukti cukup. |

## 4. Bukti Eksperimen yang Sah

Dataset final terdiri atas 44 citra dan 44 anotasi visual-relatif. Distribusi confidence adalah 40 `medium`, 4 `low`, dan 0 `high`. Label jarak terdiri atas 25 `dekat`, 10 `sedang`, 7 `jauh`, dan 2 `sangat_dekat`; label obstacle terdiri atas 27 `yes` dan 17 `no`.

Cabang depth memperoleh:

- distance-category accuracy 68,18%;
- obstacle accuracy 84,09%;
- precision 88,46%;
- recall 85,19%;
- F1 86,79%;
- confusion matrix 23 TP, 3 FP, 14 TN, dan 4 FN.

Angka tersebut hanya berlaku pada 44 citra lokal dan label visual-relatif. Angka itu bukan akurasi jarak meter dan bukan bukti keselamatan navigasi.

### Perbandingan kualitas teks yang benar

Audit menemukan bahwa `final_predictions_active_20260714.csv` masih memuat teks fusion verbose lama. Karena itu, skor 3,7348 dari summary lama tidak mewakili runtime evidence-constrained saat ini.

Perbandingan pasangan yang benar memakai baseline Gemma dan evidence-constrained fusion dari cabang Gemma yang sama:

| Metrik | Baseline | Evidence-constrained | Selisih | Bootstrap 95% snapshot |
|---|---:|---:|---:|---:|
| Semantic correctness | 3,8788 | 3,9773 | +0,0985 | [-0,0076; 0,2045] |
| Spatial accuracy | 3,4318 | 3,4621 | +0,0303 | [-0,2348; 0,3030] |
| Groundedness | 4,0455 | 3,9621 | -0,0833 | [-0,2348; 0,0682] |
| Clarity | 4,6667 | 4,4545 | -0,2121 | [-0,3333; -0,0985] |
| Overall | 3,8636 | 3,9015 | +0,0379 | [-0,1212; 0,1970] |

Kesimpulan: tidak ada bukti bahwa fusion meningkatkan kualitas keseluruhan. Overall sedikit lebih tinggi, tetapi interval memotong nol. Clarity justru lebih rendah dan interval tidak memotong nol. Hasil yang lebih kuat hanya berlaku ketika evidence-constrained dibandingkan dengan fusion verbose lama, bukan ketika dibandingkan dengan baseline.

Object, position, dan joint accuracy pada kontrol cabang sama identik dengan baseline: 29,55%, 29,55%, dan 9,09%. Angka 34,09%, 31,82%, dan 11,36% dari run `gemma_depth` historis berasal dari pemanggilan Gemma terpisah dan tidak boleh disebut sebagai peningkatan akibat fusion.

## 5. Poin Kuat

1. **Batas klaim lebih jujur daripada mayoritas demo AI.** Sistem membedakan fakta visual Gemma, fakta depth regional, template, dan guardrail.
2. **Evaluator telah diperbaiki setelah ditemukan kebocoran.** Mengakui penurunan metrik karena koreksi lebih kuat secara akademik daripada mempertahankan angka tinggi yang salah.
3. **Ada baseline, ablasi, dan kontrol kebijakan.** Desain final tidak sekadar menjalankan satu pipeline tanpa pembanding.
4. **Hasil negatif tidak disembunyikan.** Prompting, adaptive bands, dan SoM dihentikan berdasarkan hasil, bukan dipertahankan sebagai gimmick.
5. **Instrumentasi cukup baik untuk S1.** Ada preflight, mode-specific metrics, confusion matrix, paired bootstrap snapshot, cache judge, manifest hash, dan raw per-image output.
6. **Arsitektur backend dapat dijelaskan.** HTTP 202, polling, bounded in-process queue, dan worker-thread offloading menunjukkan pemahaman software engineering.
7. **Object-depth binding tidak dipalsukan.** Pipeline mengakui tidak memiliki box, mask, atau korespondensi objek-piksel.

## 6. Poin Lemah dan Risiko Sidang

### Critical

1. **Tidak ada novelty algoritmik.** Intinya tetap integrasi dua pretrained model dan post-processing berbasis aturan.
2. **Metode aktif dan artefak utama sempat tidak identik.** File bernama `final_predictions_active` masih berisi fusion verbose. Koreksi ini harus dijelaskan dan artefak 15 Juli harus dijadikan rujukan teks final.
3. **Fusion tidak terbukti mengungguli baseline.** Nilai overall tidak berbeda meyakinkan dan clarity lebih buruk.
4. **Validitas anotasi lemah.** Semua confidence hanya medium/low, tidak ada anotator independen, agreement, sensor depth, atau reference caption.

### Major

1. Dataset 44 citra terlalu kecil untuk generalisasi dan tidak merupakan external test set.
2. Pemilihan threshold/post-processing dan evaluasi berada pada snapshot data lokal; risiko overfitting keputusan desain tetap ada.
3. Joint object-position accuracy 9,09% pada kontrol menunjukkan pemahaman objek-lokasi masih lemah.
4. Grid 3x3 hanya ringkasan kasar dan dapat salah menyamakan foreground lantai dengan objek penghalang.
5. Checkpoint bernama metric-indoor, tetapi penelitian tidak mengevaluasi akurasi metrik karena tidak memiliki intrinsics atau ground truth meter.
6. LLM judge provider-dependent dan belum diuji agreement terhadap manusia. Field `critical_errors` juga berupa daftar bebas tanpa taksonomi atau threshold formal; jumlah baris yang terisi tidak boleh diperlakukan sebagai metrik tervalidasi.
7. Label model `cx/gpt-5.5` adalah label rute 9router, bukan bukti snapshot upstream immutable.
8. Artefak final dan dokumen audit masih untracked dalam worktree; tanpa commit/tag, reproduktibilitas versi belum aman.

### Minor

1. Async/polling memperbaiki pengalaman UI, bukan latency model.
2. Queue tidak persisten, single-process, dan hilang saat restart.
3. Sistem belum diuji pada video, perangkat berbeda, pencahayaan luas, atau pengguna tunanetra.

## 7. Devil's Advocate: Argumen Terkuat untuk Menolak Proyek

> "Proyek ini hanya menempelkan output Gemma dengan ringkasan Depth Anything. Tidak ada training, tidak ada grounding objek-depth, dataset hanya 44 citra dengan anotasi satu peneliti, dan hasil fusion tidak lebih baik daripada baseline. Bahkan clarity turun. Angka object/position yang sempat terlihat meningkat ternyata berasal dari pemanggilan Gemma berbeda, bukan fusion. Maka depth belum terbukti memperbaiki deskripsi; sistem ini lebih tepat disebut demonstrasi integrasi daripada penelitian Informatika yang menghasilkan kontribusi baru."

Argumen tersebut sebagian benar dan tidak boleh dibantah dengan jargon. Titik pertahanan proyek adalah bahwa standar skripsi S1 implementatif tidak selalu mensyaratkan model baru. Kontribusi yang benar adalah perancangan pipeline yang dapat diaudit, pemisahan provenance, evaluator tanpa leakage, controlled comparison, evaluasi trade-off, dan dokumentasi kegagalan. Pertahanan ini hanya bekerja bila judul, rumusan masalah, Bab 4, dan kesimpulan konsisten dengan kontribusi tersebut.

## 8. Simulasi Pertanyaan Penguji dan Jawaban yang Sah

### "Apa novelty penelitian Anda?"

Jawab: "Penelitian ini tidak mengklaim novelty algoritmik. Kontribusinya adalah implementasi dan evaluasi pipeline fusi visual-depth dengan kontrak bukti regional, pembanding berpasangan, serta koreksi evaluator agar klaim posisi tidak bocor dari teks fusion."

Jangan jawab: "Saya menciptakan arsitektur AI baru."

### "Kalau fusion tidak lebih baik, mengapa proyek ini dipertahankan?"

Jawab: "Pertanyaan penelitian saya mengukur pengaruh dan trade-off, bukan mengasumsikan peningkatan. Depth menghasilkan metadata kategori relatif dan obstacle yang dapat diukur, tetapi belum meningkatkan kualitas bahasa keseluruhan. Temuan negatif tersebut menjadi hasil penelitian dan menjelaskan batas late fusion berbasis aturan."

### "Bukankah depth metric-indoor bisa memberi jarak meter?"

Jawab: "Checkpoint memang varian metric-indoor, tetapi dataset saya tidak memiliki intrinsics kamera dan ground truth sensor. Karena itu output hanya ditransformasikan dan dievaluasi sebagai kategori visual-relatif."

### "Mengapa hanya 44 citra?"

Jawab: "Dataset ini dibatasi sebagai proof-of-concept lokal. Saya tidak mengklaim generalisasi. Keterbatasan jumlah, distribusi, dan sumber citra dilaporkan eksplisit."

### "Siapa yang membuat ground truth?"

Jawab: "Saya membuat anotasi visual-relatif terstruktur dan melakukan revalidasi manual. Saya tidak menyebutnya ground truth fisik, expert annotation, atau inter-annotator agreement."

### "Mengapa memakai LLM judge?"

Jawab: "Dataset tidak memiliki reference caption independen. Judge digunakan sebagai bukti sekunder, melihat citra asli, dibutakan dari nama mode, dijalankan tiga kali, dan hasil per citra disimpan. Judge tidak menggantikan manusia dan bias provider tetap menjadi keterbatasan."

### "Mengapa ROUGE-L dihapus?"

Jawab: "ROUGE membutuhkan reference description yang sah. Menggunakan notes atau output model sendiri akan menghasilkan evaluasi sirkular."

### "Mengapa tidak melatih detector agar objek terhubung dengan depth?"

Jawab: "Object-grounded fusion membutuhkan bounding box/mask, label grounding, dan evaluasi detector tersendiri. Prototipe awal tidak memenuhi ambang kelayakan. Menambah detector tanpa validasi akan memperbesar klaim dan risiko metodologis."

### "Apakah async membuat inferensi lebih cepat?"

Jawab: "Tidak. Polling membuat request UI tidak menunggu koneksi tunggal dan menjaga event loop responsif. Waktu komputasi model tetap ada."

### "Mengapa menggunakan Waterfall padahal proyek mengalami banyak perubahan?"

Jawab: "Waterfall digunakan sebagai kerangka SDLC untuk requirement, design, implementation, testing, dan maintenance. Metode penelitian eksperimen dijelaskan terpisah. Karena implementasi mengalami feedback dan koreksi, istilah yang jujur adalah modified Waterfall atau Waterfall dengan verification feedback, bukan Waterfall murni satu arah."

## 9. Hal yang Wajib Konsisten dalam Penulisan

Gunakan:

- deskripsi visual-spasial indoor;
- estimasi kedalaman monokular;
- kategori visual-relatif;
- potensi halangan visual;
- area/region relatif lapang;
- evidence-constrained regional late fusion;
- proof-of-concept lokal;
- implementasi dan evaluasi trade-off.

Hindari:

- navigasi aman atau rekomendasi arah berjalan;
- jarak absolut/presisi meter;
- human ground truth atau expert annotation;
- model baru atau novelty arsitektur;
- fusion terbukti meningkatkan kualitas;
- temperature 0 menjamin determinisme;
- 9router localhost berarti citra tidak keluar dari perangkat;
- F1 86,79% berarti sistem akurat secara umum.

## 10. Putusan ala Pembimbing/Penguji

**Keputusan: layak dilanjutkan dengan major revision pada argumentasi dan penguncian artefak, bukan mengganti topik.**

Alasannya:

- software dan jejak eksperimen cukup untuk standar implementasi S1;
- desain evaluasi sekarang lebih jujur dan memiliki pembanding;
- mengganti topik dalam batas waktu sekarang lebih berisiko daripada memperbaiki pertanggungjawaban;
- tetapi proyek akan terlihat lemah atau bahkan menyesatkan bila masih mengklaim peningkatan, novelty, ground truth, atau menggunakan artefak verbose sebagai keluaran metode aktif.

Urutan prioritas sebelum diserahkan:

1. jadikan artefak perbandingan baseline-vs-evidence-constrained 15 Juli sebagai sumber angka kualitas teks;
2. selaraskan Bab 1, Bab 3, Bab 4, dan Bab 5 dengan pertanyaan trade-off;
3. masukkan failure cases konkret dan jelaskan mengapa depth tidak otomatis memperbaiki deskripsi;
4. lakukan pemeriksaan manual anotasi dan contoh output, tetapi jangan mengklaim agreement;
5. commit/tag kode, dokumen, konfigurasi, dan hash artefak final;
6. siapkan demonstrasi UI serta jawaban sidang pada Bagian 8.
