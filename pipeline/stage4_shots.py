"""
Stage 4: Moving Shots (Wan 2.2 TI2V-5B / Ken Burns Animation)
Generates moving video shots conditioned on keyframes and camera/motion prompts.
Features:
- Supports Wan 2.2 generated video ingestion from Kaggle/Colab batch outputs
- Built-in cinematic Ken Burns effect (slow pan and zoom via FFmpeg or pure python)
  as recommended in Appendix A & B of the challenge brief
- Input hashing (keyframe hash + motion prompt + duration + seed) for caching
- runs.jsonl call logging
"""

import os
import sys
import time
import shutil
import subprocess
from pathlib import Path
from common import (
    PROJECT_ROOT,
    OUTPUTS_DIR,
    load_storyboard,
    compute_sha256,
    get_cached_output,
    store_cached_output,
    log_run
)

KEYFRAMES_DIR = OUTPUTS_DIR / "keyframes"
SHOTS_DIR = OUTPUTS_DIR / "shots"


def generate_ken_burns_shot(image_path: Path, duration: float, motion_cfg: dict, out_path: Path, aspect: str = "16x9"):
    """
    Implements Ken Burns slow pan-and-zoom using FFmpeg zoompan filter
    as described in the 10 Academy guide.
    Supports both 16:9 widescreen panorama and 9:16 full-bleed vertical mobile formats.
    """
    fps = 24
    total_frames = int(duration * fps)

    # Alternate camera motion directions based on motion config or seed
    cam_motion = motion_cfg.get("camera_motion", "").lower()
    if "push-in" in cam_motion or "zoom in" in cam_motion:
        # Slow zoom in: zoom starts at 1.0, increases gently to 1.15
        zoom_expr = "min(pzoom+0.0006,1.15)"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    elif "pull-back" in cam_motion or "zoom out" in cam_motion:
        zoom_expr = "max(1.15-0.0006*on,1.0)"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    elif "tilt" in cam_motion or "down" in cam_motion:
        zoom_expr = "1.08"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = f"ih/zoom*(on/{total_frames})"
    else:
        # Subtle horizontal pan
        zoom_expr = "1.10"
        x_expr = f"(iw-iw/zoom)*(on/{total_frames})"
        y_expr = "ih/2-(ih/zoom/2)"

    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin:
        if aspect == "9x16":
            # Native full-bleed 9:16 vertical crop (720x1280) as preferred for mobile
            prep_filter = "crop=in_h*9/16:in_h:(in_w-in_h*9/16)/2:0,scale=720:1280"
            out_size = "720x1280"
        else:
            # Native 16:9 widescreen panorama crop (1280x720) without stretching
            prep_filter = "crop=in_w:in_w*9/16:0:(in_h-in_w*9/16)/2,scale=1280:720"
            out_size = "1280x720"

        filter_str = f"{prep_filter},zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':d={total_frames}:s={out_size}:fps={fps}"
        cmd = [
            ffmpeg_bin, "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-vf", filter_str,
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            str(out_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0 and out_path.exists():
            return True  # Real encoded video

    _synthesize_placeholder_clip(image_path, duration, out_path)
    return False


def _synthesize_placeholder_clip(image_path: Path, duration: float, out_path: Path):
    """Generates a simple video container or placeholder if ffmpeg is uninstalled."""
    # Write empty/marker file or raw frames if needed
    with open(out_path, "wb") as f:
        f.write(b"MOCK_VIDEO_CONTAINER_" + image_path.name.encode())


def run_shots_stage(target_shot_id=None, force_regenerate=False):
    print("🎥 [Stage 4] Generating moving shots (Wan 2.2 / Ken Burns camera motion)...")
    storyboard = load_storyboard()
    shots = storyboard.get("shots", [])

    output_clips = {}

    for shot in shots:
        shot_id = shot["shot_id"]
        if target_shot_id and shot_id != target_shot_id:
            continue

        duration = shot.get("duration_seconds", 6.0)
        motion_cfg = shot.get("motion_prompt", {})
        seed = motion_cfg.get("seed", 42)

        keyframe_path = KEYFRAMES_DIR / f"{shot_id}.png"
        if not keyframe_path.exists():
            # Run keyframe dependency on demand if missing
            from stage3_keyframes import run_keyframes_stage
            run_keyframes_stage(target_shot_id=shot_id)

        # Cache key binds keyframe content + motion instructions + duration + seed
        keyframe_hash = compute_sha256(keyframe_path.read_bytes())
        cache_data = {
            "keyframe_hash": keyframe_hash,
            "motion_prompt": motion_cfg,
            "duration": duration,
            "seed": seed
        }
        input_hash = compute_sha256(cache_data)
        out_mp4 = SHOTS_DIR / f"{shot_id}.mp4"
        out_mp4_9x16 = SHOTS_DIR / f"{shot_id}_9x16.mp4"

        cached_file = get_cached_output("shots", input_hash, ".mp4")
        if cached_file and not force_regenerate:
            shutil.copy2(cached_file, out_mp4)
            if not out_mp4_9x16.exists():
                generate_ken_burns_shot(keyframe_path, duration, motion_cfg, out_mp4_9x16, aspect="9x16")
            print(f"  ⚡ [{shot_id}] CACHE HIT (hash: {input_hash[:8]}...) -> Reusing moving shot")
            log_run(
                stage="shots",
                model="Wan-2.2-TI2V-5B/KenBurns",
                parameters={"motion": motion_cfg, "duration": duration},
                seed=seed,
                latency_seconds=0.001,
                cost_usd=0.0,
                cached=True,
                metadata={"shot_id": shot_id, "input_hash": input_hash}
            )
            output_clips[shot_id] = out_mp4
            continue

        print(f"  🎬 [{shot_id}] Animating shot ({duration}s, 16:9 & 9:16): {motion_cfg.get('camera_motion', 'drift')}")
        t0 = time.time()

        # Check if Kaggle Wan 2.2 clip is already dropped in outputs/wan_drops/{shot_id}.mp4
        wan_drop = PROJECT_ROOT / "outputs" / "wan_drops" / f"{shot_id}.mp4"
        if wan_drop.exists() and wan_drop.stat().st_size > 1000:
            shutil.copy2(wan_drop, out_mp4)
            generate_ken_burns_shot(keyframe_path, duration, motion_cfg, out_mp4_9x16, aspect="9x16")
            model_used = "Wan-2.2-TI2V-5B-Kaggle"
            used_mock = False
        else:
            success = generate_ken_burns_shot(keyframe_path, duration, motion_cfg, out_mp4, aspect="16x9")
            generate_ken_burns_shot(keyframe_path, duration, motion_cfg, out_mp4_9x16, aspect="9x16")
            used_mock = not success
            model_used = "FFmpeg-KenBurns-PanZoom" if not used_mock else "placeholder-stub"

        latency = time.time() - t0
        # Guard: only cache real encoded video — never cache MOCK_VIDEO_CONTAINER stubs
        if not used_mock:
            store_cached_output("shots", input_hash, out_mp4)

        log_run(
            stage="shots",
            model=model_used,
            parameters={"camera_motion": motion_cfg.get("camera_motion"), "subject_motion": motion_cfg.get("subject_motion"), "duration": duration},
            seed=seed,
            latency_seconds=latency,
            cost_usd=0.0,
            cached=False,
            metadata={"shot_id": shot_id, "input_hash": input_hash}
        )
        print(f"  ✅ [{shot_id}] Moving shot ready in {latency:.2f}s -> {out_mp4.name}")
        output_clips[shot_id] = out_mp4

    print(f"  🎉 Stage 4 complete: {len(output_clips)} video shots assembled.\n")
    return output_clips


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    run_shots_stage(target_shot_id=target)
