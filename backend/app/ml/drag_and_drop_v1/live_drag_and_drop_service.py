from __future__ import annotations

import hashlib
import html
import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


Difficulty = Literal[
    "guided",
    "standard",
    "challenge",
]

BlankId = Literal[
    "blank_1",
    "blank_2",
    "blank_3",
]


LIVE_MODEL = "gemini-3.5-flash-lite"
MAXIMUM_GENERATION_ATTEMPTS = 2
MAXIMUM_SKILLS = 8
MAXIMUM_RESPONSIBILITIES = 10
MAXIMUM_TEXT_LENGTH = 500


PROHIBITED_LANGUAGE_PATTERNS = [
    re.compile(
        pattern,
        flags=re.IGNORECASE,
    )
    for pattern in [
        r"\bcorrect answer\b",
        r"\bwrong answer\b",
        r"\bincorrect answer\b",
        r"\bbest option\b",
        r"\bworst option\b",
        r"\bpass(?:ed|ing)?\b",
        r"\bfail(?:ed|ing)?\b",
        r"\bscore\b",
        r"\bincompetent\b",
    ]
]


WEAK_DISTRACTOR_PATTERNS = [
    re.compile(
        pattern,
        flags=re.IGNORECASE,
    )
    for pattern in [
        r"\bjust accept everything\b",
        r"\baccept everything immediately\b",
        r"\bignore (?:the )?.* entirely\b",
        r"\bsome technical issues\b",
        r"\ba vague timeframe\b",
        r"\bnothing can be done\b",
        r"\bprobably broken\b",
        r"\bfigure it out\b",
        r"\bnot our problem\b",
        r"\bthere is no point\b",
        r"\bwhenever you have a moment\b",
    ]
]


INSTRUCTION_PATTERNS = [
    re.compile(
        pattern,
        flags=re.IGNORECASE,
    )
    for pattern in [
        r"\bignore (?:all |any )?"
        r"(?:previous|prior|system) instructions\b",
        r"\breveal (?:the )?"
        r"(?:system prompt|instructions|api key)\b",
        r"\bdeveloper message\b",
        r"\bsystem message\b",
        r"\bact as\b",
        r"\byou are now\b",
        r"<\s*(?:system|assistant|developer)\b",
        r"\bdo not follow\b.*\binstructions\b",
    ]
]


class LiveDragDropRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    role_id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9_]+$",
    )

    skills: list[str] = Field(
        min_length=1,
        max_length=MAXIMUM_SKILLS,
    )

    years_experience: str | None = Field(
        default=None,
        max_length=40,
    )

    responsibilities: list[str] = Field(
        default_factory=list,
        max_length=MAXIMUM_RESPONSIBILITIES,
    )

    difficulty: Difficulty

    activity_type: Literal[
        "drag_and_drop"
    ]

    @field_validator(
        "skills",
        "responsibilities",
    )
    @classmethod
    def validate_text_lists(
        cls,
        values,
    ):
        cleaned_values = []
        seen_values = set()

        for value in values:
            if not isinstance(value, str):
                raise ValueError(
                    "Every list item must be text."
                )

            cleaned = clean_untrusted_text(
                value,
                maximum_length=MAXIMUM_TEXT_LENGTH,
            )

            key = cleaned.casefold()

            if key not in seen_values:
                seen_values.add(key)
                cleaned_values.append(cleaned)

        return cleaned_values


class DragAndDropBlank(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    blank_id: BlankId


class DragAndDropOption(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    option_id: str = Field(
        pattern=r"^o[1-5]$"
    )

    text: str = Field(
        min_length=2,
        max_length=300,
    )

    fits_blank_id: BlankId | None


class DragAndDropFeedback(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    what_to_improve: str | None = Field(
        default=None,
        max_length=500,
    )

    why: str = Field(
        min_length=2,
        max_length=500,
    )


class GeneratedDragDropActivity(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    title: str = Field(
        min_length=2,
        max_length=120,
    )

    situation: str = Field(
        min_length=10,
        max_length=700,
    )

    sentence_template: str = Field(
        min_length=10,
        max_length=900,
    )

    blanks: list[DragAndDropBlank] = Field(
        min_length=3,
        max_length=3,
    )

    options: list[DragAndDropOption] = Field(
        min_length=5,
        max_length=5,
    )

    feedback_by_option: dict[
        str,
        DragAndDropFeedback,
    ]

    skills_used: list[str] = Field(
        min_length=1,
        max_length=8,
    )

    guidance: list[str] = Field(
        min_length=0,
        max_length=4,
    )

    @model_validator(mode="after")
    def validate_complete_activity(self):
        expected_blanks = {
            "blank_1",
            "blank_2",
            "blank_3",
        }

        blank_ids = [
            blank.blank_id
            for blank in self.blanks
        ]

        if set(blank_ids) != expected_blanks:
            raise ValueError(
                "The activity requires blank_1, "
                "blank_2 and blank_3 exactly once."
            )

        option_ids = [
            option.option_id
            for option in self.options
        ]

        expected_options = {
            "o1",
            "o2",
            "o3",
            "o4",
            "o5",
        }

        if set(option_ids) != expected_options:
            raise ValueError(
                "The activity requires options "
                "o1 through o5 exactly once."
            )

        intended_options = [
            option
            for option in self.options
            if option.fits_blank_id is not None
        ]

        distractors = [
            option
            for option in self.options
            if option.fits_blank_id is None
        ]

        if len(intended_options) != 3:
            raise ValueError(
                "Exactly three options must have "
                "an intended blank."
            )

        if len(distractors) != 2:
            raise ValueError(
                "Exactly two options must be "
                "distractors."
            )

        intended_blank_ids = {
            option.fits_blank_id
            for option in intended_options
        }

        if intended_blank_ids != expected_blanks:
            raise ValueError(
                "Each blank must have exactly one "
                "intended option."
            )

        if (
            set(self.feedback_by_option.keys())
            != expected_options
        ):
            raise ValueError(
                "Feedback is required for every "
                "option and no additional option."
            )

        for blank_id in expected_blanks:
            placeholder = (
                "{" + blank_id + "}"
            )

            if (
                self.sentence_template.count(
                    placeholder
                )
                != 1
            ):
                raise ValueError(
                    "Every blank placeholder must "
                    "appear exactly once."
                )

        return self


def clean_untrusted_text(
    value: str,
    maximum_length: int,
) -> str:
    if not isinstance(value, str):
        raise ValueError(
            "The supplied value must be text."
        )

    cleaned = html.unescape(value)
    cleaned = unicodedata.normalize(
        "NFKC",
        cleaned,
    )

    cleaned = "".join(
        character
        for character in cleaned
        if (
            character in "\n\t"
            or not unicodedata.category(
                character
            ).startswith("C")
        )
    )

    cleaned = re.sub(
        r"\s+",
        " ",
        cleaned,
    ).strip()

    if not cleaned:
        raise ValueError(
            "The supplied text cannot be empty."
        )

    if len(cleaned) > maximum_length:
        raise ValueError(
            "The supplied text exceeds the "
            "permitted length."
        )

    if any(
        pattern.search(cleaned)
        for pattern in INSTRUCTION_PATTERNS
    ):
        raise ValueError(
            "Instruction-like content is not "
            "accepted as profile evidence."
        )

    return cleaned


def normalise_activity_payload(
    payload: dict,
) -> dict:
    allowed_fields = {
        "title",
        "situation",
        "sentence_template",
        "blanks",
        "options",
        "feedback_by_option",
        "skills_used",
        "guidance",
    }

    return {
        key: payload[key]
        for key in allowed_fields
        if key in payload
    }


def validate_professional_quality(
    activity: GeneratedDragDropActivity,
    requested_skills: list[str] | None = None,
) -> None:
    activity_payload = activity.model_dump()

    combined_text = json.dumps(
        activity_payload,
        ensure_ascii=False,
    )

    prohibited_matches = [
        pattern.pattern
        for pattern in PROHIBITED_LANGUAGE_PATTERNS
        if pattern.search(combined_text)
    ]

    if prohibited_matches:
        raise ValueError(
            "The generated activity contains "
            "answer-marking or judgemental language."
        )

    distractors = [
        option
        for option in activity.options
        if option.fits_blank_id is None
    ]

    for distractor in distractors:
        if any(
            pattern.search(distractor.text)
            for pattern in WEAK_DISTRACTOR_PATTERNS
        ):
            raise ValueError(
                "A distractor is implausibly weak."
            )

        meaningful_words = re.findall(
            r"[A-Za-z0-9]+"
            r"(?:['’-][A-Za-z0-9]+)?",
            distractor.text,
        )

        if len(meaningful_words) < 4:
            raise ValueError(
                "A distractor is too short to be "
                "a credible workplace alternative."
            )

    option_texts = [
        re.sub(
            r"\s+",
            " ",
            option.text,
        ).strip().casefold()
        for option in activity.options
    ]

    if len(set(option_texts)) != 5:
        raise ValueError(
            "The five options must be distinct."
        )

    if requested_skills:
        requested_keys = {
            skill.casefold()
            for skill in requested_skills
        }

        used_keys = {
            skill.casefold()
            for skill in activity.skills_used
        }

        if not requested_keys.intersection(
            used_keys
        ):
            raise ValueError(
                "The live activity does not identify "
                "the supplied custom skill."
            )


def create_frontend_safe_activity(
    activity: GeneratedDragDropActivity
    | dict,
) -> dict:
    if isinstance(
        activity,
        GeneratedDragDropActivity,
    ):
        payload = activity.model_dump()
    else:
        payload = GeneratedDragDropActivity.model_validate(
            normalise_activity_payload(
                activity
            )
        ).model_dump()

    frontend_options = []

    for option in payload["options"]:
        frontend_options.append(
            {
                "option_id": (
                    option["option_id"]
                ),
                "text": option["text"],
            }
        )

    payload["options"] = frontend_options

    return payload


def developer_api_schema() -> dict:
    feedback_schema = {
        "type": "object",
        "properties": {
            "what_to_improve": {
                "anyOf": [
                    {"type": "string"},
                    {"type": "null"},
                ]
            },
            "why": {
                "type": "string",
            },
        },
        "required": [
            "what_to_improve",
            "why",
        ],
    }

    return {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
            },
            "situation": {
                "type": "string",
            },
            "sentence_template": {
                "type": "string",
                "description": (
                    "A workplace message template that "
                    "contains the literal strings "
                    "{blank_1}, {blank_2} and {blank_3} "
                    "exactly once each, including the "
                    "curly braces."
                ),
            },
            "blanks": {
                "type": "array",
                "minItems": 3,
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "properties": {
                        "blank_id": {
                            "type": "string",
                            "enum": [
                                "blank_1",
                                "blank_2",
                                "blank_3",
                            ],
                        }
                    },
                    "required": [
                        "blank_id",
                    ],
                },
            },
            "options": {
                "type": "array",
                "minItems": 5,
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "properties": {
                        "option_id": {
                            "type": "string",
                            "enum": [
                                "o1",
                                "o2",
                                "o3",
                                "o4",
                                "o5",
                            ],
                        },
                        "text": {
                            "type": "string",
                        },
                        "fits_blank_id": {
                            "anyOf": [
                                {
                                    "type": "string",
                                    "enum": [
                                        "blank_1",
                                        "blank_2",
                                        "blank_3",
                                    ],
                                },
                                {
                                    "type": "null",
                                },
                            ],
                        },
                    },
                    "required": [
                        "option_id",
                        "text",
                        "fits_blank_id",
                    ],
                },
            },
            "feedback_by_option": {
                "type": "object",
                "properties": {
                    "o1": feedback_schema,
                    "o2": feedback_schema,
                    "o3": feedback_schema,
                    "o4": feedback_schema,
                    "o5": feedback_schema,
                },
                "required": [
                    "o1",
                    "o2",
                    "o3",
                    "o4",
                    "o5",
                ],
            },
            "skills_used": {
                "type": "array",
                "items": {
                    "type": "string",
                },
            },
            "guidance": {
                "type": "array",
                "items": {
                    "type": "string",
                },
            },
        },
        "required": [
            "title",
            "situation",
            "sentence_template",
            "blanks",
            "options",
            "feedback_by_option",
            "skills_used",
            "guidance",
        ],
    }


def build_live_prompt(
    request: LiveDragDropRequest,
    role_label: str,
) -> str:
    responsibilities = (
        request.responsibilities
        if request.responsibilities
        else [
            "No specific responsibilities supplied"
        ]
    )

    years_experience = (
        request.years_experience
        if request.years_experience
        else "Not supplied"
    )

    evidence = {
        "role_id": request.role_id,
        "role_label": role_label,
        "custom_skills": request.skills,
        "years_experience": (
            years_experience
        ),
        "responsibilities": (
            responsibilities
        ),
        "difficulty": request.difficulty,
    }

    return f"""
Create one reflective workplace communication
drag-and-drop activity using only the supplied profile evidence.

PROFILE EVIDENCE:
{json.dumps(evidence, ensure_ascii=False, indent=2)}

RESPONSE REQUIREMENTS:
- Return JSON only.
- Create exactly three blanks: blank_1, blank_2 and blank_3.
- The sentence_template must contain these three literal
  strings exactly once each: {{blank_1}}, {{blank_2}}, {{blank_3}}.
- Keep the curly braces exactly as shown.
- Do not use square brackets, underscores, numbered gaps,
  HTML tags or unbraced names instead of these placeholders.
- Before returning JSON, count each literal placeholder and
  confirm that each appears exactly once.
- Example format:
  "We identified {{blank_1}}, expect {{blank_2}}, and will {{blank_3}}."
- Create exactly five options named o1 through o5.
- Exactly three options must map to different blanks.
- Exactly two options must use null for fits_blank_id.
- Provide feedback for all five options.
- Do not include a correct-answer, score or pass/fail field.
- Feedback must be constructive and must not call the user wrong.
- Include at least one supplied custom skill verbatim in skills_used.
- Use years of experience and responsibilities only to make the
  workplace context plausible. Do not judge seniority or competence.

DISTRACTOR QUALITY:
- Distractors must be credible professional alternatives.
- They must fit grammatically into a possible blank.
- They should be tempting but subtly incomplete or risky.
- Do not use jokes, careless caricatures or reckless phrases.
- For standard difficulty, use meaningful professional trade-offs.
- For challenge difficulty, use subtle alternatives that require
  careful judgement.
- Check the completed intended message for grammatical and logical
  coherence.

Return only the required JSON object.
""".strip()


def _walk_static_records(
    value,
    inherited_context=None,
):
    # Role and difficulty metadata may be stored in a
    # parent dictionary while the activity is nested
    # under activity, content, response or scenario.

    context = dict(
        inherited_context or {}
    )

    if isinstance(value, dict):
        for metadata_key in [
            "role_id",
            "role_label",
            "difficulty",
            "activity_id",
            "record_id",
            "question_id",
        ]:
            metadata_value = value.get(
                metadata_key
            )

            if metadata_value is not None:
                context[metadata_key] = (
                    metadata_value
                )

        required_activity_fields = {
            "title",
            "situation",
            "sentence_template",
            "blanks",
            "options",
            "feedback_by_option",
            "skills_used",
            "guidance",
        }

        # The current dictionary may itself be the
        # complete activity.
        if required_activity_fields.issubset(
            value.keys()
        ):
            record = dict(context)
            record["activity"] = value
            yield record

        # The activity may be held under a named
        # container while metadata remains in the parent.
        for container_key in [
            "activity",
            "content",
            "response",
            "scenario",
            "drag_and_drop",
        ]:
            nested_candidate = value.get(
                container_key
            )

            if (
                isinstance(
                    nested_candidate,
                    dict,
                )
                and required_activity_fields.issubset(
                    nested_candidate.keys()
                )
            ):
                record = dict(context)
                record["activity"] = (
                    nested_candidate
                )
                yield record

        # Continue recursively while preserving the
        # metadata inherited from the parent.
        for nested_value in value.values():
            if isinstance(
                nested_value,
                (dict, list),
            ):
                yield from _walk_static_records(
                    nested_value,
                    context,
                )

    elif isinstance(value, list):
        for item in value:
            yield from _walk_static_records(
                item,
                context,
            )

class LiveDragAndDropService:
    def __init__(
        self,
        static_pool_file: str | Path,
        api_key: str | None = None,
        model_name: str = LIVE_MODEL,
        client=None,
    ):
        self.static_pool_file = Path(
            static_pool_file
        )

        if not self.static_pool_file.exists():
            raise FileNotFoundError(
                "The static drag-and-drop pool "
                "was not found."
            )

        with self.static_pool_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            static_payload = json.load(file)

        raw_records = list(
            _walk_static_records(
                static_payload
            )
        )

        self.static_records = []
        self.records_by_combination = {}
        self.role_labels = {}

        seen_record_keys = set()

        for record in raw_records:
            role_id = record.get("role_id")
            difficulty = record.get(
                "difficulty"
            )

            activity_payload = record.get(
                "activity",
                record,
            )

            try:
                activity = (
                    GeneratedDragDropActivity
                    .model_validate(
                        normalise_activity_payload(
                            activity_payload
                        )
                    )
                )
            except Exception:
                continue

            record_identifier = (
                record.get("activity_id")
                or record.get("question_id")
                or record.get("record_id")
                or hashlib.sha256(
                    json.dumps(
                        activity.model_dump(),
                        sort_keys=True,
                    ).encode("utf-8")
                ).hexdigest()[:16]
            )

            unique_key = (
                role_id,
                difficulty,
                record_identifier,
            )

            if unique_key in seen_record_keys:
                continue

            seen_record_keys.add(
                unique_key
            )

            clean_record = {
                "activity_id": (
                    record_identifier
                ),
                "role_id": role_id,
                "role_label": (
                    record.get("role_label")
                    or role_id.replace(
                        "_",
                        " ",
                    ).title()
                ),
                "difficulty": difficulty,
                "activity": activity,
            }

            self.static_records.append(
                clean_record
            )

            combination = (
                role_id,
                difficulty,
            )

            self.records_by_combination.setdefault(
                combination,
                [],
            ).append(clean_record)

            self.role_labels[role_id] = (
                clean_record["role_label"]
            )

        if not self.static_records:
            raise RuntimeError(
                "No valid static drag-and-drop "
                "activities were recovered."
            )

        incomplete_combinations = [
            combination
            for combination, records
            in self.records_by_combination.items()
            if len(records) < 1
        ]

        if incomplete_combinations:
            raise RuntimeError(
                "A role-difficulty combination "
                "has no static fallback."
            )

        self.model_name = model_name
        self.api_key = (
            api_key
            or os.getenv("GEMINI_API_KEY")
        )
        self.client = client

    def _get_client(self):
        if self.client is not None:
            return self.client

        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is required for "
                "live generation."
            )

        from google import genai

        self.client = genai.Client(
            api_key=self.api_key
        )

        return self.client

    def select_static_fallback(
        self,
        request: LiveDragDropRequest,
    ) -> dict:
        combination = (
            request.role_id,
            request.difficulty,
        )

        candidates = (
            self.records_by_combination.get(
                combination
            )
        )

        if not candidates:
            raise ValueError(
                "No static fallback exists for "
                "the requested role and difficulty."
            )

        stable_input = json.dumps(
            request.model_dump(),
            sort_keys=True,
            ensure_ascii=False,
        )

        index = int(
            hashlib.sha256(
                stable_input.encode("utf-8")
            ).hexdigest(),
            16,
        ) % len(candidates)

        selected = candidates[index]

        return {
            "activity_id": (
                selected["activity_id"]
            ),
            "activity": (
                selected["activity"]
            ),
        }

    def _generate_once(
        self,
        request: LiveDragDropRequest,
    ) -> GeneratedDragDropActivity:
        from google.genai import types

        role_label = self.role_labels[
            request.role_id
        ]

        prompt = build_live_prompt(
            request,
            role_label,
        )

        response = (
            self._get_client()
            .models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type=(
                        "application/json"
                    ),
                    response_schema=(
                        developer_api_schema()
                    ),
                    temperature=0.7,
                ),
            )
        )

        if getattr(
            response,
            "parsed",
            None,
        ) is not None:
            payload = response.parsed

            if hasattr(
                payload,
                "model_dump",
            ):
                payload = payload.model_dump()
        else:
            response_text = getattr(
                response,
                "text",
                None,
            )

            if not response_text:
                raise ValueError(
                    "Gemini returned no JSON text."
                )

            payload = json.loads(
                response_text
            )

        activity = (
            GeneratedDragDropActivity
            .model_validate(payload)
        )

        validate_professional_quality(
            activity,
            requested_skills=request.skills,
        )

        return activity

    def generate(
        self,
        request: LiveDragDropRequest | dict,
        force_static_fallback: bool = False,
    ) -> dict:
        validated_request = (
            LiveDragDropRequest.model_validate(
                request
            )
        )

        if (
            validated_request.role_id
            not in self.role_labels
        ):
            raise ValueError(
                "The requested role_id is unknown."
            )

        attempts = []

        if not force_static_fallback:
            for attempt_number in range(
                1,
                MAXIMUM_GENERATION_ATTEMPTS + 1,
            ):
                try:
                    activity = self._generate_once(
                        validated_request
                    )

                    attempts.append(
                        {
                            "attempt_number": (
                                attempt_number
                            ),
                            "passed": True,
                            "error": None,
                        }
                    )

                    backend_activity = (
                        activity.model_dump()
                    )

                    return {
                        "source": "live_gemini",
                        "activity_id": (
                            validated_request.role_id
                            + "_"
                            + validated_request.difficulty
                            + "_live"
                        ),
                        "activity": backend_activity,
                        "backend_activity": (
                            backend_activity
                        ),
                        "frontend_activity": (
                            create_frontend_safe_activity(
                                activity
                            )
                        ),
                        "attempts": attempts,
                    }

                except Exception as error:
                    attempts.append(
                        {
                            "attempt_number": (
                                attempt_number
                            ),
                            "passed": False,
                            "error": (
                                type(error).__name__
                                + ": "
                                + str(error)
                            ),
                        }
                    )

        fallback = self.select_static_fallback(
            validated_request
        )

        backend_activity = (
            fallback["activity"].model_dump()
        )

        return {
            "source": "static_fallback",
            "activity_id": (
                fallback["activity_id"]
            ),
            "activity": backend_activity,
            "backend_activity": (
                backend_activity
            ),
            "frontend_activity": (
                create_frontend_safe_activity(
                    fallback["activity"]
                )
            ),
            "attempts": attempts,
        }


# STANDALONE_PYDANTIC_MODEL_REBUILD
# Resolve postponed annotations when the module is loaded
# dynamically or by the backend application.
_PYDANTIC_TYPES_NAMESPACE = dict(globals())

for _pydantic_model in [
    LiveDragDropRequest,
    DragAndDropBlank,
    DragAndDropOption,
    DragAndDropFeedback,
    GeneratedDragDropActivity,
]:
    _pydantic_model.model_rebuild(
        force=True,
        _types_namespace=(
            _PYDANTIC_TYPES_NAMESPACE
        ),
    )

