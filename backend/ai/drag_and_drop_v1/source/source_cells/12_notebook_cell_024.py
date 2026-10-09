# Recovered from the tested Colab notebook
# Notebook code cell: 24
# This file is source evidence and may depend on earlier notebook definitions.

# ============================================================
# CAREERTIMEMACHINE
# DRAG-AND-DROP PIPELINE
# STEP 13: TARGETED REVISION OF FLAGGED ACTIVITIES
# ============================================================

from pathlib import Path
from datetime import datetime, timezone
import json
import time

from google.genai import types
from pydantic import ValidationError

print(
    "I am preparing targeted revisions "
    "for the 11 flagged activities."
)


# ------------------------------------------------------------
# Confirm runtime objects
# ------------------------------------------------------------

required_runtime_names = [
    "gemini_client",
    "GEMINI_STATIC_GENERATOR_MODEL",
    "GEMINI_JUDGE_MODEL",
    "ACTIVITY_SCHEMA",
    "GeneratedDragDropActivity",
    "StaticDragDropRecord",
    "PROHIBITED_LANGUAGE_PATTERNS",
    "run_corrected_gemini_review",
    "assess_judge_review",
]

missing_runtime_names = [
    name
    for name in required_runtime_names
    if name not in globals()
]

if missing_runtime_names:
    raise RuntimeError(
        "I am missing required runtime objects: "
        + ", ".join(missing_runtime_names)
    )


# ------------------------------------------------------------
# Locations
# ------------------------------------------------------------

DRAG_DROP_ROOT = Path(
    "/content/drive/MyDrive/CareerTimeMachine/"
    "drag_and_drop_pipeline_v1"
)

DATA_DIRECTORY = DRAG_DROP_ROOT / "data"
OUTPUT_DIRECTORY = DRAG_DROP_ROOT / "output"
REPORT_DIRECTORY = DRAG_DROP_ROOT / "reports"

REVISION_CHECKPOINT_DIRECTORY = (
    DRAG_DROP_ROOT
    / "checkpoints"
    / "targeted_revisions"
)

REVISION_CHECKPOINT_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True
)

GENERATED_POOL_FILE = (
    OUTPUT_DIRECTORY
    / "drag_and_drop_activity_"
      "pool_v1_generated.json"
)

GENERATION_PLAN_FILE = (
    DATA_DIRECTORY
    / "drag_and_drop_generation_"
      "plan_v1_324.json"
)

REVISION_LIST_FILE = (
    REPORT_DIRECTORY
    / "drag_and_drop_activities_"
      "requiring_revision_v1.json"
)

REVIEWED_POOL_FILE = (
    OUTPUT_DIRECTORY
    / "drag_and_drop_activity_"
      "pool_v1_reviewed.json"
)

FINAL_REVISION_REPORT_FILE = (
    REPORT_DIRECTORY
    / "drag_and_drop_targeted_"
      "revision_report_v1.json"
)


# ------------------------------------------------------------
# Load source data
# ------------------------------------------------------------

with GENERATED_POOL_FILE.open(
    "r",
    encoding="utf-8"
) as file:
    generated_pool = json.load(file)

with GENERATION_PLAN_FILE.open(
    "r",
    encoding="utf-8"
) as file:
    generation_plan = json.load(file)

with REVISION_LIST_FILE.open(
    "r",
    encoding="utf-8"
) as file:
    revision_list = json.load(file)

generated_records = (
    generated_pool["activities"]
)

generation_tasks = (
    generation_plan[
        "generation_tasks"
    ]
)

flagged_review_records = (
    revision_list["activities"]
)

record_by_id = {
    record["activity_id"]: record
    for record
    in generated_records
}

task_by_id = {
    task["activity_id"]: task
    for task in generation_tasks
}

flagged_review_by_id = {
    record["activity_id"]: record
    for record
    in flagged_review_records
}

flagged_activity_ids = sorted(
    flagged_review_by_id.keys()
)

if len(flagged_activity_ids) != 11:
    print(
        "The current revision list contains "
        f"{len(flagged_activity_ids)} activities."
    )

if not flagged_activity_ids:
    raise RuntimeError(
        "The revision list is empty."
    )

unknown_flagged_ids = [
    activity_id
    for activity_id
    in flagged_activity_ids
    if (
        activity_id not in record_by_id
        or activity_id not in task_by_id
    )
]

if unknown_flagged_ids:
    raise RuntimeError(
        "I found flagged identifiers that "
        "are missing from the pool or plan."
    )


# ------------------------------------------------------------
# Display revision reasons
# ------------------------------------------------------------

print(
    "\nI found these activities requiring "
    "targeted revision:"
)

for activity_id in flagged_activity_ids:
    review_record = (
        flagged_review_by_id[
            activity_id
        ]
    )

    review = review_record[
        "review"
    ]

    print(
        "\n  - "
        f"{activity_id}"
    )

    for issue in review["issues"]:
        print(
            "    "
            f"{issue['severity']} | "
            f"{issue['criterion']}: "
            f"{issue['explanation'][:300]}"
        )


# ------------------------------------------------------------
# Build targeted revision prompt
# ------------------------------------------------------------

def build_revision_prompt(
    original_record,
    task,
    review_record,
    previous_errors=None
):
    review = review_record[
        "review"
    ]

    issue_instructions = [
        {
            "severity": issue[
                "severity"
            ],
            "criterion": issue[
                "criterion"
            ],
            "problem": issue[
                "explanation"
            ],
            "recommended_fix": issue[
                "recommended_fix"
            ],
        }
        for issue in review["issues"]
    ]

    if not issue_instructions:
        issue_instructions = [
            {
                "severity": "major",
                "criterion": (
                    "overall_quality"
                ),
                "problem": (
                    review["summary"]
                ),
                "recommended_fix": (
                    "Improve the activity according "
                    "to the review summary."
                ),
            }
        ]

    correction_text = ""

    if previous_errors:
        correction_text = (
            "\nPREVIOUS REVISION ERRORS\n"
            + "\n".join(
                f"- {error}"
                for error
                in previous_errors[:10]
            )
        )

    return f"""
Revise one workplace communication drag-and-drop activity.

ORIGINAL RECORD
{json.dumps(original_record, indent=2, ensure_ascii=False)}

QUALITY REVIEW
{json.dumps(issue_instructions, indent=2, ensure_ascii=False)}

GENERATION CONSTRAINTS
Role: {task["role_label"]}
Difficulty: {task["difficulty"]}
Communication theme:
{json.dumps(task["communication_theme"], ensure_ascii=False)}

Allowed skill labels:
{json.dumps(task["candidate_skill_labels"], ensure_ascii=False)}

Return a complete replacement activity.

The replacement must:

1. Correct every review issue.
2. Retain the same role, difficulty and communication theme.
3. Use one to three exact allowed skill labels.
4. Contain exactly three placeholders:
   {{blank_1}}, {{blank_2}} and {{blank_3}}.
5. Contain exactly five options.
6. Map exactly three options to three different blanks.
7. Give exactly two distractors a null fits_blank_id.
8. Complete the message naturally and grammatically.
9. Make distractors plausible but less specific, accountable,
   actionable or suitable.
10. Provide feedback for all five options.
11. Use what_to_improve null for intended options.
12. Give distractors constructive improvement advice.
13. Avoid correct, incorrect, right, wrong, best answer, pass,
    fail, competent and incompetent language.
14. Avoid personal or employability judgement.
15. Use British English.
16. Return no activity_id and no unexpected fields.

Guided requires at least one guidance item.
Challenge requires an empty guidance array.
{correction_text}
""".strip()


# ------------------------------------------------------------
# Local replacement validation
# ------------------------------------------------------------

def validate_replacement_activity(
    raw_activity,
    task
):
    errors = []

    try:
        validated_activity = (
            GeneratedDragDropActivity
            .model_validate(
                raw_activity
            )
        )

    except ValidationError as error:
        return None, [
            str(error)
        ]

    allowed_skill_lookup = {
        label.casefold(): label
        for label in task[
            "candidate_skill_labels"
        ]
    }

    invalid_skills = [
        skill
        for skill
        in validated_activity.skills_used
        if skill.casefold()
        not in allowed_skill_lookup
    ]

    if invalid_skills:
        errors.append(
            "skills_used contains labels "
            "outside the allowed catalogue: "
            + ", ".join(invalid_skills)
        )

    canonical_skills = []

    if not invalid_skills:
        canonical_skills = [
            allowed_skill_lookup[
                skill.casefold()
            ]
            for skill
            in validated_activity.skills_used
        ]

    activity_payload = (
        validated_activity.model_dump()
    )

    if canonical_skills:
        activity_payload[
            "skills_used"
        ] = canonical_skills

    serialised_text = json.dumps(
        activity_payload,
        ensure_ascii=False
    )

    prohibited_findings = []

    for pattern in (
        PROHIBITED_LANGUAGE_PATTERNS
    ):
        match = pattern.search(
            serialised_text
        )

        if match:
            prohibited_findings.append(
                match.group(0)
            )

    if prohibited_findings:
        errors.append(
            "Prohibited language found: "
            + ", ".join(
                sorted(
                    set(
                        prohibited_findings
                    )
                )
            )
        )

    if errors:
        return None, errors

    static_payload = {
        "activity_id": task[
            "activity_id"
        ],
        "role_id": task[
            "role_id"
        ],
        "role_label": task[
            "role_label"
        ],
        "difficulty": task[
            "difficulty"
        ],
        "target_skills": (
            canonical_skills
        ),
        "activity": (
            activity_payload
        ),
    }

    try:
        validated_record = (
            StaticDragDropRecord
            .model_validate(
                static_payload
            )
        )

    except ValidationError as error:
        return None, [
            str(error)
        ]

    return (
        validated_record.model_dump(),
        []
    )


# ------------------------------------------------------------
# Revision checkpoint helpers
# ------------------------------------------------------------

def revision_checkpoint_file(
    activity_id
):
    return (
        REVISION_CHECKPOINT_DIRECTORY
        / f"{activity_id}_revision_v1.json"
    )


def load_revision_checkpoint(
    activity_id
):
    checkpoint_file = (
        revision_checkpoint_file(
            activity_id
        )
    )

    if not checkpoint_file.exists():
        return None

    try:
        with checkpoint_file.open(
            "r",
            encoding="utf-8"
        ) as file:
            payload = json.load(file)

        validated_record = (
            StaticDragDropRecord
            .model_validate(
                payload[
                    "revised_record"
                ]
            )
        )

        if (
            payload[
                "final_assessment"
            ][
                "calculated_decision"
            ]
            != "accept"
        ):
            return None

        return {
            **payload,
            "revised_record": (
                validated_record.model_dump()
            ),
        }

    except Exception:
        return None


def save_revision_checkpoint(
    activity_id,
    payload
):
    checkpoint_file = (
        revision_checkpoint_file(
            activity_id
        )
    )

    temporary_file = (
        checkpoint_file.with_suffix(
            ".tmp"
        )
    )

    with temporary_file.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            payload,
            file,
            indent=2,
            ensure_ascii=False
        )

    temporary_file.replace(
        checkpoint_file
    )


# ------------------------------------------------------------
# Generate and judge one replacement
# ------------------------------------------------------------

def revise_one_activity(
    original_record,
    task,
    original_review_record,
    maximum_attempts=4
):
    attempt_evidence = []
    previous_errors = []

    active_review_record = (
        original_review_record
    )

    for attempt_number in range(
        1,
        maximum_attempts + 1
    ):
        prompt = build_revision_prompt(
            original_record=(
                original_record
            ),
            task=task,
            review_record=(
                active_review_record
            ),
            previous_errors=(
                previous_errors
            ),
        )

        generation_started = (
            time.perf_counter()
        )

        try:
            response = (
                gemini_client.models
                .generate_content(
                    model=(
                        GEMINI_STATIC_GENERATOR_MODEL
                    ),
                    contents=prompt,
                    config=(
                        types.GenerateContentConfig(
                            temperature=0.55,
                            top_p=0.85,
                            response_mime_type=(
                                "application/json"
                            ),
                            response_schema=(
                                ACTIVITY_SCHEMA
                            ),
                        )
                    ),
                )
            )

            raw_activity = json.loads(
                response.text
            )

            revised_record, (
                validation_errors
            ) = validate_replacement_activity(
                raw_activity,
                task,
            )

            generation_latency = round(
                time.perf_counter()
                - generation_started,
                4
            )

            if validation_errors:
                attempt_evidence.append(
                    {
                        "attempt_number": (
                            attempt_number
                        ),
                        "generation_latency_seconds": (
                            generation_latency
                        ),
                        "local_validation_passed": False,
                        "errors": (
                            validation_errors
                        ),
                    }
                )

                previous_errors = (
                    validation_errors
                )
                continue

            judge_review, judge_attempts = (
                run_corrected_gemini_review(
                    revised_record
                )
            )

            judge_assessment = (
                assess_judge_review(
                    judge_review
                )
            )

            attempt_evidence.append(
                {
                    "attempt_number": (
                        attempt_number
                    ),
                    "generation_latency_seconds": (
                        generation_latency
                    ),
                    "local_validation_passed": True,
                    "judge_review": (
                        judge_review
                    ),
                    "judge_assessment": (
                        judge_assessment
                    ),
                    "judge_attempts": (
                        judge_attempts
                    ),
                }
            )

            if (
                judge_assessment[
                    "calculated_decision"
                ]
                == "accept"
                and judge_assessment[
                    "review_consistent"
                ]
            ):
                return {
                    "revised_record": (
                        revised_record
                    ),
                    "final_review": (
                        judge_review
                    ),
                    "final_assessment": (
                        judge_assessment
                    ),
                    "attempts": (
                        attempt_evidence
                    ),
                }

            previous_errors = [
                issue[
                    "recommended_fix"
                ]
                for issue in (
                    judge_review["issues"]
                )
            ]

            if not previous_errors:
                previous_errors = [
                    judge_review[
                        "summary"
                    ]
                ]

            active_review_record = {
                "review": judge_review
            }

        except Exception as error:
            error_message = (
                f"{type(error).__name__}: "
                f"{error}"
            )

            attempt_evidence.append(
                {
                    "attempt_number": (
                        attempt_number
                    ),
                    "local_validation_passed": False,
                    "errors": [
                        error_message
                    ],
                }
            )

            previous_errors = [
                error_message
            ]

            if (
                "429" in error_message
                or "RESOURCE_EXHAUSTED"
                in error_message
            ):
                time.sleep(
                    15 * attempt_number
                )
            else:
                time.sleep(
                    2 * attempt_number
                )

    return {
        "revised_record": None,
        "final_review": None,
        "final_assessment": None,
        "attempts": attempt_evidence,
    }


# ------------------------------------------------------------
# Revise all flagged activities
# ------------------------------------------------------------

revision_results = {}
recovered_revision_count = 0
new_revision_count = 0

for index, activity_id in enumerate(
    flagged_activity_ids,
    start=1
):
    print(
        "\n"
        f"[{index}/{len(flagged_activity_ids)}] "
        f"Revising {activity_id}."
    )

    checkpoint_payload = (
        load_revision_checkpoint(
            activity_id
        )
    )

    if checkpoint_payload is not None:
        recovered_revision_count += 1

        revision_results[
            activity_id
        ] = checkpoint_payload

        print(
            "  RECOVERED accepted revision."
        )
        continue

    result = revise_one_activity(
        original_record=(
            record_by_id[
                activity_id
            ]
        ),
        task=(
            task_by_id[
                activity_id
            ]
        ),
        original_review_record=(
            flagged_review_by_id[
                activity_id
            ]
        ),
    )

    if result[
        "revised_record"
    ] is None:
        raise RuntimeError(
            "I could not produce an accepted "
            "revision for "
            f"{activity_id}. Completed revision "
            "checkpoints remain safe."
        )

    checkpoint_payload = {
        "activity_id": activity_id,
        "revised_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "original_record": (
            record_by_id[
                activity_id
            ]
        ),
        **result,
    }

    save_revision_checkpoint(
        activity_id,
        checkpoint_payload,
    )

    revision_results[
        activity_id
    ] = checkpoint_payload

    new_revision_count += 1

    print(
        "  ACCEPTED revised activity."
    )

    print(
        "  Minimum judge score: "
        f"{result['final_assessment']['minimum_score']}/5"
    )


# ------------------------------------------------------------
# Replace only the 11 flagged records
# ------------------------------------------------------------

reviewed_records = []

for original_record in (
    generated_records
):
    activity_id = original_record[
        "activity_id"
    ]

    if activity_id in revision_results:
        reviewed_records.append(
            revision_results[
                activity_id
            ][
                "revised_record"
            ]
        )
    else:
        reviewed_records.append(
            original_record
        )

if len(reviewed_records) != 324:
    raise RuntimeError(
        "The reviewed pool does not "
        "contain 324 activities."
    )

if len(
    {
        record["activity_id"]
        for record in reviewed_records
    }
) != 324:
    raise RuntimeError(
        "The reviewed pool contains "
        "duplicate identifiers."
    )

for record in reviewed_records:
    StaticDragDropRecord.model_validate(
        record
    )


# ------------------------------------------------------------
# Save the reviewed pool
# ------------------------------------------------------------

REVIEWED_POOL = {
    **{
        key: value
        for key, value
        in generated_pool.items()
        if key != "activities"
    },
    "dataset_version": "1.1-reviewed",
    "reviewed_at_utc": datetime.now(
        timezone.utc
    ).isoformat(),
    "generator_model": (
        GEMINI_STATIC_GENERATOR_MODEL
    ),
    "judge_model": (
        GEMINI_JUDGE_MODEL
    ),
    "activity_count": 324,
    "revised_activity_count": len(
        revision_results
    ),
    "activities": reviewed_records,
}

with REVIEWED_POOL_FILE.open(
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        REVIEWED_POOL,
        file,
        indent=2,
        ensure_ascii=False
    )


# ------------------------------------------------------------
# Save revision evidence
# ------------------------------------------------------------

FINAL_REVISION_REPORT = {
    "report_name": (
        "drag_and_drop_targeted_"
        "revision_report_v1"
    ),
    "created_at_utc": datetime.now(
        timezone.utc
    ).isoformat(),
    "generator_model": (
        GEMINI_STATIC_GENERATOR_MODEL
    ),
    "judge_model": (
        GEMINI_JUDGE_MODEL
    ),
    "flagged_activity_count": len(
        flagged_activity_ids
    ),
    "successfully_revised_count": len(
        revision_results
    ),
    "new_revision_count": (
        new_revision_count
    ),
    "recovered_revision_count": (
        recovered_revision_count
    ),
    "revised_activity_ids": sorted(
        revision_results.keys()
    ),
    "revision_results": (
        revision_results
    ),
    "reviewed_pool_file": str(
        REVIEWED_POOL_FILE
    ),
    "complete": True,
}

with FINAL_REVISION_REPORT_FILE.open(
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        FINAL_REVISION_REPORT,
        file,
        indent=2,
        ensure_ascii=False
    )


# ------------------------------------------------------------
# Report completion
# ------------------------------------------------------------

print(
    "\n"
    + "=" * 72
)

print(
    "I completed the targeted "
    "drag-and-drop revisions."
)

print(
    f"\nI revised and revalidated "
    f"{len(revision_results)}/"
    f"{len(flagged_activity_ids)} "
    "flagged activities."
)

print(
    f"I retained "
    f"{324 - len(revision_results)} "
    "previously accepted activities "
    "without modification."
)

print(
    "\nNew revisions: "
    f"{new_revision_count}"
)

print(
    "Recovered revision checkpoints: "
    f"{recovered_revision_count}"
)

print(
    "\nI saved the reviewed activity pool to:"
)

print(REVIEWED_POOL_FILE)

print(
    "\nI saved the revision evidence to:"
)

print(FINAL_REVISION_REPORT_FILE)

print(
    "\nSTEP 13 COMPLETE"
)