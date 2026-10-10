
from __future__ import annotations

from typing import Literal
import re

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


Difficulty = Literal[
    "guided",
    "standard",
    "challenge",
]

OptionId = Literal["a", "b", "c", "d"]


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class CodeReviewOption(StrictModel):
    option_id: OptionId

    text: str = Field(
        min_length=1,
        max_length=500,
    )


class SkillToExplore(StrictModel):
    skill: str = Field(
        min_length=1,
        max_length=120,
    )

    why_relevant: str = Field(
        min_length=1,
        max_length=500,
    )


class CodeReviewFeedback(StrictModel):
    what_worked_well: list[str] = Field(
        min_length=1,
        max_length=2,
    )

    areas_to_consider: list[str] = Field(
        min_length=1,
        max_length=2,
    )

    skill_to_explore: SkillToExplore


class CodeReviewOptionFeedback(StrictModel):
    option_id: OptionId
    feedback: CodeReviewFeedback


class StaticCodeReviewRecord(StrictModel):
    question_id: str = Field(
        min_length=1,
        max_length=160,
        pattern=(
            r"^[a-z0-9_]+_"
            r"(guided|standard|challenge)_"
            r"code_review_v1_[0-9]{2}$"
        ),
    )

    role_id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9_]+$",
    )

    role_label: str = Field(
        min_length=1,
        max_length=160,
    )

    difficulty: Difficulty

    activity_type: Literal["code_review"]

    title: str = Field(
        min_length=1,
        max_length=120,
    )

    situation: str = Field(
        min_length=1,
        max_length=700,
    )

    language: str = Field(
        min_length=1,
        max_length=60,
        pattern=r"^[a-zA-Z0-9+#./ _-]+$",
    )

    code_snippet: str = Field(
        min_length=10,
        max_length=5000,
    )

    options: list[CodeReviewOption] = Field(
        min_length=4,
        max_length=4,
    )

    correct_option_id: OptionId

    skills_used: list[str] = Field(
        min_length=1,
        max_length=4,
    )

    guidance: list[str] = Field(
        min_length=0,
        max_length=2,
    )

    option_feedback: list[
        CodeReviewOptionFeedback
    ] = Field(
        min_length=4,
        max_length=4,
    )

    @model_validator(mode="after")
    def validate_complete_record(self):
        expected_ids = {"a", "b", "c", "d"}

        option_ids = [
            option.option_id
            for option in self.options
        ]

        if len(set(option_ids)) != 4:
            raise ValueError(
                "Option identifiers must be unique."
            )

        if set(option_ids) != expected_ids:
            raise ValueError(
                "Options must use identifiers a, b, c and d."
            )

        feedback_ids = [
            item.option_id
            for item in self.option_feedback
        ]

        if len(set(feedback_ids)) != 4:
            raise ValueError(
                "Feedback option identifiers must be unique."
            )

        if set(feedback_ids) != expected_ids:
            raise ValueError(
                "Feedback is required for all four options."
            )

        if self.correct_option_id not in option_ids:
            raise ValueError(
                "The correct option must exist in the options."
            )

        option_texts = [
            option.text.casefold()
            for option in self.options
        ]

        if len(set(option_texts)) != 4:
            raise ValueError(
                "Option text must be distinct."
            )

        prohibited_option_phrases = (
            "all of the above",
            "none of the above",
            "obviously correct",
            "obviously wrong",
            "correct answer",
            "wrong answer",
        )

        for option in self.options:
            lowered = option.text.casefold()

            if any(
                phrase in lowered
                for phrase in prohibited_option_phrases
            ):
                raise ValueError(
                    "Options must not contain answer-marking "
                    "or shortcut phrases."
                )

        if "```" in self.code_snippet:
            raise ValueError(
                "code_snippet must contain raw text without "
                "Markdown code fences."
            )

        non_empty_lines = [
            line
            for line in self.code_snippet.splitlines()
            if line.strip()
        ]

        if not 3 <= len(non_empty_lines) <= 30:
            raise ValueError(
                "The code snippet must contain between "
                "3 and 30 non-empty lines."
            )

        expected_guidance_counts = {
            "guided": 2,
            "standard": 1,
            "challenge": 0,
        }

        required_guidance_count = (
            expected_guidance_counts[
                self.difficulty
            ]
        )

        if (
            len(self.guidance)
            != required_guidance_count
        ):
            raise ValueError(
                f"{self.difficulty} activities require "
                f"exactly {required_guidance_count} "
                "guidance item(s)."
            )

        normalised_skills = [
            skill.casefold()
            for skill in self.skills_used
        ]

        if (
            len(normalised_skills)
            != len(set(normalised_skills))
        ):
            raise ValueError(
                "skills_used must not contain duplicates."
            )

        # Reject direct judgement of the learner's response,
        # while allowing neutral technical phrases such as
        # "failed transaction", "incorrect state" or
        # "failure handling".
        judgemental_pattern = re.compile(
            r"\b(?:"
            r"wrong answer|"
            r"incorrect answer|"
            r"bad answer|"
            r"your (?:answer|choice|response) "
            r"(?:is|was) (?:wrong|incorrect)|"
            r"you (?:are|were) wrong|"
            r"you failed|"
            r"obvious mistake|"
            r"you should have"
            r")\b",
            flags=re.IGNORECASE,
        )

        for item in self.option_feedback:
            feedback_texts = (
                item.feedback.what_worked_well
                + item.feedback.areas_to_consider
                + [
                    item.feedback.skill_to_explore.skill,
                    item.feedback.skill_to_explore.why_relevant,
                ]
            )

            for text in feedback_texts:
                if judgemental_pattern.search(text):
                    raise ValueError(
                        "Feedback must be constructive and "
                        "must not label the learner's choice "
                        "as wrong or failed."
                    )

        return self


class BackendCodeReviewActivity(StrictModel):
    question_id: str
    activity_type: Literal["code_review"]
    title: str
    situation: str
    language: str
    code_snippet: str
    options: list[CodeReviewOption]
    correct_option_id: OptionId
    skills_used: list[str]
    guidance: list[str]
    option_feedback: list[
        CodeReviewOptionFeedback
    ]


class FrontendCodeReviewActivity(StrictModel):
    question_id: str
    activity_type: Literal["code_review"]
    title: str
    situation: str
    language: str
    code_snippet: str
    options: list[CodeReviewOption]
    skills_used: list[str]
    guidance: list[str]


class CodeReviewFeedbackResponse(StrictModel):
    what_worked_well: list[str] = Field(
        min_length=1,
        max_length=2,
    )

    areas_to_consider: list[str] = Field(
        min_length=1,
        max_length=2,
    )

    skill_to_explore: SkillToExplore


def create_backend_activity(
    record: StaticCodeReviewRecord,
) -> BackendCodeReviewActivity:
    return BackendCodeReviewActivity(
        question_id=record.question_id,
        activity_type=record.activity_type,
        title=record.title,
        situation=record.situation,
        language=record.language,
        code_snippet=record.code_snippet,
        options=record.options,
        correct_option_id=(
            record.correct_option_id
        ),
        skills_used=record.skills_used,
        guidance=record.guidance,
        option_feedback=record.option_feedback,
    )


def create_frontend_safe_activity(
    record: StaticCodeReviewRecord,
) -> FrontendCodeReviewActivity:
    return FrontendCodeReviewActivity(
        question_id=record.question_id,
        activity_type=record.activity_type,
        title=record.title,
        situation=record.situation,
        language=record.language,
        code_snippet=record.code_snippet,
        options=record.options,
        skills_used=record.skills_used,
        guidance=record.guidance,
    )


def create_selected_feedback(
    record: StaticCodeReviewRecord,
    selected_option_id: OptionId,
) -> CodeReviewFeedbackResponse:
    for item in record.option_feedback:
        if item.option_id == selected_option_id:
            return CodeReviewFeedbackResponse(
                **item.feedback.model_dump()
            )

    raise ValueError(
        "No feedback exists for the selected option."
    )

# Resolve postponed annotations explicitly so these models
# also work when loaded through importlib in a standalone
# backend or verification environment.
for _model_class in (
    CodeReviewOption,
    SkillToExplore,
    CodeReviewFeedback,
    CodeReviewOptionFeedback,
    StaticCodeReviewRecord,
    BackendCodeReviewActivity,
    FrontendCodeReviewActivity,
    CodeReviewFeedbackResponse,
):
    _model_class.model_rebuild(
        force=True,
        _types_namespace=globals(),
    )

