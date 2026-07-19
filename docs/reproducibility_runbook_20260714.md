# Reproducibility Runbook 2026-07-14

Dokumen ini memisahkan verifikasi software, eksperimen final, evaluasi image-aware berbasis API, dan pemeriksaan manual. Jalankan dari root `Program/`.

## Environment

Environment verifikasi memakai Python 3.13.3. Untuk versi dependency langsung yang sama:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
```

Model lokal yang diverifikasi:

- `depth_anything_v2_metric_indoor_small.onnx`: SHA-256 `2A29BDF0F7C41776D83B17411DEAF5EA3B4EE15FF3553298677828D4AF02BD48`
- `depth_anything_v2_metric_indoor_small.onnx.data`: SHA-256 `600C51DA3F77BA331224D32C0ACD238E82AE11A70A2C0741AE5D1B7F012FA0F6`

Gunakan `Get-FileHash -Algorithm SHA256 <path>` untuk verifikasi ulang. Catat model Gemma aktual dari LM Studio karena nama runtime `google/gemma-4-e4b` berbeda dari label artefak historis `gemma_e2b`.

## Gate 1: Software

```powershell
python -m pytest -q
```

Semua test harus lulus. Test mock hanya memverifikasi kontrak software; hasil mock tidak boleh dipakai pada Bab 4.

## Gate 2: Preflight Final 44

```powershell
python scripts\run_batch_evaluation.py `
  --images-dir dataset\final_images `
  --annotations dataset\final_annotations.csv `
  --predictions results\final_predictions_20260714.csv `
  --output results\final_evaluation_20260714.csv `
  --preflight-only
```

Pastikan LM Studio siap, mock mati, 44 citra cocok dengan 44 anotasi, dan checkpoint depth ditemukan. Hapus `--preflight-only` hanya ketika akan menjalankan inferensi final baru. Jangan menimpa CSV final lama.

## Gate 3: Evaluasi Ulang Artefak Prediksi

```powershell
python scripts\run_evaluation.py `
  --annotations dataset\final_annotations.csv `
  --predictions results\final_predictions_active_20260714.csv `
  --output results\final_evaluation_strict_20260714.csv
```

Output evaluator aktif hanya memakai field terstruktur untuk object/position, melaporkan object-position joint accuracy, dan menulis metrik semantik `depth_only` sebagai N/A. Output tidak memuat skor kualitas teks buatan atau metrik leksikal karena anotasi final belum memiliki `reference_description` independen.

## Gate 4: Kontrol Kebijakan Fusion

Bangun dua kandidat teks dari cabang Gemma dan depth yang sama. Script ini tidak memanggil Gemma ulang; depth dihitung satu kali per citra lalu dipakai bersama oleh kedua kebijakan.

```powershell
python scripts\build_controlled_fusion_predictions.py `
  --images-dir dataset\final_images `
  --predictions results\final_predictions_active_20260714.csv `
  --output results\controlled_fusion_predictions_20260714.csv

python scripts\run_evaluation.py `
  --annotations dataset\final_annotations.csv `
  --predictions results\controlled_fusion_predictions_20260714.csv `
  --output results\controlled_fusion_evaluation_20260714.csv
```

## Gate 5: LLM-as-a-Judge Image-Aware

```powershell
$env:NINEROUTER_API_KEY="<secret>"
python scripts\run_llm_judge.py `
  --annotations dataset\final_annotations.csv `
  --predictions results\final_predictions_active_20260714.csv `
  --images-dir dataset\final_images `
  --output results\llm_judge_9router_image_full_20260714.csv `
  --cache-dir results\llm_judge_9router_image_cache `
  --modes gemma_only depth_only gemma_depth `
  --model cx/gpt-5.5 `
  --base-url http://127.0.0.1:20128/v1 `
  --api-key-env NINEROUTER_API_KEY `
  --repeats 3
```

Untuk kontrol kebijakan, jalankan perintah tersebut dua kali dengan `--predictions results\controlled_fusion_predictions_20260714.csv`, output terpisah, serta `--modes gemma_depth_legacy_controlled` dan `--modes gemma_depth_constrained_controlled`. Setelah kedua file memuat tepat 44 citra, bandingkan secara berpasangan:

```powershell
python scripts\compare_controlled_judge.py `
  --legacy results\llm_judge_9router_controlled_legacy_20260714.csv `
  --constrained results\llm_judge_9router_controlled_constrained_20260714.csv `
  --output results\llm_judge_9router_controlled_pairwise_20260714.csv
```

Script judge mengirim citra sebagai bukti utama, anotasi sebagai pembanding sekunder, serta kandidat deskripsi tanpa label metode di dalam prompt. Output memakai JSON schema, rubric version, cache per repeat, dan simpangan baku. Script perbandingan memakai pasangan citra yang identik dan menolak set citra yang berbeda. Interval bootstrap hanya deskriptif untuk snapshot 44 citra, bukan confidence interval populasi. 9router harus aktif di endpoint lokal. Jangan commit key atau mengklaim skor sebelum output CSV lengkap tersedia.

Sebelum run, verifikasi izin pemrosesan citra dan konfigurasi upstream 9router. Alamat localhost hanya menunjukkan lokasi router; ia tidak membuktikan citra tetap berada di mesin. Simpan metadata resolusi upstream jika tersedia. Jika tidak tersedia, laporkan `cx/gpt-5.5` sebagai label rute, bukan snapshot model immutable.

## Gate 6: Manual Surface Check

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Periksa `/health`, upload satu citra melalui UI, pastikan `POST /analysis-jobs` menghasilkan HTTP 202, status berubah `queued/running` menjadi `completed`, dan hasil tampil. Antrean bersifat single-process non-durable; restart server menghapus job.

## Informasi yang Harus Disimpan Bersama Hasil Bab 4

- tanggal dan waktu run;
- commit hash atau status dirty worktree;
- versi Python dan dependency;
- hash model depth;
- nama model Gemma yang benar-benar loaded;
- path dataset/anotasi/prediksi/evaluasi;
- hash atau manifest citra yang diterima judge;
- model, base URL, rubric version, dan cache directory judge;
- status mock;
- kegagalan per image-mode, bukan hanya rata-rata akhir;
- biaya dan repeat count jika LLM judge dijalankan.
