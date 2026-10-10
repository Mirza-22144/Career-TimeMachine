
from typing import Literal
import re

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


ExplanationReasonCode = Literal[
    "model_profile_match",
    "selected_skill_match",
    "previous_role_similarity",
]


class RoleExplanation(BaseModel):
    """Public evidence explaining one recommended role."""

    model_config = ConfigDict(
        extra="forbid"
    )

    summary: str = Field(
        min_length=30,
        max_length=500,
    )

    matched_skills: list[str] = Field(
        default_factory=list,
        max_length=5,
    )

    reason_codes: list[
        ExplanationReasonCode
    ] = Field(
        min_length=1,
        max_length=3,
    )


    @field_validator("summary")
    @classmethod
    def validate_summary(
        cls,
        value,
    ):
        cleaned = " ".join(
            value.strip().split()
        )

        prohibited_patterns = [
            r"\b\d+(?:\.\d+)?\s*%",
            r"\bprobability\b",
            r"\bconfidence percentage\b",
            r"\bconfidence score\b",
            r"\bguaranteed\b",
            r"\bperfect match\b",
        ]

        for pattern in prohibited_patterns:
            if re.search(
                pattern,
                cleaned,
                flags=re.IGNORECASE,
            ):
                raise ValueError(
                    "The explanation must not present "
                    "an internal score as a probability "
                    "or guaranteed outcome."
                )

        return cleaned


    @field_validator("matched_skills")
    @classmethod
    def validate_matched_skills(
        cls,
        values,
    ):
        cleaned_values = []
        observed = set()

        for value in values:
            cleaned = " ".join(
                str(value).strip().split()
            )

            normalised = cleaned.casefold()

            if not cleaned:
                raise ValueError(
                    "Matched skills must not be empty."
                )

            if normalised in observed:
                raise ValueError(
                    "Matched skills must be unique."
                )

            observed.add(normalised)
            cleaned_values.append(cleaned)

        return cleaned_values


    @field_validator("reason_codes")
    @classmethod
    def validate_reason_codes(
        cls,
        values,
    ):
        if len(set(values)) != len(values):
            raise ValueError(
                "Explanation reason codes must "
                "be unique."
            )

        return values


    @model_validator(mode="after")
    def validate_evidence_alignment(self):
        has_skill_reason = (
            "selected_skill_match"
            in self.reason_codes
        )

        has_matched_skills = bool(
            self.matched_skills
        )

        if (
            has_skill_reason
            != has_matched_skills
        ):
            raise ValueError(
                "selected_skill_match must appear "
                "if and only if matched_skills "
                "contains evidence."
            )

        if (
            "model_profile_match"
            not in self.reason_codes
        ):
            raise ValueError(
                "Every recommendation must retain "
                "the trained-model ranking reason."
            )

        return self


class ExplainedPredictedRole(BaseModel):
    """One explained role recommendation."""

    model_config = ConfigDict(
        extra="forbid"
    )

    id: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z0-9_]+$",
    )

    label: str = Field(
        min_length=1,
        max_length=120,
    )

    explanation: RoleExplanation


class ExplainedPredictionResponse(BaseModel):
    """Exactly two distinct explained recommendations."""

    model_config = ConfigDict(
        extra="forbid"
    )

    predicted_roles: list[
        ExplainedPredictedRole
    ] = Field(
        min_length=2,
        max_length=2,
    )


    @model_validator(mode="after")
    def validate_distinct_roles(self):
        role_ids = [
            role.id
            for role in self.predicted_roles
        ]

        if len(set(role_ids)) != 2:
            raise ValueError(
                "The two predicted roles must "
                "be distinct."
            )

        return self
