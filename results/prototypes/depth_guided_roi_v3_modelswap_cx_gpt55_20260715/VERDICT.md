# Model-Swap Diagnostic Verdict

Tanggal: 15 Juli 2026.

Model pembanding dicatat sebagai label rute `cx/gpt-5.5` melalui 9router. Label tersebut tidak diperlakukan sebagai snapshot provider yang immutable.

## Desain

- Menggunakan 24 citra bertanda yang sama dari V3: 12 SoM control dan 12 Depth-Guided ROI.
- Menggunakan 72 pasangan MARK yang sama: 36 per kondisi.
- Prompt, anotasi, kamus sinonim, dan gate identitas 70% tidak diubah.
- Hasil dibandingkan per MARK dengan keluaran Gemma 4 E4B yang telah dibekukan.
- Tidak dilakukan relabeling setelah melihat keluaran model pembanding.

## Hasil

| Kondisi | Gemma 4 E4B | cx/gpt-5.5 | Perubahan | Gate 70% |
|---|---:|---:|---:|---:|
| SoM control | 15/36 (41,67%) | 20/36 (55,56%) | +5 MARK / +13,89 poin | Gagal |
| Depth-Guided ROI | 17/36 (47,22%) | 24/36 (66,67%) | +7 MARK / +19,44 poin | Gagal |

Pada SoM control terdapat 8 pasangan Gemma-salah/model-kuat-benar dan 3 pasangan Gemma-benar/model-kuat-salah. Pada Depth-Guided ROI terdapat 9 pasangan Gemma-salah/model-kuat-benar dan 2 pasangan Gemma-benar/model-kuat-salah.

Seluruh 24 respons mengembalikan tiga ID yang dapat dinormalisasi, tetapi 0/24 mematuhi JSON schema mentah yang diminta. Karena itu, kepatuhan schema mentah dicatat 0% dan normalisasi adapter dicatat terpisah; keduanya tidak boleh digabung menjadi klaim structured-output 100%.

## Keputusan

Model yang lebih kuat meningkatkan akurasi identitas secara deskriptif pada kedua kondisi. Namun kedua kondisi tetap gagal mencapai gate 70%, sehingga kelemahan Gemma bukan penjelasan yang cukup atas kegagalan V3. Representasi bounding-box MARK, granularitas anotasi HomeObjects-3K, dan ambiguitas objek di dalam region tetap menjadi pembatas.

Eksperimen ini juga tidak membuktikan manfaat depth karena SoM control dan Depth-Guided ROI memilih region yang berbeda serta dataset tidak menyediakan reference depth. Depth-Guided ROI tidak layak dinaikkan menjadi kontribusi utama dan detector tidak perlu dilatih.
