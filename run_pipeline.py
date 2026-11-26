#!/usr/bin/env python3
"""
Orchestrator for The Heritage Short AI Video Pipeline
Usage:
    python3 run_pipeline.py --stage all           # Execute end-to-end pipeline
    python3 run_pipeline.py --stage radio-cut     # Execute Phase 1 radio cut deliverable
    python3 run_pipeline.py --stage shots --shot shot_03  # Live shot regeneration demo!
    python3 run_pipeline.py --stage validate      # Storyboard schema validation
"""

import sys
import argparse
from pathlib import Path

# Add pipeline directory to sys.path
pipeline_dir = Path(__file__).resolve().parent / "pipeline"
sys.path.insert(0, str(pipeline_dir))

from stage1_validate import validate_storyboard
from stage2_narration import run_narration_stage
from stage3_keyframes import run_keyframes_stage, generate_reference_sheet
from stage4_shots import run_shots_stage
from stage5_music import run_music_stage
from stage6_assemble import run_assemble_stage


def main():
    parser = argparse.ArgumentParser(description="The Heritage Short AI Production Pipeline")
    parser.add_argument(
        "--stage",
        choices=["validate", "narration", "keyframes", "reference-sheet", "shots", "music", "assemble", "radio-cut", "film", "all"],
        default="all",
        help="Pipeline stage to execute (default: all)"
    )
    parser.add_argument(
        "--shot",
        type=str,
        default=None,
        help="Optional specific shot_id to generate or regenerate (e.g. shot_03)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass cache and force regeneration"
    )

    args = parser.parse_args()

    print("================================================================================")
    print(" AI-Content Generation: The Heritage Short Pipeline")
    print(f" Stage: {args.stage} | Target Shot: {args.shot or 'All'} | Force: {args.force}")
    print("================================================================================\n")

    if args.stage in ["validate", "all"]:
        validate_storyboard()

    if args.stage in ["narration", "all", "radio-cut"]:
        run_narration_stage(target_shot_id=args.shot, force_regenerate=args.force)

    if args.stage in ["keyframes", "all"]:
        run_keyframes_stage(target_shot_id=args.shot, force_regenerate=args.force)

    if args.stage == "reference-sheet":
        from stage3_keyframes import generate_reference_sheet
        from common import load_storyboard, PROJECT_ROOT
        sb = load_storyboard()
        ref_path = PROJECT_ROOT / "references" / "boys_arba_minch_sheet.png"
        generate_reference_sheet(sb, ref_path, force=args.force)

    if args.stage in ["shots", "all", "film"]:
        run_shots_stage(target_shot_id=args.shot, force_regenerate=args.force)

    if args.stage in ["music", "all", "radio-cut", "film"]:
        run_music_stage(force_regenerate=args.force)

    if args.stage == "radio-cut":
        run_assemble_stage(radio_cut_only=True)
    elif args.stage in ["assemble", "all", "film"]:
        run_assemble_stage(radio_cut_only=False)

    print("================================================================================")
    print("✨ Pipeline execution complete! Inspect outputs in outputs/ directory.")
    print("📋 Execution log updated: runs.jsonl")
    print("================================================================================\n")


if __name__ == "__main__":
    main()
