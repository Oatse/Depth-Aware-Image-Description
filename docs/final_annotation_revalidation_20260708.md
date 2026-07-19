# Final Annotation Revalidation - 2026-07-08

> Arsip revalidasi anotasi. Baris mode Depth-to-Spatial Prompting dipertahankan sebagai sejarah eksperimen, bukan fitur atau hasil utama aktif.

Validasi ulang dilakukan bertahap per 5 gambar agar keputusan anotasi tidak terlalu kasar. Fokus validasi:

- `main_object`
- `object_position`
- `distance_category`
- `has_obstacle`
- `front_area_status`
- `open_area`

Aturan kerja yang diperbaiki:

- `distance_category` mengacu pada jarak visual objek utama atau struktur utama yang dianotasi.
- `has_obstacle` mengacu pada potensi halangan visual terhadap area depan/jalur visual dominan.
- Objek dekat di sisi gambar dapat tetap memiliki `open_area` di sisi lain, tetapi jika objek menutup sebagian jalur visual maka `has_obstacle=yes`.
- `open_area` tidak berarti jalur aman, hanya area relatif lebih lapang.

## Batch 01 - `indoor_001.webp` sampai `indoor_005.webp`

Contact sheet: `results/annotation_audit_sheets/revalidation_batch_01_001_005.png`

| Image | Keputusan | Catatan |
|---|---|---|
| `indoor_001.webp` | tetap | Kipas angin kanan cukup dekat dan relevan sebagai potensi halangan visual; area tengah relatif lebih lapang masih masuk akal. |
| `indoor_002.webp` | tetap | Kipas angin kanan/depan dominan dan dekat; label `dekat/yes` masih tepat. |
| `indoor_003.webp` | tetap | Meja kerja memenuhi depan-tengah; label `dekat/yes` tepat. |
| `indoor_004.webp` | tetap | Tumpukan barang kanan menutup sisi kanan jalur visual; label `dekat/yes` tepat. |
| `indoor_005.webp` | koreksi | Sebelumnya `sedang/no`. Kulkas/lemari kecil berada dekat di kanan depan dan menutup sisi kanan jalur visual. Diubah menjadi `dekat/yes`; area kiri tetap relatif lapang. |

## Batch 02 - `indoor_006.webp` sampai `indoor_010.webp`

Contact sheet: `results/annotation_audit_sheets/revalidation_batch_02_006_010.png`

| Image | Keputusan | Catatan |
|---|---|---|
| `indoor_006.webp` | tetap | Galon air sangat dekat di kiri bawah; label `sangat_dekat/yes` tepat. |
| `indoor_007.webp` | tetap | Kantong/kardus belanja berada dekat di kanan bawah dekat ambang pintu; label `dekat/yes` masih tepat. |
| `indoor_008.webp` | tetap | Ember besar dekat di kiri bawah; ruang kamar mandi sempit membuat `open_area` tetap `tidak_diketahui`. |
| `indoor_009.webp` | koreksi | Sebelumnya `open_area=area_kanan_relatif_lapang`. Kanan juga berisi tempat sampah dekat, sehingga area relatif lapang tidak jelas. Diubah menjadi `tidak_diketahui`. |
| `indoor_010.webp` | koreksi | Wastafel/counter berada lebih tepat di kanan depan, bukan tengah murni. Scene berupa close-up counter, sehingga `open_area` diubah menjadi `tidak_diketahui`. |

## Batch 03 - `indoor_011.webp` sampai `indoor_015.webp`

Contact sheet: `results/annotation_audit_sheets/revalidation_batch_03_011_015.png`

| Image | Keputusan | Catatan |
|---|---|---|
| `indoor_011.webp` | tetap | Galon air berada dekat di kanan/dapur kanan; label `dekat/yes` masih tepat. |
| `indoor_012.webp` | tetap | Magic com berada dekat di kiri depan lorong; area kanan-tengah relatif lapang masih masuk akal. |
| `indoor_013.webp` | tetap | Pintu berada jauh di tengah dengan lantai depan kosong; label `jauh/no` tepat. |
| `indoor_014.webp` | tetap | Objek lantai/kantong di kiri dekat lebih relevan sebagai potensi halangan daripada kasur; label `dekat/yes` masih tepat. |
| `indoor_015.webp` | koreksi | Sebelumnya `sedang/no`. Koper terlihat dekat di kiri depan, walau area tengah masih relatif lapang. Diubah menjadi `dekat/yes` dengan `open_area=area_tengah_relatif_lapang`. |

## Batch 04 - `indoor_016.webp` sampai `indoor_020.webp`

Contact sheet: `results/annotation_audit_sheets/revalidation_batch_04_016_020.png`

| Image | Keputusan | Catatan |
|---|---|---|
| `indoor_016.webp` | tetap | Lemari plastik kanan dekat dan ruang depan terbatas; label `dekat/yes` masih tepat. |
| `indoor_017.webp` | tetap | Meja kerja dan perangkat mikrofon sangat dekat di kanan depan; label `dekat/yes` tepat. |
| `indoor_018.webp` | tetap | Kantong belanja dekat di kanan bawah; label `dekat/yes` tepat. |
| `indoor_019.webp` | koreksi | Sebelumnya `sedang/no`. Kulkas kanan terlihat dekat dan menutup sisi kanan jalur visual. Diubah menjadi `dekat/yes`; area kiri-tengah tetap relatif lapang. |
| `indoor_020.webp` | tetap | Kompor/counter adalah close-up dapur dan bukan jalur berjalan; `open_area=tidak_diketahui` tetap tepat. |

## Batch 05 - `indoor_021.webp` sampai `indoor_025.webp`

Contact sheet: `results/annotation_audit_sheets/revalidation_batch_05_021_025.png`

| Image | Keputusan | Catatan |
|---|---|---|
| `indoor_021.webp` | tetap | Wastafel/counter berada dekat di kiri; pintu kamar mandi kanan membuat ruang depan terbatas. |
| `indoor_022.webp` | tetap | Daun pintu terbuka dekat di kiri dapat menjadi potensi halangan visual, sementara koridor kanan relatif lapang. |
| `indoor_023.webp` | tetap | Pintu berada jauh di tengah dan koridor tengah kosong; label `jauh/no` tepat. |
| `indoor_024.webp` | tetap | Pintu terbuka dekat di kiri dan objek lantai membuat area depan perlu diperhatikan; area kanan relatif lapang. |
| `indoor_025.webp` | tetap | Kursi putih berada dekat di kanan depan meja kerja; label `dekat/yes` tepat. |

## Batch 06 - `indoor_026.webp` sampai `indoor_030.webp`

Contact sheet: `results/annotation_audit_sheets/revalidation_batch_06_026_030.png`

| Image | Keputusan | Catatan |
|---|---|---|
| `indoor_026.webp` | koreksi | Sebelumnya `sedang/no`. Rak sepatu/sepatu kanan terlihat dekat di foreground. Diubah menjadi `dekat/yes`; area kiri-tengah tetap relatif lapang. |
| `indoor_027.webp` | tetap | Kipas angin berada di kanan tengah dan lantai depan masih terbuka; label `sedang/no` masih tepat. |
| `indoor_028.webp` | tetap | Meja komputer dan mikrofon sangat dekat memenuhi depan; label `dekat/yes` tepat. |
| `indoor_029.webp` | tetap | Kursi berada sangat dekat di tengah dan menutup area depan; label `sangat_dekat/yes` tepat. |
| `indoor_030.webp` | tetap | Pintu terbuka dekat di kiri depan; label `dekat/yes` tetap tepat meskipun koridor kanan masih terlihat. |

## Batch 07 - `1 (34).jpg` sampai `1 (8477).jpg`

Contact sheet: `results/annotation_audit_sheets/revalidation_batch_07_sample_01_05.png`

| Image | Keputusan | Catatan |
|---|---|---|
| `1 (34).jpg` | tetap | Meja konsol berada di tengah pada jarak sedang; area depan relatif terbuka. |
| `1 (1030).jpg` | tetap | Deretan mesin cuci berada kanan-tengah dengan lantai depan terbuka; label `sedang/no` masih tepat. |
| `1 (8391).jpg` | koreksi | Objek utama sebelumnya `meja kecil`; visual lebih dominan dan relevan sebagai `tangga` di tengah. Kategori jarak tetap `sedang`. |
| `1 (8466).jpg` | tetap | Kabinet dapur di kiri, sementara jalur tengah menuju pintu relatif lapang; label `sedang/no` tepat. |
| `1 (8477).jpg` | tetap | Meja ruang tamu berada di tengah tetapi tidak sangat dekat dengan kamera; label `sedang/no` masih tepat. |

## Batch 08 - `1 (8553).jpg` sampai `1 (6169).jpg`

Contact sheet: `results/annotation_audit_sheets/revalidation_batch_08_sample_06_10.png`

| Image | Keputusan | Catatan |
|---|---|---|
| `1 (8553).jpg` | koreksi | Sebelumnya `sedang`. Scene lorong/ruang kosong tidak memiliki objek dekat; struktur dominan lebih tepat dibaca `jauh`. |
| `1 (6083).jpg` | tetap | Bangku ruang ganti berada di kanan, area lantai depan relatif lapang; label `sedang/no` masih dapat dipertahankan. |
| `1 (6082).jpg` | tetap | Bangku berada kanan-belakang, area depan tengah cukup kosong; label `sedang/no` tepat. |
| `1 (6845).jpg` | tetap | Tangga berada di tengah belakang dengan area karpet depan lapang; label `sedang/no` tepat. |
| `1 (6169).jpg` | koreksi | Objek bangku berada di kanan, bukan tengah. Jarak tetap `sedang` karena bangku tidak berada di foreground. |

## Batch 09 - `1 (7248).jpg` sampai `1 (7245).jpg`

Contact sheet: `results/annotation_audit_sheets/revalidation_batch_09_sample_11_14.png`

| Image | Keputusan | Catatan |
|---|---|---|
| `1 (7248).jpg` | tetap | Lorong memanjang dengan objek kecil jauh di ujung; area depan kosong. Label `jauh/no` tepat. |
| `1 (7254).jpg` | tetap | Koridor panjang dengan area depan kosong dan struktur jauh di ujung; label `jauh/no` tepat. |
| `1 (7252).jpg` | tetap | Lorong panjang dengan pot tanaman jauh di tengah belakang; label `jauh/no` tepat. |
| `1 (7245).jpg` | tetap | Koridor panjang dengan area depan kosong dan objek jauh di ujung; label `jauh/no` tepat. |

## Ringkasan Akhir Revalidasi

Total dataset final tetap 44 gambar. Tidak ada file gambar tanpa anotasi, tidak ada anotasi tanpa file gambar, dan tidak ada nilai kategori ilegal.

Distribusi setelah revalidasi:

| Aspek | Distribusi |
|---|---|
| `distance_category` | `dekat`: 25, `sedang`: 10, `jauh`: 7, `sangat_dekat`: 2 |
| `has_obstacle` | `yes`: 27, `no`: 17 |
| `object_position` | `kanan`: 18, `tengah`: 15, `kiri`: 11 |

Jumlah koreksi: 9 gambar.

| Image | Koreksi utama |
|---|---|
| `indoor_005.webp` | `sedang/no` menjadi `dekat/yes`. |
| `indoor_009.webp` | `open_area` dari kanan menjadi `tidak_diketahui`. |
| `indoor_010.webp` | posisi `tengah` menjadi `kanan`; `open_area` menjadi `tidak_diketahui`. |
| `indoor_015.webp` | `sedang/no` menjadi `dekat/yes`. |
| `indoor_019.webp` | `sedang/no` menjadi `dekat/yes`. |
| `indoor_026.webp` | `sedang/no` menjadi `dekat/yes`. |
| `1 (8391).jpg` | objek utama `meja kecil` menjadi `tangga`. |
| `1 (8553).jpg` | `sedang` menjadi `jauh`. |
| `1 (6169).jpg` | posisi `tengah` menjadi `kanan`. |

Evaluasi ulang terhadap prediksi Gemma e2b yang sudah ada disimpan di:

`results/final_evaluation_gemma_e2b_revalidated_annotations_20260708.csv`

Artefak analisis turunan setelah revalidasi anotasi:

- `results/final_per_image_analysis_gemma_e2b_revalidated_annotations_20260708.csv`
- `results/final_distance_confusion_gemma_e2b_revalidated_annotations_20260708.csv`
- `results/final_obstacle_confusion_gemma_e2b_revalidated_annotations_20260708.csv`
- `results/final_mode_failure_summary_gemma_e2b_revalidated_annotations_20260708.csv`

| Mode | Coverage | Object | Position | Distance | Obstacle | Quality | Avg latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| `gemma_only` | 100.00% | 47.73% | 47.73% | N/A | N/A | 3.26/5 | 10,569.2 ms |
| `depth_only` | 100.00% | 0.00% | 77.27% | 68.18% | 84.09% | 3.30/5 | 1,638.2 ms |
| `gemma_depth` | 100.00% | 47.73% | 90.91% | 68.18% | 84.09% | 3.91/5 | 11,794.9 ms |
| `gemma_depth_prompted` | 100.00% | 36.36% | 88.64% | 68.18% | 84.09% | 3.77/5 | 14,274.0 ms |

Putusan setelah revalidasi: `gemma_depth` / Late Fusion tetap menjadi mode terbaik. Revalidasi justru memperkuat hasil depth-aware karena distance accuracy naik menjadi 68.18% dan obstacle warning accuracy naik menjadi 84.09%.
