import json
import subprocess
import sys
from threading import Lock
from uuid import uuid4

from reservation_app.model_store import MODEL_VERSIONS, PROJECT_ROOT


class TrainingInProgress(Exception):
    pass


class TrainingJobs:
    def __init__(self):
        self._lock = Lock()
        self._process = None
        self._job_id = None

    def start(self, refresh_data: bool) -> dict:
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                raise TrainingInProgress()

            job_id = uuid4().hex
            logs = MODEL_VERSIONS / "job_logs"
            logs.mkdir(parents=True, exist_ok=True)

            command = [
                sys.executable,
                "-B",
                "-u",
                "-m",
                "reservation_app.training",
                "--job-id",
                job_id,
            ]

            if refresh_data:
                command.append("--refresh-data")

            with (logs / f"{job_id}.log").open("wb") as log:
                process = subprocess.Popen(
                    command,
                    cwd=PROJECT_ROOT,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )

            self._process = process
            self._job_id = job_id

            return {"state": "running", "job_id": job_id}

    def status(self) -> dict:
        with self._lock:
            if self._process is None:
                return {"state": "idle"}

            job_id = self._job_id
            code = self._process.poll()

            if code is None:
                return {"state": "running", "job_id": job_id}

            if code != 0:
                return {
                    "state": "failed",
                    "job_id": job_id,
                    "message": (
                        f"Training exited with code {code}. "
                        f"Check job_logs/{job_id}.log."
                    ),
                }

            path = MODEL_VERSIONS / job_id / "metrics.json"

            try:
                report = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                return {
                    "state": "failed",
                    "job_id": job_id,
                    "message": (
                        "Training exited successfully, but its report "
                        "could not be read."
                    ),
                }

            return {"state": "succeeded", "job_id": job_id, "report": report}
