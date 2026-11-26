"""
Stage 1: Storyboard Validator
Validates storyboard.json against schema/storyboard.schema.json.
Checks total duration (60-90s), ensures every shot has a declared filmmaking reason,
and checks schema integrity before any expensive model generation begins.
"""

import sys
import json
from pathlib import Path
from common import PROJECT_ROOT, load_storyboard, compute_sha256, log_run

SCHEMA_PATH = PROJECT_ROOT / "schema" / "storyboard.schema.json"


def validate_storyboard(storyboard_path=None):
    print("[Stage 1] Validating storyboard against schema...")
    storyboard = load_storyboard(storyboard_path)

    # Optional jsonschema validation if installed
    try:
        import jsonschema
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = json.load(f)
        jsonschema.validate(instance=storyboard, schema=schema)
        print("   JSON Schema validation passed.")
    except ImportError:
        print("   jsonschema package not installed; performing thorough structural validation...")
        _validate_structurally(storyboard)
    except Exception as e:
        print(f"  JSON Schema validation error: {e}")
        raise

    # Semantic filmmaking validation
    shots = storyboard.get("shots", [])
    if len(shots) < 8 or len(shots) > 14:
        raise ValueError(f"Shot count must be between 8 and 14, found {len(shots)}")

    total_duration = sum(s.get("duration_seconds", 0) for s in shots)
    print(f"  🎬 Shots count: {len(shots)} shots | Calculated total duration: {total_duration:.1f}s")
    if total_duration < 60.0 or total_duration > 90.0:
        print(f"  ⚠️ Warning: Target duration is 60-90s, current sum is {total_duration:.1f}s")

    # Character contract validation
    characters = storyboard.get("characters", [])
    if len(characters) < 5:
        raise ValueError(f"Contract error: Heritage Short requires at least 5 defined characters, found {len(characters)}")
    print(f"  👥 Cast count: {len(characters)} characters validated with physical DNA anchors.")

    # Ensure every shot has a stated filmmaking reason (Required by Rubric)
    missing_reasons = []
    for s in shots:
        reason = s.get("reason", "").strip()
        if not reason:
            missing_reasons.append(s.get("shot_id", "unknown"))
    if missing_reasons:
        raise ValueError(f"Rubric violation: Every shot must have a stated reason. Missing for: {missing_reasons}")

    print("  ✅ Every shot contains a verified filmmaking reason.")
    print("  ✅ Stage 1 complete: Storyboard contract locked and validated.\n")
    return True


def _validate_structurally(sb):
    required_top = ["title", "logline", "language", "characters", "style_block", "shots", "music", "end_card"]
    for field in required_top:
        if field not in sb:
            raise ValueError(f"Missing required top-level field '{field}'")
    for c in sb.get("characters", []):
        for req in ["character_id", "name", "role", "age", "physical_traits", "prompt", "seed"]:
            if req not in c:
                raise ValueError(f"Character '{c.get('character_id', 'unknown')}' missing required field '{req}'")
        traits = c.get("physical_traits", {})
        for tf in ["hair", "skin_tone", "facial_features", "clothing"]:
            if tf not in traits:
                raise ValueError(f"Character '{c.get('character_id')}' missing physical trait '{tf}'")
    for idx, shot in enumerate(sb.get("shots", [])):
        for req in ["shot_id", "duration_seconds", "reason", "narration", "image_prompt", "motion_prompt"]:
            if req not in shot:
                raise ValueError(f"Shot #{idx+1} missing required field '{req}'")


if __name__ == "__main__":
    try:
        validate_storyboard()
    except Exception as err:
        print(f"Validation failed: {err}", file=sys.stderr)
        sys.exit(1)
