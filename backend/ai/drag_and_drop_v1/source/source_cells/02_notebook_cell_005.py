# Recovered from the tested Colab notebook
# Notebook code cell: 5
# This file is source evidence and may depend on earlier notebook definitions.

# ============================================================
# CAREERTIMEMACHINE
# ITERATION 3 DRAG-AND-DROP ACTIVITY PIPELINE
# STEP 5: DEFINE THE STRICT ACTIVITY SCHEMA
# ============================================================

from pathlib import Path
from datetime import datetime, timezone
from typing import Literal
import json
import re

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

print(
    "I am defining the strict drag-and-drop "
    "activity schema."
)


# ------------------------------------------------------------
# Locations
# ------------------------------------------------------------

DRAG_DROP_ROOT = Path(
    "/content/drive/MyDrive/CareerTimeMachine/"
    "drag_and_drop_pipeline_v1"
)

DATA_DIRECTORY = DRAG_DROP_ROOT / "data"
REPORT_DIRECTORY = DRAG_DROP_ROOT / "reports"

DATA_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True
)

REPORT_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True
)


# ------------------------------------------------------------
# Shared types and constants
# ------------------------------------------------------------

DifficultyLevel = Literal[
    "guided",
    "standard",
    "challenge",
]

BlankId = Literal[
    "blank_1",
    "blank_2",
    "blank_3",
]

OptionId = Literal[
    "o1",
    "o2",
    "o3",
    "o4",
    "o5",
]

EXPECTED_BLANK_IDS = {
    "blank_1",
    "blank_2",
    "blank_3",
}

EXPECTED_OPTION_IDS = {
    "o1",
    "o2",
    "o3",
    "o4",
    "o5",
}

ALLOWED_PLACEHOLDER_PATTERN = re.compile(
    r"\{(blank_[1-3])\}"
)

ANY_PLACEHOLDER_PATTERN = re.compile(
    r"\{([^{}]+)\}"
)


# ------------------------------------------------------------
# Blank schema
# ------------------------------------------------------------

class DragDropBlank(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    blank_id: BlankId


# ------------------------------------------------------------
# Option schema
# ------------------------------------------------------------

class DragDropOption(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    option_id: OptionId

    text: str = Field(
        min_length=1,
        max_length=320
    )

    fits_blank_id: BlankId | None

    @field_validator("text")
    @classmethod
    def validate_option_text(
        cls,
        value
    ):
        cleaned_value = " ".join(
            value.split()
        )

        if not cleaned_value:
            raise ValueError(
                "Option text cannot be empty."
            )

        if "{" in cleaned_value or "}" in cleaned_value:
            raise ValueError(
                "Option text cannot contain "
                "blank placeholders."
            )

        return cleaned_value


# ------------------------------------------------------------
# Feedback schema
# ------------------------------------------------------------

class DragDropOptionFeedback(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    what_to_improve: str | None = Field(
        default=None,
        max_length=500
    )

    why: str = Field(
        min_length=1,
        max_length=500
    )

    @field_validator(
        "what_to_improve",
        "why"
    )
    @classmethod
    def clean_feedback_text(
        cls,
        value
    ):
        if value is None:
            return None

        cleaned_value = " ".join(
            value.split()
        )

        if not cleaned_value:
            raise ValueError(
                "Feedback text cannot be empty."
            )

        return cleaned_value


# ------------------------------------------------------------
# Exact AI response schema
# ------------------------------------------------------------

class GeneratedDragDropActivity(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    title: str = Field(
        min_length=1,
        max_length=120
    )

    situation: str = Field(
        min_length=1,
        max_length=700
    )

    sentence_template: str = Field(
        min_length=1,
        max_length=900
    )

    blanks: list[
        DragDropBlank
    ] = Field(
        min_length=3,
        max_length=3
    )

    options: list[
        DragDropOption
    ] = Field(
        min_length=5,
        max_length=5
    )

    feedback_by_option: dict[
        OptionId,
        DragDropOptionFeedback
    ]

    skills_used: list[str] = Field(
        min_length=1,
        max_length=5
    )

    guidance: list[str] = Field(
        max_length=3
    )

    @field_validator(
        "title",
        "situation",
        "sentence_template"
    )
    @classmethod
    def clean_main_text(
        cls,
        value
    ):
        cleaned_value = " ".join(
            value.split()
        )

        if not cleaned_value:
            raise ValueError(
                "Required activity text "
                "cannot be empty."
            )

        return cleaned_value

    @field_validator("skills_used")
    @classmethod
    def validate_skills_used(
        cls,
        values
    ):
        cleaned_values = []
        observed_values = set()

        for value in values:
            cleaned_value = " ".join(
                value.split()
            )

            if not cleaned_value:
                raise ValueError(
                    "Skills used cannot contain "
                    "an empty value."
                )

            if len(cleaned_value) > 120:
                raise ValueError(
                    "A skill label exceeds "
                    "120 characters."
                )

            normalised_value = (
                cleaned_value.casefold()
            )

            if normalised_value in observed_values:
                raise ValueError(
                    "Skills used must be unique."
                )

            observed_values.add(
                normalised_value
            )

            cleaned_values.append(
                cleaned_value
            )

        return cleaned_values

    @field_validator("guidance")
    @classmethod
    def validate_guidance(
        cls,
        values
    ):
        cleaned_values = []

        for value in values:
            cleaned_value = " ".join(
                value.split()
            )

            if not cleaned_value:
                raise ValueError(
                    "Guidance cannot contain "
                    "an empty value."
                )

            if len(cleaned_value) > 500:
                raise ValueError(
                    "A guidance item exceeds "
                    "500 characters."
                )

            cleaned_values.append(
                cleaned_value
            )

        return cleaned_values

    @model_validator(mode="after")
    def validate_complete_activity(
        self
    ):
        # Verify blank identifiers.
        blank_ids = [
            blank.blank_id
            for blank in self.blanks
        ]

        if set(blank_ids) != EXPECTED_BLANK_IDS:
            raise ValueError(
                "The activity must contain "
                "blank_1, blank_2 and blank_3."
            )

        if len(blank_ids) != len(
            set(blank_ids)
        ):
            raise ValueError(
                "Blank identifiers must be unique."
            )

        # Verify placeholders.
        placeholders = (
            ANY_PLACEHOLDER_PATTERN.findall(
                self.sentence_template
            )
        )

        if len(placeholders) != 3:
            raise ValueError(
                "The sentence template must "
                "contain exactly three placeholders."
            )

        if set(placeholders) != EXPECTED_BLANK_IDS:
            raise ValueError(
                "The sentence template must use "
                "blank_1, blank_2 and blank_3."
            )

        for blank_id in EXPECTED_BLANK_IDS:
            if placeholders.count(blank_id) != 1:
                raise ValueError(
                    f"{blank_id} must appear "
                    "exactly once."
                )

        # Verify option identifiers.
        option_ids = [
            option.option_id
            for option in self.options
        ]

        if set(option_ids) != EXPECTED_OPTION_IDS:
            raise ValueError(
                "The activity must contain "
                "o1, o2, o3, o4 and o5."
            )

        if len(option_ids) != len(
            set(option_ids)
        ):
            raise ValueError(
                "Option identifiers must be unique."
            )

        # Verify option text uniqueness.
        normalised_option_text = [
            option.text.casefold()
            for option in self.options
        ]

        if len(normalised_option_text) != len(
            set(normalised_option_text)
        ):
            raise ValueError(
                "All option text must be unique."
            )

        # Verify intended options and distractors.
        intended_options = [
            option
            for option in self.options
            if option.fits_blank_id
            is not None
        ]

        distractor_options = [
            option
            for option in self.options
            if option.fits_blank_id
            is None
        ]

        if len(intended_options) != 3:
            raise ValueError(
                "Exactly three options must "
                "carry a fits_blank_id."
            )

        if len(distractor_options) != 2:
            raise ValueError(
                "Exactly two options must have "
                "fits_blank_id set to null."
            )

        intended_blank_ids = [
            option.fits_blank_id
            for option in intended_options
        ]

        if (
            set(intended_blank_ids)
            != EXPECTED_BLANK_IDS
        ):
            raise ValueError(
                "Each blank must be assigned "
                "exactly one intended option."
            )

        if len(intended_blank_ids) != len(
            set(intended_blank_ids)
        ):
            raise ValueError(
                "An intended blank mapping "
                "cannot be reused."
            )

        # Verify feedback coverage.
        feedback_ids = set(
            self.feedback_by_option.keys()
        )

        if feedback_ids != EXPECTED_OPTION_IDS:
            raise ValueError(
                "Feedback must be provided "
                "for all five options."
            )

        option_by_id = {
            option.option_id: option
            for option in self.options
        }

        # Intended options use positive explanatory
        # feedback. Distractors require an improvement.
        for option_id, feedback in (
            self.feedback_by_option.items()
        ):
            option = option_by_id[
                option_id
            ]

            if (
                option.fits_blank_id is not None
                and feedback.what_to_improve
                is not None
            ):
                raise ValueError(
                    "An intended option must use "
                    "null for what_to_improve."
                )

            if (
                option.fits_blank_id is None
                and feedback.what_to_improve
                is None
            ):
                raise ValueError(
                    "A distractor must include "
                    "constructive improvement advice."
                )

        return self


# ------------------------------------------------------------
# Static dataset record schema
# ------------------------------------------------------------

class StaticDragDropRecord(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    activity_id: str = Field(
        min_length=1,
        max_length=160,
        pattern=(
            r"^[a-z0-9_]+_"
            r"(guided|standard|challenge)_"
            r"v1_0[1-4]$"
        )
    )

    role_id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9_]+$"
    )

    role_label: str = Field(
        min_length=1,
        max_length=120
    )

    difficulty: DifficultyLevel

    target_skills: list[str] = Field(
        min_length=1,
        max_length=5
    )

    activity: GeneratedDragDropActivity

    @field_validator(
        "role_label"
    )
    @classmethod
    def clean_role_label(
        cls,
        value
    ):
        return " ".join(
            value.split()
        )

    @field_validator(
        "target_skills"
    )
    @classmethod
    def validate_target_skills(
        cls,
        values
    ):
        cleaned_values = []
        observed_values = set()

        for value in values:
            cleaned_value = " ".join(
                value.split()
            )

            if not cleaned_value:
                raise ValueError(
                    "Target skills cannot "
                    "contain an empty value."
                )

            normalised_value = (
                cleaned_value.casefold()
            )

            if normalised_value in observed_values:
                raise ValueError(
                    "Target skills must be unique."
                )

            observed_values.add(
                normalised_value
            )

            cleaned_values.append(
                cleaned_value
            )

        return cleaned_values

    @model_validator(mode="after")
    def validate_static_record(
        self
    ):
        expected_identifier_prefix = (
            f"{self.role_id}_"
            f"{self.difficulty}_v1_"
        )

        if not self.activity_id.startswith(
            expected_identifier_prefix
        ):
            raise ValueError(
                "The activity identifier does "
                "not match its role and difficulty."
            )

        target_skill_lookup = {
            skill.casefold()
            for skill in self.target_skills
        }

        used_skill_lookup = {
            skill.casefold()
            for skill
            in self.activity.skills_used
        }

        if not used_skill_lookup.issubset(
            target_skill_lookup
        ):
            raise ValueError(
                "Every skill used must appear "
                "in the target skill list."
            )

        if (
            self.difficulty == "guided"
            and len(
                self.activity.guidance
            ) < 1
        ):
            raise ValueError(
                "A guided activity requires "
                "at least one guidance item."
            )

        if (
            self.difficulty == "challenge"
            and len(
                self.activity.guidance
            ) != 0
        ):
            raise ValueError(
                "A challenge activity must not "
                "contain guidance."
            )

        return self


# ------------------------------------------------------------
# Validate one complete example
# ------------------------------------------------------------

TEST_RECORD = {
    "activity_id": (
        "software_developer_guided_v1_01"
    ),
    "role_id": "software_developer",
    "role_label": "Software Developer",
    "difficulty": "guided",
    "target_skills": [
        "Stakeholder communication"
    ],
    "activity": {
        "title": (
            "Explaining a Deployment Delay"
        ),
        "situation": (
            "A deployment is running late and "
            "a manager needs a concise update."
        ),
        "sentence_template": (
            "The deployment is delayed because "
            "{blank_1}. We expect it to be "
            "resolved by {blank_2}. In the "
            "meantime, {blank_3}."
        ),
        "blanks": [
            {"blank_id": "blank_1"},
            {"blank_id": "blank_2"},
            {"blank_id": "blank_3"},
        ],
        "options": [
            {
                "option_id": "o1",
                "text": (
                    "an integration test failed "
                    "late in the pipeline"
                ),
                "fits_blank_id": "blank_1",
            },
            {
                "option_id": "o2",
                "text": "tomorrow afternoon",
                "fits_blank_id": "blank_2",
            },
            {
                "option_id": "o3",
                "text": (
                    "I will send another update "
                    "if the timeline changes"
                ),
                "fits_blank_id": "blank_3",
            },
            {
                "option_id": "o4",
                "text": (
                    "something probably stopped "
                    "working"
                ),
                "fits_blank_id": None,
            },
            {
                "option_id": "o5",
                "text": (
                    "nothing else can be done"
                ),
                "fits_blank_id": None,
            },
        ],
        "feedback_by_option": {
            "o1": {
                "what_to_improve": None,
                "why": (
                    "A specific cause helps the "
                    "stakeholder understand the delay."
                ),
            },
            "o2": {
                "what_to_improve": None,
                "why": (
                    "A clear timeframe helps the "
                    "stakeholder plan."
                ),
            },
            "o3": {
                "what_to_improve": None,
                "why": (
                    "A follow-up commitment establishes "
                    "a useful next step."
                ),
            },
            "o4": {
                "what_to_improve": (
                    "Name the verified cause "
                    "rather than guessing."
                ),
                "why": (
                    "Uncertain language does not "
                    "provide enough information "
                    "for planning."
                ),
            },
            "o5": {
                "what_to_improve": (
                    "Offer a practical next step."
                ),
                "why": (
                    "The stakeholder needs to know "
                    "what will happen next."
                ),
            },
        },
        "skills_used": [
            "Stakeholder communication"
        ],
        "guidance": [
            (
                "A useful status update explains "
                "the cause, timeframe and next step."
            )
        ],
    },
}

validated_test_record = (
    StaticDragDropRecord.model_validate(
        TEST_RECORD
    )
)

if (
    len(
        validated_test_record.activity.options
    )
    != 5
):
    raise RuntimeError(
        "The schema smoke test failed."
    )


# ------------------------------------------------------------
# Confirm rejection of an invalid mapping
# ------------------------------------------------------------

invalid_test_record = json.loads(
    json.dumps(TEST_RECORD)
)

invalid_test_record[
    "activity"
]["options"][1][
    "fits_blank_id"
] = "blank_1"

invalid_mapping_rejected = False

try:
    StaticDragDropRecord.model_validate(
        invalid_test_record
    )

except ValidationError:
    invalid_mapping_rejected = True

if not invalid_mapping_rejected:
    raise RuntimeError(
        "The schema did not reject an "
        "invalid duplicate blank mapping."
    )


# ------------------------------------------------------------
# Save JSON schemas
# ------------------------------------------------------------

AI_RESPONSE_SCHEMA_FILE = (
    DATA_DIRECTORY
    / "drag_and_drop_ai_response_"
      "schema_v1.json"
)

STATIC_RECORD_SCHEMA_FILE = (
    DATA_DIRECTORY
    / "drag_and_drop_static_record_"
      "schema_v1.json"
)

with AI_RESPONSE_SCHEMA_FILE.open(
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        GeneratedDragDropActivity.model_json_schema(),
        file,
        indent=2,
        ensure_ascii=False
    )

with STATIC_RECORD_SCHEMA_FILE.open(
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        StaticDragDropRecord.model_json_schema(),
        file,
        indent=2,
        ensure_ascii=False
    )


# ------------------------------------------------------------
# Save schema-verification evidence
# ------------------------------------------------------------

SCHEMA_VERIFICATION_REPORT = {
    "report_name": (
        "drag_and_drop_schema_"
        "verification_v1"
    ),
    "created_at_utc": datetime.now(
        timezone.utc
    ).isoformat(),
    "ai_response_fields": list(
        GeneratedDragDropActivity.model_fields.keys()
    ),
    "static_record_fields": list(
        StaticDragDropRecord.model_fields.keys()
    ),
    "required_blank_ids": sorted(
        EXPECTED_BLANK_IDS
    ),
    "required_option_ids": sorted(
        EXPECTED_OPTION_IDS
    ),
    "intended_option_count": 3,
    "distractor_option_count": 2,
    "feedback_required_for_all_options": True,
    "unexpected_fields_forbidden": True,
    "invalid_mapping_rejected": (
        invalid_mapping_rejected
    ),
    "valid_example_passed": True,
    "ai_response_schema_file": str(
        AI_RESPONSE_SCHEMA_FILE
    ),
    "static_record_schema_file": str(
        STATIC_RECORD_SCHEMA_FILE
    ),
}

SCHEMA_VERIFICATION_FILE = (
    REPORT_DIRECTORY
    / "drag_and_drop_schema_"
      "verification_v1.json"
)

with SCHEMA_VERIFICATION_FILE.open(
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        SCHEMA_VERIFICATION_REPORT,
        file,
        indent=2,
        ensure_ascii=False
    )


# ------------------------------------------------------------
# Report completion
# ------------------------------------------------------------

print(
    "\nI successfully validated the "
    "drag-and-drop response schema."
)

print(
    "I confirmed exactly three blanks."
)

print(
    "I confirmed exactly five options."
)

print(
    "I confirmed exactly three intended "
    "placements and two distractors."
)

print(
    "I confirmed feedback is required "
    "for all five options."
)

print(
    "I confirmed duplicate blank mappings "
    "are rejected."
)

print(
    "I confirmed unexpected fields "
    "are forbidden."
)

print(
    "\nI saved the AI response schema to:"
)
print(AI_RESPONSE_SCHEMA_FILE)

print(
    "\nI saved the static record schema to:"
)
print(STATIC_RECORD_SCHEMA_FILE)

print(
    "\nI saved my verification evidence to:"
)
print(SCHEMA_VERIFICATION_FILE)

print(
    "\nSTEP 5 COMPLETE"
)