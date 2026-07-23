# Laporan Maturitas dan Penyelesaian Proyek Bridge-Gap

Tanggal audit: 23 Juli 2026
Lokasi audit: `D:\Tugas\SKRIPSI\Bride-Gap\Program`
Branch: `feat/complete-iot-assisted-analysis` pada commit `0455019`

## Putusan eksekutif

Bridge-Gap sudah layak disebut **prototipe teknis terintegrasi yang bekerja**, tetapi **belum layak disebut penelitian skripsi yang selesai**. Implementasi utama, kontrak sensor, kalibrasi, dataset beku, dan regression test sudah kuat. Bukti penelitian masih terlalu sempit untuk menopang klaim umum: evaluasi visual hanya memakai 18 citra dari satu koper pada satu setup, dinilai satu evaluator, tanpa baseline, tanpa inter-rater agreement, dan tanpa pengujian generalisasi. Folder `Penulisan/` juga masih kosong.

Estimasi audit:

| Dimensi | Kematangan | Status |
|---|---:|---|
| Implementasi software | 88% | Substantially complete |
| Integrasi hardware dan sensor | 85% | Complete untuk PoC terkendali |
| Reproducibility dan provenance | 78% | Kuat, tetapi provenance provider historis tidak lengkap |
| Dataset dan evaluasi penelitian | 52% | Pilot/hasil awal, belum cukup sebagai evaluasi final |
| Penulisan skripsi | 5% | Belum dimulai; hanya gudang fakta hasil |
| Kesiapan sidang keseluruhan | 55% | Belum siap |

Persentase tersebut adalah penilaian audit berbobot, bukan metrik otomatis atau persentase baris kode.

## Bukti yang telah terverifikasi

### Implementasi dan pengujian

- `90 passed` pada regression suite Python.
- `2 passed` pada test klien job JavaScript.
- `static/app.js` lolos `node --check`.
- `git diff --check` tidak menemukan whitespace error; hanya peringatan normalisasi LF/CRLF.
- Backend dapat diluncurkan dan permukaan `/`, `/health`, serta `/readiness` memberi HTTP 200.
- Saat audit, backend sehat tetapi readiness analisis `false` karena LM Studio/Gemma tidak aktif dan sensor fisik tidak terhubung. Ini kondisi dependency runtime, bukan kegagalan boot backend.

### Dataset dan manifest

- Manifest dataset v2 valid: 18 capture, 18 `capture_id`, 18 gambar, dan 18 checksum unik.
- Evaluation manifest valid: 18 run unik, 8 artefak terverifikasi, serta checksum run, output, snapshot sensor, dan skor visual cocok untuk seluruh 18 record.
- Semua 18 job selesai, tidak ada job gagal, mismatch capture-run, atau mismatch snapshot sensor.
- Raw provider response Gemma tidak dipertahankan; model ID dan prompt untuk run historis adalah derived provenance dari source/config aktif.

### Sensor

- Profil kalibrasi valid menggunakan 150 capture pada 20, 60, 100, 150, dan 200 cm.
- Verifikasi terpisah valid menggunakan 120 capture pada 40, 80, 125, dan 175 cm.
- Hasil verifikasi koreksi: MAE 0,673 cm, RMSE 1,045 cm, dan maksimum absolute error 5,271 cm; lolos gate 10 cm.
- Dataset evaluasi v2 memiliki valid-read rate 100% dan 18/18 evidence `paired`.
- Pada dataset v2, koreksi mengurangi bias tetapi sedikit menaikkan MAE dibanding raw reading yang disejajarkan. Karena itu tidak boleh diklaim bahwa koreksi selalu memperbaiki setiap metrik pada setiap dataset.

### Evaluasi deskripsi

- Skor rata-rata: objek 3,4444/4; posisi 3,4444/4; kejelasan 3,9444/4; naturalness 3,9444/4; kelengkapan 3,5556/4.
- Tidak ditemukan unsupported claim pada 18 output menurut satu evaluator teknis.
- Identitas koper tepat hanya 9/18; seluruh kegagalan identifikasi terjadi pada 30, 50, dan 75 cm.
- Rata-rata latency sekitar 41 detik per capture pada setup yang diuji; sistem tidak layak diklaim real-time.

## Yang sudah selesai

1. Scope kanonik sudah konsisten: RGB ke Gemma untuk deskripsi, dua HC-SR04 sebagai referensi frontal terpisah.
2. Capture dan analisis tertunda sudah dipisahkan; satu capture menghasilkan satu job dan memakai snapshot sensor tersimpan.
3. Status `paired`, `partial`, `pair_conflict`, `stale`, `direction_mismatch`, dan `unavailable` mempunyai kontrak eksplisit.
4. Sensor tidak dipakai sebagai identitas objek dan angka tidak dilekatkan pada objek bernama.
5. Kalibrasi dan verifikasi sensor memakai dataset terpisah.
6. Dataset v2 dan output evaluasi sudah dibekukan serta mempunyai checksum.
7. Legacy depth/fusion sudah dikeluarkan dari scope aktif dan dipisahkan sebagai sejarah.

## Yang belum selesai atau belum cukup kuat

### Blocker penelitian

1. **Dataset visual terlalu sempit.** Hanya satu koper, satu lingkungan, enam jarak, dan tiga pengulangan. Ini menguji satu seri terkendali, bukan kemampuan deskripsi indoor secara umum.
2. **Tidak ada baseline.** Belum ada pembanding yang memungkinkan klaim unggul atau kontribusi relatif Gemma/sistem.
3. **Hanya satu evaluator.** Skor visual belum mempunyai inter-rater agreement dan berisiko bias subjektif.
4. **Tidak ada split/pengujian generalisasi visual.** Pengulangan jarak pada target sama bukan pengganti variasi objek, scene, pencahayaan, sudut, dan material.
5. **Provenance model historis tidak lengkap.** Raw response provider, model ID per run, dan prompt/version per run tidak tersimpan langsung.
6. **Klaim gabungan sistem lemah.** Sensor dan deskripsi memang terintegrasi di UI/log, tetapi dievaluasi terpisah. Ini sah untuk PoC, namun bukan bukti fusion atau peningkatan kualitas deskripsi oleh sensor.

### Blocker operasional dan delivery

1. `Penulisan/` kosong; Bab I-V belum tersedia.
2. Worktree belum dibekukan: sebelum laporan ini terdapat 60 path berubah (43 deleted, 8 modified, 9 untracked) akibat cleanup dan finalisasi evaluasi.
3. `.venv` proyek tidak menyediakan executable Python; audit harus memakai Python 3.13 sistem. Setup baru belum reproducible hanya dengan mengikuti path virtual environment yang ada.
4. Readiness live saat audit `false`: Gemma error karena LM Studio tidak aktif dan sensor unavailable karena hardware tidak terhubung.
5. Belum ada bukti end-to-end live terbaru yang sekaligus menunjukkan Gemma ready, dua sensor fresh, capture kamera, job selesai, dan hasil tampil di UI setelah cleanup saat ini.

## Batas klaim yang aman

Proyek saat ini dapat mengklaim bahwa prototipe:

- menghasilkan deskripsi visual-spasial indoor Bahasa Indonesia pada dataset terkendali;
- mencocokkan capture dengan snapshot dua HC-SR04 dan mempertahankan provenance;
- mengukur error sensor pada target planar dalam setup dan rentang yang diuji;
- menahan angka rata-rata pada evidence yang tidak memenuhi gate.

Proyek belum dapat mengklaim:

- performa umum pada beragam scene indoor;
- keunggulan dibanding metode/model lain;
- jarak sensor ke objek yang disebut Gemma;
- fusion multimodal yang meningkatkan deskripsi;
- manfaat aksesibilitas, keselamatan, navigasi, atau kemandirian pengguna;
- operasi real-time universal.

## Urutan next step yang direkomendasikan

### Gate 1 - bekukan baseline engineering

Selesaikan dan review perubahan cleanup/evaluasi, perbaiki environment setup, jalankan ulang seluruh test, validasi manifest, dan commit sebagai satu baseline yang dapat direproduksi. Jangan menambah fitur baru sebelum gate ini selesai.

Kriteria lulus:

- worktree bersih;
- environment baru dapat dibuat dari requirement yang terkunci;
- 90 Python test dan 2 JavaScript test tetap lulus;
- kedua validator manifest tetap valid;
- hasil checksum dataset tidak berubah.

### Gate 2 - tentukan desain penelitian final sebelum mengambil data tambahan

Bekukan rumusan masalah, unit analisis, dataset, baseline, rubrik, evaluator, dan acceptance rule. Pilihan paling aman adalah mempertahankan penelitian sebagai evaluasi teknis dua jalur, bukan fusion dan bukan navigasi.

Minimum yang disarankan:

- beberapa objek dan scene indoor yang ditentukan sebelum eksekusi;
- holdout yang benar-benar berbeda dari seri koper saat ini;
- baseline yang relevan dan murah dijalankan;
- dua evaluator atau lebih dengan aturan disagreement dan inter-rater agreement;
- model ID, prompt hash/text, parameter, raw response, dan timestamp disimpan per run;
- failure/missing output tetap masuk denominator.

### Gate 3 - jalankan evaluasi final sekali

Setelah protokol dibekukan, jalankan dataset final tanpa mengubah prompt/rubrik berdasarkan hasil. Dataset koper 18 capture dipertahankan sebagai pilot atau controlled-distance subset, bukan seluruh bukti generalisasi.

### Gate 4 - mulai penulisan dari Bab I, bukan dari Bab IV

Gunakan `docs/hasil_sementara_penelitian_v2_20260723.md` sebagai gudang fakta, lalu tulis Bab I-III agar judul, rumusan masalah, tujuan, batasan, dan metode cocok dengan eksperimen final. Bab IV hanya disusun setelah Gate 3 selesai.

### Gate 5 - lakukan rehearsal sidang berbasis bukti

Siapkan demonstrasi live dan fallback rekaman/artifact. Uji pertanyaan kritis: alasan dua sensor, alasan tanpa object binding, arti kontribusi ilmiah, keterbatasan satu model, alasan baseline, validitas penilaian manusia, dan mengapa hasil tidak menyatakan manfaat pengguna.

## Keputusan akhir

**GO untuk melanjutkan Bridge-Gap, tetapi STOP feature development.** Fokus berikutnya bukan menambah model, depth, fusion, UI, atau sensor baru. Fokus berikutnya adalah membekukan engineering baseline, memperbaiki desain evaluasi visual, menjalankan evaluasi final yang defensible, lalu menulis skripsi.

Jika targetnya hanya demo prototipe, proyek sudah sekitar 85-90% selesai. Jika targetnya skripsi siap sidang, proyek baru sekitar 55% selesai karena kekurangan utama berada pada validitas penelitian dan penulisan, bukan pada kode.
