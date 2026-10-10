
import joblib


class CareerRolePredictorV2:
    """I recommend two future IT roles from a role and skills."""

    def __init__(self, bundle_path):
        # I load only a trusted project bundle.
        self.bundle = joblib.load(
            bundle_path
        )

        self.model = self.bundle["model"]
        self.role_labels = self.bundle[
            "role_labels"
        ]
        self.skill_labels = self.bundle[
            "skill_labels"
        ]
        self.skill_weights = self.bundle[
            "skill_weights"
        ]
        self.scoring_weights = self.bundle[
            "scoring_weights"
        ]

        self.role_skill_sets = {
            role_id: set(skill_ids)
            for role_id, skill_ids
            in self.bundle[
                "role_skill_sets"
            ].items()
        }

        self.skill_id_by_label = {
            self._normalise(skill_label): skill_id
            for skill_id, skill_label
            in self.skill_labels.items()
        }


    @staticmethod
    def _normalise(value):
        return " ".join(
            str(value)
            .strip()
            .lower()
            .split()
        )


    def _remove_duplicate_labels(
        self,
        supplied_labels
    ):
        unique_labels = []
        observed_labels = set()

        for supplied_label in supplied_labels:
            cleaned_label = " ".join(
                str(supplied_label)
                .strip()
                .split()
            )

            normalised_label = (
                self._normalise(
                    cleaned_label
                )
            )

            if (
                cleaned_label
                and normalised_label
                not in observed_labels
            ):
                unique_labels.append(
                    cleaned_label
                )

                observed_labels.add(
                    normalised_label
                )

        return unique_labels


    @staticmethod
    def _scale(score_dictionary):
        values = list(
            score_dictionary.values()
        )

        minimum_value = min(values)
        maximum_value = max(values)

        if minimum_value == maximum_value:
            return {
                key: 0.0
                for key in score_dictionary
            }

        return {
            key: (
                value - minimum_value
            ) / (
                maximum_value
                - minimum_value
            )
            for key, value
            in score_dictionary.items()
        }


    def _weighted_jaccard(
        self,
        first_skill_set,
        second_skill_set
    ):
        union = (
            first_skill_set
            | second_skill_set
        )

        if not union:
            return 0.0

        intersection = (
            first_skill_set
            & second_skill_set
        )

        intersection_weight = sum(
            self.skill_weights.get(
                skill_id,
                1.0
            )
            for skill_id in intersection
        )

        union_weight = sum(
            self.skill_weights.get(
                skill_id,
                1.0
            )
            for skill_id in union
        )

        return (
            intersection_weight
            / union_weight
        )


    def _skill_fit(
        self,
        user_skill_ids,
        candidate_skill_ids
    ):
        if not user_skill_ids:
            return 0.0

        total_weight = sum(
            self.skill_weights.get(
                skill_id,
                1.0
            )
            for skill_id in user_skill_ids
        )

        matched_weight = sum(
            self.skill_weights.get(
                skill_id,
                1.0
            )
            for skill_id in (
                user_skill_ids
                & candidate_skill_ids
            )
        )

        return (
            matched_weight
            / total_weight
        )


    def predict(
        self,
        payload,
        return_diagnostics=False
    ):
        if not isinstance(payload, dict):
            raise ValueError(
                "The prediction payload must "
                "be an object."
            )

        role_object = payload.get(
            "role",
            {}
        )

        skills_object = payload.get(
            "skills",
            {}
        )

        current_role_id = role_object.get(
            "id"
        )

        if (
            current_role_id
            not in self.role_labels
        ):
            raise ValueError(
                "Unknown role ID: "
                f"{current_role_id}"
            )

        catalogue_skills = (
            skills_object.get(
                "catalogue",
                []
            )
        )

        custom_skills = (
            skills_object.get(
                "custom",
                []
            )
        )

        if not isinstance(
            catalogue_skills,
            list
        ):
            raise ValueError(
                "Catalogue skills must be a list."
            )

        if not isinstance(
            custom_skills,
            list
        ):
            raise ValueError(
                "Custom skills must be a list."
            )


        # I collect catalogue and custom labels.
        supplied_labels = []

        for skill_item in catalogue_skills:
            if not isinstance(
                skill_item,
                dict
            ):
                continue

            skill_id = skill_item.get(
                "id"
            )

            skill_label = skill_item.get(
                "label"
            )

            if skill_label:
                supplied_labels.append(
                    str(skill_label)
                )

            elif skill_id in self.skill_labels:
                supplied_labels.append(
                    self.skill_labels[
                        skill_id
                    ]
                )

        supplied_labels.extend(
            str(custom_skill)
            for custom_skill in custom_skills
            if str(custom_skill).strip()
        )

        supplied_labels = (
            self._remove_duplicate_labels(
                supplied_labels
            )
        )

        model_input = ", ".join(
            supplied_labels
        )


        # I obtain the LinearSVC decision scores.
        decision_scores = (
            self.model
            .decision_function(
                [model_input]
            )[0]
        )

        model_classes = (
            self.model
            .named_steps["classifier"]
            .classes_
        )

        complete_model_scores = {
            role_id: float(score)
            for role_id, score in zip(
                model_classes,
                decision_scores
            )
        }


        # I resolve recognised catalogue skills.
        recognised_skill_ids = set()

        for skill_item in catalogue_skills:
            if not isinstance(
                skill_item,
                dict
            ):
                continue

            skill_id = skill_item.get(
                "id"
            )

            skill_label = skill_item.get(
                "label"
            )

            if skill_id in self.skill_labels:
                recognised_skill_ids.add(
                    skill_id
                )

            elif skill_label:
                matched_skill_id = (
                    self.skill_id_by_label.get(
                        self._normalise(
                            skill_label
                        )
                    )
                )

                if matched_skill_id:
                    recognised_skill_ids.add(
                        matched_skill_id
                    )

        for custom_skill in custom_skills:
            matched_skill_id = (
                self.skill_id_by_label.get(
                    self._normalise(
                        custom_skill
                    )
                )
            )

            if matched_skill_id:
                recognised_skill_ids.add(
                    matched_skill_id
                )


        # I exclude the previous role and Other.
        candidate_role_ids = [
            role_id
            for role_id in model_classes
            if role_id not in {
                current_role_id,
                "other"
            }
        ]

        if len(candidate_role_ids) < 2:
            raise RuntimeError(
                "I found fewer than two "
                "eligible future roles."
            )

        current_role_skill_ids = (
            self.role_skill_sets.get(
                current_role_id,
                set()
            )
        )


        model_scores = {
            role_id: complete_model_scores[
                role_id
            ]
            for role_id in candidate_role_ids
        }

        skill_fit_scores = {}
        role_similarity_scores = {}

        for candidate_role_id in (
            candidate_role_ids
        ):
            candidate_skill_ids = (
                self.role_skill_sets.get(
                    candidate_role_id,
                    set()
                )
            )

            skill_fit_scores[
                candidate_role_id
            ] = self._skill_fit(
                recognised_skill_ids,
                candidate_skill_ids
            )

            if current_role_id == "other":
                role_similarity_scores[
                    candidate_role_id
                ] = 0.0
            else:
                role_similarity_scores[
                    candidate_role_id
                ] = self._weighted_jaccard(
                    current_role_skill_ids,
                    candidate_skill_ids
                )


        normalised_model_scores = (
            self._scale(
                model_scores
            )
        )

        normalised_skill_fit_scores = (
            self._scale(
                skill_fit_scores
            )
        )

        normalised_similarity_scores = (
            self._scale(
                role_similarity_scores
            )
        )


        # I activate only the components supported
        # by the supplied request.
        active_weights = {
            "trained_model": (
                self.scoring_weights[
                    "trained_model"
                ]
            )
        }

        if recognised_skill_ids:
            active_weights[
                "selected_skill_fit"
            ] = self.scoring_weights[
                "selected_skill_fit"
            ]

        if (
            current_role_id != "other"
            and current_role_skill_ids
        ):
            active_weights[
                "current_role_similarity"
            ] = self.scoring_weights[
                "current_role_similarity"
            ]

        total_active_weight = sum(
            active_weights.values()
        )

        active_weights = {
            component_name: (
                component_weight
                / total_active_weight
            )
            for (
                component_name,
                component_weight
            ) in active_weights.items()
        }


        final_scores = {}

        for candidate_role_id in (
            candidate_role_ids
        ):
            final_score = (
                active_weights[
                    "trained_model"
                ]
                * normalised_model_scores[
                    candidate_role_id
                ]
            )

            if (
                "selected_skill_fit"
                in active_weights
            ):
                final_score += (
                    active_weights[
                        "selected_skill_fit"
                    ]
                    * normalised_skill_fit_scores[
                        candidate_role_id
                    ]
                )

            if (
                "current_role_similarity"
                in active_weights
            ):
                final_score += (
                    active_weights[
                        "current_role_similarity"
                    ]
                    * normalised_similarity_scores[
                        candidate_role_id
                    ]
                )

            final_scores[
                candidate_role_id
            ] = final_score


        ranked_role_ids = sorted(
            candidate_role_ids,
            key=lambda role_id: (
                -final_scores[role_id],
                role_id
            )
        )

        selected_role_ids = (
            ranked_role_ids[:2]
        )

        response = {
            "predicted_roles": [
                {
                    "id": role_id,
                    "label": self.role_labels[
                        role_id
                    ]
                }
                for role_id
                in selected_role_ids
            ]
        }


        if not return_diagnostics:
            return response


        return {
            "response": response,
            "model_input": model_input,
            "supplied_skill_count": len(
                supplied_labels
            ),
            "recognised_catalogue_skill_count": len(
                recognised_skill_ids
            ),
            "active_component_weights": (
                active_weights
            ),
            "top_five_candidates": [
                {
                    "id": role_id,
                    "label": self.role_labels[
                        role_id
                    ],
                    "final_ranking_score": round(
                        final_scores[role_id],
                        4
                    ),
                    "model_component": round(
                        normalised_model_scores[
                            role_id
                        ],
                        4
                    ),
                    "skill_fit_component": round(
                        normalised_skill_fit_scores[
                            role_id
                        ],
                        4
                    ),
                    "previous_role_component": round(
                        normalised_similarity_scores[
                            role_id
                        ],
                        4
                    )
                }
                for role_id
                in ranked_role_ids[:5]
            ]
        }
