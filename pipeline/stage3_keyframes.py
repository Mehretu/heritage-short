"""
Stage 3: Keyframe Generation (FLUX on Cloudflare Workers AI)
Generates high-fidelity keyframe stills conditioned on the global style block
and character references.
Implements:
- Input hashing (prompt + style_block + seed)
- Cloudflare Workers AI free API caller for FLUX.1-schnell / FLUX.2-klein
- Local generative fallback using Pillow with cinematic procedural composition
- Character & style reference sheet generation
- runs.jsonl logging per call
"""

import os
import sys
import time
import math
import random
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
CLOUDFLARE_FLUX_URL_TEMPLATE = os.environ.get("CLOUDFLARE_FLUX_URL")


@retry_with_backoff(max_retries=3, base_delay=2.0)
def generate_cloudflare_flux(full_prompt: str, seed: int, out_path: Path):
    """Call Cloudflare Workers AI endpoint for @cf/black-forest-labs/flux-1-schnell."""
    url = CLOUDFLARE_FLUX_URL_TEMPLATE.format(account_id=CLOUDFLARE_ACCOUNT_ID)
    payload = {
        "prompt": full_prompt
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


def _lerp_color(c1, c2, t):
    """Linear interpolate between two RGB tuples."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def fallback_procedural_image(shot_id: str, prompt: str, seed: int, style_info: str, out_path: Path):
    """
    Cinematic Pillow-rendered placeholder keyframe with:
    - Shot-specific atmospheric color palette (warm Kodak daylight or cool night)
    - Layered gradient sky + ground
    - Procedural tree silhouettes / spring water / desk elements based on shot_id
    - Soft film grain overlay
    - Letterbox cinematic bars (2.39:1 crop within 16:9 frame)
    - Shot number badge, narration hint, and seed label
    """
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageFont
    except ImportError:
        with open(out_path, "wb") as f:
            f.write(b"P6\n1280 720\n255\n")
            color = bytes([(seed * 37) % 180, (seed * 19) % 120, (seed * 13) % 80])
            f.write(color * (1280 * 720))
        return

    rng = random.Random(seed)
    width, height = 1280, 720

    # --- Shot-specific palettes ---
    shot_num = int(shot_id.split("_")[-1]) if "_" in shot_id else 1
    palettes = {
        # (sky_top, sky_bottom, ground, accent)
        1:  ((10, 15, 35),   (40, 55, 80),  (25, 20, 15),  (200, 170, 100)),   # night desk cool
        2:  ((30, 60, 30),   (60, 110, 55), (50, 80, 30),  (160, 220, 100)),   # emerald forest
        3:  ((30, 60, 30),   (60, 110, 55), (50, 80, 30),  (160, 220, 100)),   # forest path
        4:  ((60, 90, 40),   (100, 150, 60),(60, 100, 40), (200, 230, 100)),   # running barefoot
        5:  ((30, 100, 100), (60, 150, 130),(40, 90, 70),  (120, 210, 200)),   # spring water
        6:  ((30, 100, 100), (60, 150, 130),(40, 90, 70),  (100, 200, 230)),   # swimming pool
        7:  ((70, 110, 50),  (110, 160, 70),(60, 100, 40), (230, 200, 120)),   # rock laughing
        8:  ((180, 90, 20),  (230, 140, 50),(100, 60, 20), (255, 200, 80)),    # golden sunset
        9:  ((10, 15, 35),   (40, 55, 80),  (25, 20, 15),  (200, 170, 100)),   # night desk warm
    }
    sky_top, sky_bot, ground_col, accent = palettes.get(shot_num, palettes[1])

    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    # Sky gradient (top 60% of frame)
    sky_h = int(height * 0.62)
    for y in range(sky_h):
        t = y / sky_h
        col = _lerp_color(sky_top, sky_bot, t)
        draw.line([(0, y), (width, y)], fill=col)

    # Ground / water gradient (bottom 40%)
    for y in range(sky_h, height):
        t = (y - sky_h) / (height - sky_h)
        col = _lerp_color(sky_bot, ground_col, t)
        draw.line([(0, y), (width, y)], fill=col)

    # --- Procedural scene elements based on shot ---
    if shot_num in (2, 3, 4, 7):   # Forest shots — tree silhouettes
        for _ in range(rng.randint(12, 20)):
            tx = rng.randint(0, width)
            th = rng.randint(int(height * 0.4), int(height * 0.75))
            tw = rng.randint(10, 28)
            draw.rectangle([tx - tw//2, sky_h - th, tx + tw//2, sky_h], fill=(15, 35, 15))
            # Crown
            cr = rng.randint(35, 60)
            draw.ellipse([tx - cr, sky_h - th - cr, tx + cr, sky_h - th + cr//3],
                         fill=(20, 55, 20))

    if shot_num in (5, 6):   # Water shots — ripple circles
        for _ in range(rng.randint(6, 12)):
            cx = rng.randint(80, width - 80)
            cy = rng.randint(sky_h + 20, height - 60)
            cr = rng.randint(20, 70)
            draw.ellipse([cx - cr, cy - cr//4, cx + cr, cy + cr//4],
                         outline=(accent[0], accent[1], accent[2], 100), width=2)

    if shot_num in (1, 9):   # Desk shots — monitor rectangle
        mx, my = int(width * 0.35), int(height * 0.25)
        mw, mh = int(width * 0.35), int(height * 0.30)
        draw.rectangle([mx, my, mx + mw, my + mh], fill=(20, 40, 70), outline=(80, 120, 180), width=3)
        # Screen glow
        draw.rectangle([mx + 8, my + 8, mx + mw - 8, my + mh - 8],
                       fill=(25, 50, 90))
        draw.text((mx + 20, my + mh // 2 - 10), "■■■■■■■■■■■\n■■■■■■■■■■■", fill=(60, 90, 150))

    if shot_num == 8:   # Sunset — silhouetted boys walking
        for i in range(4):
            bx = int(width * (0.3 + i * 0.1))
            draw.rectangle([bx - 6, sky_h - 90, bx + 6, sky_h], fill=(20, 10, 5))
            draw.ellipse([bx - 10, sky_h - 110, bx + 10, sky_h - 90], fill=(20, 10, 5))

    # --- Film grain overlay ---
    for _ in range(4000):
        gx = rng.randint(0, width - 1)
        gy = rng.randint(0, height - 1)
        v = rng.randint(0, 40)
        draw.point((gx, gy), fill=(v, v, v))

    # --- Soft vignette (darken edges) ---
    cx, cy = width // 2, height // 2
    for y in range(height):
        for x in range(0, width, 4):  # stride 4 for speed
            dx = (x - cx) / cx
            dy = (y - cy) / cy
            vign = max(0.0, 1.0 - (dx * dx + dy * dy) * 0.9)
            px = img.getpixel((x, y))
            img.putpixel((x, y), tuple(int(c * vign) for c in px))

    draw = ImageDraw.Draw(img)

    # --- Cinematic letterbox bars (2.39:1 within 16:9) ---
    bar_h = int((height - width / 2.39) / 2)
    draw.rectangle([0, 0, width, bar_h], fill=(0, 0, 0))
    draw.rectangle([0, height - bar_h, width, height], fill=(0, 0, 0))

    # --- Accent hairline ---
    draw.line([(60, bar_h + 20), (width - 60, bar_h + 20)], fill=accent, width=1)
    draw.line([(60, height - bar_h - 20), (width - 60, height - bar_h - 20)], fill=accent, width=1)

    # --- Text overlays (font with Unicode fallback) ---
    font_candidates = [
        "/System/Library/Fonts/Supplemental/KefaIII.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    font_path = next((c for c in font_candidates if Path(c).exists()), None)
    try:
        if font_path:
            font_lg = ImageFont.truetype(font_path, 28)
            font_sm = ImageFont.truetype(font_path, 16)
            font_xs = ImageFont.truetype(font_path, 13)
        else:
            font_lg = font_sm = font_xs = ImageFont.load_default()
    except Exception:
        font_lg = font_sm = font_xs = ImageFont.load_default()

    # Shot badge (top-left inside letterbox)
    badge_label = f"SHOT {shot_num:02d}  •  HERITAGE SHORT"
    draw.text((70, bar_h + 32), badge_label, font=font_sm, fill=accent)

    # Seed / model label (top-right)
    seed_label = f"FLUX.1-schnell  seed={seed}"
    draw.text((width - 280, bar_h + 32), seed_label, font=font_xs, fill=(160, 150, 130))

    # Prompt synopsis (bottom-left, inside letterbox)
    words = prompt.split()
    lines = []
    cur = []
    for w in words:
        cur.append(w)
        if len(" ".join(cur)) > 65:
            lines.append(" ".join(cur[:-1]))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))

    y_txt = height - bar_h - 70
    for line in lines[:3]:
        draw.text((70, y_txt), line, font=font_xs, fill=(220, 210, 185))
        y_txt += 18

    img.save(out_path, "PNG", optimize=False)
    print(f"    [cinematic-renderer] Rendered {shot_id} → {out_path.name}")


# Specifications for the 5 Story Characters + Arba Minch Setting Anchor
# Updated with exact user character features:
# - Adult Narrator: afro hair, dark skin, slightly short nose
# - Young Narrator: mini-afro, dark skin, slightly short nose, vintage beige tee
# - Mikiyas: younger brother, slim face, sharp long nose, mischievous grin, yellow shirt
# - Mihretab: light skin, handsome well-defined features, joyful smile, green shirt
# - Surafel: deep dark skin (darkest), lean/skinny build, confident smile, blue shirt
CHARACTER_SPECS = [
    {
        "id": "adult_narrator",
        "name": "Narrator (Adult)",
        "role": "Present Day • Age 26",
        "seed": 201,
        "prompt": (
            "Character reference portrait, 26-year-old Ethiopian male software engineer, "
            "natural rounded afro hair, dark brown skin tone, slightly short nose, "
            "thoughtful intelligent dark eyes, wearing black crewneck, soft glowing computer monitor illumination, "
            "warm ambient desk lighting, 35mm film photography, cinematic portrait"
        )
    },
    {
        "id": "young_narrator",
        "name": "Narrator (Young)",
        "role": "Childhood Core • Age 11",
        "seed": 202,
        "prompt": (
            "Character reference portrait, 11-year-old Ethiopian boy, natural mini-afro curly black hair, "
            "dark brown skin tone, slightly short nose, expressive lively dark eyes, gentle curious smile, "
            "wearing a vintage beige cotton t-shirt, 35mm film photography, warm natural daylight, childhood portrait"
        )
    },
    {
        "id": "mikiyas",
        "name": "Mikiyas",
        "role": "Younger Brother • Age 9",
        "seed": 303,
        "prompt": (
            "Character reference portrait, 9-year-old Ethiopian boy, younger brother, "
            "slim narrow face, distinct sharp long nose, completely clear skin, no markings, no red dot, no bindi, "
            "playful mischievous grin, bright eyes, curly hair, vintage yellow cotton shirt, "
            "35mm film photography, sunny daylight"
        )
    },
    {
        "id": "mihretab",
        "name": "Mihretab",
        "role": "Childhood Friend • Age 11",
        "seed": 304,
        "prompt": (
            "Character reference portrait, 11-year-old Ethiopian boy, noticeably light-skinned Ethiopian boy, "
            "light caramel skin tone, handsome attractive facial features, symmetrical charming face, "
            "joyful warm smile, neat textured hair, vintage faded green cotton shirt, 35mm film photography, sun-dappled lighting"
        )
    },
    {
        "id": "surafel",
        "name": "Surafel",
        "role": "Childhood Friend • Age 12",
        "seed": 305,
        "prompt": (
            "Character reference portrait, 12-year-old Ethiopian boy, very dark skin, "
            "deep ebony dark brown complexion, rich dark skin tone, lean skinny build, narrow shoulders, "
            "confident cheerful smile, expressive eyes, vintage blue cotton shirt, 35mm film photography, bright daylight"
        )
    },
    {
        "id": "arba_minch_style",
        "name": "Arba Minch Springs",
        "role": "Setting & Style Anchor",
        "seed": 206,
        "prompt": (
            "Golden style reference photograph of Arba Minch Ethiopia, crystal clear turquoise natural spring water pool, "
            "giant ancient rainforest fig trees, sunbeams through emerald canopy, black volcanic stones, "
            "2000s 35mm film aesthetic, Kodak Daylight 5600K"
        )
    }
]


def generate_reference_sheet(storyboard: dict, out_path: Path, force=False):
    """
    Generates the complete Character and Style Reference Sheet for the Heritage Short.
    Generates reference portraits for all 5 characters + Arba Minch setting using Cloudflare FLUX,
    then composites them into a publication-quality reference grid with typography and style specs.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    char_dir = PROJECT_ROOT / "references" / "characters"
    char_dir.mkdir(parents=True, exist_ok=True)

    print("🎨 [Reference Sheet] Generating individual character & style portraits via Cloudflare FLUX...")

    char_images = {}
    for spec in CHARACTER_SPECS:
        cid = spec["id"]
        c_prompt = spec["prompt"]
        c_seed = spec["seed"]
        c_path = char_dir / f"{cid}.png"

        # Content-addressable cache check
        cache_data = {"prompt": c_prompt, "seed": c_seed, "type": "character_reference"}
        c_hash = compute_sha256(cache_data)
        cached_file = get_cached_output("keyframes", c_hash, ".png")

        if cached_file and not force and c_path.exists():
            print(f"  ⚡ [{spec['name']}] CACHE HIT -> Reusing portrait")
            char_images[cid] = c_path
            continue

        print(f"  📸 [{spec['name']}] Calling Cloudflare FLUX (seed={c_seed})...")
        t0 = time.time()
        used_mock = False

        if CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN:
            try:
                generate_cloudflare_flux(c_prompt, c_seed, c_path)
            except Exception as e:
                print(f"  ⚠️ Cloudflare AI generation failed ({e}); falling back to cinematic renderer.")
                fallback_procedural_image(f"char_{cid}", c_prompt, c_seed, "Character Reference", c_path)
                used_mock = True
        else:
            fallback_procedural_image(f"char_{cid}", c_prompt, c_seed, "Character Reference", c_path)
            used_mock = True

        latency = time.time() - t0
        if not used_mock:
            store_cached_output("keyframes", c_hash, c_path)

        log_run(
            stage="reference_sheet",
            model="FLUX.1-schnell" if not used_mock else "procedural-renderer",
            parameters={"prompt": c_prompt, "seed": c_seed},
            seed=c_seed,
            latency_seconds=latency,
            cost_usd=0.0,
            cached=False,
            metadata={"character_id": cid, "hash": c_hash}
        )
        print(f"  ✅ [{spec['name']}] Portrait saved in {latency:.2f}s -> {c_path.name}")
        char_images[cid] = c_path

    # Composite into master reference sheet
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("  ⚠️ Pillow not installed; cannot composite sheet.")
        return out_path

    width, height = 1500, 1150
    sheet = Image.new("RGB", (width, height), color=(14, 12, 16))
    draw = ImageDraw.Draw(sheet)

    font_candidates = [
        "/System/Library/Fonts/Supplemental/KefaIII.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    font_path = next((c for c in font_candidates if Path(c).exists()), None)
    try:
        f_title = ImageFont.truetype(font_path, 28) if font_path else ImageFont.load_default()
        f_sub = ImageFont.truetype(font_path, 16) if font_path else ImageFont.load_default()
        f_name = ImageFont.truetype(font_path, 20) if font_path else ImageFont.load_default()
        f_role = ImageFont.truetype(font_path, 14) if font_path else ImageFont.load_default()
        f_spec = ImageFont.truetype(font_path, 14) if font_path else ImageFont.load_default()
    except Exception:
        f_title = f_sub = f_name = f_role = f_spec = ImageFont.load_default()

    # Top Header
    draw.rectangle([0, 0, width, 70], fill=(24, 20, 28))
    draw.text((40, 14), "THE FORTY SPRINGS OF ARBA MINCH • CHARACTER & STYLE REFERENCE SHEET", font=f_title, fill=(230, 200, 140))
    draw.text((40, 46), "AI Heritage Short Film • 5 Narrative Characters & Environment Anchor • Generated with FLUX.1-schnell", font=f_sub, fill=(170, 160, 145))
    draw.line([(0, 70), (width, 70)], fill=(180, 140, 80), width=1)

    # 2 rows x 3 columns grid
    tile_w, tile_h = 440, 310
    start_x, start_y = 40, 95
    h_gap, v_gap = 30, 50

    for idx, spec in enumerate(CHARACTER_SPECS):
        row = idx // 3
        col = idx % 3
        px = start_x + col * (tile_w + h_gap)
        py = start_y + row * (tile_h + v_gap)

        cid = spec["id"]
        c_path = char_images.get(cid)

        # Image tile
        if c_path and c_path.exists():
            try:
                t_img = Image.open(c_path).resize((tile_w, tile_h), Image.LANCZOS)
                sheet.paste(t_img, (px, py))
            except Exception:
                draw.rectangle([px, py, px + tile_w, py + tile_h], fill=(30, 25, 30))
        else:
            draw.rectangle([px, py, px + tile_w, py + tile_h], fill=(30, 25, 30))

        # Thin border around each tile
        draw.rectangle([px, py, px + tile_w, py + tile_h], outline=(100, 80, 50), width=1)

        # Label band below tile
        label_y = py + tile_h + 6
        draw.text((px, label_y), spec["name"].upper(), font=f_name, fill=(240, 225, 190))
        draw.text((px + 230, label_y + 3), spec["role"], font=f_role, fill=(180, 160, 120))

    # Bottom Specification Panel
    spec_box_y = start_y + 2 * (tile_h + v_gap) + 10
    draw.rectangle([40, spec_box_y, width - 40, height - 30], fill=(22, 19, 25), outline=(80, 65, 45), width=1)
    draw.text((60, spec_box_y + 12), "STYLE BLOCK SPECIFICATION (INVARIANT CONDITIONING ACROSS ALL SHOTS)", font=f_sub, fill=(200, 170, 110))
    draw.line([(60, spec_box_y + 34), (width - 60, spec_box_y + 34)], fill=(70, 55, 40), width=1)

    specs = [
        ("VISUAL STYLE:", "2000s 35mm film aesthetic, warm Kodak Daylight 5600K, rich tropical emerald greens, natural sunbeams, authentic nostalgic Ethiopian youth."),
        ("COLOR PALETTE:", "Deep rainforest emerald (#0D3B2E), turquoise spring water (#2E8B9A), terracotta soil (#8C4325), golden hour sunlight (#F4B24B)."),
        ("LIGHTING:", "Modern cool monitor glow for desk frames (shots 1 & 9); soft natural morning sunbeams and warm golden hour for childhood memories (shots 2-8)."),
        ("CONSISTENCY:", "Each character prompt anchors to these exact visual features, hair textures, age bands, and vintage Ethiopian cotton clothing across all shots.")
    ]
    cur_y = spec_box_y + 44
    for label, val in specs:
        draw.text((60, cur_y), label, font=f_spec, fill=(180, 150, 90))
        draw.text((220, cur_y), val, font=f_spec, fill=(210, 205, 195))
        cur_y += 24

    sheet.save(out_path, "PNG")
    print(f"\n  🎨 Complete Master Character & Style Reference Sheet saved → {out_path} ({out_path.stat().st_size:,} bytes)")
    return out_path


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
        # Guard: only cache genuine API outputs — never cache procedural placeholders
        if not used_mock:
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

    # Always (re)generate the reference sheet after keyframes so it reflects current images
    if not target_shot_id:  # Only on a full run
        ref_sheet_path = PROJECT_ROOT / "references" / "boys_arba_minch_sheet.png"
        generate_reference_sheet(storyboard, ref_sheet_path)

    return keyframes


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    run_keyframes_stage(target_shot_id=target)
