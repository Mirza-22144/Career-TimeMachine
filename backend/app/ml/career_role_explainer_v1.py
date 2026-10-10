
from typing import Any

from app.ml.career_role_predictor_v2 import (
    CareerRolePredictorV2,
)

from app.ml.predictive_role_explanation_models_v1 import (
    ExplainedPredictionResponse,
)


class CareerRoleExplainerV1:
    """Adds deterministic evidence-based explanations.

    The wrapped Version 2 predictor remains responsible
    for choosing and ranking the two roles.
    """

    def __init__(self, bundle_path):
        self.predictor = CareerRolePredictorV2(
            bundle_path
        )

        self.role_labels = (
            self.predictor.role_labels
        )

        self.skill_labels = (
            self.predictor.skill_labels
        )

        self.skill_weights = (
            self.predictor.skill_weights
        )

        self.role_skill_sets = (
            self.predictor.role_skill_sets
        )

        self.skill_id_by_label = (
            self.predictor.skill_id_by_label
        )


    @staticmethod
    def _normalise(value):
        return " ".join(
            str(value)
            .strip()
            .lower()
            .split()
        )


    @staticmethod
    def _human_join(values):
        if not values:
            return ""

        if len(values) == 1:
            return values[0]

        if len(values) == 2:
            return (
                f"{values[0]} and {values[1]}"
            )

        return (
            ", ".join(values[:-1])
            + f", and {values[-1]}"
        )


    def _recognised_user_skill_ids(
        self,
        payload,
    ):
        skills_object = payload.get(
            "skills",
            {},
        )

        catalogue_skills = (
            skills_object.get(
                "catalogue",
                [],
            )
        )

        custom_skills = (
            skills_object.get(
                "custom",
                [],
            )
        )

        recognised_ids = set()

        for skill_item in catalogue_skills:
            if not isinstance(
                skill_item,
                dict,
            ):
                continue

            skill_id = skill_item.get("id")
            skill_label = skill_item.get(
                "label"
            )

            if skill_id in self.skill_labels:
                recognised_ids.add(
                    skill_id
                )

            elif skill_label:
                resolved_id = (
                    self.skill_id_by_label.get(
                        self._normalise(
                            skill_label
                        )
                    )
                )

                if resolved_id:
                    recognised_ids.add(
                        resolved_id
                    )

        for custom_skill in custom_skills:
            resolved_id = (
                self.skill_id_by_label.get(
                    self._normalise(
                        custom_skill
                    )
                )
            )

            if resolved_id:
                recognised_ids.add(
                    resolved_id
                )

        return recognised_ids


    def _matched_skill_labels(
        self,
        recognised_user_skill_ids,
        candidate_role_id,
    ):
        candidate_skill_ids = (
            self.role_skill_sets.get(
                candidate_role_id,
                set(),
            )
        )

        matched_ids = (
            recognised_user_skill_ids
            & candidate_skill_ids
        )

        ranked_ids = sorted(
            matched_ids,
            key=lambda skill_id: (
                -float(
                    self.skill_weights.get(
                        skill_id,
                        1.0,
                    )
                ),
                self._normalise(
                    self.skill_labels.get(
                        skill_id,
                        skill_id,
                    )
                ),
            ),
        )

        matched_labels = []
        observed_labels = set()

        for skill_id in ranked_ids:
            skill_label = " ".join(
                str(
                    self.skill_labels[
                        skill_id
                    ]
                )
                .strip()
                .split()
            )

            normalised_label = (
                self._normalise(
                    skill_label
                )
            )

            if (
                skill_label
                and normalised_label
                not in observed_labels
            ):
                matched_labels.append(
                    skill_label
                )
                observed_labels.add(
                    normalised_label
                )

            if len(matched_labels) == 5:
                break

        return matched_labels


    def _has_previous_role_similarity(
        self,
        current_role_id,
        candidate_role_id,
    ):
        if current_role_id == "other":
            return False

        current_skills = (
            self.role_skill_sets.get(
                current_role_id,
                set(),
            )
        )

        candidate_skills = (
            self.role_skill_sets.get(
                candidate_role_id,
                set(),
            )
        )

        return bool(
            current_skills
            & candidate_skills
        )


    def _build_explanation(
        self,
        role_id,
        matched_skills,
        current_role_id,
    ):
        role_label = self.role_labels[
            role_id
        ]

        previous_role_label = (
            self.role_labels.get(
                current_role_id
            )
        )

        has_previous_similarity = (
            self._has_previous_role_similarity(
                current_role_id,
                role_id,
            )
        )

        reason_codes = [
            "model_profile_match"
        ]

        sentences = [
            (
                f"{role_label} was one of the two "
                "highest-ranked roles produced by "
                "the trained career model for the "
                "profile you supplied."
            )
        ]

        if matched_skills:
            reason_codes.append(
                "selected_skill_match"
            )

            skill_text = self._human_join(
                matched_skills
            )

            sentences.append(
                "Your selected "
                f"{'skill' if len(matched_skills) == 1 else 'skills'} "
                f"in {skill_text} "
                f"{'also appears' if len(matched_skills) == 1 else 'also appear'} "
                "in the catalogue profile for "
                "this role."
            )

        if (
            has_previous_similarity
            and previous_role_label
        ):
            reason_codes.append(
                "previous_role_similarity"
            )

            sentences.append(
                "It also shares catalogue skill "
                "areas with your previous role, "
                f"{previous_role_label}, supporting "
                "it as a possible career transition."
            )

        return {
            "summary": " ".join(sentences),
            "matched_skills": matched_skills,
            "reason_codes": reason_codes,
        }


    def predict(
        self,
        payload: dict[str, Any],
    ):
        # The existing predictor alone chooses
        # the two roles and their order.
        original_response = (
            self.predictor.predict(
                payload
            )
        )

        current_role_id = (
            payload
            .get("role", {})
            .get("id")
        )

        recognised_skill_ids = (
            self._recognised_user_skill_ids(
                payload
            )
        )

        explained_roles = []

        for role in original_response[
            "predicted_roles"
        ]:
            role_id = role["id"]

            matched_skills = (
                self._matched_skill_labels(
                    recognised_skill_ids,
                    role_id,
                )
            )

            explained_roles.append(
                {
                    "id": role_id,
                    "label": role["label"],
                    "explanation": (
                        self._build_explanation(
                            role_id,
                            matched_skills,
                            current_role_id,
                        )
                    ),
                }
            )

        validated_response = (
            ExplainedPredictionResponse
            .model_validate(
                {
                    "predicted_roles": (
                        explained_roles
                    )
                }
            )
        )

        return validated_response.model_dump(
            mode="json"
        )
