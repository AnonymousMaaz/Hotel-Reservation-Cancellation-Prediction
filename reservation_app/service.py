from typing import Annotated

import bentoml
from pydantic import Field
from reservation_app.model_store import ModelStore
from reservation_app.predictor import Booking
from reservation_app.training_jobs import TrainingJobs
from reservation_app.web import web_app


@bentoml.service(workers=1)
@bentoml.asgi_app(web_app, path="/desk")
class HotelPredictionService:
    def __init__(self):
        self.predictor = ModelStore()
        self.training_jobs = TrainingJobs()

    @bentoml.api
    def predict(
        self,
        bookings: Annotated[list[Booking], Field(min_length=1, max_length=1000)],
    ) -> dict:
        results = self.predictor.predict(bookings)
        return {"count": len(results), "results": results}
