import json
from pathlib import Path
from threading import Lock
from uuid import UUID

from reservation_app.predictor import Booking, BookingPredictor

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASELINE_MODEL = PROJECT_ROOT / "artifacts" / "models" / "lgbm_model.pkl"
BASELINE_MAPPING = PROJECT_ROOT / "config" / "mapping.json"
MODEL_VERSIONS = Path(__file__).resolve().parent / "model_versions"


class ModelStore:
    def __init__(self, directory: Path = MODEL_VERSIONS):
        self.directory = directory
        self._lock = Lock()
        self._version = None
        self._predictor = None
        self._active_predictor()

    def _read_version(self) -> str:
        try:
            text = (self.directory / "current.json").read_text(encoding="utf-8")
        except FileNotFoundError:
            return "baseline"

        version = json.loads(text)["version"]

        if UUID(version).hex != version:
            raise ValueError("Invalid model version in current.json.")

        return version

    def _active_predictor(self) -> BookingPredictor:
        with self._lock:
            version = self._read_version()

            if self._predictor is None or version != self._version:
                if version == "baseline":
                    model_path = BASELINE_MODEL
                    mapping_path = BASELINE_MAPPING
                else:
                    folder = self.directory / version
                    model_path = folder / "model.pkl"
                    mapping_path = folder / "mapping.json"

                predictor = BookingPredictor(model_path, mapping_path)
                self._predictor = predictor
                self._version = version

            return self._predictor

    def predict(self, bookings: list[Booking]) -> list[dict]:
        predictor = self._active_predictor()
        return predictor.predict(bookings)
