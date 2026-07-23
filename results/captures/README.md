# Paket Evaluasi Dataset v2

Folder ini memuat satu paket evaluasi final:

- 18 citra sumber di `images/dataset_v2_clean/`;
- 18 record capture yang dirujuk `dataset_capture_ids_v2.json`;
- 36 run terpilih di `dataset_selected_analysis_runs_v2_fresh.jsonl`;
- hasil analisis, evaluasi blind, score lock, manifest, dan validation report terbaru.

`dataset_manifest_v2.json` mengunci input, sedangkan
`evaluation_manifest_v2_fresh.json` mengunci run dan artefak hasil. Paket ini tidak
menjadi target tulis endpoint runtime.

Capture setelah pembekuan disimpan terpisah:

```text
results/captures/incoming/images/capture_candidates/
results/captures/incoming/records/
```

Capture di area `incoming` bukan bagian dataset penelitian sampai memiliki protokol,
daftar capture, manifest, dan evaluasi baru.
