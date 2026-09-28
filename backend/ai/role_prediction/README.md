# Career role prediction handover

## Purpose

I recommend one future IT role from a previous role and selected skills.

## Installation

```bash
pip install -r requirements.txt
```

## Python usage

```python
from career_role_predictor import CareerRolePredictor

predictor = CareerRolePredictor(
    "career_role_recommender_bundle.joblib"
)

response = predictor.predict(request_payload)
```

## Example response

```json
{
  "predicted_role": {
    "id": "data_scientist",
    "label": "Data Scientist"
  }
}
```

## Constraints and limitations

- I return one of the 27 supported IT roles.
- I exclude the supplied previous role.
- I never return `other`.
- I accept catalogue and custom skill labels.
- I recommend role suitability rather than a guaranteed career outcome.
- I load the joblib file only as a trusted project artefact.
