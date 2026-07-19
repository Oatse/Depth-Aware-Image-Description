# Manifest Artefak Evaluasi Aktif 2026-07-14

Manifest ini mengunci artefak yang dipakai setelah koreksi evaluator dan implementasi fusi regional berbatas bukti. Seluruh hash memakai SHA-256.

| Artefak | Baris data | SHA-256 |
|---|---:|---|
| `results/final_predictions_active_20260714.csv` | 132 (44 citra x 3 mode) | `02EDF466A0195D2368A7332B2FD8ACA7497EA78D415E8F1FF7D2E85C913FA0BA` |
| `results/final_evaluation_strict_20260714.csv` | 9 (3 mode x keseluruhan/2 subgroup) | `A8B0627A77949B5FD81CED35D2B5E3BCA4DF7E9D6CE7065C43183272A0C03A4E` |
| `results/llm_judge_9router_image_full_20260714.csv` | 132 (44 citra x 3 mode) | `9DF17C471FB4DA70EAC9E5549231DBA6282D2E5607861F6EECC7803DA56B742B` |
| `results/llm_judge_9router_image_summary_20260714.csv` | 3 mode | `0D1F5FA7ED2C6660C71FDDD5BB2724283B593E1E63D7D0C1F58EA104A0164187` |
| `results/llm_judge_9router_image_paired_comparison_20260714.csv` | 10 perbandingan metrik | `A210FB69660BE03E2353D44D04894DF31FA04D627B72844FFCE4FE39272F43E1` |
| `results/controlled_fusion_predictions_20260714.csv` | 88 (44 citra x 2 kebijakan) | `65752388BB8BDB3408EFE4EC1C0434AFA6BDF11245B6E6FE0569F990C7F200D8` |
| `results/controlled_fusion_evaluation_20260714.csv` | 6 (2 kebijakan x keseluruhan/2 subgroup) | `0A170C8B281E150CDCCD0B82773374344D56F833E550A010F19FCDEC4427744D` |
| `results/llm_judge_9router_controlled_legacy_20260714.csv` | 44 | `E01F31D5D4DD08F7B177B4128A5C52E8A576CEA80DB236C7B374750BA9516E76` |
| `results/llm_judge_9router_controlled_constrained_20260714.csv` | 44 | `24884418D721BE2C788719910D6572080F8B3EBF92B003A1AC927C0245C293A9` |
| `results/llm_judge_9router_controlled_pairwise_20260714.csv` | 5 metrik pasangan | `7D02B696FB3614E92DC2102E96ED22483F27CDDDBDF6375785484849378FAE47` |
| `results/llm_judge_9router_constrained_vs_baseline_paired_20260715.csv` | 5 metrik pasangan | `9A9CC0CB9CE818889669EE66882E07040B6C57005A6EBDC4AD3DD813DD71FEFB` |

Mode aktif: `gemma_only`, `depth_only`, dan `gemma_depth`. Kebijakan aktif `gemma_depth` adalah `evidence_constrained`; `legacy_verbose` hanya kontrol. Setiap baris judge memakai tiga pengulangan, model/rute `cx/gpt-5.5`, dan rubric `spatial-description-judge-v2-image-aware`. Label rute tidak dianggap sebagai snapshot upstream immutable.

Koreksi 15 Juli 2026: `final_predictions_active_20260714.csv` adalah sumber komponen historis yang masih memuat teks `gemma_depth` verbose dan tidak memiliki kolom provenance kebijakan. Evaluasi terstruktur file tersebut tetap dipertahankan sebagai jejak run, tetapi perbandingan kualitas teks runtime aktif terhadap baseline harus memakai `llm_judge_9router_image_gemma_only_20260714.csv` dan `llm_judge_9router_controlled_constrained_20260714.csv`, yang diringkas secara berpasangan di artefak 15 Juli. Kenaikan object/position dari dua pemanggilan Gemma terpisah tidak diatribusikan kepada fusion.

`results/final_evaluation_metrics_20260714.csv` memakai evaluator lama dan bukan lagi artefak metrik aktif karena pencocokan posisi dari `final_description` menyebabkan kebocoran. File tidak dihapus agar jejak koreksi tetap dapat diaudit.

`results/retired_prompted_decision_evidence_20260714.csv` bukan artefak hasil aktif. File tersebut hanya menyimpan bukti per-citra yang mendasari penghapusan Depth-to-Spatial Prompting.
