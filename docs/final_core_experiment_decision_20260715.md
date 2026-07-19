# Keputusan Final Eksperimen Inti Bride-Gap

Tanggal keputusan: 15 Juli 2026.

## Putusan

Eksperimen final memakai tiga mode aktif pada 44 citra yang sama:

1. `gemma_only` sebagai baseline deskripsi visual dari citra;
2. `depth_only` sebagai ablasi komponen depth, bukan model deskripsi pesaing;
3. `gemma_depth` sebagai metode utama evidence-constrained regional late fusion.

Perbandingan utama adalah `gemma_only` versus `gemma_depth`. `depth_only` hanya menjawab seberapa baik dan seberapa mahal komponen depth menghasilkan kategori spasial terstruktur. Depth-to-Spatial Prompting, adaptive banding, serta SoM/Depth-Guided ROI tidak menjadi fitur atau pembanding final. Ketiganya disimpan sebagai jejak keputusan negatif karena tidak memenuhi bukti manfaat pada pengujian masing-masing.

Proyek tidak mengklaim novelty algoritmik, navigasi aman, jarak absolut, object-depth grounding, generalisasi global, human ground truth, atau inter-annotator agreement. Kontribusi yang dapat dipertahankan adalah implementasi serta evaluasi lokal pipeline deskripsi visual-spasial indoor dengan kontrak bukti dan provenance yang eksplisit.

## Integritas Artefak

- Dataset: 44 baris anotasi unik dan 44 file citra dengan nama yang selaras.
- Prediksi historis: `final_predictions_active_20260714.csv` memuat 132 baris, tepat 44 citra x 3 mode, tanpa pasangan duplikat, mock, atau error. Namun, teks `gemma_depth` di file ini masih berasal dari kebijakan verbose lama dan belum memiliki field `fusion_policy`; file tersebut tidak boleh disebut keluaran final runtime evidence-constrained.
- Evaluasi ketat: 9 baris dan dapat dihitung ulang byte-for-byte dari prediksi aktif; SHA-256 hasil ulang sama dengan manifest, yaitu `A8B0627A77949B5FD81CED35D2B5E3BCA4DF7E9D6CE7065C43183272A0C03A4E`.
- Preflight `depth_only` pada dataset final lulus dengan 44 citra, 44 anotasi, dan status model depth `ready`.
- Daftar hash lengkap berada di `docs/evaluation_artifact_manifest_20260714.md`.

## Hasil yang Boleh Dinyatakan

### Evaluator terstruktur

| Mode | Object accuracy | Position accuracy | Joint accuracy | Distance accuracy | Obstacle F1 | Rerata latensi |
|---|---:|---:|---:|---:|---:|---:|
| `gemma_only` | 29,55% | 29,55% | 9,09% | N/A | N/A | 10.569 ms |
| `depth_only` | N/A | N/A | N/A | 68,18% | 86,79% | 1.638 ms |
| `gemma_depth` historis, inferensi terpisah | 34,09% | 31,82% | 11,36% | 68,18% | 86,79% | 11.795 ms |
| `gemma_depth` evidence-constrained, kontrol cabang sama | 29,55% | 29,55% | 9,09% | 68,18% | 86,79% | 11.280 ms |

Kenaikan object/position pada baris historis tidak boleh diatribusikan kepada fusion karena `gemma_only` dan `gemma_depth` berasal dari pemanggilan Gemma yang berbeda. Pada kontrol yang memakai cabang Gemma identik, object, position, dan joint accuracy juga identik. Fusion tidak mengenali objek dan tidak mengubah field terstruktur tersebut.

Metrik depth menunjukkan bahwa komponen depth membawa metadata yang memang tidak diekstrak baseline. Angka itu tidak boleh dipakai untuk mengatakan `gemma_depth` mengalahkan `gemma_only`, karena metrik depth tidak berlaku pada baseline.

### LLM-as-a-Judge image-aware

Judge `cx/gpt-5.5`, rubric `spatial-description-judge-v2-image-aware`, tiga pengulangan per citra, menghasilkan perbandingan yang sah antara baseline dan evidence-constrained fusion dengan cabang Gemma yang sama:

| Mode | Overall mean | Selisih berpasangan terhadap `gemma_only` | Bootstrap 95% snapshot interval |
|---|---:|---:|---:|
| `gemma_only` | 3,8636 | 0 | N/A |
| `gemma_depth` evidence-constrained | 3,9015 | +0,0379 | [-0,1212; 0,1970] |

`gemma_depth` evidence-constrained tidak terbukti lebih baik daripada baseline pada kualitas keseluruhan karena interval overall memotong nol. Clarity justru turun -0,2121 dengan interval [-0,3333; -0,0985]. Semantic correctness, spatial accuracy, dan groundedness juga tidak menunjukkan selisih yang intervalnya tidak memotong nol.

Skor overall 3,7348 dan selisih -0,1288 pada `llm_judge_9router_image_summary_20260714.csv` berlaku untuk teks `gemma_depth` verbose historis di `final_predictions_active_20260714.csv`, bukan kebijakan runtime aktif. Artefak baru `llm_judge_9router_constrained_vs_baseline_paired_20260715.csv` mengunci koreksi pasangan ini.

Kontrol pasangan terhadap kebijakan fusion lama memberi hasil berbeda: evidence-constrained fusion lebih baik daripada `legacy_verbose` pada groundedness, clarity, dan overall, dengan interval snapshot yang tidak memotong nol. Ini hanya membuktikan bahwa kebijakan aktif lebih baik daripada versi fusion lama ketika input cabangnya identik; bukan bahwa fusion aktif mengalahkan Gemma baseline.

## Konsekuensi terhadap Argumen Skripsi

Pertanyaan yang dapat dijawab adalah: **bagaimana penambahan metadata depth regional mengubah keluaran, kelengkapan metadata spasial, latensi, dan failure case deskripsi visual indoor dibanding baseline citra saja?**

Jawabannya berdasarkan data saat ini: depth menambahkan keluaran spasial terstruktur dan dapat dievaluasi pada kategori relatif, tetapi manfaat kualitas bahasa keseluruhan belum terbukti dan datang dengan kenaikan latensi komponen sekitar 0,71 detik pada kontrol cabang sama. Karena itu penelitian harus dilaporkan sebagai evaluasi trade-off dan failure analysis, bukan demonstrasi metode yang unggul.

`depth_only` tetap penting sebagai ablasi karena memisahkan performa dan biaya komponen depth dari VLM. Ia tidak boleh ditempatkan sebagai pesaing kualitas deskripsi. Dengan desain ini, pembanding tidak kembali menjadi satu jenis analisis saja: baseline menguji citra-only, metode utama menguji citra plus metadata depth melalui late fusion, dan ablasi mengisolasi cabang depth.

## Metode yang Dikeluarkan

- **Depth-to-Spatial Prompting:** overall judge 3,5682, lebih rendah daripada baseline 3,8636, serta latensi 14.274 ms. Jalur runtime dan UI telah dihapus; bukti keputusan tetap disimpan.
- **Adaptive depth banding + variance filter:** obstacle recall turun 18,52 poin dan F1 turun 8,53 poin dibanding `grid_p10`.
- **SoM/Depth-Guided ROI:** prototipe dan uji model lebih kuat tetap tidak melewati ambang kelayakan yang ditetapkan; tidak ada dasar untuk melatih detector dalam batas waktu penelitian ini.
- **ROUGE-L:** tidak digunakan karena tidak tersedia reference description independen.

## Status Anotasi dan Evaluasi Manusia

`dataset/final_annotations.csv` adalah anotasi terstruktur untuk snapshot penelitian. Pemeriksaan manual peneliti dapat disebut revalidasi peneliti, tetapi tidak boleh disebut human ground truth, expert annotation, atau inter-annotator agreement karena belum ada protokol dua anotator independen dan pengukuran agreement. LLM judge tetap bukti sekunder yang provider-dependent meskipun melihat citra asli.

## Keputusan Eksekusi Lima Hari

Tidak dilakukan inference final ulang, pergantian model, pelatihan detector, atau penambahan dataset. Artefak aktif lengkap, hash-nya konsisten, dan evaluator dapat direproduksi. Sisa waktu dialokasikan untuk penulisan metode, hasil, batasan, failure case, dan demonstrasi software berdasarkan artefak terkunci tersebut.
