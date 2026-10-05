# Local model deployment

## Model

- Hugging Face identifier: `gliner-community/gliner_small-v2.5`
- Saved Colab directory: `CareerTimeMachine/job_description_extractor_v1/models/gliner_small_v2_5`
- Approximate size: 1,277.52 MB
- Runtime device tested: CPU

## Why the model is not in this ZIP

GitHub rejects ordinary files larger than 100 MB. The model is therefore delivered separately from the source-code handover.

## Recommended Cloud Run approach

1. Make the model directory available to the backend team through approved project storage.
2. Copy the model directory into the backend container during the image build.
3. Load it with `local_files_only=True` by calling `load_extractor`.
4. Load the extractor once during FastAPI application start-up.
5. Use at least 2 GiB of Cloud Run memory and measure production memory before release.

The application does not need network access to Hugging Face after the container has been built.
