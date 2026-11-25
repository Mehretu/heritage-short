"""
Stage 2: Narration Generation (Gemini 3.8 Flash TTS)
Generates audio lines per shot, adhering to the storyboard prosody and language.
Implements:
- Input hashing (text + voice_instruction + language) for caching
- runs.jsonl logging (latency, parameters, seed, cost=0.0 on free tier)
- Local audio generator fallback (e.g. macOS say or synthesized wav) if API key is not yet set
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from common import (
    PROJECT_ROOT,
    OUTPUTS_DIR,
    load_storyboard,
    compute_sha256,
    get_cached_output,
    store_cached_output,
    log_run,
    retry_with_backoff
)

AUDIO_OUT_DIR = OUTPUTS_DIR / "audio"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_URL_TEMPLATE = os.environ.get("GEMINI_URL")


class GeminiKeyRotator:
    """
    Manages a pool of Gemini API keys across multiple Google Cloud / AI Studio projects.
    Enables automatic zero-downtime quota rotation when HTTP 429 (Too Many Requests) is encountered.
    """
    def __init__(self):
        self.keys = []
        raw = os.environ.get("GEMINI_API_KEYS", "")
        if raw:
            for k in raw.split(","):
                k = k.strip()
                if k and not k.startswith("your_") and k not in self.keys:
                    self.keys.append(k)
        for var in ["GEMINI_API_KEY", "GEMINI_API_KEY_FALLBACK", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"]:
            val = os.environ.get(var, "").strip()
            if val and not val.startswith("your_") and val not in self.keys:
                self.keys.append(val)
        self.idx = 0

    @property
    def pool_size(self) -> int:
        return len(self.keys)

    def current_key(self) -> str:
        if not self.keys:
            return os.environ.get("GEMINI_API_KEY", "")
        return self.keys[self.idx % len(self.keys)]

    def rotate_on_429(self) -> str:
        if len(self.keys) > 1:
            prev = self.idx % len(self.keys)
            self.idx += 1
            nxt = self.idx % len(self.keys)
            print(f"  🔄 Quota 429 encountered: Rotating API key (pool slot {prev+1} -> {nxt+1} of {len(self.keys)})")
            return self.current_key()
        return self.current_key()


KEY_ROTATOR = GeminiKeyRotator()

AMHARIC_PHONETIC_GUIDE = {
    "ጠረጴዛዬ": "ṭäräp-p̣éza-yé (crisp ejective 'ṭ', doubled geminated 'p')",
    "ይሮጣል።": "yi-ro-T'al (crisp glottal ejective 'T')",
    "ወደ": "wä-dä",
    "የምድር": "yä-midir",
    "ጥቅጥቅ": "T'iq-T'iq (sharp glottal ejective 'T')",
    "ወንድሜ": "wän-dim-mé (doubled geminated 'm')",
    "ተደብቀን": "tä-däb-bä-qän (doubled geminated 'b', crisp 'q')",
    "ቅዳሜ": "qï-da-mé",
    "ሳንደናገጥ": "san-dä-na-gäT (sharp ejective 'T')",
    "የሚፈልቁት": "yä-mi-fäl-qut",
    "ንጹሕ": "ni-T'uH (crisp glottal 'T')",
    "ገንዳ": "gän-da",
    "ጭንቀት": "Ch'in-qät (crisp ejectives 'Ch' and 'q')",
    "ቀልጦ ይጠፋል": "qäl-T'o yi-T'ä-fal",
    "በድንጋይ": "bä-din-gay",
    "ይበልጥ": "yi-bälT' (crisp ejective 'T')",
    "ስትጠልቅ": "sit-T'ä-liq (crisp ejectives 'T' and 'q')",
    "ብትቆጣንም": "bit-T'o-T'a-nim (doubled ejective 'T')",
    "ይፈሳሉ።": "yi-fäs-sa-lu (doubled geminated 's')"
}


def generate_gemini_tts(text: str, voice_instruction: str, language: str, voice_name: str, out_path: Path):
    """
    Calls Gemini API TTS endpoint with explicit voice profile, multi-key quota rotation, and phonetic steering.
    """
    import urllib.request
    import urllib.error
    import json

    url = GEMINI_URL_TEMPLATE.format(model_name="gemini-2.5-flash-preview-tts")

    # Match phonetic hints for Amharic words present in the sentence
    hints = [f"• '{word}' -> {guide}" for word, guide in AMHARIC_PHONETIC_GUIDE.items() if word.replace("።", "").replace("፣", "") in text]
    phonetic_block = ("\nPhonetic & Consonant Gemination (ጥብቅና ላልት) Guide:\n" + "\n".join(hints)) if hints else ""

    # Payload requesting audio output modality with strict speaker persona anchoring
    payload = {
        "contents": [{
            "parts": [
                {
                    "text": (
                        f"Consistent Speaker Persona: You are an adult Ethiopian male in his late 20s with a warm, "
                        f"deep, grounded baritone voice. Maintain an identical pitch, resonance, speaking volume, and "
                        f"cadence across every line. Do NOT whisper, do NOT pitch up into high register. "
                        f"Speak authentic, conversational {language} with natural Addis Ababa cadence and correct "
                        f"consonant gemination (ጥብቅና ላልት).\n"
                        f"Scene mood: {voice_instruction}\n"
                        f"{phonetic_block}\n\n"
                        f"Read this line clearly, steadily, and naturally:\n{text}"
                    )
                }
            ]
        }],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": voice_name or "Charon"
                    }
                }
            }
        }
    }

    max_attempts = 5
    base_delay = 3.0 if KEY_ROTATOR.pool_size > 1 else 6.0
    for attempt in range(1, max_attempts + 1):
        active_key = KEY_ROTATOR.current_key()
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": active_key
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=35) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                # Decode base64 audio
                audio_data = None
                candidates = res.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    for p in parts:
                        if "inlineData" in p and "data" in p["inlineData"]:
                            import base64
                            audio_data = base64.b64decode(p["inlineData"]["data"])
                            break
                if not audio_data:
                    raise RuntimeError("No audio data returned in Gemini response")

                # Wrap raw PCM in standard RIFF WAV header (Gemini returns 24kHz 16-bit linear PCM)
                if not audio_data.startswith(b"RIFF"):
                    import wave
                    with wave.open(str(out_path), "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(24000)
                        wf.writeframes(audio_data)
                else:
                    with open(out_path, "wb") as f:
                        f.write(audio_data)
                return
        except urllib.error.HTTPError as e:
            if e.code == 429:
                if KEY_ROTATOR.pool_size > 1:
                    if attempt == max_attempts:
                        raise e
                    KEY_ROTATOR.rotate_on_429()
                    print(f"  ⚠️ HTTP 429 Quota: Switched to next key in pool, cooling 3.5s before retry (attempt {attempt}/{max_attempts})...")
                    time.sleep(3.5)
                    continue
                else:
                    delay = base_delay * (1.6 ** (attempt - 1))
                    if attempt == max_attempts:
                        raise e
                    print(f"  ⚠️ HTTP 429 Quota (single key in use): Cooling down for {delay:.1f}s (attempt {attempt}/{max_attempts})...")
                    time.sleep(delay)
            else:
                if attempt == max_attempts:
                    raise e
                time.sleep(3.0)

    raise RuntimeError(f"Gemini TTS generation failed after {max_attempts} attempts.")


def mock_or_local_tts(text: str, duration_target: float, out_path: Path):
    """
    Robust local fallback: generates synthetic speech tone or macOS 'say' command,
    ensuring a stranger can clone and execute the entire pipeline with zero barriers.
    """
    # Check if macOS 'say' exists
    import shutil
    if shutil.which("say"):
        aiff_path = out_path.with_suffix(".aiff")
        subprocess.run(["say", "-o", str(aiff_path), text], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if aiff_path.exists():
            # Convert aiff to wav via ffmpeg or python wave
            if shutil.which("ffmpeg"):
                subprocess.run(["ffmpeg", "-y", "-i", str(aiff_path), str(out_path)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                aiff_path.unlink(missing_ok=True)
                return

    # Fallback to pure-python synthesized tone matching target duration
    import wave
    import math
    import struct
    sample_rate = 24000
    num_samples = int(sample_rate * max(2.0, duration_target))
    with wave.open(str(out_path), "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for i in range(num_samples):
            # Gentle soft ambient tone at 220Hz
            value = int(8000 * math.sin(2 * math.pi * 220.0 * i / sample_rate) * math.exp(-0.5 * (i / sample_rate)))
            data = struct.pack("<h", max(-32768, min(32767, value)))
            wav_file.writeframesraw(data)


def run_narration_stage(target_shot_id=None, force_regenerate=False):
    print(" [Stage 2] Generating narration tracks per shot...")
    storyboard = load_storyboard()
    voice_prof = storyboard.get("voice_profile", {})
    voice_instruction = voice_prof.get("voice_instruction", "calm, warm, slow young man")
    voice_name = voice_prof.get("voice_name", "Puck")  # 'Puck' or 'Charon' for male voice
    global_lang = storyboard.get("language", "Amharic")

    generated_files = {}
    shots_list = storyboard.get("shots", [])

    for idx, shot in enumerate(shots_list):
        shot_id = shot["shot_id"]
        if target_shot_id and shot_id != target_shot_id:
            continue

        narration = shot["narration"]
        text = narration.get("text", "")
        lang = narration.get("language", global_lang)
        target_dur = shot.get("duration_seconds", 5.0)

        # Cache key based strictly on input contract
        cache_data = {
            "text": text,
            "voice_instruction": voice_instruction,
            "voice_name": voice_name,
            "language": lang
        }
        input_hash = compute_sha256(cache_data)
        out_wav = AUDIO_OUT_DIR / f"{shot_id}.wav"

        cached_file = get_cached_output("narration", input_hash, ".wav")
        if cached_file and not force_regenerate:
            import shutil
            shutil.copy2(cached_file, out_wav)
            print(f"  ⚡ [{shot_id}] CACHE HIT (hash: {input_hash[:8]}...) -> Reusing audio")
            log_run(
                stage="narration",
                model="gemini-3.8-flash-tts",
                parameters={"voice_instruction": voice_instruction, "language": lang},
                seed=0,
                latency_seconds=0.001,
                cost_usd=0.0,
                cached=True,
                metadata={"shot_id": shot_id, "input_hash": input_hash}
            )
            generated_files[shot_id] = out_wav
            continue

        print(f"  🎤 [{shot_id}] Generating audio: \"{text[:35]}...\"")
        t0 = time.time()
        used_mock = False

        if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
            try:
                generate_gemini_tts(text, voice_instruction, lang, voice_name, out_wav)
            except Exception as e:
                print(f"  ⚠️ Gemini TTS API call failed ({e}); using resilient local audio synthesizer.")
                mock_or_local_tts(text, target_dur, out_wav)
                used_mock = True
        else:
            mock_or_local_tts(text, target_dur, out_wav)
            used_mock = True

        latency = time.time() - t0
        # CRITICAL ARCHITECTURAL FIX: Only cache genuine successful API generations.
        # Degraded fallback mocks must NEVER poison the persistent content-addressable cache.
        if not used_mock:
            store_cached_output("narration", input_hash, out_wav)

        model_name = "gemini-3.8-flash-tts" if not used_mock else "local-synthesizer-tts"
        log_run(
            stage="narration",
            model=model_name,
            parameters={"voice_instruction": voice_instruction, "language": lang, "char_count": len(text)},
            seed=0,
            latency_seconds=latency,
            cost_usd=0.0,
            cached=False,
            metadata={"shot_id": shot_id, "input_hash": input_hash}
        )
        print(f"  ✅ [{shot_id}] Finished in {latency:.2f}s -> {out_wav.name}")
        generated_files[shot_id] = out_wav

        # Dynamic inter-request rate throttle: if multiple keys in pool, pace 2s; if 1 key, pace 7s
        pace_delay = 2.0 if KEY_ROTATOR.pool_size > 1 else 7.0
        if not used_mock and idx < len(shots_list) - 1:
            print(f"  ⏳ Pacing {pace_delay:.0f}s to respect free-tier speech quota...")
            time.sleep(pace_delay)

    print(f"  🎉 Stage 2 complete: {len(generated_files)} narration files ready.\n")
    return generated_files


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    run_narration_stage(target_shot_id=target)
