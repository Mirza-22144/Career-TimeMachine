# CareerTimeMachine Job Description Extractor

## Purpose

I extract structured requirements from a pasted job description using a local hybrid NLP pipeline.

## Runtime interface

```python
from job_description_extractor import load_extractor

extractor = load_extractor(
    model_directory="/app/models/gliner_small_v2_5",
    catalogue_file="skill_catalogue.json"
)

result = extractor.extract(raw_text)
```

The `extract` method returns exactly five fields:

- `skills`
- `responsibilities`
- `min_years_experience`
- `keywords`
- `role_title_guess`

## Backend request

```json
{
  "raw_text": "Pasted job description"
}
```

## Important runtime behaviour

- I run locally without a paid AI API or an external runtime model request.
- I limit input to 20,000 characters.
- I remove common instruction-like segments before extraction.
- I validate the fixed five-field output contract.
- I load the model once when the backend starts.

## Verified holdout performance

- Technical-skill F1: 0.7723
- Soft-skill F1: 0.8980
- Responsibility F1: 0.7917
- Experience exact-match accuracy: 100%
- Role-title exact-match accuracy: 100%
- Schema pass rate: 100%
- Mean CPU latency: 1.52 seconds
- P95 CPU latency: 3.15 seconds
- Robustness tests: 13/13 passed

## Interpretation

The output is supportive extraction guidance. It must not be presented as an employability score, hiring decision or guarantee.
