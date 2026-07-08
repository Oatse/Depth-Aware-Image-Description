# Final Experiment Report - Gemma e2b Isolated

Tanggal eksekusi: 2026-07-08

> Catatan pembaruan: anotasi final telah divalidasi ulang per batch 5 gambar pada `docs/final_annotation_revalidation_20260708.md`. Untuk metrik setelah koreksi anotasi, gunakan `results/final_evaluation_gemma_e2b_revalidated_annotations_20260708.csv`.

## Status Dataset Final

Dataset final dibekukan sebagai artefak baru, bukan mengganti dataset awal.

- Gambar final: `dataset/final_images/` sebanyak 44 gambar.
- Anotasi final: `dataset/final_annotations.csv` sebanyak 44 baris.
- Manifest freeze: `dataset/final_manifest.csv` berisi `source_path`, `final_path`, dan `sha256` tiap file.
- Contact sheet audit: `results/annotation_audit_sheets/final_dataset_44_audit_sheet.png`.
- Komposisi sumber: {'original_30': 30, 'sample_new_balancing_medium_far': 14}.
- Distribusi distance: {'dekat': 21, 'sedang': 15, 'sangat_dekat': 2, 'jauh': 6}.
- Distribusi obstacle: {'yes': 23, 'no': 21}.
- Distribusi posisi: {'kanan': 16, 'tengah': 16, 'kiri': 12}.

Keputusan dataset: 30 gambar asli dipertahankan seluruhnya. Tambahan 14 gambar diambil dari `dataset/sample_new/`, bukan `sample_new_excluded_close/`, karena kebutuhan utama dataset final adalah menambah kasus `sedang` dan `jauh`; menambah close-up baru akan memperbesar bias kelas `dekat`.

## Validasi Anotasi

Validasi dilakukan pada dua lapis: audit visual contact sheet dan validasi skema/logika CSV.

Hasil validasi skema:

- file gambar tanpa anotasi: 0;
- anotasi tanpa file gambar: 0;
- duplikasi `image_name`: 0;
- kolom wajib untuk evaluator: lengkap;
- aturan `has_obstacle=yes` hanya muncul pada `sangat_dekat/dekat`: valid;
- aturan `has_obstacle=no` hanya muncul pada `sedang/jauh`: valid.

Kolom konseptual tambahan ditambahkan pada anotasi final:

- `obstacle_warning`: turunan eksplisit dari `has_obstacle`;
- `open_area`: turunan eksplisit dari `safer_direction` sebagai area relatif lebih lapang.

Catatan ambiguitas yang tetap dipertahankan: beberapa gambar dapur/kamar mandi close-up dan pintu terbuka tidak sepenuhnya merepresentasikan jalur berjalan. Gambar tersebut tidak dihapus karena berguna untuk menguji batas sistem, tetapi ditandai pada analisis per gambar sebagai `scene/anotasi ambigu` bila menyebabkan mismatch.

## Definisi Distance Final

Definisi ground-truth anotasi memakai objek atau struktur navigasi yang paling relevan di area depan, bukan rata-rata seluruh scene.

Prioritas pemilihan objek:

1. objek terdekat yang berpotensi menjadi halangan visual di area depan;
2. bila tidak ada halangan dekat, objek/struktur dominan yang menjelaskan ruang, misalnya pintu, lorong, meja, bangku, atau area terbuka;
3. bila scene berupa ruang/lantai kosong, label dapat memakai struktur dominan jauh seperti pintu/lorong.

Kategori anotasi final:

- `sangat_dekat`: estimasi visual objek relevan kurang dari 0.5 m;
- `dekat`: 0.5 sampai kurang dari 1.0 m;
- `sedang`: 1.0 sampai kurang dari 2.0 m;
- `jauh`: 2.0 m atau lebih.

Penting: nilai di atas adalah definisi anotasi visual, bukan output meter presisi dari depth model.

## Threshold Depth Final

Threshold depth yang digunakan tetap threshold terkalibrasi di `services/depth_analysis.py`:

- `sangat_dekat`: p10 depth score `< 1.0`;
- `dekat`: p10 depth score `< 1.6`;
- `sedang`: p10 depth score `< 2.4`;
- `jauh`: p10 depth score `>= 2.4`.

Depth pipeline memakai p10 tiap region 3x3, lalu memilih region prioritas navigasi: `lower_center`, `middle_center`, `lower_left`, `lower_right`, `middle_left`, `middle_right`. Threshold ini tidak dikalibrasi ulang setelah dataset final dibentuk agar evaluasi tidak makin overfit pada data uji.

Implikasi kalibrasi final: obstacle warning cukup stabil, tetapi kategori `sangat_dekat` masih lemah karena dua gambar GT `sangat_dekat` diprediksi `dekat`.

## Konfigurasi Eksperimen Final

Model utama:

- LM Studio model: `google/gemma-4-e2b`;
- context length: 4096;
- parallel: 1;
- GPU offload: `max` pada perintah `lms load`;
- `LM_STUDIO_MAX_TOKENS=1200`;
- `LM_STUDIO_TIMEOUT=240`;
- mock runtime: tidak aktif;
- mode run: resumable, `--limit-jobs 1`, satu gambar-mode per job.

Command utama:

```powershell
lms load google/gemma-4-e2b --identifier google/gemma-4-e2b --context-length 4096 --parallel 1 --gpu max -y
$env:LM_STUDIO_MODEL='google/gemma-4-e2b'; $env:LM_STUDIO_MAX_TOKENS='1200'; $env:LM_STUDIO_TIMEOUT='240'
python scripts\run_resumable_evaluation.py --images-dir dataset\final_images --annotations dataset\final_annotations.csv --predictions results\final_predictions_gemma_e2b_20260708.csv --output results\final_evaluation_gemma_e2b_20260708.csv --modes gemma_only depth_only gemma_depth gemma_depth_prompted --limit-jobs 1
```

Preflight dan tes:

```powershell
python scripts\run_batch_evaluation.py --images-dir dataset\final_images --annotations dataset\final_annotations.csv --predictions results\final_predictions_gemma_e2b_20260708.csv --output results\final_evaluation_gemma_e2b_20260708.csv --modes gemma_only depth_only gemma_depth gemma_depth_prompted --preflight-only
python -m pytest tests\test_evaluator.py tests\test_experiment_preflight.py tests\test_run_batch_evaluation.py tests\test_depth_analysis.py tests\test_depth_prompting.py tests\test_fusion.py -q
```

Verification result:

- preflight final: passed;
- relevant tests: 20 passed;
- final jobs: 176/176 success;
- runtime error log: `results/final_errors_gemma_e2b_20260708.log` kosong.

## Tabel Hasil Seluruh Mode

| Mode | Coverage | Object | Position | Distance | Obstacle | Quality | Avg latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| `gemma_only` | 100.00% | 45.45% | 47.73% | N/A | N/A | 3.22/5 | 10,569.2 ms |
| `depth_only` | 100.00% | 0.00% | 72.73% | 63.64% | 79.55% | 3.16/5 | 1,638.2 ms |
| `gemma_depth` | 100.00% | 45.45% | 88.64% | 63.64% | 79.55% | 3.77/5 | 11,794.9 ms |
| `gemma_depth_prompted` | 100.00% | 34.09% | 86.36% | 63.64% | 79.55% | 3.64/5 | 14,274.0 ms |

## Distance Confusion - Prompt Fusion

Depth output identik untuk `depth_only`, `gemma_depth`, dan `gemma_depth_prompted`, sehingga tabel ini cukup mewakili semua mode depth-aware.

| Ground truth | Prediction | Count |
|---|---|---:|
| dekat | dekat | 17 |
| dekat | jauh | 1 |
| dekat | sangat_dekat | 1 |
| dekat | sedang | 2 |
| jauh | jauh | 5 |
| jauh | sedang | 1 |
| sangat_dekat | dekat | 2 |
| sedang | dekat | 6 |
| sedang | jauh | 3 |
| sedang | sedang | 6 |

Ringkasan confusion:

- `dekat`: 17/21 benar;
- `sedang`: 6/15 benar, 6 bergeser ke `dekat`, 3 bergeser ke `jauh`;
- `jauh`: 5/6 benar;
- `sangat_dekat`: 0/2 benar, keduanya bergeser ke `dekat`;
- obstacle warning: 35/44 benar pada semua mode depth-aware.

## Perbandingan Antarmode

- `gemma_only` masih paling lemah pada posisi karena tidak menerima metadata depth eksplisit: 47.73%.
- `depth_only` tidak mengenali objek, tetapi memberi baseline depth/obstacle: distance 63.64%, obstacle 79.55%.
- `gemma_depth` adalah mode terbaik secara keseluruhan untuk dataset final: object 45.45%, position 88.64%, quality 3.77/5, latency 11.79 detik.
- `gemma_depth_prompted` tidak mengalahkan late fusion pada dataset final: object turun ke 34.09%, position sedikit turun ke 86.36%, quality turun ke 3.64/5, dan latency naik ke 14.27 detik.

Rekomendasi mode terbaik: gunakan `gemma_depth` / Late Fusion sebagai mode utama Bab 4. Prompt Fusion tetap valid sebagai mode pembanding, tetapi tidak direkomendasikan sebagai mode utama karena lebih lambat dan tidak meningkatkan metrik utama pada dataset final.

## Qwen Subset A/B

Qwen tidak dijalankan full evaluation karena latency tidak praktis. Qwen dijalankan hanya pada subset representatif 10 gambar final dengan mode `gemma_depth_prompted`.

Subset: `indoor_006.webp`, `indoor_029.webp`, `indoor_001.webp`, `indoor_022.webp`, `indoor_005.webp`, `1 (6083).jpg`, `1 (34).jpg`, `1 (7248).jpg`, `1 (7254).jpg`, `indoor_013.webp`.

| Model | Images | Coverage | Object | Position | Distance | Obstacle | Quality | Avg latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Gemma e2b prompted | 10 | 100.00% | 40.00% | 90.00% | 40.00% | 80.00% | 3.50/5 | 14,376.9 ms |
| Qwen prompted | 10 | 100.00% | 50.00% | 100.00% | 40.00% | 80.00% | 3.70/5 | 54,605.5 ms |

Interpretasi: Qwen lebih baik pada object, position, dan quality di subset kecil, tetapi distance/obstacle sama dan latency rata-rata 3.8x Gemma e2b. Qwen layak disebut pembanding, bukan model utama final.

## Analisis Per Gambar

Kolom `success modes` menghitung jumlah mode dari empat mode utama yang seluruh kriteria heuristiknya lulus pada gambar tersebut. CSV detail per mode tersedia di `results/final_per_image_analysis_gemma_e2b_20260708.csv`.

| Image | Source | Ground truth | Success modes | Prompted prediction | Depth-only distance | Penyebab dominan | Catatan ambiguitas |
|---|---|---|---:|---|---|---|---|
| `indoor_001.webp` | original_30 | kipas angin / kanan / dekat / obs=yes | 0/4 | ruangan / tengah / sedang | sedang | model+depth | - |
| `indoor_002.webp` | original_30 | kipas angin / kanan / dekat / obs=yes | 0/4 | ruangan / tengah / sedang | sedang | model+depth | - |
| `indoor_003.webp` | original_30 | meja kerja / tengah / dekat / obs=yes | 3/4 | Meja kerja / tengah / dekat | dekat | depth-only grid | - |
| `indoor_004.webp` | original_30 | tumpukan barang / kanan / dekat / obs=yes | 2/4 | pintu dan barang / tengah / dekat | dekat | model: objek+posisi | - |
| `indoor_005.webp` | original_30 | kulkas / kanan / sedang / obs=no | 0/4 | koridor / tengah / dekat | dekat | model+depth | - |
| `indoor_006.webp` | original_30 | galon air / kiri / sangat_dekat / obs=yes | 0/4 | area dapur / tengah / dekat | dekat | model+depth | - |
| `indoor_007.webp` | original_30 | kantong belanja / kanan / dekat / obs=yes | 1/4 | area kamar / tengah / dekat | dekat | model: objek+posisi | - |
| `indoor_008.webp` | original_30 | ember / kiri / dekat / obs=yes | 0/4 | tempat sampah / bawah / dekat | dekat | scene/anotasi ambigu | small bathroom; area relatif lapang intrinsically unclear |
| `indoor_009.webp` | original_30 | ember / kiri / dekat / obs=yes | 0/4 | wadah plastik / bawah / jauh | jauh | scene/anotasi ambigu | small bathroom; two containers split left/right |
| `indoor_010.webp` | original_30 | wastafel / tengah / dekat / obs=yes | 3/4 | wastafel dan area wastafel / tengah / dekat | dekat | scene/anotasi ambigu | sink/counter close-up, not pure walking path |
| `indoor_011.webp` | original_30 | galon air / kanan / dekat / obs=yes | 0/4 | area ruangan / tengah / dekat | dekat | model: objek | - |
| `indoor_012.webp` | original_30 | magic com / kiri / dekat / obs=yes | 1/4 | Perabotan dan lorong / tengah / dekat | dekat | model: objek+posisi | - |
| `indoor_013.webp` | original_30 | pintu / tengah / jauh / obs=no | 2/4 | Pintu / kanan / jauh | jauh | depth-only grid | - |
| `indoor_014.webp` | original_30 | bantal lantai / kiri / dekat / obs=yes | 1/4 | Perabotan dan barang di lantai / tengah-kiri / dekat | dekat | model: objek+posisi | - |
| `indoor_015.webp` | original_30 | koper / kiri / sedang / obs=no | 3/4 | koper dan sepatu / tengah/bawah / sedang | sedang | model: posisi | - |
| `indoor_016.webp` | original_30 | lemari plastik / kanan / dekat / obs=yes | 1/4 | rak dinding kayu / tengah / dekat | dekat | model: objek+posisi | - |
| `indoor_017.webp` | original_30 | meja kerja / kanan / dekat / obs=yes | 2/4 | setup meja / tengah-kanan / dekat | dekat | model: posisi | - |
| `indoor_018.webp` | original_30 | kantong belanja / kanan / dekat / obs=yes | 0/4 | area dapur dan lantai / tengah / dekat | dekat | model: objek | - |
| `indoor_019.webp` | original_30 | kulkas / kanan / sedang / obs=no | 0/4 | furniture / tengah-kanan / dekat | dekat | model+depth | - |
| `indoor_020.webp` | original_30 | kompor / tengah / dekat / obs=yes | 2/4 | area dapur / tengah / dekat | dekat | scene/anotasi ambigu | stove/kitchen counter close-up, not pure walking path |
| `indoor_021.webp` | original_30 | wastafel / kiri / dekat / obs=yes | 0/4 | wastafel dan area kamar mandi / tengah / sangat_dekat | sangat_dekat | scene/anotasi ambigu | sink and door frame both visible; left/front interpretation borderline |
| `indoor_022.webp` | original_30 | pintu / kiri / dekat / obs=yes | 2/4 | Lorong interior / tengah / dekat | dekat | scene/anotasi ambigu | open door as obstacle while corridor still visible |
| `indoor_023.webp` | original_30 | pintu / tengah / jauh / obs=no | 1/4 | pintu kayu / tengah / jauh | jauh | model: posisi | - |
| `indoor_024.webp` | original_30 | pintu / kiri / dekat / obs=yes | 3/4 | Interior ruangan / tengah / dekat | dekat | scene/anotasi ambigu | open door and floor objects; path/right openness depends on interpretation |
| `indoor_025.webp` | original_30 | kursi / kanan / dekat / obs=yes | 2/4 | setup meja kerja / tengah / dekat | dekat | model: posisi | - |
| `indoor_026.webp` | original_30 | rak sepatu / kanan / sedang / obs=no | 0/4 | koper dan sepatu / tengah/kanan / dekat | dekat | model+depth | - |
| `indoor_027.webp` | original_30 | kipas angin / kanan / sedang / obs=no | 3/4 | kipas angin dan bangku / kanan / sedang | sedang | model: posisi | - |
| `indoor_028.webp` | original_30 | meja komputer / tengah / dekat / obs=yes | 0/4 | setup meja kerja / tengah / dekat | dekat | model: objek | - |
| `indoor_029.webp` | original_30 | kursi / tengah / sangat_dekat / obs=yes | 1/4 | kursi / tengah / dekat | dekat | depth | - |
| `indoor_030.webp` | original_30 | pintu / kiri / dekat / obs=yes | 0/4 | pintu / tengah / dekat | dekat | scene/anotasi ambigu | open door dominates left foreground but corridor remains visible |
| `1 (34).jpg` | sample_new_balancing_medium_far | meja konsol / tengah / sedang / obs=no | 1/4 | Perabotan ruangan / tengah / sedang | sedang | model: objek | - |
| `1 (1030).jpg` | sample_new_balancing_medium_far | mesin cuci / kanan / sedang / obs=no | 3/4 | mesin cuci / tengah / sedang | sedang | model: posisi | - |
| `1 (8391).jpg` | sample_new_balancing_medium_far | meja kecil / kiri / sedang / obs=no | 0/4 | Tangga dan Interior / tengah / jauh | jauh | model+posisi+depth | - |
| `1 (8466).jpg` | sample_new_balancing_medium_far | kabinet dapur / kiri / sedang / obs=no | 0/4 | Dapur / tengah / dekat | dekat | model+posisi+depth | - |
| `1 (8477).jpg` | sample_new_balancing_medium_far | meja ruang tamu / tengah / sedang / obs=no | 0/4 | Ruang tamu / tengah / dekat | dekat | scene/anotasi ambigu | living-room table appears central but foreground openness is subjective |
| `1 (8553).jpg` | sample_new_balancing_medium_far | lorong / tengah / sedang / obs=no | 1/4 | Interior ruangan / tengah / dekat | dekat | depth | - |
| `1 (6083).jpg` | sample_new_balancing_medium_far | bangku ruang ganti / kanan / sedang / obs=no | 0/4 | bangku / tengah / jauh | jauh | model+depth | - |
| `1 (6082).jpg` | sample_new_balancing_medium_far | bangku ruang ganti / kanan / sedang / obs=no | 0/4 | koridor / tengah / jauh | jauh | model+depth | - |
| `1 (6845).jpg` | sample_new_balancing_medium_far | tangga / tengah / sedang / obs=no | 3/4 | ruangan / tengah / sedang | sedang | prompted: objek | - |
| `1 (6169).jpg` | sample_new_balancing_medium_far | bangku / tengah / sedang / obs=no | 2/4 | koridor interior / tengah / sedang | sedang | scene/anotasi ambigu | bench is right-wall object but perspective makes center/right borderline |
| `1 (7248).jpg` | sample_new_balancing_medium_far | lorong / tengah / jauh / obs=no | 0/4 | koridor / tengah / sedang | sedang | model+depth | - |
| `1 (7254).jpg` | sample_new_balancing_medium_far | lorong / tengah / jauh / obs=no | 3/4 | koridor / tengah / jauh | jauh | model: objek | - |
| `1 (7252).jpg` | sample_new_balancing_medium_far | lorong / tengah / jauh / obs=no | 3/4 | lorong / tengah / jauh | jauh | model: objek | - |
| `1 (7245).jpg` | sample_new_balancing_medium_far | lorong / tengah / jauh / obs=no | 3/4 | koridor / tengah / jauh | jauh | model: objek | - |

## Dokumentasi Reproducibility

Artefak utama:

- `dataset/final_images/`
- `dataset/final_annotations.csv`
- `dataset/final_manifest.csv`
- `dataset/ab_qwen_subset_20260708/annotations.csv`
- `results/final_predictions_gemma_e2b_20260708.csv`
- `results/final_evaluation_gemma_e2b_20260708.csv`
- `results/final_runtime_gemma_e2b_20260708.log`
- `results/final_errors_gemma_e2b_20260708.log`
- `results/final_evaluation_gemma_e2b_revalidated_annotations_20260708.csv`
- `results/final_per_image_analysis_gemma_e2b_revalidated_annotations_20260708.csv`
- `results/final_distance_confusion_gemma_e2b_revalidated_annotations_20260708.csv`
- `results/final_obstacle_confusion_gemma_e2b_revalidated_annotations_20260708.csv`
- `results/final_mode_failure_summary_gemma_e2b_revalidated_annotations_20260708.csv`
- `results/qwen_subset_predictions_20260708.csv`
- `results/qwen_subset_evaluation_20260708.csv`
- `results/qwen_subset_runtime_20260708.log`
- `results/qwen_subset_errors_20260708.log`
- `results/gemma_e2b_subset_predictions_20260708.csv`
- `results/gemma_e2b_subset_evaluation_20260708.csv`

## Masalah Yang Masih Belum Terselesaikan

1. `sangat_dekat` belum terdeteksi benar oleh threshold depth; dua kasus GT `sangat_dekat` menjadi `dekat`.
2. Kelas `sedang` masih mudah tertukar ke `dekat` atau `jauh`, terutama pada ruangan terbuka dan objek samping.
3. Object accuracy Gemma e2b masih rendah; late fusion tidak memperbaiki semantik objek karena depth tidak mengenali objek.
4. Beberapa anotasi tetap mengandung ambiguitas konseptual: pintu terbuka sebagai halangan, close-up dapur/kamar mandi, dan area yang bukan jalur berjalan.
5. Distance ground truth masih estimasi visual, bukan pengukuran meter manual.
6. Threshold depth dikembangkan dari dataset lokal yang berdekatan; klaim generalisasi indoor harus tetap dibatasi.
7. Evaluasi kualitas deskripsi masih heuristik otomatis; untuk skripsi sebaiknya ditambah penilaian manual minimal dua penilai.

## Putusan Akhir

Dataset final sudah cukup konsisten dan reproducible untuk evaluasi pilot skripsi pada citra indoor lokal terbatas. Mode terbaik untuk laporan utama adalah `gemma_depth` Late Fusion, bukan Prompt Fusion. Narasi akademik yang aman: depth membantu metadata spasial dan obstacle warning secara terbatas, tetapi sistem belum boleh diklaim siap navigasi real-time atau general untuk semua lingkungan indoor.
