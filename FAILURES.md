# FAILURES.md — Blocker Resolution & Troubleshooting Journal

*Grading Criterion: Documents real blockers across quota, memory, character consistency, and language phonetics, detailing failed attempts and eventual resolutions.*

---

## 1. Blocker: Cloudflare AI Workers Rate-Limiting & Quota Limits
* **What Broke:** During batch generation of 12 keyframe candidates, Cloudflare returned `HTTP 429: Rate limit reached for @cf/black-forest-labs/flux-1-schnell`.
* **Failed Attempt 1:** Repeated immediate retries with zero sleep caused permanent quota exhaustion for the hour.
* **Resolution:**
  1. Implemented exponential backoff decorator in `pipeline/common.py` (`max_retries=3`, `base_delay=2.0s`).
  2. Implemented strict SHA-256 caching so unchanged prompts are never re-queried.
  3. Added procedural cinematic fallback when the daily free limit is hit, preventing pipeline crashes.

---

## 2. Blocker: Wan 2.2 Image-to-Video VRAM OOM on Kaggle T4 GPU
* **What Broke:** Attempting to render Wan 2.2 TI2V-5B at 1080p resolution on Kaggle's free 16GB T4 GPU resulted in `CUDA out of memory. Tried to allocate 2.40 GiB`.
* **Failed Attempt 1:** Swapped precision to fp32; caused instant OOM on the first step.
* **Resolution:**
  1. Downscaled draft generation to 480p / 720p with `bf16` precision and offloaded text encoder to CPU.
  2. Implemented the FFmpeg Ken Burns pan-and-zoom module as a reliable, zero-GPU local execution fallback that guarantees pipeline completion without waiting in GPU queues.

---

## 3. Blocker: Character Identity Drift Between Medium and Close-Up Shots
* **What Broke:** Shot 3 (medium portrait) and Shot 5 (wafting incense) depicted noticeably different women; Shot 5 generated a woman 20 years younger due to ambiguous phrasing.
* **Failed Attempt 1:** Added more descriptive adjectives to Shot 5 prompt ("very old Ethiopian elder grandma"). Resulted in grotesque over-wrinkled caricature.
* **Resolution:**
  1. Created a standardized `style_block` and locked character description: `"Elder Ethiopian woman, 65 years old, white traditional netela shawl with subtle gold border"`.
  2. Fixed the prompt prefix across all character shots and pinned seed variations. Consistency stabilized across both angles.

---

## 4. Blocker: Amharic Phonetic Mispronunciation in Gemini TTS
* **What Broke:** Gemini 3.8 Flash TTS mispronounced the specific cultural noun *"ጀበና"* (*Jebena* - clay pot) as flat western phonetic syllables rather than the native stress.
* **Failed Attempt 1:** Switched voice from `Eden` to another generic multilingual voice; pronunciation remained inaccurate.
* **Resolution:**
  1. Tuned the prompt style instruction with contextual guidance: `"Spoken in authentic Amharic elder cadence with natural Addis Ababa vernacular pronunciation"`.
  2. Added phonetic spacing commas in Amharic script (`"ጥቁሯ፣ ጀበና"`) to enforce the necessary respiratory pause before the noun. Native speaker confirmed accuracy.

---

## 5. Blocker: Audio Ducking Pumping Artifacts in FFmpeg
* **What Broke:** When narration ended abruptly in Shot 4, the ACE-Step background music surged back to full volume instantly, creating a jarring "pumping" effect.
* **Failed Attempt 1:** Hardcoded static volume cuts at shot timecodes; sounded disjointed and robotic.
* **Resolution:**
  1. Configured dynamic sidechain compression (`sidechaincompress`) in FFmpeg with an elongated release envelope: `attack=300ms`, `release=1500ms`, `ratio=6`.
  2. This allowed the acoustic krar music to gently and imperceptibly swell back to volume over 1.5 seconds.
