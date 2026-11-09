from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile

import pandas as pd
from pydantic import ValidationError
from reservation_app.predictor import Booking

MAX_ROWS = 1000
MAX_BYTES = 2 * 1024 * 1024
MAX_EXCEL_CONTENT = 20 * 1024 * 1024

SAMPLE_CSV = (
    "lead_time,no_of_special_requests,avg_price_per_room,market_segment_type,"
    "arrival_year,arrival_month,arrival_date,no_of_week_nights,"
    "no_of_weekend_nights,no_of_adults\n"
    "224,0,65,Offline,2017,10,2,2,1,2\n"
    "1,0,60,Online,2018,2,28,1,2,1\n"
)


def read_bookings(contents: bytes, filename: str) -> list[Booking]:
    suffix = Path(filename).suffix.lower()

    if suffix not in {".csv", ".xlsx"}:
        raise ValueError("Choose a .csv or .xlsx file.")

    source = BytesIO(contents)
    options = {
        "header": None,
        "dtype": object,
        "keep_default_na": False,
        "nrows": MAX_ROWS + 2,
    }

    if suffix == ".xlsx":
        try:
            with ZipFile(source) as workbook:
                unpacked_size = sum(entry.file_size for entry in workbook.infolist())
        except BadZipFile as error:
            raise ValueError("This file is not a readable Excel workbook.") from error

        if unpacked_size > MAX_EXCEL_CONTENT:
            raise ValueError("The Excel workbook contains too much unpacked data.")

        source.seek(0)

    try:
        if suffix == ".csv":
            frame = pd.read_csv(source, encoding="utf-8-sig", **options)
        else:
            frame = pd.read_excel(source, sheet_name=0, engine="openpyxl", **options)
    except ImportError as error:
        raise ValueError("Excel support requires openpyxl on the server.") from error
    except (ValueError, OSError, KeyError, BadZipFile, SyntaxError) as error:
        raise ValueError(
            "The file could not be read. Check its format and rows."
        ) from error

    if len(frame) < 2:
        raise ValueError("Add a header and at least one booking row.")

    if len(frame) - 1 > MAX_ROWS:
        raise ValueError(f"Upload at most {MAX_ROWS:,} bookings at a time.")

    headers = [str(value).strip() for value in frame.iloc[0]]

    if len(set(headers)) != len(headers):
        raise ValueError("Column names must be unique.")

    required = list(Booking.model_fields)
    missing = [name for name in required if name not in headers]

    if missing:
        raise ValueError("Missing columns: " + ", ".join(missing))

    frame.columns = headers
    records = frame.iloc[1:].loc[:, required].to_dict(orient="records")

    bookings = []

    for number, record in enumerate(records, start=1):
        try:
            bookings.append(Booking.model_validate(record))
        except ValidationError as error:
            problem = error.errors()[0]
            field = ".".join(map(str, problem["loc"])) or "arrival date"
            raise ValueError(
                f"Booking row {number}, {field}: {problem['msg']}"
            ) from error

    return bookings
