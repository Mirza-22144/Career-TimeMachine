# Builds the backend into a container image for Cloud Run.
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Cloud Run sets $PORT and expects the app to listen on it (defaults to
# 8080 if not set, e.g. when running this image locally).
ENV PORT=8080
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
