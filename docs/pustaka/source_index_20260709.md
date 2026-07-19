# Source Index - Bride-Gap Research Basis - 2026-07-09

Indeks ini berisi sumber eksternal yang dapat digunakan sebagai dasar Bab 1, Bab 2, Bab 3, dan Bab 4. Fokus tahun: 2018-2026, sesuai batas 10 tahun terakhir untuk skripsi 2026. Pedoman Gunadarma tetap mensyaratkan minimum 20 sumber dan sekitar 70% artikel ilmiah.

## Core Sources

| No | Source | Year | Type | Local file | Use in thesis |
|---:|---|---:|---|---|---|
| 1 | World Health Organization, "Blindness and vision impairment" | 2026 | Official fact sheet | `2026-who-blindness-visual-impairment.html` | Bab 1, urgensi gangguan penglihatan |
| 2 | Gemma Team, "Gemma 3 Technical Report" | 2025 | Technical report | `2025-gemma-3-technical-report.pdf` | Bab 2/3, basis VLM lokal multimodal |
| 3 | Yang et al., "Depth Anything V2" | 2024 | NeurIPS paper | `2024-depth-anything-v2.pdf` | Bab 2/3, basis monocular depth estimation |
| 4 | Hugging Face, "Depth Anything V2 Metric Indoor Small model card" | 2024 | Official model card | `2024-depth-anything-v2-metric-indoor-small-model-card.html` | Bab 3, model depth indoor |
| 5 | Bhat et al., "ZoeDepth" | 2023 | Paper | `2023-zoedepth.pdf` | Bab 2, pembanding monocular metric depth |
| 6 | Chen et al., "SpatialVLM" | 2024 | CVPR paper | `2024-spatialvlm-cvpr.pdf` | Bab 2, VLM spatial reasoning |
| 7 | Cheng et al., "SpatialRGPT" | 2024 | NeurIPS paper | `2024-spatialrgpt.pdf`; `2024-spatialrgpt-grounded-spatial-reasoning.pdf` | Bab 2, depth/region-aware VLM |
| 8 | Liu, Emerson and Collier, "Visual Spatial Reasoning" | 2023 | TACL paper | `2023-visual-spatial-reasoning-vsr.pdf` | Bab 2, kelemahan VLM pada relasi spasial |
| 9 | Zhang et al., "Do Vision-Language Models Represent Space and How?" | 2024 | arXiv/ICLR paper | `2024-vlm-represent-space-comfort.pdf`; `2024-comfort-vlm-spatial-frame-reference.pdf` | Bab 2, ambiguity frame of reference |
| 10 | MERL, "AxisBench / SPINBench: What Can Go Wrong in VLMs' Spatial Reasoning?" | 2025 | Technical report | `2025-spinbench-axisbench-vlm-spatial-reasoning.pdf` | Bab 2, risiko spatial reasoning VLM |
| 11 | Gurari et al., "VizWiz Grand Challenge" | 2018 | CVPR paper | `2018-vizwiz-grand-challenge-blind-vqa.pdf` | Bab 2, dataset BLV dan kebutuhan nyata pengguna |
| 12 | Huh et al., "Long-Form Answers to Visual Questions from Blind and Low Vision People" | 2024 | COLM paper | `2024-vizwiz-lf-long-form-answers-blv.pdf` | Bab 2/4, hallucination dan abstention |
| 13 | Xiao et al., "EgoBlind" | 2025 | NeurIPS dataset paper | `2025-egoblind-egocentric-visual-assistance.pdf` | Bab 2, egocentric assistive visual QA |
| 14 | Wang et al., "Dense captioning and multidimensional evaluations for indoor robotic scenes" | 2023 | Frontiers paper | `2023-rgbd2cap-frontiers.pdf`; `2023-rgbd2cap-frontiers-dense-captioning.pdf` | Bab 2, RGB-D captioning dan evaluasi multidimensi |
| 15 | Valipoor, "Analysis and design framework for indoor scene understanding assistive solutions" | 2024 | Springer paper | `2024-indoor-scene-understanding-assistive-valipoor.pdf` | Bab 2, user-centered assistive indoor scene understanding |
| 16 | Delloul and Larabi, "Towards Real Time Egocentric Segment Captioning..." | 2023 | arXiv paper | `2023-egocentric-segment-captioning-blind-rgbd.pdf` | Bab 2, captioning posisi kiri/kanan/depan untuk BVI |
| 17 | Srinivasaiah et al., "Turn-by-Turn Indoor Navigation for the Visually Impaired" | 2024 | arXiv paper | `2024-turn-by-turn-indoor-navigation-visually-impaired.pdf` | Bab 2, indoor navigation dan multimodal guidance |
| 18 | Zheng, Maredia and Zahabi, "Scoping Literature Review of Navigation Apps for BVI Users" | 2022 | HFES paper | `2022-scoping-review-navigation-apps-bvi.pdf` | Bab 2, fitur aplikasi navigasi BVI |
| 19 | Yu and Saniie, "Visual Impairment Spatial Awareness System..." | 2025 | Journal article | PDF blocked; official page: https://www.mdpi.com/2313-433X/11/1/9 | Bab 2, sistem holistik object, depth, STT/TTS |
| 20 | Shahid et al., "Assistive Systems for Visually Impaired Persons" | 2024 | Review article | PDF blocked; official page: https://www.mdpi.com/1424-8220/24/11/3572 | Bab 2, review assistive navigation |
| 21 | Srivastava et al., "A comprehensive review of navigation systems for visually impaired individuals" | 2024 | Review article | `2024-heliyon-navigation-systems-review-pubmed.html` | Bab 2, klasifikasi navigation assistance |
| 22 | Xiao et al., "GuideDog" | 2026 | ACL paper | `2026-guidedog-real-world-blv-dataset.pdf` | Bab 2, dataset real-world BLV terbaru |
| 23 | "Sight Guide: A wearable assistive perception and navigation system" | 2025 | arXiv paper | `2025-sight-guide-wearable-assistive-navigation.pdf` | Bab 2, wearable perception and navigation |

## Suggested Thesis Use

### Bab 1

Use WHO and recent navigation review papers to frame the problem:

- visual impairment affects independence and daily activity;
- indoor environments are hard because GPS is unavailable and obstacles are dynamic;
- existing aids still have limitations in scene understanding and object localization.

### Bab 2

Use four clusters:

1. Assistive technology and BLV needs: WHO, VizWiz, VizWiz-LF, EgoBlind, GuideDog.
2. Indoor navigation and scene understanding: VISA, assistive systems review, Heliyon review, scoping review.
3. Depth estimation and RGB-D captioning: Depth Anything V2, Depth Anything model card, ZoeDepth, RGBD2Cap.
4. VLM spatial reasoning limits: SpatialVLM, SpatialRGPT, VSR, COMFORT, SPINBench.

### Bab 3

Use Depth Anything V2 and Gemma 3 technical report to justify model choices. Use RGBD2Cap and SpatialRGPT to justify why depth metadata is a valid signal for spatial description.

### Bab 4

Use VSR, COMFORT, SPINBench, VizWiz-LF, and SpatialRGPT to interpret why Prompt Fusion can fail and why Late Fusion can be more stable in a constrained local prototype.

## Harvard-style Candidate References

These entries still need final checking in Zotero/Mendeley before submission.

Chen, B. et al. (2024) 'SpatialVLM: Endowing Vision-Language Models with Spatial Reasoning Capabilities', CVPR 2024. Available at: https://arxiv.org/abs/2401.12168.

Cheng, A.C. et al. (2024) 'SpatialRGPT: Grounded Spatial Reasoning in Vision-Language Models', NeurIPS 2024. Available at: https://arxiv.org/abs/2406.01584.

Delloul, K. and Larabi, S. (2023) 'Towards Real Time Egocentric Segment Captioning for The Blind and Visually Impaired in RGB-D Theatre Images', arXiv preprint, arXiv:2308.13892. Available at: https://arxiv.org/abs/2308.13892.

Gemma Team (2025) 'Gemma 3 Technical Report', arXiv preprint, arXiv:2503.19786. Available at: https://arxiv.org/abs/2503.19786.

Gurari, D. et al. (2018) 'VizWiz Grand Challenge: Answering Visual Questions from Blind People', Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR). Available at: https://arxiv.org/abs/1802.08218.

Huh, M. et al. (2024) 'Long-Form Answers to Visual Questions from Blind and Low Vision People', COLM 2024. Available at: https://arxiv.org/abs/2408.06303.

Liu, F., Emerson, G. and Collier, N. (2023) 'Visual Spatial Reasoning', Transactions of the Association for Computational Linguistics, 11, pp. 635-651. doi: 10.1162/tacl_a_00566.

Srinivasaiah, S., Nekkanti, S.K. and Nedhunuri, R.R. (2024) 'Turn-by-Turn Indoor Navigation for the Visually Impaired', arXiv preprint, arXiv:2410.19954. Available at: https://arxiv.org/abs/2410.19954.

Wang, H. et al. (2023) 'Dense captioning and multidimensional evaluations for indoor robotic scenes', Frontiers in Neurorobotics, 17. doi: 10.3389/fnbot.2023.1280501.

World Health Organization (2026) 'Blindness and vision impairment'. Available at: https://www.who.int/news-room/fact-sheets/detail/blindness-and-visual-impairment (Accessed: 9 July 2026).

Yang, L. et al. (2024) 'Depth Anything V2', NeurIPS 2024. Available at: https://arxiv.org/abs/2406.09414.

Yu, X. and Saniie, J. (2025) 'Visual Impairment Spatial Awareness System for Indoor Navigation and Daily Activities', Journal of Imaging, 11(1), 9. doi: 10.3390/jimaging11010009.

Zhang, Z. et al. (2024) 'Do Vision-Language Models Represent Space and How? Evaluating Spatial Frame of Reference Under Ambiguities', arXiv preprint, arXiv:2410.17385. Available at: https://arxiv.org/abs/2410.17385.

