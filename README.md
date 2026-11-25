# AI-Content Generation: The Heritage Short

> **"The Scent of Roasted Coffee: A Mother's Sunday"**
> A 68-second generative short film exploring intergenerational family continuity through the Ethiopian coffee ceremony.

---

## 🚀 Quickstart: One-Command Pipeline Execution
From a clean clone, run the entire pipeline end-to-end:

```bash
# 1. Install dependencies (optional for mock run, recommended for production)
pip install -r requirements.txt

# 2. Run the entire film production pipeline
make film
```
*Outputs will be generated in `outputs/exports/`:*
* Horizontal Master: `outputs/exports/heritage_short_16x9.mp4`
* Vertical Master: `outputs/exports/heritage_short_9x16.mp4`
* Synchronized Subtitles: `outputs/exports/subtitles.srt`
* Complete Model Audit Log: `runs.jsonl`

---

## 📻 Generate Radio Cut Prototype (Phase 1 Deliverable)
```bash
make radio-cut
```
Exports narration synchronized over background acoustic score on a black screen to `outputs/exports/radio_cut.mp4` for rapid user testing.

---

## ⚡ Live Shot Regeneration Demo (Walkthrough Video)
To demonstrate content-addressable caching during your walkthrough recording:
```bash
# Regenerate only shot_03 (simulates changing one prompt without recomputing others)
python3 run_pipeline.py --stage shots --shot shot_03
```
Inspect `runs.jsonl` to prove only `shot_03` executed a model call while all other shots registered instant cache hits.

---

## 📂 Repository Structure
```
├── README.md                      # Pipeline execution instructions & project overview
├── storyboard.json                # Single source of truth: shots, durations, prompts, cues
├── schema/
│   └── storyboard.schema.json     # JSON Schema enforcing pipeline contract
├── pipeline/
│   ├── common.py                  # SHA-256 caching, runs.jsonl logging, retry backoff
│   ├── stage1_validate.py         # Storyboard schema and timing validation
│   ├── stage2_narration.py        # Gemini 3.8 Flash TTS generation
│   ├── stage3_keyframes.py        # FLUX.1 Schnell keyframe generation via Cloudflare
│   ├── stage4_shots.py            # Wan 2.2 / Ken Burns camera motion animation
│   ├── stage5_music.py            # ACE-Step 1.5 original acoustic score auditioning
│   └── stage6_assemble.py         # FFmpeg ducking, loudnorm, subtitles, dual export
├── run_pipeline.py                # Unified CLI orchestrator
├── Makefile                       # Developer shortcuts (make film, make radio-cut, etc.)
├── DESIGN.md                      # Audience, intent, 2 user tests, shot justifications
├── ARCHITECTURE.md                # System boundaries, contracts, caching, error recovery
├── EXPERIMENTS.md                 # 10 logged experiments (hypothesis -> change -> result)
├── FAILURES.md                    # Blocker journal: quota, VRAM, phonetics, ducking
├── COSTS.md                       # Measured latency, GPU minutes, zero-cost vs commercial
├── ETHICS.md                      # Informed consent record, model licenses, AI disclosure
├── requirements.txt               # Python package dependencies
├── .env.example                   # API key configuration template
└── outputs/                       # Generated media assets and execution cache
```

---

## 🔑 Environment Setup (Optional for Cloud APIs)
Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```
* **Gemini API:** Free key from [Google AI Studio](https://aistudio.google.com/)
* **Cloudflare Workers AI:** Account ID & Token from [Cloudflare Dashboard](https://dash.cloudflare.com/)
* **Kaggle:** Phone-verified account for Wan 2.2 GPU batching (30 hrs/week free).
*(Note: If API keys are omitted, the pipeline runs gracefully using robust built-in procedural and audio synthesizers).*
