# backend/app/core/job_manager.py
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any

# -----------------------------------------------------------------------------
# In-memory job status table (kept for compatibility with existing imports)
# -----------------------------------------------------------------------------
job_statuses: Dict[str, Dict[str, Any]] = {}

# -----------------------------------------------------------------------------
# Job directories handling
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class JobDirs:
    """A simple container of per-job directories."""
    base: Path
    di_results: Path
    output: Path
    tmp: Path

def _resolve_data_root() -> Path:
    """
    Decide where to store job data.
    Priority:
      1) DATA_DIR env var (if set)
      2) '/data' (docker-compose mounts ./data:/data)
      3) '.data' (fallback)
    """
    env_dir = os.getenv("DATA_DIR")
    if env_dir:
        return Path(env_dir).resolve()
    # prefer /data inside containers when volume is mounted
    default_container_path = Path("/data")
    if default_container_path.exists():
        return default_container_path.resolve()
    # local fallback
    return Path(".data").resolve()

def get_job_dirs(job_id: str) -> JobDirs:
    """
    Ensure and return the set of directories used by a given job.

    Structure:
      <DATA_ROOT>/jobs/<job_id>/
        ├─ di_results/   # raw DI JSONs written by Document Intelligence step
        ├─ output/       # final artifacts (e.g. Excel summary)
        └─ tmp/          # any scratch/temporary files

    Returns:
      JobDirs with absolute Paths; all directories are guaranteed to exist.
    """
    data_root = _resolve_data_root()
    base = data_root / "jobs" / job_id
    di_results = base / "di_results"
    output = base / "output"
    tmp = base / "tmp"

    # create all directories if missing
    for p in (base, di_results, output, tmp):
        p.mkdir(parents=True, exist_ok=True)

    return JobDirs(base=base, di_results=di_results, output=output, tmp=tmp)
