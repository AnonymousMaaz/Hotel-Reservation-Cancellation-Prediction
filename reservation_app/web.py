from pathlib import Path
from typing import Annotated, Any

import bentoml
import pandas as pd
from fastapi import Depends, FastAPI, File, Request, UploadFile
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from reservation_app.batch import MAX_BYTES, SAMPLE_CSV, read_bookings
from reservation_app.training_jobs import TrainingInProgress

APP_DIR = Path(__file__).resolve().parent

web_app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

web_app.mount(
    "/static",
    StaticFiles(directory=APP_DIR / "static"),
    name="desk-static",
)

templates = Jinja2Templates(directory=APP_DIR / "templates")


@web_app.get("/", response_class=HTMLResponse)
def desk(request: Request):
    return templates.TemplateResponse(request=request, name="desk.html", context={})


@web_app.get("/batch", response_class=HTMLResponse)
def batch_page(request: Request):
    return templates.TemplateResponse(request=request, name="batch.html", context={})


@web_app.get("/batch/sample.csv")
def batch_sample():
    return Response(
        content=SAMPLE_CSV,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="sample-bookings.csv"'},
    )


@web_app.post("/batch", response_class=HTMLResponse)
def batch_predict(
    request: Request,
    file: Annotated[UploadFile, File()],
    service: Annotated[Any, Depends(bentoml.get_current_service)],
):
    filename = file.filename or ""
    contents = file.file.read(MAX_BYTES + 1)

    if len(contents) > MAX_BYTES:
        return templates.TemplateResponse(
            request=request,
            name="batch.html",
            context={"error": "Choose a file of 2 MiB or smaller."},
            status_code=413,
        )

    try:
        bookings = read_bookings(contents, filename)
    except ValueError as error:
        return templates.TemplateResponse(
            request=request,
            name="batch.html",
            context={"error": str(error)},
            status_code=422,
        )

    results = service.predictor.predict(bookings)
    canceled = sum(row["status"] == "Canceled" for row in results)

    return templates.TemplateResponse(
        request=request,
        name="batch.html",
        context={
            "filename": filename,
            "results": results,
            "canceled": canceled,
            "kept": len(results) - canceled,
            "export_csv": pd.DataFrame(results).to_csv(index=False),
        },
    )


class TrainingRequest(BaseModel):
    refresh_data: bool = False


@web_app.get("/training", response_class=HTMLResponse)
def training_page(request: Request):
    return templates.TemplateResponse(request=request, name="training.html", context={})


@web_app.post("/training/jobs", status_code=202)
def start_training(
    options: TrainingRequest,
    service: Annotated[Any, Depends(bentoml.get_current_service)],
):
    try:
        return service.training_jobs.start(options.refresh_data)
    except TrainingInProgress as error:
        raise HTTPException(409, detail="A training run is already active.") from error
    except OSError as error:
        raise HTTPException(
            500, detail="Could not start the training process."
        ) from error


@web_app.get("/training/jobs/latest")
def training_status(
    response: Response,
    service: Annotated[Any, Depends(bentoml.get_current_service)],
):
    response.headers["Cache-Control"] = "no-store"
    return service.training_jobs.status()
