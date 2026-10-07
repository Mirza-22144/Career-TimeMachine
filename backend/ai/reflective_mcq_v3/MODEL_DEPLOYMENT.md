# Live MCQ Model Deployment

## Required environment variable

Set `GEMINI_API_KEY` in the backend deployment environment.

Do not commit the API key to GitHub or include it in a JSON file.

## Local embedding model

The service uses:

`sentence-transformers/all-MiniLM-L6-v2`

The model weights are deliberately excluded from this handover and from Git.

For a reproducible container build, download the model during the Docker build and set:

`LIVE_MCQ_EMBEDDING_MODEL_PATH=/app/models/all_minilm_l6_v2`

The Python service also supports loading the model by its Hugging Face identifier when no local path is configured.

## Gemini model

The tested live model is:

`gemini-3.5-flash-lite`

## Fallback behaviour

If Gemini is unavailable, times out, returns malformed output or fails validation twice, the service returns the matching Version 2 static scenario.

## Security

Custom skills are limited to 120 characters and checked for instruction-like patterns. Gemini output is constrained by a JSON schema and then validated again in Python.
