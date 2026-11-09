from pathlib import Path

from .predictor import Booking, BookingPredictor

source = Path(__file__).resolve().parents[1]

predictor = BookingPredictor(
    model_path=source / "artifacts" / "models" / "lgbm_model.pkl",
    mapping_path=source / "config" / "mapping.json",
)

first = Booking(
    lead_time=224,
    no_of_special_requests=0,
    avg_price_per_room=65.0,
    market_segment_type="Offline",
    arrival_year=2017,
    arrival_month=10,
    arrival_date=2,
    no_of_week_nights=2,
    no_of_weekend_nights=1,
    no_of_adults=2,
)

second = Booking(
    lead_time=1,
    no_of_special_requests=0,
    avg_price_per_room=60.0,
    market_segment_type="Online",
    arrival_year=2018,
    arrival_month=2,
    arrival_date=28,
    no_of_week_nights=1,
    no_of_weekend_nights=2,
    no_of_adults=1,
)

print("Single:", predictor.predict([first]))
print("Batch:", predictor.predict([first, second]))
