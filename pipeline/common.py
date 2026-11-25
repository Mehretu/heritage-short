"""
Common utilities for The Heritage Short AI Pipeline:
- Centralized runs.jsonl logging (model, parameters, seed, latency, cost, timestamp)
- SHA-256 caching per stage to prevent redundant generations
- Exponential backoff retry decorators
- Storyboard loaders and environment config
"""

from __future__ import annotations
import os
import json
import time
import hashlib
import functools
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Union

# Resolve project base directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
CACHE_DIR = OUTPUTS_DIR / "cache"
RUNS_LOG_PATH = PROJECT_ROOT / "runs.jsonl"

CACHE_DIR.mkdir(parents=True, exist_ok=True)
for sub in ["keyframes", "shots", "audio", "music", "exports"]:
    (OUTPUTS_DIR / sub).mkdir(parents=True, exist_ok=True)


def load_storyboard(storyboard_path=None):
    """Load and parse storyboard.json."""
    path = Path(storyboard_path or (PROJECT_ROOT / "storyboard.json"))
    if not path.exists():
        raise FileNotFoundError(f"Storyboard not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_sha256(data) -> str:
    """Compute deterministic SHA-256 hex digest for any serializable object or string."""
    if isinstance(data, (dict, list)):
        payload = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    elif isinstance(data, str):
        payload = data.encode("utf-8")
    elif isinstance(data, bytes):
        payload = data
    else:
        payload = str(data).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def log_run(
    stage: str,
    model: str,
    parameters: dict,
    seed: int,
    latency_seconds: float,
    cost_usd: float = 0.0,
    cached: bool = False,
    metadata: dict = None
):
    """
    Log an entry to runs.jsonl conforming to the challenge grading specification:
    (model, parameters, seed, latency, cost)
    """
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "stage": stage,
        "model": model,
        "seed": seed,
        "parameters": parameters,
        "latency_seconds": round(latency_seconds, 3),
        "cost_usd": round(cost_usd, 6),
        "cached": cached,
        "metadata": metadata or {}
    }

    with open(RUNS_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def get_cached_output(stage: str, input_hash: str, output_suffix: str) -> Path | None:
    """Check if cached artifact exists for the given stage and input hash."""
    stage_cache_dir = CACHE_DIR / stage
    stage_cache_dir.mkdir(parents=True, exist_ok=True)
    candidate = stage_cache_dir / f"{input_hash}{output_suffix}"
    if candidate.exists() and candidate.stat().st_size > 0:
        return candidate
    return None


def store_cached_output(stage: str, input_hash: str, source_path: Path) -> Path:
    """Store generated file into stage cache."""
    stage_cache_dir = CACHE_DIR / stage
    stage_cache_dir.mkdir(parents=True, exist_ok=True)
    target = stage_cache_dir / f"{input_hash}{source_path.suffix}"
    if source_path != target:
        import shutil
        shutil.copy2(source_path, target)
    return target


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, exceptions=(Exception,)):
    """Retry decorator with exponential backoff for external API calls."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_exc = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt == max_retries:
                        break
                    print(f"⚠️ [Attempt {attempt}/{max_retries}] {func.__name__} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2
            raise last_exc
        return wrapper
    return decorator
