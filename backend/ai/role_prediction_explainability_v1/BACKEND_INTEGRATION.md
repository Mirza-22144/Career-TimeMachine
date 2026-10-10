# Predictive-role explainability backend integration

## Purpose

This handover adds deterministic explanations to the existing two-role career recommender.
It does not retrain the model, change the selected roles or require Gemini.

## Existing backend components retained

- `backend/app/ml/career_role_predictor_v2.py`
- `backend/app/ml/career_role_recommender_v2_bundle.joblib`
- `backend/app/providers/ml_two_role_prediction_provider.py`
- `backend/app/services/role_prediction_service.py`
- `backend/app/schemas/predicted_roles.py`
- `GET /api/v1/predicted-roles`

The existing vacancy and market-data enrichment must remain unchanged.

## New AI source

- `career_role_explainer_v1.py`
- `predictive_role_explanation_models_v1.py`
- `explained_role_prediction_provider_v1.py`

The included `career_role_predictor_v2.py` is an unchanged reference copy.

## Recommended integration

1. Place the explanation engine and models beside the existing Version 2 predictor.
2. Update `MLTwoRolePredictionProvider` to instantiate the explanation engine using the existing Version 2 bundle.
3. Preserve the existing conversion from AI fields `id` and `label` to backend fields `role_id` and `role_label`.
4. Add `explanation` to each predicted role.
5. Add the explanation object to the provider validation model, service result and API schema.
6. Keep the current `market_data` enrichment unchanged.
7. Extend `test_predicted_roles_api.py` with explanation and regression assertions.

## Explanation fields

- `summary`
- `matched_skills`
- `reason_codes`

## Important interpretation rule

LinearSVC decision values and hybrid-ranking scores are not calibrated probabilities.
Do not display them as percentages, confidence values or guaranteed career outcomes.

## Runtime requirements

- No Gemini API key
- No external network call
- No model retraining
- Existing Version 2 model bundle
- Dependencies listed in `requirements.txt`
