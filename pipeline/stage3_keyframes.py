"""
Stage 3: Keyframe Generation (FLUX on Cloudflare Workers AI)
Generates high-fidelity keyframe stills conditioned on the global style block
and character references.
Implements:
- Input hashing (prompt + style_block + seed)
- Cloudflare Workers AI free API caller for FLUX.1-schnell / FLUX.2-klein
- Local generative fallback using Pillow with procedural composition
- runs.jsonl logging per call
"""

import os
import sys
import time
import urllib.request
import json
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

KEYFRAMES_DIR = OUTPUTS_DIR / "keyframes"
CLOUDFLARE_ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN")


@retry_with_backoff(max_retries=3, base_delay=2.0)
def generate_cloudflare_flux(full_prompt: str, seed: int, out_path: Path):
    """Call Cloudflare Workers AI endpoint for @cf/black-forest-labs/flux-1-schnell."""
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    payload = {
        "prompt": full_prompt,
        "seed": seed,
        "num_steps": 4
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        # CF returns image bytes directly or JSON with base64 'image'
        content_type = resp.headers.get("Content-Type", "")
        body = resp.read()
        if "application/json" in content_type:
            res = json.loads(body.decode("utf-8"))
            if "result" in res and "image" in res["result"]:
                import base64
                with open(out_path, "wb") as f:
                    f.write(base64.b64decode(res["result"]["image"]))
                return
        with open(out_path, "wb") as f:
            f.write(body)


def fallback_procedural_image(shot_id: str, prompt: str, seed: int, style_info: str, out_path: Path):
    """
    Pure Python fallback creating an aesthetic cinematic placeholder keyframe
    with warm Kodak aesthetic, title overlay, and shot metadata.
    """
    try:
        from PIL import Image, ImageDraw
        width, height = 1280, 720
        # Determine warm tones from seed
        r = (seed * 37) % 60 + 40
        g = (seed * 19) % 40 + 25
        b = (seed * 13) % 30 + 15
        img = Image.new("RGB", (width, height), color=(r, g, b))
        draw = ImageDraw.Draw(img)

        # Draw decorative cinematic frames and gradients
        draw.rectangle([40, 40, width - 40, height - 40], outline=(180, 150, 100), width=2)
        draw.text((60, 60), f"AI Heritage Short • {shot_id.upper()}", fill=(240, 230, 210))
        draw.text((60, 90), f"Seed: {seed} | Style: {style_info[:50]}...", fill=(200, 190, 170))

        # Wrap prompt text across middle
        words = prompt.split()
        lines = []
        cur = []
        for w in words:
            cur.append(w)
            if len(" ".join(cur)) > 60:
                lines.append(" ".join(cur))
                cur = []
        if cur:
            lines.append(" ".join(cur))

        y_offset = height // 2 - (len(lines) * 15)
        for line in lines[:6]:
            draw.text((60, y_offset), line, fill=(255, 245, 220))
            y_offset += 30

        img.save(out_path, "PNG")
    except ImportError:
        # Minimal PPM binary format if Pillow is absent
        with open(out_path, "wb") as f:
            f.write(f"P6\n1280 720\n255\n".encode())
            color = bytes([(seed * 37) % 180, (seed * 19) % 120, (seed * 13) % 80])
            f.write(color * (1280 * 720))


def run_keyframes_stage(target_shot_id=None, force_regenerate=False):
    print("🎨 [Stage 3] Generating keyframe stills per shot...")
    storyboard = load_storyboard()
    style_block = storyboard.get("style_block", {})
    style_desc = style_block.get("visual_style", "")

    keyframes = {}

    for shot in storyboard.get("shots", []):
        shot_id = shot["shot_id"]
        if target_shot_id and shot_id != target_shot_id:
            continue

        img_cfg = shot.get("image_prompt", {})
        prompt = img_cfg.get("prompt", "")
        neg_prompt = img_cfg.get("negative_prompt", "")
        seed = img_cfg.get("seed", 42)

        # Full prompt appends global style block to guarantee visual consistency
        full_prompt = f"{prompt}. Style: {style_desc}"

        cache_data = {
            "prompt": full_prompt,
            "negative_prompt": neg_prompt,
            "seed": seed
        }
        input_hash = compute_sha256(cache_data)
        out_png = KEYFRAMES_DIR / f"{shot_id}.png"

        cached_file = get_cached_output("keyframes", input_hash, ".png")
        if cached_file and not force_regenerate:
            import shutil
            shutil.copy2(cached_file, out_png)
            print(f"  ⚡ [{shot_id}] CACHE HIT (hash: {input_hash[:8]}...) -> Reusing keyframe")
            log_run(
                stage="keyframes",
                model="FLUX.1-schnell",
                parameters={"prompt": full_prompt, "steps": 4},
                seed=seed,
                latency_seconds=0.001,
                cost_usd=0.0,
                cached=True,
                metadata={"shot_id": shot_id, "input_hash": input_hash}
            )
            keyframes[shot_id] = out_png
            continue

        print(f"  🖼️ [{shot_id}] Generating keyframe (seed={seed})...")
        t0 = time.time()
        used_mock = False

        if CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN:
            try:
                generate_cloudflare_flux(full_prompt, seed, out_png)
            except Exception as e:
                print(f"  ⚠️ Cloudflare AI generation failed ({e}); falling back to cinematic renderer.")
                fallback_procedural_image(shot_id, full_prompt, seed, style_desc, out_png)
                used_mock = True
        else:
            fallback_procedural_image(shot_id, full_prompt, seed, style_desc, out_png)
            used_mock = True

        latency = time.time() - t0
        store_cached_output("keyframes", input_hash, out_png)

        model_name = "FLUX.1-schnell" if not used_mock else "procedural-cinematic-renderer"
        log_run(
            stage="keyframes",
            model=model_name,
            parameters={"prompt": full_prompt, "negative_prompt": neg_prompt, "seed": seed},
            seed=seed,
            latency_seconds=latency,
            cost_usd=0.0,
            cached=False,
            metadata={"shot_id": shot_id, "input_hash": input_hash}
        )
        print(f"  ✅ [{shot_id}] Keyframe ready in {latency:.2f}s -> {out_png.name}")
        keyframes[shot_id] = out_png

    print(f"  🎉 Stage 3 complete: {len(keyframes)} keyframes generated.\n")
    return keyframes


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    run_keyframes_stage(target_shot_id=target)
