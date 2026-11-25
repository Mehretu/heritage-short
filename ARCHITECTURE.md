# ARCHITECTURE.md — Pipeline Architecture & Technical Contracts

## 1. System Overview & Stage Boundaries
The pipeline operates as a modular, deterministic state machine orchestrated by `run_pipeline.py`. The single source of truth across all stages is `storyboard.json`, strictly validated by `schema/storyboard.schema.json`.

```mermaid
flowchart LR
    A[storyboard.json] -->|Validated by JSON Schema| B[Stage 1: Validate]
    B --> C[Stage 2: Narration<br/>Gemini 3.8 Flash TTS]
    B --> D[Stage 3: Keyframes<br/>FLUX.1 Schnell]
    D --> E[Stage 4: Moving Shots<br/>Wan 2.2 / Ken Burns]
    B --> F[Stage 5: Music Score<br/>ACE-Step 1.5]
    C --> G[Stage 6: Assembly<br/>FFmpeg Ducking & Loudnorm]
    E --> G
    F --> G
    G --> H[Final 16:9 & 9:16 Exports]
```

---

## 2. Data Contracts
* **Contract Specification:** `schema/storyboard.schema.json` defines all required shot attributes: `shot_id`, `duration_seconds`, `reason`, `narration`, `image_prompt`, `motion_prompt`, `music_cue`.
* **Immutability Principle:** Upstream stages cannot alter the storyboard contract. Downstream stages consume only the declared fields and outputs of previous stages.

---

## 3. Caching & Deterministic Re-runs
To prevent burning GPU/API quotas and enable instantaneous re-runs, every generative stage implements content-addressable SHA-256 caching:

* **Narration Cache Key:** `SHA256(text + voice_instruction + language)`
* **Keyframe Cache Key:** `SHA256(prompt + negative_prompt + style_block + seed)`
* **Moving Shot Cache Key:** `SHA256(keyframe_bytes_hash + motion_prompt + duration + seed)`
* **Music Cache Key:** `SHA256(caption + tempo + key + duration + seed)`

*Behavior:* When a developer changes only `shot_03`'s prompt in `storyboard.json` and runs `python3 run_pipeline.py --stage all`, the pipeline detects cache hits for shots 1, 2, 4–9, regenerating **only** `shot_03`. This fulfills the live demonstration requirement for Assignment 2.

---

## 4. Failure Handling & Offline Fallbacks
The pipeline is designed to execute successfully from a clean clone even when external cloud services are offline or unconfigured:

1. **Gemini TTS Failure / Offline:** If `GEMINI_API_KEY` is unavailable or rate-limited, the system falls back to macOS native `say` or procedural audio waveform synthesis matching shot duration.
2. **Cloudflare AI Workers FLUX Failure:** If Cloudflare quotas are exhausted, the procedural cinematic renderer generates formatted keyframes preserving prompt metadata.
3. **Wan 2.2 GPU Ingestion vs Ken Burns Pan-and-Zoom:**
   - If Kaggle/Colab GPU outputs exist in `outputs/wan_drops/`, the pipeline seamlessly ingests them.
   - If offline or on CPU, the built-in FFmpeg Ken Burns module applies smooth 24fps pan-and-zoom motion matching the storyboard camera prompts.
4. **Assembly Audio Ducking & Loudnorm:**
   - Uses FFmpeg's `sidechaincompress` filter (`threshold=0.02, ratio=6, attack=300ms, release=1500ms`) to duck score dynamically under speech.
   - Normalizes audio to broadcast standard **-14 LUFS (EBU R128)** with **-1.0 dB true peak** to avoid platform distortion.

---

## 5. Configuration & Endpoint Decoupling
All external API URLs are completely abstracted out of the code and defined as environment templates in `.env`:
* **`GEMINI_URL`:** Parameterized model template (`.../models/{model_name}:generateContent`) supporting dynamic fallback across `gemini-flash-lite`, `gemini-3.8-flash`, and TTS preview endpoints.
* **`CLOUDFLARE_FLUX_URL`:** Parameterized account template (`.../accounts/{account_id}/ai/run/@cf/black-forest-labs/flux-1-schnell`).
* **`KAGGLE_API_URL`:** Base endpoint for remote dataset and GPU execution.

*Benefit:* Eliminates hardcoded URLs, facilitates switching between cloud regions or local proxies, and adheres strictly to Twelve-Factor App config separation.

---

## 6. Architectural Decision Records (ADRs) for Error & Edge Handling

### ADR 01: Circuit Breaker & Fallback Policy (Zero Fatal Crashes)
* **Context:** The evaluation criteria mandate that an external reviewer can clone and execute the entire pipeline with zero fatal crashes, even without API keys or when cloud providers experience downtime.
* **Decision:** Every cloud API stage encapsulates remote calls inside a defensive try/except circuit breaker that falls back to a deterministic, zero-dependency offline generator (`mock_or_local_tts` in Stage 2, PIL gradient canvas in Stage 3, Ken Burns pan-zoom in Stage 4, acoustic pink noise + krar in Stage 5).
* **Consequence & Invariant:** Degraded/mock fallback artifacts must **never** be committed to the content-addressable SHA-256 cache (`store_cached_output()`). Caching is strictly reserved for authenticated, high-fidelity API generations to prevent poisoning future runs with placeholder content.

### ADR 02: Pacing & Token-Bucket Rate Limiting for Foundation Model APIs
* **Context:** Free-tier AI endpoints (e.g., Google AI Studio's 15 RPM limit) fail with HTTP 429 when hit in burst sequences across 9–14 shots.
* **Decision:**
  1. Wrapped all external network requests in an exponential backoff decorator (`@retry_with_backoff(max_retries=5, base_delay=5.0)`).
  2. Implemented proactive inter-request sleep (`time.sleep(3.5)`) between consecutive pipeline shot calls to smooth out request spikes below provider burst thresholds.

### ADR 03: Mitigation of Stateless LLM Voice Timbre Drift
* **Context:** Autoregressive audio foundation models lack persistent acoustic latching. Stateless API requests cause vocal pitch, formant resonance, and emotional tone to drift between shots.
* **Decision:**
  1. Injected an explicit persona anchor into every prompt: fixed age, gender, baritone register, and anti-whisper directives.
  2. Implemented per-shot dynamic peak normalization (scaling to 24,000 peak / -2.7 dBFS) in `pipeline/stage6_assemble.py` before concatenating individual audio frames, ensuring loudness uniformity across the narrative arc.

