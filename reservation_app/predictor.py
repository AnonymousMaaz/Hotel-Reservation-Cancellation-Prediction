import json
from datetime import date
from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Booking(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    lead_time: int = Field(ge=0)
    no_of_special_requests: int = Field(ge=0)
    avg_price_per_room: float = Field(ge=0)
    market_segment_type: Literal[
        "Aviation", "Complementary", "Corporate", "Offline", "Online"
    ]
    arrival_year: int = Field(ge=1, le=9999)
    arrival_month: int = Field(ge=1, le=12)
    arrival_date: int = Field(ge=1, le=31)
    no_of_week_nights: int = Field(ge=0)
    no_of_weekend_nights: int = Field(ge=0)
    no_of_adults: int = Field(ge=0)

    @model_validator(mode="after")
    def check_arrival_date(self):
        date(self.arrival_year, self.arrival_month, self.arrival_date)
        return self


class BookingPredictor:
    def __init__(self, model_path: Path, mapping_path: Path):
        self.model = joblib.load(model_path)

        mapping = json.loads(mapping_path.read_text(encoding="utf-8"))

        self.channel_codes = mapping["market_segment_type"]
        self.status_codes = mapping["booking_status"]

        self.features = list(self.model.feature_name_)
        self.classes = self.model.classes_.tolist()

        if set(self.features) != set(Booking.model_fields):
            raise ValueError("The model features and booking fields differ.")

        if set(self.classes) != set(self.status_codes.values()):
            raise ValueError("The model classes and status mapping differ.")

    def predict(self, bookings: list[Booking]) -> list[dict]:
        if not bookings:
            raise ValueError("Supply at least one booking.")

        frame = pd.DataFrame([booking.model_dump() for booking in bookings])

        frame["market_segment_type"] = frame["market_segment_type"].map(
            self.channel_codes
        )

        if frame["market_segment_type"].isna().any():
            raise ValueError("The model mapping is missing a booking channel.")

        frame = frame.loc[:, self.features]

        probabilities = self.model.predict_proba(frame)

        canceled_index = self.classes.index(self.status_codes["Canceled"])

        status_names = {code: label for label, code in self.status_codes.items()}

        results = []

        for row_number, scores in enumerate(probabilities, start=1):
            winning_index = int(scores.argmax())
            winning_code = self.classes[winning_index]

            results.append(
                {
                    "row": row_number,
                    "status": status_names[winning_code],
                    "cancellation_score": round(float(scores[canceled_index]), 4),
                }
            )

        return results
