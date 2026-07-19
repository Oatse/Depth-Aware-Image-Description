# PROTOTYPE — Oracle-Box Depth-Guided ROI V3

## Pertanyaan

Apakah Gemma dapat melakukan grounding objek pada region oracle-box yang telah melewati QA geometri, dan apakah structured output menghilangkan kegagalan parsing yang mengganggu V2?

## Kondisi

1. `baseline`: gambar asli tanpa mark dan tanpa metadata depth.
2. `som_control`: tiga oracle-box terbesar yang tidak bertumpang tindih, tanpa informasi depth.
3. `depth_guided`: tiga oracle-box dengan median estimasi depth terendah, diurutkan relatif dekat ke jauh.

Metrik baseline dan marked-region tidak diperlakukan sebagai metrik yang identik. Baseline mengukur recall kelas target, sedangkan dua kondisi bertanda mengukur grounding per region.

## Batas Klaim

- HomeObjects-3K tidak menyediakan reference depth.
- Ranking depth berasal dari estimasi model, bukan jarak fisik terukur.
- Prototipe tidak membuktikan manfaat depth terhadap keselamatan atau navigasi.
- Detector tidak dilatih oleh prototipe ini.
- LLM judge tidak digunakan untuk menentukan identitas objek atau ground-truth depth.

## Menjalankan

Dari `Program`:

```powershell
python prototypes\depth_guided_roi_v3\run_v3.py --prepare-only
python prototypes\depth_guided_roi_v3\run_v3.py
```

Respons per gambar disimpan sebagai cache. Eksekusi dapat dilanjutkan tanpa mengulang respons yang telah selesai.
