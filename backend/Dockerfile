# Builds the backend into a container image for Cloud Run.
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
# --extra-index-url is required for torch==...+cpu (Iteration 3, job
# description extraction) - the +cpu build isn't published to regular
# PyPI, only to PyTorch's own index. Everything else still resolves from
# PyPI as normal; this just adds a second source, it doesn't replace PyPI.
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# The live practice question (Iteration 3, AC 4.4.6) retrieves context with
# a small local embedding model. Baked into the image so a cold start never
# downloads it; see ai/reflective_mcq_v3/MODEL_DEPLOYMENT.md.
ENV LIVE_MCQ_EMBEDDING_MODEL_PATH=/app/models/all_minilm_l6_v2
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2').save('/app/models/all_minilm_l6_v2')"

COPY app ./app

# Cloud Run sets $PORT and expects the app to listen on it (defaults to
# 8080 if not set, e.g. when running this image locally).
ENV PORT=8080
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
