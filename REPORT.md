# The Forty Springs of Arba Minch (የአርባ ምንጭ 40 ምንጮች)
## Final Project Report — AI-Content Generation Challenge
**Author:** Mehret  
**Date:** November 2026  
**Project Repository:** `/Users/mehret/Desktop/heritage-short`  
**Master Exports:** 
* 16:9 Cinema Master: `outputs/exports/heritage_short_16x9.mp4` (1280×720, 72.5s, -14 LUFS, 48kHz Stereo AAC)
* 9:16 Vertical Mobile Master: `outputs/exports/heritage_short_9x16.mp4` (720×1280, 72.5s, Full-Bleed Native Framing)

---

## 1. Executive Summary & Creative Vision

### 1.1 The Narrative Concept
*The Forty Springs of Arba Minch* is a 72.5-second generative short film exploring memory, brotherhood, and natural heritage. It centers on an Ethiopian software developer working late into the night behind a glowing monitor in a concrete office. Exhausted and isolated by modern professional routines, his sensory memory is triggered by a glass of water on his desk.

The narrative shifts dynamically into an evocative flashback: Arba Minch, Southern Ethiopia. Under the ancient groundwater forest canopy nestled between Lake Abaya and Lake Chamo, four barefoot boys—the narrator, his younger brother **Mikiyas**, and their inseparable neighborhood companions **Mihretab** and **Surafel**—sneak past their mothers' Sunday morning watch. They sprint through sun-dappled acacia forests to dive into the bubbling, crystal-clear sanctuary of the forty natural springs (*Arba Minch*). The memory restores the narrator's emotional equilibrium, returning him to his desk with a peaceful, anchored smile.

```mermaid
flowchart LR
    A["Present: Late-Night Desk<br/>(Visual Anchor)"] --> B["The Awakening<br/>(Arba Minch Canopy)"]
    B --> C["The Mischief<br/>(Conspiracy by Gate)"]
    C --> D["The Escape<br/>(Running Barefoot)"]
    D --> E["The Sacred Springs<br/>(Bubbling Water)"]
    E --> F["The Joy & Bond<br/>(Swimming & Laughter)"]
    F --> G["The Sunset Walk<br/>(Silhouettes)"]
    G --> H["Present: Grounded Smile<br/>(Memory as Sanctuary)"]
```

### 1.2 Creative Motivation
The film reflects a real personal experience shared across the modern diaspora and urban tech workers: the longing for childhood innocence, untamed nature, and the deep solidarity of shared heritage. The production serves as an intentional tribute to living family and childhood friends while setting a high technical benchmark for zero-cost, code-orchestrated generative filmmaking.

---

## 2. System Architecture & Technical Workflow

The entire film production—from schema validation to audio ducking and dual aspect ratio exports—is orchestrated deterministically through code via `run_pipeline.py`.

```mermaid
flowchart TD
    subgraph Config ["1. Schema & Storyboard Contract"]
        SB["storyboard.json"] -->|Validated by| S1["pipeline/stage1_validate.py<br/>schema/storyboard.schema.json"]
    end

    subgraph Generation ["2. Generative Stage Execution"]
        S1 --> S2["pipeline/stage2_narration.py<br/>Gemini 3.8 Flash TTS (Amharic)"]
        S1 --> S3["pipeline/stage3_keyframes.py<br/>Cloudflare FLUX.1 Schnell"]
        S3 --> S4["pipeline/stage4_shots.py<br/>Wan 2.2 I2V / Ken Burns Pan-Zoom"]
        S1 --> S5["pipeline/stage5_music.py<br/>ACE-Step 1.5 Polyphonic Score"]
    end

    subgraph Caching ["3. Deterministic Caching Engine"]
        CACHE["pipeline/common.py<br/>Content-Addressable SHA-256"]
        S2 -.-> CACHE
        S3 -.-> CACHE
        S4 -.-> CACHE
        S5 -.-> CACHE
        CACHE --> LOG["runs.jsonl (Audit Trail)"]
    end

    subgraph Post ["4. Assembly & Audio Mastering"]
        S2 --> S6["pipeline/stage6_assemble.py<br/>FFmpeg 6.0 Audio Compositor"]
        S4 --> S6
        S5 --> S6
        S6 --> DUCK["Dynamic Sidechain Ducking<br/>(attack=300ms, release=1500ms)"]
        DUCK --> NORM["EBU R128 Loudness Normalization<br/>(-14 LUFS, -1.0 dB True Peak, 48kHz Stereo AAC)"]
        NORM --> SUB["Subtitle Burn-in & mov_text Encoding<br/>(Amharic & English synced to TTS timestamps)"]
        SUB --> CARD["Automated 3s 'Made with AI' End Card"]
    end

    subgraph Deliverables ["5. Final Multi-Aspect Exports"]
        CARD --> EXP1["outputs/exports/heritage_short_16x9.mp4<br/>(1280x720 Cinema Master)"]
        CARD --> EXP2["outputs/exports/heritage_short_9x16.mp4<br/>(720x1280 Mobile Vertical Master)"]
    end
```

---

## 3. Detailed Technical Implementation

### 3.1 Contract-Driven Schema Architecture (ADR 08)
To prevent prompt drift and guarantee repeatability across runs, `schema/storyboard.schema.json` strictly governs `storyboard.json`. The schema enforces:
1. **Shot-by-Shot Timing & Purpose:** Exact `duration_seconds` and mandatory `reason` fields justifying every dramatic beat.
2. **Character DNA Enforcement:** A top-level `"characters"` dictionary locking physical anchors across all generated shots:
   - *Mehret (Narrator):* 28yo Ethiopian male, thoughtful warm gaze, subtle dark beard, glasses, navy charcoal crewneck.
   - *Young Mehret:* 10yo barefoot Ethiopian boy, curious dark eyes, faded yellow cotton tee.
   - *Mikiyas:* 8yo younger brother, bright radiant smile, athletic build, green cotton shirt.
   - *Mihretab:* 10yo childhood friend, charismatic wide grin, buzzed curly hair, red striped t-shirt.
   - *Surafel:* 11yo adventurous friend, slender runner's build, blue pocket t-shirt.

### 3.2 Narration & Phonetic Gemination (Gemini 3.8 Flash TTS)
* **Model:** Gemini 3.8 Flash TTS preview endpoint (`en-US-Standard` / Amharic multilingual engine).
* **Voice Profile:** `Charon` baritone voice tuned for emotional warmth and reflective pacing.
* **The Amharic Gemination Challenge:** Amharic Ge'ez script does not explicitly write consonant gemination (*ጥብቅና ላልት*). Initial TTS passes mispronounced 19 key vocabulary words (e.g., `ጠረጴዛዬ`, `የምድር`, `ተደብቀን`, `ቀልጦ ይጠፋል`). We solved this via strict prompt conditioning and phonetic spacing directives, resulting in authentic native inflection.

### 3.3 Visual Keyframe Generation & Ethnic Steering (FLUX.1 Schnell)
* **Model:** FLUX.1 Schnell 4-step distilled latent diffusion via Cloudflare Workers AI.
* **Ethnic Steering:** Standard AI diffusion models exhibit strong bias toward Western or generic South Asian facial structures when prompted for "boys". Through rigorous parameter tuning (Experiment 12), we injected explicit East African Habesha anthropomorphic keywords (*"authentic Ethiopian Habesha boys, warm caramel and dark umber skin, natural short curly afro hair, highland Horn of Africa facial structure"*), completely eliminating drift across Shots 03 and 07.
* **Character Consistency Sheet:** Built a master 2×3 character reference grid (`references/boys_arba_minch_sheet.png`) anchoring facial identity across all subsequent scenes.

### 3.4 Motion Synthesis: Wan 2.2 I2V & Decoupled Drop-In Engine (ADR 09)
* **Architecture:** Implemented an asynchronous drop-in folder architecture (`outputs/wan_drops/`).
* **Wan 2.2 Execution:** Designed a standalone Jupyter notebook (`notebooks/wan2_kaggle_pipeline.ipynb`) for Kaggle 2× T4 GPU free tier.
* **Procedural Fallback:** When external GPU resources are unavailable, the local pipeline immediately executes a high-fidelity Ken Burns pan-and-zoom engine using FFmpeg, animating all 9 shots in both 16:9 and 9:16 without blocking execution.

### 3.5 Original Score Composition & Candidate Selection (ACE-Step 1.5)
Three score candidates were generated using ACE-Step 1.5 and evaluated against the storyboard's dramatic arc:
* **Candidate 1 (Seed 40401) — APPROVED:** Sacred Southern Ethiopian polyphonic humming with resonant open fifths and organic water-drop acoustics. Perfectly matches the mist and spiritual sanctity of Arba Minch.
* **Candidate 2 (Seed 40502):** Dynamic acoustic krar and masenqo rhythm. Energetic but competed with the narrator's voice.
* **Candidate 3 (Seed 40603):** Ambient electronic pads with rain stick. Modern but lacked indigenous Ethiopian emotional grounding.

### 3.6 Mastering, Ducking & Universal Audio Playback (Blocker 11 Fix)
* **Sidechain Compression:** FFmpeg `sidechaincompress` dynamically ducks the score by **-14 dB** during voice narration with a smooth **300ms attack** and **1500ms release**, eliminating harsh volume stepping.
* **Loudness Compliance:** Audio is normalized to **-14 LUFS (EBU R128)** with a **-1.0 dB true peak** ceiling.
* **The QuickTime 96kHz Codec Blocker:** FFmpeg's `loudnorm` filter previously upsampled audio to 96,000 Hz mono, causing macOS CoreAudio (`AudioToolbox`) to mute audio with error `kAudioFileUnsupportedDataFormatError (-66680)`. We enforced strict **48,000 Hz Stereo AAC** across both exports, restoring universal playback across Apple QuickTime, iOS, Android, and web players.

---

## 4. Quantitative Metrics & Cost Accounting

### 4.1 Latency & Resource Utilization
*Full pipeline benchmark measured on an Apple M-series developer machine:*

| Pipeline Stage | Fresh Execution Latency | Cached Re-run Latency | Compute Provider | VRAM / CPU Usage |
| :--- | :--- | :--- | :--- | :--- |
| **Stage 1: Validation** | 0.04s | 0.04s | Local CPU | < 15 MB |
| **Stage 2: Narration** | 11.2s | 0.001s | Google AI Studio | Serverless |
| **Stage 3: Keyframes** | 14.8s | 0.001s | Cloudflare Workers AI | Serverless |
| **Stage 4: Moving Shots** | 48.0s (Ken Burns) | 0.001s | Local FFmpeg / Kaggle | Multi-core CPU |
| **Stage 5: Music Score** | 8.5s | 0.001s | Local / Kaggle Synthesis | < 4 GB |
| **Stage 6: Assembly** | 1.8s | 1.8s | Local FFmpeg 6.0 | Multi-core CPU |
| **Total Pipeline** | **~84.3s** | **< 3.9s** | **100% Free Tier** | **Zero Memory Leaks** |

### 4.2 Economic Analysis: Commercial SaaS vs. Open Zero-Cost Pipeline
By orchestrating open weights and legitimate developer tiers with content-addressable SHA-256 caching, our total production cost was **$0.00**, saving substantial commercial fees:

| Component | Commercial Equivalent | SaaS Provider Unit Rate | Commercial Cost | Our Pipeline Cost |
| :--- | :--- | :--- | :--- | :--- |
| Storyboard & Script | GPT-4o | $0.005 / 1k tokens | $0.03 | **$0.00** (Gemini Free Tier) |
| Voice Narration | ElevenLabs Multilingual | $0.30 / 1k characters | $0.28 | **$0.00** (Gemini Flash TTS) |
| Keyframes (9 stills) | Midjourney v6 / DALL-E 3 | $0.04 / image | $0.36 | **$0.00** (Cloudflare FLUX) |
| Video Motion (68s) | Runway Gen-3 / Sora | $0.10 / second | $6.80 | **$0.00** (Wan 2.2 / Ken Burns) |
| Score (3 candidates) | Suno v3 / Udio | $0.10 / generation | $0.30 | **$0.00** (ACE-Step Open Weights) |
| **Total Production Cost**| | | **$7.77 / run** | **$0.00 (100% Free)** |

---

## 5. User Testing Rounds & Audience Feedback

### User Test 1: The Radio Cut Prototype (Audio Audit)
* **Format:** Audio-only prototype (`outputs/exports/radio_cut.wav`).
* **Audience:** Native Ethiopian listener and family members.
* **Key Findings:** Flagged female voice mismatch for first-person brother memory and identified 19 phonetic gemination errors.
* **Iterative Fix:** Switched to male baritone voice profile (`Charon`) and added strict Amharic pronunciation steering.

### User Test 2: The Near-Final Master Polish (Visual & Codec Audit)
* **Participants:**
  1. **Surafel ("Abulala" — Inseparable Childhood Friend & Named Protagonist):** Provided direct, heartfelt reactions upon watching his childhood recreation:
     > **[26/11/2026 10:16 AM] Abulala:** *"Bro WTF! i was not ready for this"*  
     > **[26/11/2026 10:24 AM] Abulala:** *"Mareamn it gave me mixed emotions , ye ai amaregna besak gedelegn and the nostalgia made me cry fr, ahun yalenbetn saseb,,,,,the freedom eza sinhed yalkew sinmeles ebet bikotunem worth yaderg neber mnamn as you said, brooo also the ጠረጴዛ part broooooo i was not ready for these 😢"*  
     *Significance:* Confirmed that the dramatic structure (the contrast between childhood natural freedom in Arba Minch and adult desk isolation) resonated at the deepest personal level.
  2. **Mikiyas (Brother & Real-Life Protagonist):** Praised Candidate 1 score (Gamo polyphonic humming) for capturing the Arba Minch morning mist; validated emotional authenticity and the dedication end card.
  3. **Dawit (Senior Multimedia Video Editor & Sound Engineer, Addis Ababa):** Identified silent audio in QuickTime due to 96kHz AAC container mismatch, directly driving our 48kHz Stereo AAC standard.
* **Iterative Fixes:**
  * Switched vertical mobile export to native full-bleed 720×1280 framing.
  * Enforced broadcast standard 48 kHz Stereo AAC encoding.
  * Embedded bilingual subtitles (`subtitles.srt`) and dedicated 3s AI transparency end card.

---

## 6. Architectural Decisions (ADR Summary)

* **ADR 01: Single Source of Truth Storyboard:** All downstream processes derive exclusively from `storyboard.json`.
* **ADR 04: Gemini 429 Key Rotator:** Automated round-robin rotation across multiple API keys with exponential jitter backoff.
* **ADR 08: Schema-Enforced Character Consistency:** Physical identity DNA declared directly in JSON schema, dynamically injected into prompts.
* **ADR 09: Asynchronous Kaggle Drop-In Pattern:** Remote GPU generation decoupled via folder watcher (`outputs/wan_drops/`), guaranteeing zero local pipeline blocking.

---

## 7. Ethical Considerations & AI Transparency

1. **Consent & Living Representations:** The names **Mikiyas**, **Mihretab**, and **Surafel** represent real individuals whose explicit verbal consent was obtained. Prompts were intentionally crafted to preserve nostalgic, respectful, and joyful framing.
2. **Cultural Safeguards:** Prompts explicitly prohibited exoticized tropes or war imagery, centering instead on Ethiopia's lush natural landscapes and joyful childhood brotherhood.
2. **Mandatory AI Disclosure:** Both video masters include a burned 3-second end card (*"Made with AI • For Mikiyas, Mihretab, and Surafel"*), and all public social posts are published with the platform's AI transparency label active.

---

## 8. Conclusion
*The Forty Springs of Arba Minch* proves that production-grade generative cinema does not require commercial subscriptions or opaque SaaS tools. By treating generative filmmaking as a rigorous software engineering discipline—anchored in schema contracts, content-addressable caching, and strict audio-visual mastering standards—we achieved a culturally resonant, emotionally moving short film with complete determinism, zero commercial cost, and rapid re-render capabilities.
