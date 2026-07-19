---
topic: "Bridge-Gap + 2x HC-SR04: evaluasi ulang alternatif dan roadmap integrasi"
type: "academic-technical"
goals: "Menentukan bagian alternatif lama yang masih dapat dipakai, menguji kelayakan dua HC-SR04 sebagai bukti fisik sparse, dan menyusun next plan skripsi yang dapat diaudit"
date: "2026-07-19"
methodology: "Audit artefak repository, telaah literatur primer/official documentation, dan sintesis desain berbasis decision gates; klaim eksternal diberi tautan dan tanggal akses."
---

# Riset Upgrade Bridge-Gap dengan 2x HC-SR04

> **Status:** rencana keputusan, bukan hasil integrasi. Data sensor baru yang dilaporkan pengguna belum memiliki capture terarsip di repository.
>
> **Batas scope:** deskripsi visual-spasial indoor dan evaluasi trade-off; bukan alat navigasi aman, bukan pengukur jarak objek yang disebut Gemma, dan bukan sistem real-time safety-critical.

## 1. Keputusan eksekutif

Bridge-Gap masih dapat diperkuat tanpa membuang baseline, tetapi upgrade yang paling defensible bukan “memasukkan jarak sensor ke caption”. Jalur yang layak adalah **evaluasi referensi jarak fisik sparse dan deteksi konflik bukti**: dua HC-SR04 mengukur sumbu/region pemasangannya, lalu hasilnya dibandingkan dengan ringkasan depth monocular pada frame yang sama. Sistem hanya menerbitkan metadata regional ketika pemetaan, kualitas sensor, dan timestamp memenuhi gate; ketika bukti bertentangan, sistem abstain dari klaim spasial tambahan.

Alternatif 1 tetap berguna sebagai **mekanisme metodologis**, bukan sebagai metode yang sudah terbukti meningkatkan kualitas bahasa. Run deterministic e2b 20 citra menghasilkan structured JSON 20/20, tetapi judge blinded memberi overall `4,267` untuk `gemma_only` versus `4,100` untuk `gemma_depth`; interval pasangan overall masih memotong nol dan clarity cenderung turun. Artefak itu sendiri menyimpulkan bahwa Alternatif 1 layak sebagai ablation/evaluasi terkontrol, bukan demonstrasi superiority ([REPORT Alternatif 1](D:/Tugas/SKRIPSI/Bride-Gap/alt1_followup_20260718/REPORT.md)).

**Rekomendasi utama:** lakukan hardware characterization → sensor-to-camera mapping → paired scene evaluation → conflict-gated ablation. Jangan mengubah dataset 44 citra lama menjadi ground truth sensor dan jangan menghapus `gemma_only`.

## 2. Bukti lokal yang harus menjadi titik awal

### 2.1 Scope dan klaim aktif

Repository sudah menetapkan bahwa depth monocular adalah kategori relatif, grid 3x3 adalah post-processing, dan object-depth binding belum terbukti tanpa box/mask atau korespondensi piksel ([CONTEXT.md](D:/Tugas/SKRIPSI/Bride-Gap/Program/CONTEXT.md), [evaluation protocol](D:/Tugas/SKRIPSI/Bride-Gap/Program/docs/evaluation_protocol.md)). Karena itu HC-SR04 tidak boleh diberi nama “ground truth depth” atau digunakan untuk menyimpulkan objek yang disebut Gemma berada pada jarak tertentu.

### 2.2 Alternatif yang sudah diuji

| Ide/artefak | Bukti lokal | Keputusan | Yang masih dapat dipakai | Dampak jika dipaksa menjadi metode utama |
|---|---|---|---|---|
| **Evidence-constrained late fusion** | Kontrol cabang Gemma yang sama membuat object/position/joint tidak berubah; depth menambah metadata regional tetapi manfaat kualitas bahasa belum terbukti ([final decision](D:/Tugas/SKRIPSI/Bride-Gap/Program/docs/final_core_experiment_decision_20260715.md)). | **Pertahankan sebagai baseline aktif** | Kontrak bukti, provenance, mode `gemma_only`/`gemma_depth`, evaluator mode-specific, failure analysis. | Klaim “fusion meningkatkan kualitas” akan melampaui data. |
| **Depth-to-Spatial Prompting / prompt fusion** | Overall judge historis `3,5682`, lebih rendah dari baseline `3,8636`, dengan latensi lebih tinggi; runtime sudah dipensiunkan ([keputusan inti](D:/Tugas/SKRIPSI/Bride-Gap/Program/docs/final_core_experiment_decision_20260715.md)). | **Reject sebagai runtime**; simpan sebagai ablation negatif | Bukti bahwa metadata tambahan dapat menurunkan clarity; kontrol historis untuk pembahasan. | Mengulang prompt hanya menambah latensi dan membuka kembali masalah grounding. |
| **Adaptive depth banding + variance filter** | Recall obstacle dan F1 turun dibanding `grid_p10` ([evaluation protocol](D:/Tugas/SKRIPSI/Bride-Gap/Program/docs/evaluation_protocol.md)). | **Reject** | Failure case dan alasan memilih post-processing sederhana. | Tuning pasca-hasil berisiko HARKing dan tidak menyelesaikan referensi fisik. |
| **Oracle-box / depth-guided ROI V3** | Structured output lulus, tetapi identitas end-to-end hanya `47,22%` pada depth-guided dan protokol MARK gagal; tidak ada reference depth fisik ([NOTES V3](D:/Tugas/SKRIPSI/Bride-Gap/Program/prototypes/depth_guided_roi_v3/NOTES.md)). | **Freeze sebagai hasil negatif; jangan melatih detector** | QA geometri, structured schema, aturan menolak box terpotong/overlap tinggi. | Training detector dari label/ROI yang tidak valid memperluas scope dan memperkuat kesalahan. |
| **Depth-ranked Set-of-Mark** | Respons tervalidasi `9/12`, mark returned `71,43%`, identity end-to-end `37,14%`, latensi sekitar `162 s/citra` ([NOTES SOM](D:/Tugas/SKRIPSI/Bride-Gap/Program/prototypes/depth_ranked_som/NOTES.md)). | **Reject sebagai jalur utama** | Gate eksplisit sebelum training; prinsip “jangan melatih sebelum oracle-box lulus”. | Dataset kecil, label ambigu, dan parsing buruk tidak cukup untuk klaim grounding. |
| **Confidence-gated Alternative 1** | Pilot 6 sampel lulus feasibility, tetapi calibration/held-out 20+20 hanya menghasilkan coverage `0,60`, joint accuracy gated `0,3333`, risk difference `-0,0833` dengan interval `[-0,25; 0,0667]`; bukan scene-stratified dan belum memakai VLM ([calibration decision](D:/Tugas/SKRIPSI/Bride-Gap/Program/docs/confidence_gated_calibration_holdout_decision_20260718.md)). | **Reuse bersyarat sebagai desain abstention** | `coverage`, `selective risk`, `error capture`, `false rejection`, calibration split, held-out split, frozen thresholds. | Menyebut gate sebagai verifier kebenaran atau mengulang judge tanpa bukti baru hanya memoles hipotesis yang belum terbukti. |
| **2x HC-SR04 isolated pilot** | Firmware dua sensor dapat build/flash dan memicu bergantian 70 ms; log lokal terakhir masih mencatat `0` valid pada kedua sensor, sementara pengguna melaporkan uji terbaru berhasil. | **Conditional go** setelah capture terkontrol | Logger JSON, sensor ID, timestamp, sequential trigger, isolasi sensor satu-per-satu. | Menganggap “program jalan” = sensor akurat akan menghasilkan data palsu dan klaim tidak dapat dipertanggungjawabkan. |

## 3. Apa yang didukung literatur

HC-SR04 cocok sebagai **referensi metrik sparse indoor**, bukan sebagai pengganti depth map. Studi perbandingan langsung melaporkan ultrasonic lebih konsisten pada jarak frontal/lintas rentang, sedangkan IR lebih bergantung pada jarak pendek, sudut, reflektansi, dan cahaya ([Téllez-Garzón et al. 2025](https://doi.org/10.14483/23448393.22458), diindeks DOAJ, diakses 2026-07-19). Studi lain menguji HC-SR04 bersama sensor ToF dan melaporkan bahwa penggabungan/averaging sensor dapat menurunkan variasi, tetapi manfaat bergantung pada setup dan tidak otomatis menjadi ground truth ([Komarizadehasl et al. 2022](https://www.mdpi.com/2076-3417/12/6/3186), diakses 2026-07-19).

Literatur sensor jaringan menunjukkan bahwa distribusi sensor, bentuk target, sudut, dan overlap beam harus diukur sebelum region kamera diberi jarak; satu sistem membagi frame menjadi region yang sesuai posisi sensor dan mensinkronkan sensor untuk mencegah interferensi ([Mocanu, Tapu & Zaharia 2016](https://www.mdpi.com/1424-8220/16/11/1807), lines 295–315, diakses 2026-07-19). Studi fusion stereo–ultrasonic juga memosisikan ultrasonic sebagai cross-check/layer prior, bukan sebagai peta semantik lengkap ([Gholami, Khanmirza & Riahi 2022](https://doi.org/10.1016/j.measurement.2022.110718), diakses 2026-07-19).

Dua sensor aktif harus ditembakkan bergantian atau disinkronkan; literatur multi-sonar secara eksplisit membahas interferensi dan firing sequence ([Meng et al. 2005](https://actapress.com/PDFViewer.aspx?paperId=23007), diakses 2026-07-19). HC-SR04 juga dipengaruhi suhu; studi eksperimental menunjukkan error meningkat ketika suhu dan jarak berubah sehingga kalibrasi a priori perlu dicatat ([Teixeira Júnior et al. 2024](https://doi.org/10.29327/1863744.1-9), diakses 2026-07-19). Ini mendukung pencatatan suhu/lingkungan, bukan klaim bahwa sensor nominal ±3 mm selalu tercapai.

Untuk desain abstention, risk–coverage memang merupakan trade-off formal antara proporsi prediksi yang diterbitkan dan risiko pada prediksi yang diterbitkan ([El-Yaniv & Wiener 2010](https://jmlr.csail.mit.edu/papers/v11/el-yaniv10a.html), diakses 2026-07-19). Literatur reject-option yang lebih baru membedakan target bounded-risk dan bounded-coverage ([Franc, Průša & Voráček 2023](https://www.jmlr.org/beta/papers/v24/21-0048.html), diakses 2026-07-19). Maka metrik Alternatif 1 dapat dipakai ulang, tetapi gate sensor harus dikalibrasi pada split terpisah dan tidak boleh dinilai sebagai “bukti AI tahu dirinya salah”.

Pada level listrik, ESP32 memiliki batas tegangan domain sampai 3,6 V pada datasheet; ECHO HC-SR04 yang 5 V harus diturunkan sebelum masuk GPIO ([ESP32 Series Datasheet](https://documentation.espressif.com/api/resource/doc/file/JyPJqKY3/FILE/esp32_datasheet_en.pdf), lines 2022–2032, diakses 2026-07-19). Espressif juga menandai GPIO5 sebagai strapping pin dan mendokumentasikan keterbatasan ADC2 saat Wi-Fi aktif ([ESP Hardware Design Guidelines](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32/schematic-checklist.html), lines 453–459 dan [ADC guide](https://docs.espressif.com/projects/esp-idf/en/v4.2/esp32/api-reference/peripherals/adc.html), diakses 2026-07-19). Pilot saat ini memakai GPIO5 untuk TRIG; ini tidak otomatis salah karena board sudah boot, tetapi harus masuk risk register dan dipindah ke GPIO non-strapping bila revisi bracket/wiring memungkinkan.

## 4. Desain upgrade yang diusulkan

### 4.1 Pertanyaan penelitian yang aman

**RQ1 — reliability:** Seberapa stabil dua HC-SR04 pada jarak, sudut, material, suhu, dan urutan trigger yang ditetapkan?

**RQ2 — alignment:** Seberapa sering pengukuran sensor yang sudah dipetakan ke region kamera konsisten dengan kategori depth relatif pada frame yang sama?

**RQ3 — trade-off:** Apakah penambahan sensor sebagai kanal konflik/abstention mengubah coverage, selective risk, false acceptance/rejection, failure type, dan latency dibanding `gemma_only` serta `gemma_depth`?

Hipotesis harus dua arah: H1 sensor dapat menurunkan klaim regional yang tidak didukung pada sebagian kondisi; H0 sensor tidak menurunkan risk atau menurunkan coverage/clarity lebih besar daripada manfaatnya. Jangan menetapkan H1 sebagai kesimpulan sebelum data.

### 4.2 Arsitektur yang disarankan

```text
camera capture (image_ts)
        +
ESP32 sensor_1 / sensor_2 (sensor_ts, distance_cm, valid, quality)
        ↓ time-window matcher + provenance logger
camera calibration + fixed sensor-to-camera transform
        ↓
depth model → regional summary      sensor sparse region evidence
        └────────────── conflict / agreement gate ──────────────┘
        ↓
gemma_only | gemma_depth | gemma_depth_sensor_guarded
        ↓
regional visual-spatial description, or abstain from extra spatial claim
```

Sensor tidak mengubah teks Gemma secara paksa. `sensor_guarded` hanya boleh menambahkan fakta regional jika: (a) sensor valid, (b) frame dan sample berada dalam window waktu yang dipra-daftarkan, (c) transformasi region sudah lolos QA, dan (d) sensor-depth agreement berada dalam threshold calibration. Konflik menghasilkan `sensor_depth_conflict=true` dan fallback ke deskripsi visual yang lebih sempit; bukan “bahaya”, “aman”, atau jarak objek.

### 4.3 Geometri dua sensor

Jangan langsung menempatkan dua sensor sebagai “kiri/kanan” lalu menganggap cone-nya sama dengan grid 3x3. Lakukan dua tahap:

1. **Karakterisasi co-aligned:** satu target planar pada sumbu yang sama untuk mengukur bias dan perbedaan antar unit.
2. **Mount final:** sensor diarahkan ke dua sektor tetap yang dapat dipetakan secara empiris ke region kamera; overlap beam dan blind spot diukur, bukan diasumsikan.

Jika mounting kiri/kanan tidak dapat dipetakan dengan repeatable QA, gunakan kedua sensor sebagai replikasi/validasi fisik pada satu sektor terlebih dahulu dan jangan menerbitkan label kiri/kanan.

## 5. Roadmap bertahap dan decision gates

### Gate 0 — host, wiring, dan keselamatan listrik (stop/go)

**Tindakan:** ukur VCC tiap modul; ukur level ECHO pada kondisi HIGH; foto wiring; pastikan pembagi tiap ECHO; uji boot berulang; uji satu sensor tanpa sensor kedua; simpan firmware hash dan serial capture mentah.

**Stop jika:** ECHO melebihi 3,6 V, boot tidak konsisten, GND/VCC tidak stabil, atau sensor belum menghasilkan satu pun pulsa valid pada target planar yang dikontrol.

**Dampak:** mencegah data “valid” yang sebenarnya berasal dari wiring salah; biaya rendah tetapi wajib sebelum penelitian.

### Gate 1 — karakterisasi metrik sensor

**Tindakan:** gunakan target planar matte dan reference distance independen (jig mekanik, pita ukur, atau laser distance meter). Uji 20, 40, 60, 80, 100, 150, 200, 300 cm; sudut 0°, 10°, 20°, 30°; minimal 30 pembacaan per kondisi; ulangi material penting (kardus, kayu, plastik, hitam/matte, permukaan kecil/silinder). Trigger sensor bergantian, bukan bersamaan.

**Log minimum:** `sensor_id`, `seq`, `timestamp_ms`, `distance_cm`, `pulse_us`, `valid`, `status`, `temperature_c`, `supply_v`, `sample_count`, `firmware_hash`, kondisi target, sudut, dan reference distance.

**Metrik:** MAE, RMSE, signed bias, standard deviation, valid-read rate, outlier rate, latency, sensor-to-sensor disagreement, dan missed detection.

**Usulan engineering gate (tetapkan/pradaftarkan sebelum melihat hasil):** kondisi nominal harus mencapai valid-read rate ≥90% per sensor; MAE tidak lebih dari `max(5 cm, 10% reference)`; dan disagreement median antar sensor co-aligned ≤10%. Angka ini adalah ambang desain awal, bukan hasil literatur atau klaim universal; dosen pembimbing perlu menyetujui sebelum data final dikumpulkan.

**Stop/branch:** jika gate gagal, jadikan HC-SR04 hanya eksperimen hardware feasibility dan pertahankan skripsi software baseline; jangan memaksa fusion.

### Gate 2 — synchronisation dan sensor-to-camera mapping

**Tindakan:** pasang kamera dan bracket rigid; gunakan timestamp dari sumber yang sama atau ukur offset; gunakan papan/target planar pada jarak diketahui; dokumentasikan intrinsics kamera, posisi sensor, tinggi, yaw/pitch, dan region kamera yang dipilih. Simpan visual overlay untuk setiap sensor.

**Kriteria:** overlay sensor berulang pada region yang sama; perubahan pose kecil tidak mengubah pemetaan secara tak terjelaskan; frame matcher menolak sample di luar time window; sensor tidak dikaitkan ke objek semantik tanpa box/mask.

**Kekurangan:** kalibrasi ini memperbesar beban setup dan tidak menghasilkan full depth map. **Kelebihan:** inilah komponen yang mengubah sensor dari angka terpisah menjadi bukti regional yang dapat diuji.

### Gate 3 — paired dataset baru, bukan relabel dataset lama

**Tindakan:** kumpulkan scene indoor baru dengan image + dua sensor + reference distance/target region dalam satu provenance record; pisahkan calibration/dev/test pada level scene atau sequence; jangan mengambil frame hampir identik lintas split. Minimal pilot 30 scene unik; 50–100 gambar/scene memberi stabilitas lebih baik bila waktu memungkinkan ([evaluation protocol lokal](D:/Tugas/SKRIPSI/Bride-Gap/Program/docs/evaluation_protocol.md) juga merekomendasikan 50–100 untuk hasil yang lebih stabil).

**Kondisi pembanding pada frame/image yang sama:** `gemma_only`, `gemma_depth`, dan `gemma_depth_sensor_guarded`. Bekukan prompt, model, seed, evaluator, dan threshold sebelum test.

**Kriteria data:** setiap sample dapat diaudit dari image hash → sensor timestamps → firmware/config hash → output mode → evaluator row.

### Gate 4 — evaluasi sensor-guarded

Laporkan dua lapis hasil:

1. **Sensor layer:** MAE/RMSE/bias/valid rate/latency per sensor dan per kondisi.
2. **Bridge-Gap layer:** regional category agreement, sensor-depth conflict rate, false acceptance, false rejection, coverage, selective risk, error capture, unsupported-claim rate, structured object/position/joint accuracy, text length/clarity, end-to-end latency, dan packet loss.

Interpretasi wajib memisahkan:

- sensor tepat tetapi objek tidak ter-grounding;
- sensor konflik dengan monocular depth;
- sensor invalid/missing;
- Gemma salah objek/posisi tanpa hubungan dengan sensor;
- latency atau packet loss membuat sample ditolak.

Gunakan structured evaluator untuk klaim objek/posisi; gunakan blinded LLM judge hanya sebagai bukti sekunder. Tanpa dua penilai manusia independen atau reference caption independen, jangan menyebut LLM judge sebagai ground truth.

### Gate 5 — keputusan akademik

| Hasil gate | Keputusan skripsi |
|---|---|
| Gate 0 gagal | Stop hardware integration; simpan sebagai feasibility failure; baseline software tetap jalur utama. |
| Gate 0–1 lulus, Gate 2 gagal | Laporkan karakterisasi HC-SR04 dan keterbatasan mapping; jangan fusi ke teks. |
| Gate 0–2 lulus, benefit Gate 4 nol/interval memotong nol | Jadikan sensor sebagai ablation/negative finding; klaim utama tetap evaluasi trade-off. |
| Gate 4 menunjukkan risk turun pada held-out dengan coverage yang wajar | Klaim lokal: sensor guard dapat mengurangi sebagian klaim regional unsupported pada kondisi uji; bukan superiority global/navigasi aman. |
| Gate 4 hanya menaikkan coverage/metadata tetapi bukan kualitas teks | Klaim sensor sebagai physical-reference/provenance channel, bukan caption-improvement method. |

## 6. Cara upgrade kualitas akademik

Judul kerja yang aman: **“Evaluasi Referensi Jarak Ultrasonik Sparse pada Deskripsi Visual-Spasial Berbasis Depth untuk Citra Indoor.”** Judul ini mengunci objek penelitian pada evaluasi dan tidak menjanjikan navigasi.

Rumusan masalah cukup tiga RQ di atas. Tujuan harus mengikuti RQ: mengukur reliabilitas, memvalidasi pemetaan regional, dan membandingkan trade-off sensor-guarded terhadap baseline. Bab metode harus memuat wiring, level shifting, protokol firing, timestamp matcher, geometri, split scene, gate, dan metrik. Bab hasil harus menampilkan tabel per kondisi, bukan hanya screenshot UI.

Kontribusi yang dapat dipertanggungjawabkan bila semua gate lulus:

1. prototype hardware–software dengan provenance dan sinkronisasi;
2. karakterisasi dua HC-SR04 pada kondisi indoor yang eksplisit;
3. evaluasi paired terhadap baseline dan ablation depth;
4. conflict-aware/abstention policy dengan coverage–risk trade-off;
5. failure taxonomy yang menunjukkan kapan sensor tidak cukup.

Kontribusi yang tetap tidak boleh diklaim: novelty algoritmik umum, full depth map, precise object distance, real-time safety, navigasi aman, manfaat tervalidasi untuk pengguna tunanetra, atau generalisasi lintas gedung/perangkat.

## 7. Register risiko

| Risiko | Probabilitas awal | Dampak | Mitigasi | Evidence yang harus disimpan |
|---|---:|---:|---|---|
| ECHO 5 V masuk GPIO | tinggi sampai diverifikasi | kerusakan ESP32/data tidak valid | divider/level shifter terukur; cek ≤3,6 V | foto wiring, pengukuran tegangan |
| Dua sensor saling mendengar | sedang | outlier/ghost | sequential trigger, jeda, sensor orientation test | raw pulse + schedule |
| Cone beam mengukur objek/permukaan terdekat yang bukan target visual | tinggi | false region/object binding | target planar, overlay, no object claim | geometry QA + failure labels |
| Temperatur/permukaan/sudut menggeser error | sedang | threshold tidak general | condition matrix + temperature log | per-condition metrics |
| timestamp kamera dan sensor berbeda | tinggi | salah pasangan bukti | shared clock/time-window rejection | raw timestamps, rejected rows |
| user report sensor “berjalan” tidak sama dengan capture terarsip | sedang | klaim tidak reproducible | rerun controlled capture dan commit log | serial capture + hash |
| sensor menambah latency/packet loss | sedang | coverage turun | measure E2E, fallback baseline | latency/packet metrics |
| evaluator memberi kredit pada kata fusion | tinggi | leakage | field-only evaluator + provenance | evaluator config/tests |
| hasil positif hanya pada sample kecil | tinggi | overclaim generalisasi | scene split + held-out + interval | manifest dan split file |

## 8. Rencana eksekusi praktis

1. **Hari 1:** dokumentasikan board/model HC-SR04, ukur ECHO, foto wiring, pindai boot, dan capture serial satu sensor.
2. **Hari 2:** jalankan karakterisasi nominal per sensor; jangan menghubungkan ke FastAPI sebelum valid-read dan error terukur.
3. **Hari 3:** uji material/sudut/suhu; tetapkan threshold Gate 1 sebelum memperluas data.
4. **Hari 4:** buat bracket rigid, timestamp matcher, dan overlay sensor-to-camera; validasi dengan target planar.
5. **Hari 5+:** kumpulkan paired scenes baru, jalankan tiga mode, evaluasi risk–coverage, lalu putuskan keep/ablation/stop.

Artefak minimum per tahap: frozen protocol JSON, raw serial log, parsed sensor CSV, calibration report, geometry overlay, paired manifest, predictions per mode, evaluator config, metrics CSV, failure taxonomy, hash manifest, dan keputusan gate tertulis.

## 9. Daftar pustaka kerja

Gunakan sumber primer/official di atas sebagai inti Bab 2; tambahkan artikel peer-reviewed sampai memenuhi pedoman Gunadarma (minimum 20 sumber, ≥70% artikel ilmiah, Harvard, DOI bila ada). Pedoman lokal mengharuskan Bab 3 menjelaskan hardware, algoritma, pengumpulan/analisis data, uji coba, evaluasi, dan cara menarik kesimpulan; setiap hasil harus disajikan sesuai urutan tujuan ([pedoman struktur Gunadarma](D:/Tugas/SKRIPSI/Bride-Gap/.agents/skills/skripsi-gunadarma/references/PEDOMAN_STRUKTUR.md)).

Semua angka eksperimen dalam dokumen ini yang berasal dari run Bridge-Gap/Alternatif 1 adalah angka artefak lokal, bukan hasil baru. Ambang Gate 1 diberi label **design inference** dan harus dibekukan sebelum pengumpulan data final.

## 10. Red-team review sebelum implementasi

**Counter-argument terkuat:** dua HC-SR04 mungkin hanya membuat sistem lebih yakin terhadap permukaan terdekat dalam cone beam, bukan membuat deskripsi Gemma lebih benar. Jika transformasi sensor-to-camera tidak stabil atau sample tidak sinkron, “sensor agreement” dapat menjadi false reassurance; jika sensor dan depth sama-sama salah pada permukaan tertentu, confidence gate tidak akan menangkap error sistematik.

Konsekuensinya, keberhasilan hardware tidak cukup untuk melanjutkan ke fusi. Gate 2 (geometry/timestamp) dan Gate 3 (paired held-out scenes) harus menjadi hard gate; jika salah satu gagal, artefak sensor tetap berguna sebagai karakterisasi/negative finding, tetapi tidak boleh masuk ke klaim peningkatan teks. Ini menjaga proyek tetap bisa dipertahankan bahkan ketika hipotesis H1 gagal.
