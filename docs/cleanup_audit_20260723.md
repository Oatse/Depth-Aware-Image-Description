# Audit Kandidat Pembersihan Workspace Bridge-Gap

Tanggal audit: 23 Juli 2026
Mode awal: read-only; rekomendasi kemudian dieksekusi setelah persetujuan pengguna
Zona terlindungi: `results/`

## Putusan ringkas

Pembersihan aman dapat dilakukan pada cache, log runtime, bytecode, virtual environment lokal, dan build PlatformIO. Folder `notebooks/` hanya berisi `.gitkeep` dan dapat dihapus. Tiga prototipe depth lama sudah tidak mempunyai pemanggil aktif dan bertentangan dengan pipeline Gemma + HC-SR04 saat ini; source-nya layak dipindahkan ke arsip atau dihapus melalui commit terpisah setelah snapshot Git dipastikan tersedia.

`results/`, `archive/historical_depth_experiment_20260722/`, source pilot ESP32, dokumen kanonik, test aktif, konfigurasi, dan artefak evaluasi 23 Juli tidak boleh dibersihkan. Folder `research/` bukan sampah runtime; isinya perlu ditata berdasarkan status aktif/historis, bukan dihapus massal.

## Dasar keputusan

Scope aktif menurut `CONTEXT.md` dan `instructions/PROJECT_INITIALIZATION.md` adalah satu deskripsi citra indoor berbahasa Indonesia memakai Gemma 4 E2B, ditambah referensi frontal dari dua HC-SR04 dengan provenance terpisah. Scope tidak lagi mencakup Depth Anything, fusion depth, objek terdekat, navigasi, atau pengikatan angka sensor ke objek bernama.

Commit `0455019` (`refactor: focus pipeline on Gemma and HC-SR04`) telah menghapus runtime, dataset, test, laporan, dan hasil pipeline depth/fusion lama, lalu menyimpan snapshot historis terverifikasi pada `archive/historical_depth_experiment_20260722/`. Karena itu, artefak depth yang masih tersisa harus diperlakukan sebagai residu historis, bukan komponen aktif.

## Inventaris ukuran utama

| Area | File | Ukuran | Status |
|---|---:|---:|---|
| `.git/` | 3.212 | 296,28 MiB | Metadata Git; jangan hapus manual |
| `docs/` | 35 | 201,22 MiB | Aktif + pustaka |
| `prototypes/` | 2.604 | 72,19 MiB | Source historis + pilot ESP32 + generated files |
| `results/` | 91 | 2,29 MiB | Dilindungi |
| `.codegraph/` | 3 | 3,20 MiB | Cache generated |
| `logs/` | 28 | 0,88 MiB | Log runtime ignored |
| `archive/` | 5 | 0,34 MiB | Bukti historis tracked |
| `notebooks/` | 1 | praktis 0 | Hanya `.gitkeep` |

## Kelas A - aman dibersihkan sekarang

Semua kandidat berikut ignored oleh Git atau sepenuhnya regenerable.

| Path | Alasan | Dampak |
|---|---|---|
| `.pytest_cache/` | Cache pytest | Tidak memengaruhi source atau hasil penelitian |
| `.codegraph/` | Indeks tooling lokal | Akan dibuat ulang oleh tooling |
| `logs/` | 28 log server/judge/tunnel; terbesar `origin-server.out.log` sekitar 0,79 MiB | Menghilangkan log diagnostik lama saja |
| `.uvicorn*.log` di root | Log proses lokal | Regenerable |
| seluruh `__pycache__/` dan `*.pyc` | Bytecode Python | Regenerable |
| `prototypes/esp32_hcsr04_isolated_pilot/.pio/` | Build PlatformIO; memuat `.elf`, `.map`, `.bin`, object files | Regenerable dari `platformio.ini` dan `src/main.cpp` |
| `prototypes/esp32_hcsr04_isolated_pilot/.venv/` | Environment Python lokal | Regenerable; source pilot tetap aman |
| `notebooks/` | Hanya `.gitkeep`; tidak ada notebook dan tidak ada referensi aktif | Folder kosong dapat dihapus |
| `.codex/`, `.venv/`, `certs/`, `model_weights/` bila tetap kosong | Placeholder lokal kosong | Tidak ada payload saat audit |

Perkiraan penghematan utama berasal dari `.pio/` dan `.venv/` pilot ESP32; keseluruhan prototype ESP32 saat audit sekitar 71,83 MiB.

## Kelas B - layak dibersihkan lewat commit terpisah

| Path | Bukti tidak aktif | Rekomendasi |
|---|---|---|
| `prototypes/confidence_gated_spatial_pilot/` | Pilot Alternative 1 berbasis Depth Anything; tidak dirujuk runtime/test/docs aktif di luar foldernya | Hapus source tracked atau pindahkan ringkasan README ke arsip |
| `prototypes/depth_guided_roi_v3/` | Eksperimen oracle-box/depth; runtime dan test pasangannya telah dihapus pada `0455019` | Hapus source tracked; sejarah tetap tersedia di Git |
| `prototypes/depth_ranked_som/` | README menyatakan bukan fitur runtime dan bukan hasil final; tidak ada caller aktif | Hapus source tracked; sejarah tetap tersedia di Git |

Ketiga folder tersebut tidak perlu dipertahankan di root aktif hanya karena pernah dipakai. Git sudah menyediakan histori, dan snapshot hasil lama yang relevan telah dipensiunkan pada refactor 23 Juli. Namun penghapusannya sebaiknya satu commit khusus agar mudah direview atau direvert.

## Kelas C - rapikan, jangan hapus massal

### `docs/pustaka/`

Folder ini adalah arsip sumber penulisan, bukan dependency runtime. Audit hash menemukan dua pasangan duplikat identik:

- `2023-rgbd2cap-frontiers.pdf` sama persis dengan `2023-rgbd2cap-frontiers-dense-captioning.pdf` (sekitar 2,52 MiB dapat dihemat);
- `2024-comfort-vlm-spatial-frame-reference.pdf` sama persis dengan `2024-vlm-represent-space-comfort.pdf` (sekitar 5,43 MiB dapat dihemat).

Simpan satu nama kanonik per pasangan dan perbarui `source_index.md` bila nama yang dihapus masih dirujuk.

`source_index.md` sendiri perlu diperbaiki, bukan dihapus. Dokumen itu masih menyebut Depth Anything, ZoeDepth, Hybrid Fusion, input dua gambar, dan evaluasi objek terdekat sebagai arah aktif. Isi tersebut bertentangan dengan `CONTEXT.md` 23 Juli yang memisahkan Gemma dan HC-SR04 serta tidak lagi memakai depth. Sumber depth/spatial lama boleh tetap sebagai arsip pustaka, tetapi harus dipisahkan dari indeks sumber aktif.

File `2024-indoor-scene-understanding-assistive-valipoor.pdf` hanya sekitar 3 KiB dan perlu divalidasi format/integritas sebelum dipertahankan sebagai sumber. Jangan mengutipnya hanya berdasarkan nama file.

### `research/`

Tidak ada file cache/build/temp di folder ini. Klasifikasi yang disarankan:

**Pertahankan sebagai dasar langsung arah aktif:**

- `academic-hcsr04-optimal-indoor-range-2026-07-22.md`;
- `source-digest-farhan-aufar-image-description-2025.md`.

**Arsipkan sebagai keputusan/eksplorasi historis:**

- `academic-bride-gap-supervisor-fit-2026-07-15.md`;
- `academic-event-driven-local-vlm-hcsr04-array-2026-07-21.md`;
- `academic-litedesc-go-no-go-2026-07-16.md`;
- `academic-low-burden-alternative-thesis-directions-2026-07-15.md`;
- `academic-mbg-vs-litedesc-decision-2026-07-16.md`;
- `academic-thesis-problem-architecture-gunadarma-adang-2026-07-22.md`;
- `academic-thesis-project-alternatives-supervisor-fit-2026-07-15.md`.

**Superseded dan berpotensi menyesatkan jika dibiarkan sebagai dokumen aktif:**

- `plan-pivot-hybrid-fusion-closest-object-2026-07-22.md`.

Dokumen terakhir menyebut dirinya kontrak implementasi aktif dan mengizinkan pengikatan jarak ke objek setelah gate tertentu. Ini bertentangan langsung dengan `CONTEXT.md`, yang melarang pengikatan angka sensor ke objek bernama. Pindahkan ke `research/archive/` dengan label `SUPERSEDED`, atau hapus bila jejak Git/backup lain telah dipastikan. Jangan biarkan statusnya tetap “aktif”.

## Kelas D - wajib dipertahankan

- seluruh `results/`, termasuk capture, source image, `analysis_runs.jsonl`, `sensor_captures.jsonl`, dan `predictions.csv`;
- `archive/historical_depth_experiment_20260722/` beserta `SHA256SUMS`;
- `CONTEXT.md`, `instructions/PROJECT_INITIALIZATION.md`, `README.md`;
- `docs/README.md`, `docs/architecture.md`, `docs/evaluation_protocol.md`, `docs/DESIGN.md`;
- `docs/pustaka/hcsr04_indoor_evidence_context.md` dan sumber yang benar-benar dipakai untuk argumen HC-SR04;
- `docs/dataset_v2_final_evaluation_20260723.md` dan `docs/hasil_sementara_penelitian_v2_20260723.md` yang sedang menjadi artefak evaluasi aktif;
- source `prototypes/esp32_hcsr04_isolated_pilot/` di luar `.pio/`, `.venv/`, dan cache;
- `app/`, `services/`, `models/`, `scripts/`, `tests/`, `static/`, `templates/`, serta konfigurasi aktif.

## Urutan pembersihan yang disarankan

1. Snapshot `git status` dan hash/count `results/`; hentikan jika ada target yang masuk `results/`.
2. Hapus hanya generated/ignored artifacts Kelas A.
3. Jalankan test aktif untuk membuktikan cleanup tidak merusak runtime.
4. Hapus tiga prototipe depth tracked dalam commit terpisah.
5. Deduplicate dua pasangan PDF dan selaraskan `source_index.md` dengan scope tanpa depth.
6. Buat `research/archive/`, pindahkan dokumen eksplorasi lama, dan beri label superseded pada rencana Hybrid Fusion.
7. Verifikasi ulang bahwa seluruh file dan hash di `results/` identik dengan baseline.

## Batas audit

Audit ini menentukan keterikatan file terhadap source, test, dokumentasi, Git, dan scope aktif. Audit tidak menyatakan bahwa semua pustaka lama tidak bernilai akademik; sumber yang tidak aktif pada runtime masih dapat berguna sebagai jejak keputusan atau tinjauan pustaka. Worktree memiliki perubahan pengguna pada `results/predictions.csv`, skrip, test, dan dokumen evaluasi 23 Juli; perubahan tersebut dipertahankan selama cleanup.

## Hasil eksekusi setelah persetujuan

Pembersihan dijalankan setelah pengguna menyetujui rekomendasi audit:

- cache pytest, CodeGraph, log lama, bytecode Python, build PlatformIO, dan virtual environment pilot dibersihkan;
- `notebooks/` dan tiga prototipe depth lama dihapus dari worktree Git;
- dua salinan PDF identik dihapus dengan mempertahankan satu nama kanonik;
- `2024-indoor-scene-understanding-assistive-valipoor.pdf` dihapus setelah pemeriksaan byte membuktikan file tersebut sebenarnya halaman HTML 3.038 byte, bukan PDF;
- `source_index.md` diselaraskan dengan pipeline Gemma 4 E2B + HC-SR04 tanpa depth;
- delapan dokumen eksplorasi lama dipindahkan ke `research/archive/`, dan rencana Hybrid Fusion diberi status `SUPERSEDED`;
- regression suite selesai dengan `90 passed`;
- perbandingan sebelum/sesudah terhadap 91 file di `results/` menghasilkan nol file bertambah, hilang, atau berubah hash.

Dua log root, `.uvicorn.err.log` dan `.uvicorn.out.log`, tidak dihapus karena sedang dibuka dan terus ditulis oleh proses runtime aktif. Keduanya bukan artefak penelitian dan dapat dibersihkan setelah server berhenti.
