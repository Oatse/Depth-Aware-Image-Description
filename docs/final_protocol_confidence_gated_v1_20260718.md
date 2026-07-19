# Candidate Final Protocol: Controlled VLM Validation for Confidence-Gated Spatial Description

Protocol ID: `cgsp-final-candidate-vlm-20260718-v1`  
Status: **frozen before VLM inference**  
Source depth run: `cgsp-calibration-holdout-20260718-v1`

## Research Question

Pada held-out indoor images, apakah confidence-gated regional depth claim dapat ditambahkan ke deskripsi visual VLM dengan kontrak output dan runtime yang stabil, sementara claim yang diterbitkan tetap diukur terhadap ground-truth depth regional?

Penelitian tidak menguji efektivitas caption secara umum, tidak menggunakan UAT, dan tidak mengklaim object-specific distance atau navigation safety.

## Data dan Split

- Dua puluh RGB images held-out yang sudah dipisahkan sebelum VLM prompting.
- Indeks: 15, 33, 51, 69, 87, 105, 123, 141, 159, 177, 195, 213, 231, 249, 267, 285, 303, 321, 339, 357.
- Ground truth regional depth diambil dari keputusan held-out yang dibekukan sebelum run VLM.
- Konfigurasi gate tidak diubah lagi:

```json
{
  "minimum_nearest_region_agreement": 1.0,
  "minimum_distance_category_agreement": 0.6,
  "maximum_relative_mad": 0.05
}
```

## Controlled Conditions

Setiap image menerima tepat satu panggilan VLM. Output mentah yang sama dipakai untuk dua kondisi:

1. `baseline_visual_only`: deskripsi visual tanpa depth claim;
2. `gated_regional_depth_claim`: deskripsi yang sama, ditambah satu regional depth claim hanya jika gate menerima sampel.

Dengan demikian, perbedaan antar-kondisi tidak berasal dari pemanggilan VLM kedua. Repeat dilakukan pada lima image dengan dua panggilan per image untuk mengukur variasi runtime.

## Frozen VLM Configuration

- Endpoint: `http://localhost:1234/v1/chat/completions`.
- Model: `google/gemma-4-e4b`.
- Temperature: 0,1 sesuai client proyek.
- Max tokens: 900.
- Prompt: `DEFAULT_GEMMA_PROMPT` dari `models/gemma_client.py`.
- Parser dan sanitizer: fungsi yang sudah ada di `models/gemma_client.py`.
- Tidak ada prompt tuning setelah melihat held-out output.

## Metrik

Runtime:

- VLM success rate;
- structured JSON rate;
- mean, p50, dan p95 latency;
- repeat variation rate;
- same-VLM-branch rate.

Spatial claim:

- gated depth-claim coverage;
- regional joint accuracy pada claim yang diterbitkan;
- unsupported gated depth claim rate;
- jumlah claim yang ditambahkan dibanding baseline.

## Feasibility Gate

Run dianggap lolos secara mekanis jika:

- VLM success rate 100%;
- structured JSON rate minimal 90%;
- baseline dan gated memakai output VLM yang sama 100%;
- repeat variation rate maksimal 60% pada lima image.

Lulus gate hanya berarti pipeline dapat diuji secara reproducible. Itu bukan bukti kualitas caption atau superiority metode.

## Batas Klaim

- Tidak ada klaim human ground truth untuk bahasa.
- Tidak ada klaim caption quality tanpa reference captions independen.
- Tidak ada klaim keselamatan, navigasi, pengguna tunanetra, atau real-time umum.
- Regional depth claim tidak boleh diubah menjadi jarak objek tanpa object-depth correspondence.
- Jika spatial claim accuracy tetap rendah, hasil harus dilaporkan sebagai failure analysis meskipun runtime gate lulus.

