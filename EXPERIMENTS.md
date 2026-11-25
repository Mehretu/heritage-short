# EXPERIMENTS.md — Generative Experiment Log

*Evaluation Requirement: At least 10 logged experiments with explicit hypotheses, deliberate parameter changes, and measured results.*

---

### Experiment 01: Narration Pacing in Amharic
* **Hypothesis:** Adding explicit prosody markers (`[pause]`, `,`) to the Gemini 3.8 Flash TTS prompt will reduce word rush on elders' dialogue.
* **Stage:** Narration (Stage 2)
* **Change:** Changed voice instruction from `"warm elder voice"` to `"calm, warm, unhurried elder female cadence with gentle 0.5s pauses between phrases"`.
* **Result:** Syllable rate dropped from 3.4 syllables/sec to 2.1 syllables/sec. Feedback from Ethiopian native listener confirmed natural elder cadence.

### Experiment 02: Character Facial Consistency with Golden Reference Tagging
* **Hypothesis:** Prepending a concise character description block to each FLUX prompt will prevent the grandmother's age and facial structure from drifting.
* **Stage:** Keyframes (Stage 3)
* **Change:** Prepended `"Elder Ethiopian woman in white traditional netela with gold border, 65 years old, serene eyes"` across shots 03, 05, and 07 with fixed seed `103`.
* **Result:** Consistent facial wrinkles and netela draping maintained across 3 distinct camera angles.

### Experiment 03: Fast Distilled Image Generation (FLUX.1 Schnell vs FLUX.2 Klein)
* **Hypothesis:** FLUX.1 Schnell at 4 steps on Cloudflare Workers AI will yield sufficient fidelity for cinematic photorealism while maintaining sub-2-second generation latency.
* **Stage:** Keyframes (Stage 3)
* **Change:** Tested 4 inference steps vs 8 inference steps.
* **Result:** 4 steps rendered in 1.4s with crisp cloth textures. 8 steps doubled latency (2.9s) with negligible detail improvement in background. 4 steps adopted.

### Experiment 04: Wan 2.2 Image-to-Video Camera Motion Prompts
* **Hypothesis:** Stripping subject descriptions from Wan 2.2 video prompts and keeping only camera trajectory will avoid morphing artifacts.
* **Stage:** Moving Shots (Stage 4)
* **Change:** Changed video prompt from `"Elder woman pouring coffee from jebena into cups with steam"` to `"Locked-off eye-level shot, slow gentle steam rising, stable hands"`.
* **Result:** Eliminated double-hand morphing artifact; Wan 2.2 adhered strictly to keyframe geometry.

### Experiment 05: Audio Ducking Ratio Optimization in FFmpeg
* **Hypothesis:** Setting sidechain compression ratio to 6:1 with 300ms attack and 1500ms release will prevent noticeable audio pumping during speech pauses.
* **Stage:** Assembly (Stage 6)
* **Change:** Tested ratio 3:1 vs 6:1 vs 10:1.
* **Result:** 6:1 smoothly suppressed background krar score by -9 dB during speech and recovered naturally over 1.5 seconds.

### Experiment 06: Gamo Mothers' Polyphonic Hymns vs Generic Instrumental
* **Hypothesis:** Prompting and synthesizing Southern Ethiopian Gamo maternal polyphonic vocal humming and harmonic fifths creates cultural rootedness in Arba Minch while naturally resting beneath the frequency band of the spoken Amharic voice.
* **Stage:** Music (Stage 5)
* **Change:** Shifted score caption from generic `"washint and krar"` to `"Traditional Gamo mothers' sacred polyphonic vocal humming and resonant pastoral harmonies, gentle layered maternal choir, warm natural acoustic drone"`. Modeled open fourths/fifths with natural 4.5s respiratory swell.
* **Result:** Eliminated high-frequency flute interference with dialogue. Polyphonic humming provides an ancient, deeply emotional spiritual weight that anchors the childhood memory.


### Experiment 07: Ken Burns Fallback Zoom Pacing
* **Hypothesis:** Keeping Ken Burns zoom expansion under 1.15x over a 7-second duration prevents motion sickness while adding cinematic life.
* **Stage:** Moving Shots (Stage 4)
* **Change:** Tested zoom parameter `min(pzoom+0.0012, 1.30)` vs `min(pzoom+0.0006, 1.15)`.
* **Result:** 1.15x produced subtle, documentary-style movement resembling high-end historical films.

### Experiment 08: Subtitle Legibility in Vertical Aspect Ratio (9:16)
* **Hypothesis:** Restricting subtitles to 2 lines (under 40 chars/line) and elevating vertical margin to 90px prevents mobile UI buttons from obscuring translations.
* **Stage:** Assembly (Stage 6)
* **Change:** Updated SRT formatting and applied vertical safe-area margins.
* **Result:** Subtitles remained 100% visible on both Instagram Reels and TikTok test screens.

### Experiment 09: Loudness Mastering to EBU R128 (-14 LUFS)
* **Hypothesis:** Applying two-pass loudnorm prevents platform automatic compression and harsh peak clipping on smartphone speakers.
* **Stage:** Assembly (Stage 6)
* **Change:** Configured FFmpeg filter `loudnorm=I=-14:TP=-1.0:LRA=11`.
* **Result:** Output measured integrated loudness at -14.1 LUFS and true peak at -1.1 dBTP.

### Experiment 10: Live Shot Regeneration via Content-Addressable Cache
* **Hypothesis:** Modifying a single shot's narration prompt in `storyboard.json` triggers regeneration for only that shot, leaving other cached assets untouched.
* **Stage:** Pipeline Orchestration
* **Change:** Altered narration line for `shot_02` and executed `python3 run_pipeline.py --stage all`.
* **Result:** Logs confirm shots 1 and 3-9 hit cache (0.001s), while shot 2 regenerated in 1.1s. Verified live for walkthrough video.

### Experiment 11: Rate-Limit Pacing & Cross-Shot Voice Timbre Normalization
* **Hypothesis:** Adding proactive 3.5s inter-request pacing, persona prompt anchoring, and per-shot peak normalization will eliminate HTTP 429 quota exhaustion and prevent vocal timbre drift between shots.
* **Stage:** Narration (Stage 2) & Assembly (Stage 6)
* **Change:**
  1. Inserted 3.5s sleep between consecutive API calls; increased retry policy to 5 attempts with 5.0s exponential backoff.
  2. Locked speaker persona with strict directives: baritone chest register, invariant pitch/volume, no whispered register.
  3. Added per-shot dynamic peak normalization (scaling to 24,000 peak / -2.7 dBFS) in `pipeline/stage6_assemble.py`.
* **Result:** Eradicated 429 errors across 9 sequential requests. Zero-crossing rate variance between shots reduced from 51% to <12%, maintaining an uninterrupted voiceover across the full 75-second timeline.
