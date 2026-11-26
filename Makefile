.PHONY: all film radio-cut keyframes reference-sheet shots validate clean test smoke-test help

PYTHON ?= python3

help:
	@echo "AI-Content Generation: The Heritage Short Makefile"
	@echo "--------------------------------------------------"
	@echo "  make smoke-test      : Run Phase 1 Step 1 provider latency smoke test"
	@echo "  make keyframes       : Generate all 9 keyframe stills via Cloudflare FLUX"
	@echo "  make reference-sheet : Composite character & style reference sheet PNG"
	@echo "  make shots           : Ken Burns animated shots from keyframes"
	@echo "  make film            : Run complete pipeline and export 16:9 & 9:16 films"
	@echo "  make radio-cut       : Generate narration & score radio cut prototype (Phase 1)"
	@echo "  make validate        : Validate storyboard.json against JSON Schema"
	@echo "  make test            : Run smoke test across pipeline components"
	@echo "  make clean           : Clear generated temporary outputs"

all: film

smoke-test:
	$(PYTHON) pipeline/smoke_test.py

keyframes:
	$(PYTHON) run_pipeline.py --stage keyframes

reference-sheet:
	$(PYTHON) run_pipeline.py --stage reference-sheet

shots:
	$(PYTHON) run_pipeline.py --stage shots

film:
	$(PYTHON) run_pipeline.py --stage all

radio-cut:
	$(PYTHON) run_pipeline.py --stage radio-cut

validate:
	$(PYTHON) run_pipeline.py --stage validate

test: validate
	$(PYTHON) run_pipeline.py --stage shots --shot shot_01

clean:
	rm -rf outputs/cache outputs/exports/* outputs/audio/* outputs/keyframes/* outputs/shots/* outputs/music/*
