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

# Job description analysis (AC 5.1.1) uses a local GLiNER model. It is too
# large for Git (GitHub rejects files over 100 MB), so it is downloaded
# into the image here - see ai/job_description_extraction/MODEL_DEPLOYMENT.md.
# Only the files the loader reads are fetched (about 670 MB, not the extra
# half-precision copies). The last command loads it once with
# local_files_only, so a build that cannot serve it offline fails here
# rather than in production.
ENV HF_HOME=/app/hf_cache
ENV JOB_DESCRIPTION_MODEL_DIR=/app/models/gliner_small_v2_5
RUN python -c "from huggingface_hub import snapshot_download; snapshot_download('gliner-community/gliner_small-v2.5', local_dir='/app/models/gliner_small_v2_5', allow_patterns=['*.json', '*.bin', '*.model'])"  && python -c "from transformers import AutoConfig; AutoConfig.from_pretrained('microsoft/deberta-v3-small')"  && python -c "from gliner import GLiNER; GLiNER.from_pretrained('/app/models/gliner_small_v2_5', local_files_only=True)"

COPY app ./app

# Every model is now inside the image: never reach out to Hugging Face at
# run time (it would only slow a cold start, or fail it).
ENV HF_HUB_OFFLINE=1

# Cloud Run sets $PORT and expects the app to listen on it (defaults to
# 8080 if not set, e.g. when running this image locally).
ENV PORT=8080
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
