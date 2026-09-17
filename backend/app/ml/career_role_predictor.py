"""Career role prediction model, delivered by the AI team (career-role
prediction card). Loaded once from a trusted, version-controlled project
artefact (see app/data/career_role_recommender_bundle.joblib) - never from a
user-supplied or externally-fetched path.

This class is intentionally kept close to the AI team's own delivered code
(backend/ai/role_prediction/career_role_predictor.py) so behaviour matches
what they trained and evaluated. The one thing this backend adds on top is
in app/services/role_prediction_service.py: the bundle is loaded behind a
try/except so a missing or corrupt file degrades the one endpoint that needs
it (503) instead of preventing the whole app from starting, and every
prediction is re-validated against a Pydantic schema before it can reach a
response.
"""

from typing import Any

import joblib


class CareerRolePredictor:
    """Recommends one future IT role from a previous role and selected
    skills. Excludes the supplied previous role and never returns "other"."""

    def __init__(self, bundle_path: str) -> None:
        self.bundle = joblib.load(bundle_path)
        self.model = self.bundle["model"]
        self.role_labels: dict[str, str] = self.bundle["role_labels"]
        self.skill_labels: dict[str, str] = self.bundle["skill_labels"]
        self.skill_weights: dict[str, float] = self.bundle["skill_weights"]
        self.scoring_weights: dict[str, float] = self.bundle["scoring_weights"]

        self.role_skill_sets: dict[str, set[str]] = {
            role_id: set(skill_ids) for role_id, skill_ids in self.bundle["role_skill_sets"].items()
        }

        self.skill_id_by_label: dict[str, str] = {
            self._normalise(label): skill_id for skill_id, label in self.skill_labels.items()
        }

    @staticmethod
    def _normalise(value: Any) -> str:
        return " ".join(str(value).strip().lower().split())

    @staticmethod
    def _scale(scores: dict[str, float]) -> dict[str, float]:
        values = list(scores.values())
        minimum = min(values)
        maximum = max(values)

        if minimum == maximum:
            return {key: 0.0 for key in scores}

        return {key: (value - minimum) / (maximum - minimum) for key, value in scores.items()}

    def _weighted_jaccard(self, first_skills: set[str], second_skills: set[str]) -> float:
        union = first_skills | second_skills
        if not union:
            return 0.0

        intersection = first_skills & second_skills
        intersection_weight = sum(self.skill_weights.get(skill_id, 1.0) for skill_id in intersection)
        union_weight = sum(self.skill_weights.get(skill_id, 1.0) for skill_id in union)
        return intersection_weight / union_weight

    def _skill_fit(self, user_skills: set[str], candidate_skills: set[str]) -> float:
        if not user_skills:
            return 0.0

        total_weight = sum(self.skill_weights.get(skill_id, 1.0) for skill_id in user_skills)
        matched_weight = sum(
            self.skill_weights.get(skill_id, 1.0) for skill_id in (user_skills & candidate_skills)
        )
        return matched_weight / total_weight

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        """payload: {"role": {"id", "label"}, "skills": {"catalogue": [...], "custom": [...]}}.
        Returns {"predicted_role": {"id", "label"}}. Raises ValueError for an
        unrecognised role id - callers must map that to a client error, not a
        500."""
        role_object = payload.get("role", {})
        skills_object = payload.get("skills", {})

        current_role_id = role_object.get("id")
        if current_role_id not in self.role_labels:
            raise ValueError(f"Unknown role ID: {current_role_id}")

        catalogue_skills = skills_object.get("catalogue", [])
        custom_skills = skills_object.get("custom", [])

        supplied_labels = []
        for skill in catalogue_skills:
            skill_id = skill.get("id")
            skill_label = skill.get("label")
            if skill_label:
                supplied_labels.append(str(skill_label))
            elif skill_id in self.skill_labels:
                supplied_labels.append(self.skill_labels[skill_id])
        supplied_labels.extend(str(skill) for skill in custom_skills if str(skill).strip())

        model_input = ", ".join(supplied_labels)
        probabilities = self.model.predict_proba([model_input])[0]
        model_classes = self.model.named_steps["classifier"].classes_

        model_scores = {role_id: 0.0 for role_id in self.role_labels if role_id != "other"}
        for role_id, probability in zip(model_classes, probabilities):
            if role_id in model_scores:
                model_scores[role_id] = float(probability)

        recognised_skill_ids: set[str] = set()
        for skill in catalogue_skills:
            skill_id = skill.get("id")
            skill_label = skill.get("label")
            if skill_id in self.skill_labels:
                recognised_skill_ids.add(skill_id)
            elif skill_label:
                matched_id = self.skill_id_by_label.get(self._normalise(skill_label))
                if matched_id:
                    recognised_skill_ids.add(matched_id)
        for custom_skill in custom_skills:
            matched_id = self.skill_id_by_label.get(self._normalise(custom_skill))
            if matched_id:
                recognised_skill_ids.add(matched_id)

        candidate_role_ids = [
            role_id for role_id in self.role_labels if role_id not in {"other", current_role_id}
        ]
        current_role_skills = self.role_skill_sets.get(current_role_id, set())

        candidate_model_scores = {role_id: model_scores[role_id] for role_id in candidate_role_ids}
        skill_fit_scores = {}
        transition_scores = {}

        for role_id in candidate_role_ids:
            candidate_skills = self.role_skill_sets.get(role_id, set())
            skill_fit_scores[role_id] = self._skill_fit(recognised_skill_ids, candidate_skills)
            transition_scores[role_id] = (
                0.0
                if current_role_id == "other"
                else self._weighted_jaccard(current_role_skills, candidate_skills)
            )

        model_scores = self._scale(candidate_model_scores)
        skill_fit_scores = self._scale(skill_fit_scores)
        transition_scores = self._scale(transition_scores)

        final_scores = {
            role_id: (
                self.scoring_weights["trained_model"] * model_scores[role_id]
                + self.scoring_weights["selected_skill_fit"] * skill_fit_scores[role_id]
                + self.scoring_weights["current_role_similarity"] * transition_scores[role_id]
            )
            for role_id in candidate_role_ids
        }

        predicted_role_id = max(final_scores, key=final_scores.get)
        return {
            "predicted_role": {
                "id": predicted_role_id,
                "label": self.role_labels[predicted_role_id],
            }
        }
