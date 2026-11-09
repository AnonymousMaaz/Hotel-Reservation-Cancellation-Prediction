import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import get_args
from uuid import UUID, uuid4

import numpy as np
import pandas as pd
from mlflow import MlflowClient
from pydantic import ValidationError
from reservation_app.model_store import MODEL_VERSIONS, PROJECT_ROOT
from reservation_app.predictor import Booking, BookingPredictor

RAW_CSV = Path("artifacts/raw/raw.csv")
MODEL_FILE = Path("artifacts/models/lgbm_model.pkl")
MAPPING_FILE = Path("config/mapping.json")
PROCESSED_CSV = Path("artifacts/processed/processed.csv")
CHANNEL = "market_segment_type"


def run_existing_pipeline(
    workspace: Path,
    log_path: Path,
    refresh_data: bool,
):
    workspace.mkdir(parents=True)

    for name in ("config", "pipeline", "src", "utils"):
        shutil.copytree(
            PROJECT_ROOT / name,
            workspace / name,
            ignore=shutil.ignore_patterns("__pycache__", "mapping.json"),
        )

    if refresh_data:
        modules = ["pipeline.training_pipeline"]
    else:
        raw_file = workspace / RAW_CSV
        raw_file.parent.mkdir(parents=True)
        shutil.copy2(PROJECT_ROOT / RAW_CSV, raw_file)
        modules = ["src.data_preprocessing", "src.model_trainer"]

    with log_path.open("wb") as log:
        for module in modules:
            print(f"Running {module}. Log: {log_path}", flush=True)

            subprocess.run(
                [sys.executable, "-B", "-u", "-m", module],
                cwd=workspace,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=True,
            )


def check_candidate(workspace: Path):
    predictor = BookingPredictor(
        workspace / MODEL_FILE,
        workspace / MAPPING_FILE,
    )

    channels = get_args(Booking.model_fields[CHANNEL].annotation)

    if set(channels) != set(predictor.channel_codes):
        raise ValueError("The trained channel choices differ from the booking form.")

    if predictor.status_codes != {"Canceled": 0, "Not_Canceled": 1}:
        raise ValueError("The trained status codes differ from the desk's contract.")

    raw = pd.read_csv(workspace / RAW_CSV)
    raw = raw.drop(columns=["Booking_ID"]).drop_duplicates()

    expected = raw.loc[:, predictor.features].copy()
    expected[CHANNEL] = expected[CHANNEL].map(predictor.channel_codes)

    processed = pd.read_csv(
        workspace / PROCESSED_CSV,
        usecols=predictor.features,
    )
    processed = processed.loc[:, predictor.features]

    if expected.shape != processed.shape or not np.allclose(
        expected.to_numpy(dtype=float),
        processed.to_numpy(dtype=float),
        rtol=1e-9,
        atol=1e-12,
    ):
        raise ValueError(
            "Training transformed one or more selected features differently "
            "from the desk predictor. Review preprocessing before publishing."
        )

    for record in raw.loc[:, predictor.features].to_dict(orient="records"):
        try:
            booking = Booking.model_validate(record)
        except ValidationError:
            continue

        predictor.predict([booking])
        return

    raise ValueError("No valid booking was available for the prediction check.")


def read_run_report(workspace: Path) -> dict:
    database = workspace / "mlflow.db"

    if not database.is_file():
        raise ValueError("The pipeline did not produce its MLflow database.")

    client = MlflowClient(tracking_uri=f"sqlite:///{database.as_posix()}")
    experiment = client.get_experiment_by_name("Hotel_Reservation")

    if experiment is None:
        raise ValueError("The Hotel_Reservation MLflow experiment is missing.")

    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        filter_string="attributes.status = 'FINISHED'",
        max_results=1,
    )

    if not runs:
        raise ValueError("MLflow has no finished training run.")

    run = runs[0]

    return {
        "mlflow_run_id": run.info.run_id,
        "positive_class": "Not_Canceled",
        "accuracy": run.data.metrics["accuracy"],
        "precision": run.data.metrics["precision"],
        "recall": run.data.metrics["recall"],
        "f1": run.data.metrics["f1"],
    }


def train_and_publish(
    refresh_data: bool = False,
    directory: Path = MODEL_VERSIONS,
    job_id: UUID | None = None,
) -> dict:
    version = (job_id or uuid4()).hex
    folder = directory / version
    workspace = folder / "workspace"

    run_existing_pipeline(workspace, folder / "training.log", refresh_data)
    check_candidate(workspace)

    report = {
        "version": version,
        "published_at": datetime.now(timezone.utc).isoformat(),  # noqa: UP017
        "data_source": "gcs" if refresh_data else "local_snapshot",
        **read_run_report(workspace),
    }

    shutil.copy2(workspace / MODEL_FILE, folder / "model.pkl")
    shutil.copy2(workspace / MAPPING_FILE, folder / "mapping.json")

    (folder / "metrics.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    pending = directory / f".current-{version}.json"
    pending.write_text(json.dumps({"version": version}), encoding="utf-8")
    pending.replace(directory / "current.json")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-data", action="store_true")
    parser.add_argument("--job-id", type=UUID)
    arguments = parser.parse_args()

    report = train_and_publish(
        refresh_data=arguments.refresh_data,
        job_id=arguments.job_id,
    )
    print(json.dumps(report, indent=2))
