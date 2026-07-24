# Audit Ulang Maturitas dan Kesiapan Penulisan Bridge-Gap

Tanggal audit: 24 Juli 2026
Lokasi: `D:\Tugas\SKRIPSI\Bride-Gap\Program`
Branch: `feat/complete-iot-assisted-analysis`
Peran audit: auditor teknis perangkat lunak dan reviewer metodologi skripsi

## Putusan

**CONDITIONAL GO untuk mulai menulis dokumen sementara Bab I–II dan inventaris
hasil faktual. NO-GO untuk membekukan Bab III, Bab IV, abstrak, kesimpulan, atau
klaim final.**

Bridge-Gap sudah merupakan prototipe fungsional dengan dataset terkunci, run model
berprovenance, kalibrasi, verifikasi sensor, dan evaluasi blind. Namun implementasi
aktif dan paket hasil final masih melanggar batas klaim kanonik karena angka sensor
diikat ke objek yang dinamai Gemma. Ada pula bias seleksi pada capture, provenance
kalibrasi yang belum menjadi bagian paket mandiri, dan evaluasi visual yang hanya
menilai segmen Gemma, bukan deskripsi akhir sistem.

Laporan `project_maturity_report_20260724.md` sebelumnya tidak lagi boleh digunakan
sebagai dasar penulisan karena menyatakan tidak ada object binding dan mencatat 105
test, sedangkan audit ulang menemukan object binding aktif dan 104 test Python.

## Skala maturitas

| Level | Arti |
|---|---|
| L0 | Belum ada |
| L1 | Eksplorasi |
| L2 | Prototipe fungsional |
| L3 | Eksperimen terkendali dapat direproduksi |
| L4 | Bukti dan klaim siap dipertahankan dalam skripsi |
| L5 | Siap sidang dan demonstrasi |

| Dimensi | Level saat ini | Dasar penilaian |
|---|---:|---|
| Implementasi software | L3 | Alur utama berfungsi dan test hijau, tetapi kontrak output dilanggar |
| Integrasi sensor | L2.5 | Kalibrasi/verifikasi tersedia; sensor live sedang unavailable |
| Provenance dan reproducibility | L2.5 | Run dan checksum kuat; profil/raw kalibrasi tidak masuk paket tracked |
| Dataset dan evaluasi | L2.5 | Dataset terkunci dan blind; satu objek, satu setup, satu evaluator |
| Konsistensi metodologi | L2 | Kode dan test bertentangan dengan dokumen kanonik |
| Kesiapan penulisan | L2 | Dokumen sementara dapat dimulai; hasil final belum aman |
| Kesiapan sidang | L1.5 | Belum ada naskah dan demo live terbaru |

**Maturitas keseluruhan: sekitar L2.5 dari L5.** Angka ini adalah rubric audit,
bukan metrik otomatis.

## Arsitektur dan aliran data yang terverifikasi

```text
Kamera + metadata waktu + ground_truth_cm
  -> POST /captures
  -> pencocokan snapshot dua HC-SR04
  -> results/captures/incoming
  -> POST /captures/{id}/analysis-jobs
  -> job in-memory serial
  -> preprocessing RGB
  -> validasi/kalibrasi snapshot tersimpan
  -> prompt default atau sensor-conditioned
  -> LM Studio / Gemma 4 E2B
  -> deskripsi Gemma
  -> post-processing sensor
  -> API, UI, analysis run, CSV/JSONL
```

Bagian yang sudah sesuai:

- capture dan analisis dipisahkan;
- stored-capture job memakai gambar dan snapshot sensor tersimpan;
- queue memproses job satu per satu;
- hanya contribution `applied` yang mengondisikan prompt;
- conflict, stale, partial, direction mismatch, dan unavailable tidak membentuk
  `frontal_reference_cm`;
- dataset v2 berada di luar target tulis endpoint runtime;
- 18 gambar dan checksum dataset berhasil divalidasi ulang.

## Temuan kritis

### K1 — Angka sensor aktif diikat ke objek bernama

`models/sensor_fusion.py:150-167` mengambil `closest_object` dari keluaran Gemma.
Jika disagreement tidak lebih dari 2 cm, fungsi menghasilkan kalimat:

```text
... objek terdekat dari kamera, dengan estimasi jarak sekitar X cm.
```

`services/pipeline.py:49-50` memakai hasil tersebut sebagai `final_description`, dan
`static/app.js:195-209` menampilkannya sebagai deskripsi utama UI.

Perilaku ini dipertahankan oleh
`tests/test_sensor_fusion.py:56-73`. Test `test_reference_is_not_bound_to_named_object`
hanya melarang pola kata tertentu, sedangkan test berikutnya justru mewajibkan
binding berdasarkan `closest_object`.

Konflik langsung:

- `CONTEXT.md:170-179` melarang object binding;
- `CONTEXT.md:193` melarang angka sensor sebagai atribut objek;
- `CONTEXT.md:216-224` melarang klaim sensor mengukur objek Gemma;
- `docs/DESIGN.md:127` melarang copy “objek terdekat X cm”;
- `README.md:125` menyatakan binding tidak ada;
- laporan maturitas lama baris 50–51 menyatakan sensor tidak dipakai sebagai jarak
  ke objek Gemma.

Paket final juga terdampak: 17 dari 18 run `sensor_assisted` terpilih mengandung
frasa object binding dan “estimasi jarak”, sementara 18/18 menyimpan bagian
referensi frontal.

**Dampak:** deskripsi akhir sistem melampaui bukti fisik HC-SR04 dan membuat klaim
metodologis utama tidak benar.

**Gate:** hapus seluruh cabang `closest_object` dari post-processing. Selalu
tambahkan bagian sensor sebagai kalimat terpisah. Balik test agar setiap bentuk
object binding gagal.

**Tidak perlu capture ulang atau inference ulang.** `gemma_description`, snapshot,
dan contribution tersimpan dapat dipakai untuk membangun ulang `final_description`
secara deterministik, kemudian manifest/checksum hasil diperbarui.

### K2 — Evaluasi blind tidak menilai deskripsi akhir sistem

`scripts/build_fresh_dataset_reports.py:380-388` memasukkan
`gemma_description` ke lembar blind, bukan `final_description`. Karena itu skor
unsupported claim = 0 hanya berlaku pada segmen visual Gemma. Skor tersebut tidak
membuktikan bahwa deskripsi akhir yang tampil di UI bebas klaim tidak didukung.

**Dampak:** laporan final mencampur “kualitas keluaran Gemma” dengan “kualitas
deskripsi sistem”.

**Gate:** pertahankan evaluasi sekarang dengan label
`evaluasi_segmen_visual_gemma`, lalu tambahkan audit terpisah terhadap
`final_description` hasil post-processing yang sudah diperbaiki. Jangan mengubah
skor lama seolah-olah ia menilai output sistem.

### K3 — Capture hanya menyimpan kondisi sukses paired

`app/routes/captures.py:97-109` menolak capture dengan HTTP 409 jika evidence tidak
`paired` atau salah satu sensor tidak `ok`. UI juga menonaktifkan tombol capture
ketika pasangan live tidak tersedia.

Kontrak akademik meminta conflict, stale, partial, unavailable, kegagalan, dan
missing data tetap dilaporkan. Implementasi sekarang mengeluarkan kondisi tersebut
sebelum record dataset dibuat.

**Dampak:** valid-read rate, availability rate, dan proporsi status evidence dari
dataset capture tidak dapat dihitung tanpa bias seleksi.

**Gate:** pilih salah satu desain dan tulis eksplisit:

1. simpan semua attempt beserta statusnya, lalu terapkan kriteria inklusi setelah
   penyimpanan; atau
2. tetap memakai dataset paired-only, tetapi simpan log seluruh attempt/rejection
   sebagai denominator terpisah.

Dataset v2 masih sah sebagai **subset paired terkendali**, tetapi tidak boleh
digunakan untuk mengklaim availability atau distribusi status sistem.

### K4 — Paket “mandiri” tidak memuat provenance kalibrasi

Runtime memakai empat file di `config/`:

- profil kalibrasi;
- 150 measurement kalibrasi;
- ringkasan verifikasi;
- 120 measurement verifikasi.

Keempatnya diabaikan oleh `.gitignore` dan tidak tercantum sebagai artefak checksum
paket evaluasi final. Run terpilih hanya menyimpan versi kalibrasi dan nilai hasil,
bukan koefisien lengkap serta raw measurement.

**Dampak:** hasil dapat diaudit, tetapi koreksi sensor tidak dapat direproduksi dari
clone repository atau paket evaluasi saja. Klaim “paket final mandiri” terlalu kuat.

**Gate:** salin snapshot read-only profil, measurement kalibrasi, measurement
verifikasi, firmware identity, dan checksum ke paket penelitian final. Jangan
memindahkan atau menimpa file runtime aktif.


## Temuan validitas akademik

### A1 — “Pengaruh sensor” masih bercampur dengan stochastic inference

LM Studio mendukung parameter `seed`, tetapi client tidak mengirim seed. Setiap
gambar hanya mempunyai satu run per mode dan urutan eksekusi tidak dibuktikan
random/interleaved. Perbedaan teks dapat berasal dari prompt, variasi sampling,
urutan, cache, atau kondisi runtime.

Klaim aman:

> Pada 18 pasangan run yang diamati, keluaran kedua kondisi berbeda dan latency
> `sensor_assisted` lebih tinggi.

Klaim yang belum aman:

> Konteks sensor menyebabkan perubahan atau kenaikan latency sebesar nilai tertentu
> secara umum.

Jika tujuan tetap memakai kata “pengaruh”, gunakan seed yang sama per pasangan atau
beberapa repetisi inference per mode dengan urutan teracak/interleaved. Jika waktu
terbatas, ubah tujuan menjadi “membandingkan keluaran dan latency yang diamati”.

Dokumentasi resmi LM Studio mengonfirmasi endpoint yang dipakai sudah benar:
`GET /api/v1/models` dengan `loaded_instances` dan
`POST /v1/chat/completions`. LM Studio juga mendukung structured output berbasis
JSON schema dan seed; implementasi sekarang hanya meminta JSON melalui prompt.

### A2 — Unit analisis tidak mendukung generalisasi gambar indoor

Dataset berisi 18 capture satu koper dalam satu setup: enam jarak dengan tiga
pengulangan. Capture adalah unit pasangan untuk perbandingan dua mode, tetapi bukan
18 scene independen dari populasi gambar indoor. Bootstrap atas 18 capture tidak
mengatasi dependensi satu objek/satu setup.

Gunakan hasil sebagai evaluasi terkendali satu target. Jika judul tetap menyebut
gambar indoor secara umum, dataset beragam harus menjadi ekstensi terpisah yang
dipraregistrasikan sebelum capture.

### A3 — Satu evaluator dan scoring hanya segmen Gemma

Evaluasi blind dan score lock merupakan kekuatan, tetapi hanya satu evaluator.
Tidak ada inter-rater agreement. Evaluator juga memahami tujuan umum penelitian.
Hasil harus dilabeli audit teknis, bukan validasi pengguna atau kualitas populasi.

### A4 — Sumber pustaka belum siap

`docs/pustaka/source_index.md` hanya memuat 13 sumber aktif. Citation bank berisi
16 entri, tetapi banyak entri terkait komponen depth yang sudah tidak aktif dan
belum memuat seluruh sumber HC-SR04 aktif.

Pedoman Gunadarma mensyaratkan minimal 20 sumber dengan sekitar 70% artikel ilmiah
dan kemutakhiran yang sesuai. Keberadaan PDF tidak sama dengan sumber yang sudah
dipakai dan disitasi.

## Temuan engineering dan operasional

### E1 — Laporan maturitas lama memuat fakta salah

- tertulis 105 test Python; audit ulang mengumpulkan dan menjalankan 104 test;
- tertulis tidak ada object binding; implementasi dan artefak final membuktikan
  sebaliknya;
- paket disebut mandiri, padahal snapshot kalibrasi tidak ikut paket tracked.

### E2 — Smoke test default tidak reliabel

`scripts/smoke_test.py:20-46`:

- tidak memeriksa apakah child Uvicorn berhasil bind;
- menyembunyikan stdout/stderr child;
- memakai port 8000 yang mungkin sudah dipakai;
- timeout request 30 detik, lebih pendek dari latency eksperimen rata-rata
  34–44 detik dan timeout konfigurasi 240 detik.

Audit membuktikan smoke test default gagal ketika port 8000 sudah ditempati, tetapi
smoke test isolated pada port 8765 dengan mock lulus.

### E3 — Dua CLI evaluasi gagal bila dijalankan sebagai file

Perintah berikut gagal dengan `ModuleNotFoundError`:

```powershell
python scripts/validate_capture_manifest.py
python scripts/finalize_dataset_v2_evaluation.py
```

Keduanya bekerja sebagai module (`python -m scripts...`). README belum
mendokumentasikan perintah yang benar.

### E4 — Provenance software belum mengunci build nyata

`app_version` ditulis statis sebagai `0.1.0`. Run tidak menyimpan commit SHA,
versi LM Studio, revision/quantization model, versi firmware, atau seed. Raw response
disimpan sebagai representasi `str(dict)`, bukan JSON kanonik.

### E5 — Dokumentasi meminta target/scene, UI tidak mengirimnya

README menyuruh operator memasukkan identitas target/scene, tetapi form capture hanya
mengirim jarak. Backend mendukung `target_id` pada repository, namun route dan UI
tidak menyediakan field tersebut. Repeat index akhirnya dikelompokkan hanya oleh
batch dan jarak.

### E6 — “Frozen calibration” masih dapat ditulis ulang

`GET /sensor-calibration` membangun ulang dan menulis profil bila measurement ada.
Reset juga tetap tersedia. “Frozen” saat ini berarti capture kalibrasi baru ditolak,
bukan artefak immutable secara operasional.

## Bukti yang lulus pada audit ulang

- Git worktree bersih pada branch aktif.
- `python -m pytest -q`: **104 passed**.
- `node --test tests/analysis_job_client.test.cjs`: **3 passed**.
- `python -m compileall -q app services models scripts tests`: lulus.
- `node --check static/app.js`: lulus.
- `node --check static/analysis-job-client.js`: lulus.
- Smoke test isolated mock pada port 8765: lulus.
- Runtime `/readiness`: Gemma `ready`, kalibrasi `validated`, sensor live
  `unavailable`.
- Validasi manifest dijalankan ulang: 18 capture, 18 image checksum unik, 18/18
  checksum terverifikasi, seluruh record dataset berstatus paired.
- Paket final menyimpan 36 run terpilih, 36 raw provider response, dan 36 prompt
  checksum.
- Kalibrasi lokal: 150 pasangan pada lima titik.
- Verifikasi lokal: 120 pasangan pada empat holdout distance; corrected MAE
  0,673 cm dan RMSE 1,045 cm.
- Evaluasi blind: 36 item dari 18 pasangan, skor dikunci sebelum unblinding.
- Temuan negatif dipertahankan: delta skor keseluruhan -0,0778 dengan bootstrap
  95% CI [-0,2222; 0,0556], latency teramati +26,41%.

## Urutan perbaikan minimum

1. Hapus object binding dan perbaiki test kontrak.
2. Regenerasi deterministic `final_description` dari run tersimpan; perbarui
   checksum paket tanpa capture atau inference ulang.
3. Tambahkan audit blind/otomatis untuk final system output.
4. Bekukan snapshot kalibrasi, verifikasi, firmware, dan environment ke manifest.
5. Putuskan denominator capture attempt dan dokumentasikan paired-only selection.
6. Ubah kata “pengaruh” menjadi perbandingan observasional atau tambahkan kontrol
   seed/repetisi inference.
7. Lindungi route mutasi dan `results/` sebelum tunnel dipakai saat demo.
8. Tambah sumber aktif sampai memenuhi minimum formal dan rasio Gunadarma.
9. Jalankan demonstrasi live terbaru dengan dua sensor serta simpan bukti fallback.
10. Sinkronkan README, architecture, UI, test, dan laporan final.

## Keputusan penulisan per bagian

| Bagian | Keputusan |
|---|---|
| Dokumen sementara fakta/provenance | Mulai sekarang |
| Bab I | Mulai, tetapi judul/rumusan final menunggu pembimbing |
| Bab II | Mulai sambil melengkapi dan memverifikasi pustaka |
| Bab III | Draft saja; bekukan setelah K1–K4 selesai |
| Bab IV | Jangan finalisasi sebelum output dan klaim dievaluasi ulang |
| Bab V, abstrak, kesimpulan | Belum |
| Pengembangan fitur baru | Stop; hanya perbaikan audit |

## Batas klaim sementara

Yang sudah dapat ditulis sebagai fakta:

- prototipe memproses satu citra RGB dan menghasilkan deskripsi Bahasa Indonesia;
- dua HC-SR04 menyediakan snapshot referensi frontal dengan provenance;
- kalibrasi dan verifikasi lokal pada setup terkendali telah dilakukan;
- 18 pasangan run final tersedia dan integritas file tervalidasi;
- mode berbeda menghasilkan output teramati berbeda dan latency teramati berbeda;
- dataset ini tidak menunjukkan peningkatan kualitas oleh `sensor_assisted`.

Yang belum boleh ditulis:

- sensor mengukur koper atau objek yang disebut Gemma;
- final system description telah terbukti bebas unsupported claim;
- sensor menyebabkan peningkatan atau perubahan kualitas;
- performa berlaku untuk gambar indoor secara umum;
- sistem memberi manfaat aksesibilitas, navigasi, atau keselamatan;
- paket eksperimen sudah mandiri sepenuhnya;
- proyek siap sidang.
