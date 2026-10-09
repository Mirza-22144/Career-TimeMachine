# Recovered from the tested Colab notebook
# Notebook code cell: 29
# This file is source evidence and may depend on earlier notebook definitions.

# ============================================================
# STEP 16B
# Strengthen live distractor quality and retest only the two
# failed balanced-evaluation cases.
# ============================================================

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path


print(
    "I am applying the live drag-and-drop "
    "distractor-quality correction."
)


# ------------------------------------------------------------
# 1. Preserve the original functions once
# ------------------------------------------------------------

if (
    "_build_live_prompt_before_plausibility_patch"
    not in globals()
):
    _build_live_prompt_before_plausibility_patch = (
        build_live_prompt
    )

if (
    "_validate_live_activity_before_plausibility_patch"
    not in globals()
):
    _validate_live_activity_before_plausibility_patch = (
        validate_live_activity
    )


# ------------------------------------------------------------
# 2. Add clearer generation requirements
# ------------------------------------------------------------

LIVE_DISTRACTOR_QUALITY_INSTRUCTIONS = """
ADDITIONAL QUALITY REQUIREMENTS:

The two distractors must be realistic professional alternatives.
They must not be jokes, careless caricatures or choices that an
experienced professional would immediately reject.

For standard and challenge activities:
- make distractors tempting but subtly incomplete or risky;
- each distractor must fit naturally into its possible sentence
  position;
- use credible trade-offs such as premature commitment,
  incomplete consultation, compressed testing, uncertain
  escalation or over-specific timelines;
- do not make the activity easy through obviously poor wording.

Do not use distractors such as:
- "we can just accept everything immediately"
- "we can ignore the timeline constraints entirely"
- "some technical issues"
- "a vague timeframe"
- "nothing can be done"
- "the system is probably broken"

Every option must:
- read naturally when placed into the sentence template;
- contain enough context to be a credible workplace phrase;
- avoid absolute or reckless language;
- remain distinct from the other options.

Check the completed intended message for grammar and meaning.
The subject causing an impact must be logically clear. For
example, the outage affects services, not the escalation process.

Difficulty expectations:
- guided: clearer distinctions with useful guidance;
- standard: plausible alternatives with meaningful trade-offs;
- challenge: subtle professional alternatives requiring careful
  judgement.
""".strip()


def build_live_prompt(*args, **kwargs):
    original_prompt = (
        _build_live_prompt_before_plausibility_patch(
            *args,
            **kwargs
        )
    )

    return (
        str(original_prompt).rstrip()
        + "\n\n"
        + LIVE_DISTRACTOR_QUALITY_INSTRUCTIONS
    )


print(
    "I strengthened the live generation prompt."
)


# ------------------------------------------------------------
# 3. Add a deterministic plausibility gate
# ------------------------------------------------------------

OBVIOUSLY_WEAK_DISTRACTOR_PATTERNS = [
    r"\bjust accept everything\b",
    r"\baccept everything immediately\b",
    r"\bignore (?:the )?.* entirely\b",
    r"\bsome technical issues\b",
    r"\ba vague timeframe\b",
    r"\bnothing can be done\b",
    r"\bprobably broken\b",
    r"\bfigure it out\b",
    r"\bwhenever you have a moment\b",
    r"\bthere is no point\b",
    r"\bnot our problem\b",
]

compiled_weak_distractor_patterns = [
    re.compile(pattern, flags=re.IGNORECASE)
    for pattern in OBVIOUSLY_WEAK_DISTRACTOR_PATTERNS
]


def _value_to_dictionary(value):
    if isinstance(value, dict):
        return value

    if hasattr(value, "model_dump"):
        return value.model_dump()

    return None


def _find_activity_payload(args, kwargs):
    candidate_values = list(args) + list(
        kwargs.values()
    )

    for candidate in candidate_values:
        candidate_dictionary = (
            _value_to_dictionary(candidate)
        )

        if not candidate_dictionary:
            continue

        required_fields = {
            "sentence_template",
            "options",
        }

        if required_fields.issubset(
            candidate_dictionary.keys()
        ):
            return candidate_dictionary

        for nested_key in [
            "activity",
            "response",
            "generated_activity",
        ]:
            nested_value = candidate_dictionary.get(
                nested_key
            )
            nested_dictionary = (
                _value_to_dictionary(nested_value)
            )

            if (
                nested_dictionary
                and required_fields.issubset(
                    nested_dictionary.keys()
                )
            ):
                return nested_dictionary

    return None


def validate_live_activity(*args, **kwargs):
    original_result = (
        _validate_live_activity_before_plausibility_patch(
            *args,
            **kwargs
        )
    )

    activity_payload = _find_activity_payload(
        args,
        kwargs,
    )

    if activity_payload is None:
        raise ValueError(
            "The generated activity could not be "
            "inspected by the plausibility gate."
        )

    options = activity_payload.get(
        "options",
        [],
    )

    distractors = [
        option
        for option in options
        if option.get("fits_blank_id") is None
    ]

    if len(distractors) != 2:
        raise ValueError(
            "The activity must contain exactly "
            "two distractors."
        )

    for distractor in distractors:
        distractor_text = str(
            distractor.get("text", "")
        ).strip()

        if any(
            pattern.search(distractor_text)
            for pattern
            in compiled_weak_distractor_patterns
        ):
            raise ValueError(
                "A distractor contains an obviously "
                "weak or unrealistic phrase: "
                f"{distractor_text}"
            )

        meaningful_words = re.findall(
            r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)?",
            distractor_text,
        )

        if len(meaningful_words) < 4:
            raise ValueError(
                "A distractor is too short to provide "
                "a credible workplace alternative: "
                f"{distractor_text}"
            )

    return original_result


print(
    "I added the deterministic professional-"
    "plausibility gate."
)


# ------------------------------------------------------------
# 4. Helper functions for different saved response shapes
# ------------------------------------------------------------

def normalise_value(value):
    if hasattr(value, "model_dump"):
        return value.model_dump()

    if isinstance(value, dict):
        return value

    if isinstance(value, list):
        return [
            normalise_value(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            normalise_value(item)
            for item in value
        ]

    return value


def extract_served_activity(served_result):
    payload = normalise_value(served_result)

    if isinstance(payload, dict):
        if {
            "title",
            "situation",
            "sentence_template",
            "options",
        }.issubset(payload.keys()):
            return payload

        for key in [
            "activity",
            "response",
            "generated_activity",
            "result",
        ]:
            nested = payload.get(key)

            if isinstance(nested, dict):
                if {
                    "title",
                    "situation",
                    "sentence_template",
                    "options",
                }.issubset(nested.keys()):
                    return nested

    raise RuntimeError(
        "I could not locate the generated activity "
        "inside the live service response."
    )


def extract_source(served_result):
    payload = normalise_value(served_result)

    if isinstance(payload, dict):
        return payload.get(
            "source",
            "unknown",
        )

    return "unknown"


def extract_attempt_count(served_result):
    payload = normalise_value(served_result)

    if isinstance(payload, dict):
        for key in [
            "attempts",
            "attempts_used",
            "generation_attempts",
        ]:
            if key in payload:
                return payload[key]

    return None


def extract_calculated_decision(
    review,
    assessment,
):
    review_payload = normalise_value(review)
    assessment_payload = normalise_value(
        assessment
    )

    possible_values = [
        assessment_payload,
        review_payload,
    ]

    for value in possible_values:
        if isinstance(value, str):
            lowered = value.strip().lower()

            if lowered in {
                "accept",
                "revision_required",
                "reject",
            }:
                return lowered

        if isinstance(value, dict):
            for key in [
                "calculated_decision",
                "decision",
                "model_decision",
                "status",
            ]:
                decision = value.get(key)

                if isinstance(decision, str):
                    decision = (
                        decision.strip().lower()
                    )

                    if decision in {
                        "accept",
                        "revision_required",
                        "reject",
                    }:
                        return decision

        if isinstance(value, list):
            for nested in value:
                if isinstance(nested, str):
                    nested = nested.strip().lower()

                    if nested in {
                        "accept",
                        "revision_required",
                        "reject",
                    }:
                        return nested

    raise RuntimeError(
        "I could not recover the calculated "
        "judge decision."
    )


# ------------------------------------------------------------
# 5. Retest only the two failed requests
# ------------------------------------------------------------

failed_live_requests = [
    {
        "test_id": "standard_project_scope",
        "request": {
            "role_id": "it_project_manager",
            "skills": [
                "Scope negotiation",
            ],
            "years_experience": "7",
            "responsibilities": [
                "Led cross-functional delivery teams",
            ],
            "difficulty": "standard",
            "activity_type": "drag_and_drop",
        },
    },
    {
        "test_id": "challenge_network_outage",
        "request": {
            "role_id": (
                "network_and_systems_administrator"
            ),
            "skills": [
                "Critical outage escalation",
            ],
            "years_experience": "8",
            "responsibilities": [
                (
                    "Coordinated on-call response "
                    "and mentored junior staff"
                ),
            ],
            "difficulty": "challenge",
            "activity_type": "drag_and_drop",
        },
    },
]

corrected_results = []

print(
    "\nI am retesting only the two activities "
    "that previously required revision."
)

for index, test_case in enumerate(
    failed_live_requests,
    start=1,
):
    test_id = test_case["test_id"]

    request_model = (
        LiveDragDropRequest.model_validate(
            test_case["request"]
        )
    )

    print("\n" + "=" * 72)
    print(
        f"[{index}/2] Retesting {test_id}."
    )

    started_at = time.perf_counter()

    served_result = (
        generate_live_drag_and_drop(
            request_model
        )
    )

    elapsed_seconds = round(
        time.perf_counter() - started_at,
        4,
    )

    activity = extract_served_activity(
        served_result
    )

    source = extract_source(served_result)
    attempts = extract_attempt_count(
        served_result
    )

    judge_result = (
        run_corrected_gemini_review(
            activity
        )
    )

    if (
        isinstance(judge_result, tuple)
        and len(judge_result) == 2
    ):
        review = judge_result[0]
        judge_attempts = judge_result[1]
    else:
        review = judge_result
        judge_attempts = None

    assessment = assess_judge_review(
        review
    )

    calculated_decision = (
        extract_calculated_decision(
            review,
            assessment,
        )
    )

    test_passed = (
        source == "live_gemini"
        and calculated_decision == "accept"
    )

    corrected_record = {
        "test_id": test_id,
        "request": test_case["request"],
        "served_source": source,
        "generation_attempts": attempts,
        "generation_latency_seconds": (
            elapsed_seconds
        ),
        "activity": activity,
        "judge_review": normalise_value(
            review
        ),
        "judge_assessment": normalise_value(
            assessment
        ),
        "judge_attempts": judge_attempts,
        "calculated_decision": (
            calculated_decision
        ),
        "test_passed": test_passed,
    }

    corrected_results.append(
        corrected_record
    )

    print(
        f"  Source: {source}"
    )
    print(
        f"  Generation attempts: {attempts}"
    )
    print(
        f"  Latency: {elapsed_seconds:.4f} seconds"
    )
    print(
        f"  Judge decision: {calculated_decision}"
    )
    print(
        f"  Test passed: {test_passed}"
    )


# ------------------------------------------------------------
# 6. Save correction evidence
# ------------------------------------------------------------

CORRECTION_REPORT_DIRECTORY = Path(
    "/content/drive/MyDrive/"
    "CareerTimeMachine/"
    "drag_and_drop_pipeline_v1/"
    "reports"
)

CORRECTION_OUTPUT_DIRECTORY = Path(
    "/content/drive/MyDrive/"
    "CareerTimeMachine/"
    "drag_and_drop_pipeline_v1/"
    "live_service/output/"
    "balanced_evaluation"
)

CORRECTION_REPORT_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)

CORRECTION_OUTPUT_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)

all_corrections_passed = all(
    result["test_passed"]
    for result in corrected_results
)

correction_report = {
    "step": "16B",
    "created_at_utc": datetime.now(
        timezone.utc
    ).isoformat(),
    "change": (
        "Strengthened the live prompt and added "
        "a deterministic professional-plausibility "
        "gate for distractors."
    ),
    "production_generation_attempt_limit": 2,
    "tests_repeated": 2,
    "tests_passed": sum(
        result["test_passed"]
        for result in corrected_results
    ),
    "all_corrections_passed": (
        all_corrections_passed
    ),
    "results": corrected_results,
}

corrected_output_file = (
    CORRECTION_OUTPUT_DIRECTORY
    / (
        "corrected_failed_live_drag_and_drop_"
        "outputs_v1.json"
    )
)

correction_report_file = (
    CORRECTION_REPORT_DIRECTORY
    / (
        "live_drag_and_drop_quality_"
        "correction_v1.json"
    )
)

with corrected_output_file.open(
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        corrected_results,
        file,
        indent=2,
        ensure_ascii=False,
        default=str,
    )

with correction_report_file.open(
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        correction_report,
        file,
        indent=2,
        ensure_ascii=False,
        default=str,
    )


print("\n" + "=" * 72)
print(
    "I completed the targeted live "
    "drag-and-drop correction."
)
print()
print(
    "Corrected tests passed: "
    f"{sum(result['test_passed'] for result in corrected_results)}/2"
)
print(
    "All corrected tests passed: "
    f"{all_corrections_passed}"
)
print()
print(
    "I preserved Step 16 as the "
    "pre-correction evidence."
)
print()
print(
    "I saved the corrected outputs to:"
)
print(corrected_output_file)
print()
print(
    "I saved the correction evidence to:"
)
print(correction_report_file)

if not all_corrections_passed:
    print()
    print(
        "STEP 16B REQUIRES REVIEW"
    )
else:
    print()
    print(
        "STEP 16B COMPLETE"
    )