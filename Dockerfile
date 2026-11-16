FROM python:3.10-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE = 1 \
    PYTHONUNBUFFERED = 1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --no-cache-dir \
    -e . \
    "bentoml==1.4.40" \
    "scikit-learn==1.7.2" \
    "lightgbm==4.7.0" \
    "numpy==2.2.6" \
    "pandas==2.3.3" \
    fastapi \
    jinja2 \
    python-multipart

EXPOSE 5000

CMD ["bentoml", "serve", "reservation_app.service:HotelPredictionService", "--host", "0.0.0.0", "--port", "5000"]