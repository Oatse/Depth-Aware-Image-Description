# Laporan Maturitas dan Penyelesaian Proyek Bridge-Gap

Tanggal audit: 24 Juli 2026
Lokasi audit: `D:\Tugas\SKRIPSI\Bride-Gap\Program`
Branch: `feat/complete-iot-assisted-analysis`

## Putusan eksekutif

Bridge-Gap sudah layak disebut **prototipe penelitian teknis yang terintegrasi dan
dapat direproduksi pada setup terkendali**. Implementasi, kalibrasi, verifikasi
sensor, baseline `gemma_only`, mode `sensor_assisted`, evaluasi blind berpasangan,
dan provenance run final telah tersedia.

Proyek belum siap disebut skripsi selesai karena naskah belum disusun, sumber aktif
belum memenuhi minimum formal, evaluasi visual masih terbatas pada satu koper dan
satu evaluator, serta demonstrasi sensor live belum diverifikasi kembali setelah
pembekuan baseline.

| Dimensi | Kematangan | Status |
|---|---:|---|
| Implementasi software | 95% | Selesai untuk scope aktif |
| Integrasi hardware dan sensor | 90% | Selesai untuk PoC; demo live perlu diulang |
| Reproducibility dan provenance | 94% | Paket final mandiri dan tervalidasi |
| Dataset dan evaluasi penelitian | 78% | Final untuk seri terkendali; generalisasi terbatas |
| Penulisan skripsi | 5% | Belum dimulai |
| Kesiapan sidang keseluruhan | 65% | Belum siap |

Persentase merupakan penilaian audit berbobot, bukan metrik otomatis.

## Bukti terverifikasi

### Implementasi

- 105 test Python lulus.
- 3 test klien JavaScript lulus.
- `node --check static/app.js` dan compileall Python lulus.
- Environment `.venv` tersedia dan dependency check tidak menemukan paket rusak.
- Capture dan analisis terpisah; satu capture menjadi satu job serial.
- Job memakai citra dan snapshot sensor tersimpan, bukan membaca sensor ulang.
- Capture runtime baru dialihkan ke `results/captures/incoming/`.
- Endpoint runtime tidak menulis ke dataset v2 final.

### Pipeline sensor-conditioned

- `gemma_only` menggunakan prompt visual default.
- `sensor_assisted` hanya menerima konteks frontal jika contribution berstatus
  `applied`, terkalibrasi, segar, searah, dan lolos disagreement gate.
- Backend tetap menambahkan bagian sensor deterministik setelah keluaran Gemma.
- Provenance visual dan sensor dipertahankan sebagai segmen terpisah.
- Sensor tidak dipakai sebagai identitas objek, koordinat piksel, atau jarak ke objek
  yang disebut Gemma.

Tujuan sensor conditioning adalah mengamati pengaruh konteks frontal terverifikasi,
bukan membuktikan bahwa deskripsi menjadi lebih benar atau lebih baik.

### Kalibrasi dan verifikasi sensor

- Kalibrasi: 150 pasangan pada 20, 60, 100, 150, dan 200 cm.
- Verifikasi independen: 120 pasangan pada 40, 80, 125, dan 175 cm.
- Corrected MAE verifikasi: 0,673 cm.
- Corrected RMSE verifikasi: 1,045 cm.
- Maksimum absolute error terkoreksi: 5,271 cm.
- Seluruh titik verifikasi memenuhi residual gate 10 cm.

### Dataset dan evaluasi final

- 18 citra independen: enam jarak dan tiga pengulangan.
- 18/18 evidence sensor `paired`.
- 18 run `gemma_only` dan 18 run `sensor_assisted`, tanpa kegagalan.
- 36 raw provider response dan 36 prompt checksum dipertahankan.
- 36 item evaluasi visual dinilai secara blind.
- Skor dikunci sebelum key mode dibuka.
- Unit analisis statistik: 18 pasangan citra.
- Snapshot 36 run final disimpan terpisah dari log runtime.

Hasil utama:

| Metrik | `gemma_only` | `sensor_assisted` | Delta |
|---|---:|---:|---:|
| Skor keseluruhan | 4,4667 | 4,3889 | -0,0778 |
| Latency rata-rata | 34.475,06 ms | 43.581,17 ms | +26,41% |

Bootstrap 95% CI delta skor keseluruhan adalah [-0,2222; 0,0556]. Dataset ini tidak
memberikan bukti bahwa sensor conditioning meningkatkan kualitas. Hasil yang dapat
dipertahankan adalah konteks sensor memengaruhi keluaran dan menambah latency.

### Cleanup dan pembekuan

- Artefak evaluasi sebelum reanalisis telah dikeluarkan.
- Eksperimen depth historis dan runtime log campuran telah dikeluarkan.
- Hanya 18 record dataset final yang dipertahankan.
- Script dan test evaluasi generasi lama yang sudah digantikan telah dihapus.
- Dataset, blind copy, score lock, run snapshot, laporan, dan manifest final menjadi
  satu paket aktif.
- Riwayat file tracked yang dihapus tetap tersedia melalui Git.

## Pekerjaan yang masih terbuka

### Blocker sebelum naskah final

1. Folder `Penulisan/` masih kosong.
2. Indeks sumber aktif baru memuat 13 sumber; citation bank memuat 16 entri, belum
   memenuhi minimum 20 sumber dan rasio artikel ilmiah sesuai pedoman.
3. Judul dan rumusan masalah final tetap memerlukan persetujuan dosen pembimbing.
4. Bab III harus memakai satu flow yang sudah dibekukan: capture kandidat,
   snapshot sensor, gate, prompt sesuai mode, Gemma, bagian sensor, logging.

### Risiko validitas

1. Dataset visual hanya memakai satu koper dan satu setup.
2. Hanya satu evaluator; inter-rater agreement belum tersedia.
3. Tidak ada pengujian generalisasi pada scene multiobjek.
4. Inferensi tidak memakai seed.
5. Hasil bukan UAT dan tidak mendukung klaim manfaat pengguna atau keselamatan.

Risiko tersebut tidak membatalkan evaluasi terkendali, tetapi membatasi kesimpulan.
Jika judul tetap menyatakan deskripsi gambar indoor secara umum, dataset beragam
perlu ditambahkan sebagai ekstensi terpisah.

### Kesiapan operasional

- Backend dan Gemma pernah terverifikasi ready pada baseline ini.
- Sensor live belum terhubung pada audit terakhir karena COM7 tidak tersedia.
- Sebelum sidang perlu satu demonstrasi end-to-end terbaru dan fallback rekaman.

## Batas klaim

Proyek dapat mengklaim bahwa prototipe:

- menghasilkan deskripsi indoor Bahasa Indonesia pada dataset terkendali;
- menggunakan konteks frontal terverifikasi pada prompt ketika seluruh gate lolos;
- mempertahankan provenance prompt, output Gemma, dan contribution sensor;
- menahan konteks/angka ketika evidence tidak memenuhi gate;
- mengukur error dua HC-SR04 terhadap ground truth eksternal pada setup yang diuji.

Proyek tidak dapat mengklaim:

- sensor membuat deskripsi lebih akurat atau lebih baik;
- performa umum pada beragam scene indoor;
- jarak sensor ke objek yang dinamai Gemma;
- manfaat aksesibilitas, navigasi, atau keselamatan;
- operasi real-time universal.

## Keputusan

**GO untuk penulisan dan STOP pengembangan fitur baru.** Dataset v2 tetap menjadi
seri terkendali final. Jika dilakukan capture beragam, hasilnya harus menjadi
dataset ekstensi baru dengan protokol, folder, manifest, dan evaluasi terpisah.
