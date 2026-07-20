# Arsitektur runtime IoT-assisted

```mermaid
sequenceDiagram
    participant HP as Browser HP
    participant API as FastAPI
    participant ESP as ESP32 HC-SR04
    participant L as LM Studio
    participant D as Depth Anything
    HP->>API: time-sync + capture metadata
    ESP->>API: serial sample buffer
    HP->>API: image + capture_id + normalized clock
    API->>API: match sensor evidence by backend time
    API->>L: one Gemma inference
    API->>D: one depth inference
    API->>API: render gemma_only / gemma_depth / iot_assisted
    API-->>HP: provenance + warnings + contribution
    API->>API: append versioned analysis_runs.jsonl
```

Sensor evidence adalah channel terpisah dari semantik Gemma. Dua sensor yang konflik tidak dirata-ratakan. Mode IoT hanya menambah referensi frontal pada capture kamera environment yang fresh; sistem tidak mengikat sensor ke objek bernama dan tidak menghasilkan navigasi aman.

Record runtime kanonik berada di `results/analysis_runs.jsonl`. `results/predictions.csv` adalah export kompatibilitas evaluator, bukan sumber kebenaran.
