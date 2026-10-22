"""Checkpoint and Progress Tracker for Talentra Bulk and Scaled Seeding."""

import os
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class CheckpointManager:
    """Manages resumable seed checkpoints and throughput metrics."""

    def __init__(self, checkpoint_file: str = "scratch/seed_checkpoint.json"):
        self.checkpoint_file = checkpoint_file
        self.state: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "last_completed_stage": None,
            "batches_completed": 0,
            "records_inserted": 0,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "status": "INITIALIZED",
        }

    def save(self):
        os.makedirs(os.path.dirname(self.checkpoint_file), exist_ok=True)
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        with open(self.checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)

    def record_batch(self, stage_name: str, count: int, batch_index: int):
        self.state["last_completed_stage"] = stage_name
        self.state["batches_completed"] += 1
        self.state["records_inserted"] += count
        self.state["status"] = "IN_PROGRESS"
        self.save()

    def mark_complete(self):
        self.state["status"] = "COMPLETED"
        self.save()

    def reset(self):
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
        self.state = {
            "last_completed_stage": None,
            "batches_completed": 0,
            "records_inserted": 0,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "status": "INITIALIZED",
        }


class SeedingTelemetry:
    """Measures batch throughput, latency, and memory metrics."""

    def __init__(self):
        self.start_time = time.perf_counter()
        self.total_rows = 0

    def update(self, rows_added: int) -> Dict[str, Any]:
        self.total_rows += rows_added
        elapsed = max(0.001, time.perf_counter() - self.start_time)
        rows_per_sec = self.total_rows / elapsed
        return {
            "total_rows": self.total_rows,
            "elapsed_seconds": round(elapsed, 2),
            "throughput_rows_per_second": round(rows_per_sec, 1),
        }
