"""
Wan 2.2 / Wan 2.1 Image-to-Video Batch Runner for Kaggle
Designed for Kaggle 2x T4 or P100 GPU (30 hours/week free tier).
Generates animated MP4 video clips conditioned on shot keyframes from FLUX.
Outputs are saved into wan_drops/ for automatic pipeline ingestion.
"""

import os
import sys
import numpy as np
import torch
from pathlib import Path
from PIL import Image

# 1. Hardware Verification
print("=== Hardware Verification ===")
device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.bfloat16 if (torch.cuda.is_available() and torch.cuda.is_bf16_supported()) else torch.float16
print(f"🖥️ Execution device: {device} ({dtype})")
if torch.cuda.is_available():
    print(f"✅ GPU Available: {torch.cuda.get_device_name(0)}")
    print(f"✅ VRAM: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.1f} GB")
else:
    print("⚠️ No CUDA GPU detected. Running on CPU mode.")

# 2. Output directory setup
OUTPUT_DIR = Path("wan_drops")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 3. Shot Motion Manifest from storyboard.json
SHOTS_MANIFEST = [
    {
        "shot_id": "shot_01",
        "image_file": "shot_01.png",
        "motion_prompt": "Slow subtle push-in toward the narrator's thoughtful face, gentle computer monitor flicker, slight eye blink, cinematic camera motion",
        "seed": 2011,
        "duration": 6.0
    },
    {
        "shot_id": "shot_02",
        "image_file": "shot_02.png",
        "motion_prompt": "Expansive slow aerial drift over the lush emerald rainforest canopy of Arba Minch, morning mist gently dissipating, golden sunbeams slicing through trees",
        "seed": 2021,
        "duration": 6.5
    },
    {
        "shot_id": "shot_03",
        "image_file": "shot_03.png",
        "motion_prompt": "Subtle handheld camera motion, boys whispering conspiratorially, looking over shoulders, playful natural expressions",
        "seed": 2031,
        "duration": 9.0
    },
    {
        "shot_id": "shot_04",
        "image_file": "shot_04.png",
        "motion_prompt": "Forward tracking shot following the four barefoot boys running joyfully down the sun-dappled dirt path into the dense forest, dynamic kinetic movement",
        "seed": 2041,
        "duration": 8.0
    },
    {
        "shot_id": "shot_05",
        "image_file": "shot_05.png",
        "motion_prompt": "Gentle slow vertical drift following crystal-clear spring water bubbling continuously up through volcanic pebbles and sand, sparkling sunlight refractions",
        "seed": 2051,
        "duration": 7.5
    },
    {
        "shot_id": "shot_06",
        "image_file": "shot_06.png",
        "motion_prompt": "Slow-motion side tracking along the surface of the emerald natural pool, four boys splashing and swimming, water droplets glinting in sunlight",
        "seed": 2061,
        "duration": 6.0
    },
    {
        "shot_id": "shot_07",
        "image_file": "shot_07.png",
        "motion_prompt": "Slow gentle arc around the two boys seated on the warm mossy rock, sharing a laugh, natural head turns and joyful smiles",
        "seed": 2071,
        "duration": 10.5
    },
    {
        "shot_id": "shot_08",
        "image_file": "shot_08.png",
        "motion_prompt": "Slow pull-back camera following the four boys' silhouettes walking away along the earthen trail at golden sunset, lengthening shadows",
        "seed": 2081,
        "duration": 8.5
    },
    {
        "shot_id": "shot_09",
        "image_file": "shot_09.png",
        "motion_prompt": "Very slow gentle push-in toward the adult narrator smiling serenely at his desk, soft warm light fading gently",
        "seed": 2091,
        "duration": 7.5
    }
]

# 4. Model Loading with Diffusers
pipe = None
try:
    from diffusers import WanImageToVideoPipeline
    from diffusers.utils import export_to_video

    model_id = "Wan-AI/Wan2.1-I2V-14B-480P-Diffusers"
    print(f"⏳ Attempting to load {model_id} with CPU offload...")
    pipe = WanImageToVideoPipeline.from_pretrained(model_id, torch_dtype=dtype)
    pipe.enable_model_cpu_offload()
    print("✅ WanImageToVideoPipeline loaded successfully!")
except Exception as e:
    print(f"⚠️ Could not initialize Wan 14B pipeline ({e}).")
    print("ℹ️ Falling back to cinematic Ken Burns camera motion.")

# 5. Batch Generation Loop
for shot in SHOTS_MANIFEST:
    sid = shot["shot_id"]
    out_file = OUTPUT_DIR / f"{sid}.mp4"
    if out_file.exists() and out_file.stat().st_size > 1000:
        print(f"⚡ [{sid}] Already generated, skipping.")
        continue

    img_path = Path(shot["image_file"])
    if not img_path.exists():
        print(f"⚠️ [{sid}] Input keyframe {img_path} not found, skipping.")
        continue

    print(f"🎬 Processing {sid}: {shot['motion_prompt'][:55]}...")
    img = Image.open(img_path).convert("RGB")

    if pipe is not None:
        try:
            max_area = 832 * 480
            aspect = img.height / img.width
            h = round(np.sqrt(max_area * aspect)) // 16 * 16
            w = round(np.sqrt(max_area / aspect)) // 16 * 16
            resized_img = img.resize((w, h))

            gen = torch.Generator(device="cpu").manual_seed(shot["seed"])
            output = pipe(
                image=resized_img,
                prompt=shot["motion_prompt"],
                height=h,
                width=w,
                num_frames=81,
                guidance_scale=5.0,
                num_inference_steps=25,
                generator=gen
            ).frames[0]

            export_to_video(output, str(out_file), fps=16)
            print(f"✅ [{sid}] Wan 2.2 video saved -> {out_file}")
            continue
        except Exception as err:
            print(f"⚠️ [{sid}] Wan error: {err}. Using Ken Burns fallback.")

    # High quality Ken Burns fallback
    import imageio
    fps = 24
    duration = shot.get("duration", 5.0)
    total_frames = int(duration * fps)
    w_out, h_out = 1280, 720
    writer = imageio.get_writer(str(out_file), fps=fps, codec="libx264", quality=8)

    im_w, im_h = img.size
    for f_idx in range(total_frames):
        t = f_idx / total_frames
        zoom = 1.0 + 0.12 * t
        cw = int(im_w / zoom)
        ch = int(im_h / zoom)
        cx = int((im_w - cw) / 2)
        cy = int((im_h - ch) / 2)
        crop = img.crop((cx, cy, cx + cw, cy + ch)).resize((w_out, h_out), Image.Resampling.BILINEAR)
        writer.append_data(np.array(crop))
    writer.close()
    print(f"✅ [{sid}] Cinematic camera shot saved -> {out_file}")

print("🎉 Complete! Zipping wan_drops for download...")
os.system("zip -r wan_drops.zip wan_drops/")
print("📦 Done! Download wan_drops.zip and place files in outputs/wan_drops/")
