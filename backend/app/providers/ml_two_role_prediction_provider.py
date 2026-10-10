"""Two-role prediction provider backed by the AI team's Version 2 trained
model (AI 3.2 - TF-IDF + tuned LinearSVC, hybrid ranking: 50% model / 40%
selected-skill fit / 10% previous-role similarity - see
app/ml/career_role_predictor_v2.py, vendored from the AI team's handover).
Runs entirely in-process: the joblib bundle is loaded once at import time,
no network call and no API key involved - same shape as the V1 provider.
"""

import logging
from pathlib import Path
from typing import Any

from app.ml.career_role_explainer_v1 import CareerRoleExplainerV1
from app.providers.role_prediction_provider import RolePredictionRequest
from app.providers.two_role_prediction_provider import (
    TwoRolePredictionProvider,
    TwoRolePredictionProviderError,
)

logger = logging.getLogger(__name__)

_BUNDLE_PATH = Path(__file__).resolve().parent.parent / "ml" / "career_role_recommender_v2_bundle.joblib"

# Loaded once at import time - inference is a few milliseconds in-process,
# not worth reloading the ~20MB bundle per request. The explainer wraps the
# same Version 2 predictor: the predictor alone still chooses and orders
# the two roles, and the explainer adds a deterministic explanation to each
# (AI team's explainability handover - no retraining, no Gemini).
_explainer = CareerRoleExplainerV1(str(_BUNDLE_PATH))
_predictor = _explainer.predictor


def _to_payload(request: RolePredictionRequest) -> dict[str, Any]:
    # Identical shape to ml_role_prediction_provider.py's _to_payload -
    # confirmed against the AI team's own role_prediction_contract_v2.json,
    # the request side is unchanged from V1.
    return {
        "role": {"id": request.role_id, "label": request.role_label},
        "skills": {
            "catalogue": [
                {"id": skill.id, "label": skill.label} for skill in request.skills if skill.id is not None
            ],
            "custom": [skill.label for skill in request.skills if skill.id is None],
        },
    }


class MLTwoRolePredictionProvider(TwoRolePredictionProvider):
    """Serves the AI team's real trained Version 2 career-role classifier."""

    def predict(self, request: RolePredictionRequest) -> dict[str, Any]:
        payload = _to_payload(request)
        try:
            try:
                raw = _explainer.predict(payload)
            except Exception:
                # An explanation that cannot be built must not cost her the
                # suggestions themselves.
                logger.warning("Role explanations unavailable; returning roles without them")
                raw = _predictor.predict(payload)
            return {
                "predicted_roles": [
                    {
                        "role_id": role["id"],
                        "role_label": role["label"],
                        "explanation": role.get("explanation"),
                    }
                    for role in raw["predicted_roles"]
                ]
            }
        except Exception as exc:
            # Matches RolePredictionProvider's "every failure becomes a
            # provider error" contract.
            raise TwoRolePredictionProviderError("role prediction failed") from exc
