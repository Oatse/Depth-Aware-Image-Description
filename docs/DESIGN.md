# Depth-Aware Image Description Design System

## 1. Atmosphere & Identity

Antarmuka ini memakai gaya experiment setup form yang bersih: satu halaman putih penuh, title ringkas di kiri atas, dropzone gambar besar sebagai fokus utama, lalu controls analisis di bawahnya. Initial state harus terasa seperti form upload riset yang jelas, bukan prompt text/chat input dan bukan card putih di dalam card lain.

UI ini bukan aplikasi navigasi. Semua copy harus membingkai keluaran sebagai experimental output, depth-based observation, nearest region detected, atau more open area indication.

## 2. Color

### Palette

| Role | Token | Value | Usage |
|------|-------|-------|-------|
| Canvas | --canvas | #fbfaf8 | Background halaman penuh |
| Surface | --surface | #ffffff | Prompt box, cards, details |
| Surface/soft | --surface-soft | #f4f2ef | Hover, technical tiles |
| Dropzone | --dropzone | #fbfaf7 | Area upload berpola titik |
| Ink | --ink | #18151f | Teks utama |
| Ink/soft | --ink-soft | #595664 | Body sekunder |
| Ink/muted | --ink-muted | #8a8793 | Helper dan metadata |
| Line | --line | #e9e5df | Border halus |
| Line/strong | --line-strong | #d8d3ca | Border dropzone |
| Accent | --accent | #6f3cc3 | Action dan orb |
| Accent/dark | --accent-dark | #4a238d | Label aktif |
| Accent/soft | --accent-soft | #f1eafa | Icon chip |
| Panel/dark | --panel | #191622 | Final description dan depth insight |
| Error | --error | #a23a32 | Inline error |
| Status/ready | --status-ready | #4f8b63 | Dot dan label system online |
| Status/warning | --status-warning | #b9843a | Dot dan label system check |

### Rules

- Initial state dominan putih/off-white, bukan ilustrasi besar, dashboard padat, atau nested container.
- Accent ungu digunakan sangat sedikit: orb, tombol analyze, dan state aktif.
- Area upload harus tampak seperti dropzone media: dotted pattern, ikon media/plus, instruksi peletakan gambar, dan format file.
- Result boleh memakai panel gelap untuk hierarki, tetapi hanya setelah analisis berjalan.
- Detail teknis, raw JSON, dan depth map tetap collapsed secara default.

## 3. Typography

### Scale

| Level | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| Display | clamp(1.35rem, 3vw, 2.2rem) | 760 | 1.14 | Judul initial state |
| H2 | 1rem | 720 | 1.35 | Heading panel |
| Body/lg | clamp(1rem, 2vw, 1.25rem) | 500 | 1.62 | Final description |
| Body | 1rem | 450 | 1.62 | Text default |
| Body/sm | 0.82rem-0.88rem | 450 | 1.5 | Helper, disclaimer |
| Caption | 0.72rem | 760 | 1.4 | Label kecil, metric label |
| Mono | 0.82rem-0.88rem | 650 | 1.45 | Latency, JSON, region code |

### Font Stack

- Primary: "Plus Jakarta Sans", "Geist", "Segoe UI", system-ui, sans-serif.
- Mono: "JetBrains Mono", "SFMono-Regular", Consolas, monospace.

## 4. Spacing & Layout

### Layout Tokens

| Token | Value | Usage |
|-------|-------|-------|
| --radius-lg | 14px | Result dan panel besar |
| --radius-md | 10px | Cards dan accordion |
| --radius-sm | 7px | Prompt, controls |
| --shadow-soft | 0 18px 54px rgba(31, 28, 36, 0.07) | Result atau surface penting |

### Rules

- Page width: full white page, inner content max width 1168px.
- Desktop initial state: title, dropzone image, controls, floating system status pill, disclaimer.
- No sidebar. No large decorative background in the initial state.
- No outer canvas/card wrapping the full page.
- Mobile: full-width white canvas, single column, no horizontal scroll.

## 5. Components

### Minimal Header
- **Structure**: small abstract mark + console label.
- **Purpose**: identity only, not navigation.
- **Rule**: no sidebar, no dense nav.

- **Structure**: large dotted upload area, media/plus icon, browse copy, accepted image formats, mode select, camera button, analyze button, compare action.
- **States**: empty, drag-over, image selected, invalid file, loading disabled, camera preview.
- **Accessibility**: file input tied to label, visible focus, named buttons.
- **Interaction**: click opens native file picker; drag-and-drop accepts the first JPG, PNG, or WebP file and shows the same selected preview state as manual upload.
- **Rule**: must not read as a text input or chat prompt.

### System Status Pill
- **Structure**: small floating pill at top-right with a green or amber dot and short readiness summary.
- **Interaction**: click opens a compact popover with Backend, Gemma, and Depth readiness; outside click closes it.
- **Purpose**: keep operational checks available without adding visual noise inside the upload form.
- **Surface**: white background, subtle border, soft shadow only for the floating layer.

### Final Description Card
- **Structure**: label, concise final summary, small experimental caption.
- **Priority**: most dominant element after result appears.
- **Surface**: dark panel for contrast.
- **Rule**: summarises visual content, depth contribution, and guarded potential-obstacle information in 2-4 sentences; does not repeat the full comparison detail.

### Metric Card
- **Structure**: label + help dot + mono value + helper sentence.
- **Variants**: Mode, Depth Category, Area Terdekat, Latency.
- **Default**: appears only after analysis.
- **Helper rule**: helper sentence stays short and scannable; detailed explanation belongs in the help popover.
- **Terminology rule**: visible UI uses "area"; technical/debug surfaces may use "region".

### Depth Insight Panel
- **Structure**: technical facts list, area-relative-open note, obstacle interpretation.
- **Purpose**: explains how depth contributes to the result.
- **Rule**: UI-facing labels say "area"; raw region code appears only as technical evidence.

### Depth Map Grid Overlay
- **Structure**: depth map preview with a 3x3 overlay and highlighted nearest area.
- **Purpose**: makes area labels such as tengah-kiri and bawah-tengah inspectable by users.
- **Rule**: grid is explained as application post-processing over a continuous depth map, not the native output format of Depth Anything.

### Mode Comparison Table
- **Structure**: Aspek, Gemma Baseline, Depth-only, Late Fusion, Prompted, Kontribusi.
- **Purpose**: makes depth contribution analyzable for Bab 4 without implying Gemma is weak when depth metadata is not extracted.
- **Rule**: compare visual-spatial baseline, metadata depth availability, strategy, kategori kedalaman relatif, potensi halangan visual, area relatif lapang, and latency.
- **Copy rule**: for Gemma Baseline depth-specific fields, say "tidak diekstrak sebagai metadata depth" instead of generic "tidak tersedia".

### Help Popover
- **Structure**: small `?` button opens a compact contextual popover with a short title and one concise explanation.
- **Interaction**: visible on hover/focus and toggleable by click/tap; `Escape` or outside click closes it.
- **Purpose**: explain metric meaning without adding permanent text to the result cards.
- **Rule**: tooltip copy stays short and contextual; broader interpretation belongs in the result-reading guide.

### Result Reading Guide
- **Structure**: collapsed accordion titled "Cara membaca hasil ini" inside the result section.
- **Purpose**: explains each section by function, how the value is determined, and interpretation limits.
- **Rule**: closed by default; Technical Details and Raw JSON remain advanced/debug information.

### Accordion Detail
- **Items**: View Depth Map, Technical Details, Raw JSON.
- **Default**: collapsed.

## 6. Motion & Interaction

| Type | Duration | Easing | Usage |
|------|----------|--------|-------|
| Micro | 180ms | cubic-bezier(0.16, 1, 0.3, 1) | Button hover/press |
| Entry | 520-560ms | cubic-bezier(0.16, 1, 0.3, 1) | Hero/prompt/result reveal |

Rules:
- Animasi hanya menggunakan transform dan opacity.
- Loading state memakai progress line dan step text.
- Reduced motion mematikan animasi dekoratif.

## 7. Depth & Surface

Depth visual tidak ditampilkan sebagai dekorasi besar di initial state. Konsep depth muncul di hasil, metric, depth insight, dan accordion depth map setelah analisis. Ini menjaga layar awal tetap bersih dan mencegah kesan aplikasi navigasi nyata.
