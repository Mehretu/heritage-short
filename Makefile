.PHONY: all film radio-cut keyframes reference-sheet shots assemble validate clean test smoke-test play help

PYTHON ?= python3

all: film

help:
	@echo "AI-Content Generation: The Heritage Short Makefile"
	@echo "--------------------------------------------------"
	@echo "  make                 : Run complete pipeline and export 16:9 & 9:16 films"
	@echo "  make film            : Run complete pipeline and export 16:9 & 9:16 films"
	@echo "  make play            : Play exported 16:9 and 9:16 films in default player"
	@echo "  make shots           : Ken Burns animated shots (16:9 & 9:16) from keyframes"
	@echo "  make assemble        : Assemble final films with ducked audio and subtitles"
	@echo "  make radio-cut       : Generate narration & score radio cut prototype (Phase 1)"
	@echo "  make keyframes       : Generate all 9 keyframe stills via Cloudflare FLUX"
	@echo "  make reference-sheet : Composite character & style reference sheet PNG"
	@echo "  make validate        : Validate storyboard.json against JSON Schema"
	@echo "  make smoke-test      : Run Phase 1 Step 1 provider latency smoke test"
	@echo "  make clean           : Clear generated temporary outputs"

smoke-test:
	$(PYTHON) pipeline/smoke_test.py

keyframes:
	$(PYTHON) run_pipeline.py --stage keyframes

reference-sheet:
	$(PYTHON) run_pipeline.py --stage reference-sheet

shots:
	$(PYTHON) run_pipeline.py --stage shots

assemble:
	$(PYTHON) run_pipeline.py --stage assemble

film:
	$(PYTHON) run_pipeline.py --stage all

radio-cut:
	$(PYTHON) run_pipeline.py --stage radio-cut

validate:
	$(PYTHON) run_pipeline.py --stage validate

play:
	open outputs/exports/heritage_short_16x9.mp4
	open outputs/exports/heritage_short_9x16.mp4

test: validate
	$(PYTHON) run_pipeline.py --stage shots --shot shot_01

clean:
	rm -rf outputs/cache outputs/exports/* outputs/audio/* outputs/keyframes/* outputs/shots/* outputs/music/*
