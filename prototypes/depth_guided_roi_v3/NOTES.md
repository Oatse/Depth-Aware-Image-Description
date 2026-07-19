# Verdict V3

Tanggal eksekusi final: 15 Juli 2026.

Keputusan: **FAIL — jangan melatih detector dan jangan mengklaim manfaat depth-guided ROI dari eksperimen ini.**

## Hasil Primer

| Kondisi | Structured output | Protokol MARK | Target ditemukan | Identitas benar | Latensi rata-rata |
|---|---:|---:|---:|---:|---:|
| Gemma baseline | 12/12 | N/A | 22/33 (66,67%) | N/A | 32.896 ms |
| SoM control | 12/12 | 12/12 | 36/36 (100%) | 15/36 (41,67%) | 26.897 ms |
| Depth-guided ROI | 12/12 | 11/12 | 35/36 (97,22%) | 17/36 (47,22%) | 32.363 ms |

Baseline mengukur recall kelas target pada gambar asli. Dua kondisi bertanda mengukur identitas per region. Angka tersebut tidak boleh diperlakukan sebagai metrik yang identik.

Gate yang dibekukan sebelum evaluasi untuk kondisi bertanda adalah structured output 100%, protokol MARK 100%, target coverage minimal 90%, identitas end-to-end minimal 70%, dan nol ID karangan. Kedua kondisi bertanda gagal pada identitas objek. Depth-guided juga gagal pada protokol MARK karena satu respons menghilangkan satu ID.

## Apa yang Berhasil Diperbaiki

- JSON schema LM Studio membuat 36/36 respons dapat diparsing sebagai structured output.
- Filter geometri menolak box kecil, menyentuh tepi, dan bertumpang tindih tinggi.
- Variance filter menolak region dengan campuran depth relatif yang terlalu besar.
- Badge collision avoidance membuat MARK 1–3 tetap terbaca pada box berdekatan.
- Tidak ada mark ID di luar ID yang diminta.
- Latensi marked-condition turun dari sekitar 162 detik/citra pada V2 menjadi sekitar 27–32 detik/citra pada V3.

Perbaikan tersebut menyelesaikan sebagian masalah test harness, tetapi tidak menyelesaikan grounding objek.

## Audit Kesalahan

Metrik primer menggunakan kamus sinonim yang dibekukan setelah smoke calibration dan sebelum 12 citra final dijalankan. Hasil final tidak diubah secara post-hoc.

Sebagian kegagalan berasal dari granularitas anotasi atau matcher, misalnya `chair` dijawab `armchair`, `photo frame` dijawab `painting`, dan beberapa anotasi `wardrobe` secara visual tampak seperti bookshelf atau cabinet. Namun terdapat juga kegagalan grounding yang tidak dapat dijelaskan sebagai sinonim, misalnya `table` dijawab `sofa`, `lamp` dijawab `wall decoration`, dan `window` dijawab `chair`.

Karena dua jenis kesalahan tersebut bercampur, angka 41,67% dan 47,22% bukan estimasi murni kemampuan model. Akan tetapi, re-labeling setelah melihat hasil tidak boleh dipakai untuk meloloskan gate. Selisih Depth-guided terhadap control hanya 2 mark atau 5,56 poin persentase pada target yang tidak selalu sama; angka itu tidak membuktikan keunggulan metode.

## Batas Bukti

- HomeObjects-3K tidak memiliki reference depth, sehingga urutan MARK hanya konsisten dengan keluaran model depth, bukan jarak fisik.
- Pemilihan ROI control dan depth-guided tidak selalu menghasilkan objek yang sama, sehingga perbandingan akurasi bukan paired causal comparison.
- Dua belas citra cukup untuk feasibility gate, tetapi tidak cukup untuk klaim generalisasi.
- LLM judge tidak digunakan untuk menentukan identitas objek atau kebenaran depth. Judge tidak dapat memperbaiki ground-truth yang ambigu.

## Keputusan Teknik

1. Bekukan V3 sebagai hasil negatif yang informatif.
2. Jangan melatih detector dari HomeObjects-3K untuk arsitektur ini.
3. Jangan memasukkan Depth-Guided ROI sebagai kontribusi yang telah terbukti.
4. Jika arah ini tetap dilanjutkan, eksperimen berikutnya memerlukan RGB-D dengan reference depth dan anotasi region yang selaras; itu merupakan penelitian baru, bukan perbaikan kecil V3.

Artefak final berada di `results/prototypes/depth_guided_roi_v3_final_run_20260715/`.
