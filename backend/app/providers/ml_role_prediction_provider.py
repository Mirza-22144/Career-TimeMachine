"""Role-prediction provider backed by the AI team's trained model.

Hybrid model: TF-IDF + multinomial logistic regression over real job-posting
data, reranked with an O*NET-based skill-fit and previous-role-similarity
score (60% classifier / 25% selected-skill fit / 15% previous-role
similarity - see app/ml/career_role_predictor.py, vendored from the AI
team's handover). Runs entirely in-process: the joblib bundle is loaded
once at import time, no network call and no API key involved.
"""

from pathlib import Path
from typing import Any

from app.ml.career_role_predictor import CareerRolePredictor
from app.providers.role_prediction_provider import (
    RolePredictionProvider,
    RolePredictionProviderError,
    RolePredictionRequest,
)

_BUNDLE_PATH = Path(__file__).resolve().parent.parent / "ml" / "career_role_recommender_bundle.joblib"

# Loaded once at import time - inference is a few milliseconds in-process,
# not worth reloading the ~13MB bundle per request.
_predictor = CareerRolePredictor(str(_BUNDLE_PATH))


def _to_payload(request: RolePredictionRequest) -> dict[str, Any]:
    return {
        "role": {"id": request.role_id, "label": request.role_label},
        "skills": {
            "catalogue": [
                {"id": skill.id, "label": skill.label} for skill in request.skills if skill.id is not None
            ],
            "custom": [skill.label for skill in request.skills if skill.id is None],
        },
    }


class MLRolePredictionProvider(RolePredictionProvider):
    """Serves the AI team's real trained career-role classifier."""

    def predict(self, request: RolePredictionRequest) -> dict[str, Any]:
        try:
            raw = _predictor.predict(_to_payload(request))
            predicted = raw["predicted_role"]
            return {"role_id": predicted["id"], "role_label": predicted["label"]}
        except Exception as exc:
            # The predictor raises ValueError for an unrecognised role id;
            # treat any failure the same way, matching ScenarioProvider's
            # "every failure becomes a provider error" contract.
            raise RolePredictionProviderError("role prediction failed") from exc
