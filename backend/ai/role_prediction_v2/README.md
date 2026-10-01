# Career role recommender Version 2

## Purpose

I recommend two distinct future IT roles from a previous role and selected skills.

## Installation

```bash
pip install -r requirements.txt
```

## Python usage

```python
from career_role_predictor_v2 import CareerRolePredictorV2

predictor = CareerRolePredictorV2(
    "career_role_recommender_v2_bundle.joblib"
)

response = predictor.predict(request_payload)
```

## Public response

```json
{
  "predicted_roles": [
    {
      "id": "data_scientist",
      "label": "Data Scientist"
    },
    {
      "id": "business_intelligence_analyst",
      "label": "Business Intelligence Analyst"
    }
  ]
}
```

## Backend schema change

Version 1 returned one `predicted_role` object.
Version 2 returns a `predicted_roles` array containing exactly two role objects.

## Model architecture

- I convert supplied skill text into word-level TF-IDF features.
- I rank 27 supported IT professions using a LinearSVC classifier.
- I combine the classifier ranking with catalogue skill fit and previous-role similarity.
- I give distinctive skills more weight using inverse role frequency.

## Constraints

- I return exactly two distinct roles.
- I exclude the supplied previous role.
- I never return the internal `other` role.
- I accept catalogue and custom skill labels.
- I do not expose internal ranking scores as probabilities.

## Evaluation

- Test accuracy: 0.8528
- Test balanced accuracy: 0.6846
- Test macro F1 across evaluable roles: 0.7007
- Test top-2 accuracy: 0.9385

## Limitations

- The model recommends role suitability, not a guaranteed career outcome.
- Training targets were weakly supervised from real job titles.
- Rare professions have limited real evaluation evidence.
- Computer and Information Research Scientist has no independent real-posting test support.
- Demographic fairness cannot be measured without suitable demographic attributes.
- I load the joblib bundle only as a trusted project artefact.
