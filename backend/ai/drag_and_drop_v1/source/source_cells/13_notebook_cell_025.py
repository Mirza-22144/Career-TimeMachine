# Recovered from the tested Colab notebook
# Notebook code cell: 25
# This file is source evidence and may depend on earlier notebook definitions.

# ============================================================
# CAREERTIMEMACHINE
# DRAG-AND-DROP PIPELINE
# STEP 14: FINAL DETERMINISTIC QUALITY AUDIT
# ============================================================

from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict
import hashlib
import json
import re

from rapidfuzz import fuzz

print(
    "I am beginning the final deterministic "
    "quality audit."
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

REVIEWED_POOL_FILE = (
    OUTPUT_DIRECTORY
    / "drag_and_drop_activity_"
      "pool_v1_reviewed.json"
)

ROLE_SKILL_CATALOGUE_FILE = (
    DATA_DIRECTORY
    / "drag_and_drop_role_skill_"
      "catalogue_v1.json"
)

GENERATION_PLAN_FILE = (
    DATA_DIRECTORY
    / "drag_and_drop_generation_"
      "plan_v1_324.json"
)

FINAL_POOL_FILE = (
    OUTPUT_DIRECTORY
    / "drag_and_drop_activity_"
      "pool_v1_final.json"
)

QUALITY_AUDIT_FILE = (
    REPORT_DIRECTORY
    / "drag_and_drop_deterministic_"
      "quality_audit_v1.json"
)

BALANCED_SAMPLE_FILE = (
    REPORT_DIRECTORY
    / "drag_and_drop_balanced_"
      "manual_review_sample_v1_27.json"
)


# ------------------------------------------------------------
# Load reviewed records and authoritative catalogue
# ------------------------------------------------------------

with REVIEWED_POOL_FILE.open(
    "r",
    encoding="utf-8"
) as file:
    reviewed_pool = json.load(file)

with ROLE_SKILL_CATALOGUE_FILE.open(
    "r",
    encoding="utf-8"
) as file:
    role_skill_catalogue = json.load(file)

with GENERATION_PLAN_FILE.open(
    "r",
    encoding="utf-8"
) as file:
    generation_plan = json.load(file)

reviewed_records = (
    reviewed_pool["activities"]
)

if len(reviewed_records) != 324:
    raise RuntimeError(
        "The reviewed pool does not contain "
        "324 activities."
    )

catalogue_skills_by_role = {
    role["role_id"]: {
        skill["label"].casefold()
        for skill in role["skills"]
    }
    for role in (
        role_skill_catalogue["roles"]
    )
}

plan_task_by_id = {
    task["activity_id"]: task
    for task in (
        generation_plan[
            "generation_tasks"
        ]
    )
}


# ------------------------------------------------------------
# Audit helpers
# ------------------------------------------------------------

def normalise_text(value):
    return " ".join(
        str(value).casefold().split()
    )


def sha256_file(file_path):
    hash_object = hashlib.sha256()

    with file_path.open("rb") as file:
        for block in iter(
            lambda: file.read(
                1024 * 1024
            ),
            b""
        ):
            hash_object.update(block)

    return hash_object.hexdigest()


PROHIBITED_PATTERNS = {
    "correct": re.compile(
        r"\bcorrect\b",
        re.IGNORECASE
    ),
    "incorrect": re.compile(
        r"\bincorrect\b",
        re.IGNORECASE
    ),
    "right": re.compile(
        r"\bright\b",
        re.IGNORECASE
    ),
    "wrong": re.compile(
        r"\bwrong\b",
        re.IGNORECASE
    ),
    "best answer": re.compile(
        r"\bbest\s+answer\b",
        re.IGNORECASE
    ),
    "pass": re.compile(
        r"\bpass\b",
        re.IGNORECASE
    ),
    "fail": re.compile(
        r"\bfail\b",
        re.IGNORECASE
    ),
    "competent": re.compile(
        r"\bcompetent\b",
        re.IGNORECASE
    ),
    "incompetent": re.compile(
        r"\bincompetent\b",
        re.IGNORECASE
    ),
}


# ------------------------------------------------------------
# Validate all 324 records
# ------------------------------------------------------------

critical_issues = []
warnings = []
validated_records = []

role_counts = Counter()
difficulty_counts = Counter()
combination_counts = Counter()
skill_usage = Counter()
title_lookup = defaultdict(list)
content_lookup = defaultdict(list)

for record_number, record in enumerate(
    reviewed_records,
    start=1
):
    activity_id = record.get(
        "activity_id",
        f"record_{record_number}"
    )

    try:
        validated_record = (
            StaticDragDropRecord
            .model_validate(
                record
            )
        )

        validated_payload = (
            validated_record.model_dump()
        )

        validated_records.append(
            validated_payload
        )

    except Exception as error:
        critical_issues.append(
            {
                "activity_id": (
                    activity_id
                ),
                "issue_type": (
                    "schema_validation"
                ),
                "detail": (
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            }
        )
        continue

    role_id = validated_payload[
        "role_id"
    ]

    difficulty = validated_payload[
        "difficulty"
    ]

    activity = validated_payload[
        "activity"
    ]

    role_counts[role_id] += 1
    difficulty_counts[difficulty] += 1

    combination_counts[
        (
            role_id,
            difficulty,
        )
    ] += 1

    # Verify that the record exists in the plan.
    if activity_id not in plan_task_by_id:
        critical_issues.append(
            {
                "activity_id": activity_id,
                "issue_type": (
                    "unplanned_identifier"
                ),
                "detail": (
                    "The activity identifier "
                    "does not exist in the "
                    "generation plan."
                ),
            }
        )

    # Verify catalogue skill grounding.
    role_catalogue_skills = (
        catalogue_skills_by_role.get(
            role_id,
            set()
        )
    )

    for skill in activity[
        "skills_used"
    ]:
        skill_usage[skill] += 1

        if (
            skill.casefold()
            not in role_catalogue_skills
        ):
            critical_issues.append(
                {
                    "activity_id": (
                        activity_id
                    ),
                    "issue_type": (
                        "invalid_skill_grounding"
                    ),
                    "detail": (
                        f"{skill} is not an exact "
                        "catalogue skill for "
                        f"{role_id}."
                    ),
                }
            )

    # Verify completed message.
    intended_by_blank = {
        option["fits_blank_id"]: (
            option["text"]
        )
        for option in activity[
            "options"
        ]
        if option[
            "fits_blank_id"
        ] is not None
    }

    completed_message = activity[
        "sentence_template"
    ]

    for blank_id in [
        "blank_1",
        "blank_2",
        "blank_3",
    ]:
        completed_message = (
            completed_message.replace(
                "{" + blank_id + "}",
                intended_by_blank[
                    blank_id
                ],
            )
        )

    if re.search(
        r"\{[^{}]+\}",
        completed_message
    ):
        critical_issues.append(
            {
                "activity_id": activity_id,
                "issue_type": (
                    "unresolved_placeholder"
                ),
                "detail": completed_message,
            }
        )

    # Verify prohibited language.
    searchable_payload = {
        "title": activity["title"],
        "situation": (
            activity["situation"]
        ),
        "sentence_template": (
            activity[
                "sentence_template"
            ]
        ),
        "options": [
            option["text"]
            for option in (
                activity["options"]
            )
        ],
        "feedback_by_option": (
            activity[
                "feedback_by_option"
            ]
        ),
        "guidance": (
            activity["guidance"]
        ),
    }

    searchable_text = json.dumps(
        searchable_payload,
        ensure_ascii=False
    )

    for phrase, pattern in (
        PROHIBITED_PATTERNS.items()
    ):
        if pattern.search(
            searchable_text
        ):
            critical_issues.append(
                {
                    "activity_id": (
                        activity_id
                    ),
                    "issue_type": (
                        "prohibited_language"
                    ),
                    "detail": (
                        f"Found prohibited phrase: "
                        f"{phrase}"
                    ),
                }
            )

    # Record duplicate keys.
    normalised_title = normalise_text(
        activity["title"]
    )

    title_lookup[
        normalised_title
    ].append(activity_id)

    combined_content = normalise_text(
        activity["situation"]
        + " "
        + activity[
            "sentence_template"
        ]
    )

    content_lookup[
        combined_content
    ].append(activity_id)


# ------------------------------------------------------------
# Verify complete coverage
# ------------------------------------------------------------

if len(validated_records) != 324:
    critical_issues.append(
        {
            "activity_id": None,
            "issue_type": (
                "validated_record_count"
            ),
            "detail": (
                "Expected 324 schema-valid "
                f"records but found "
                f"{len(validated_records)}."
            ),
        }
    )

if len(role_counts) != 27:
    critical_issues.append(
        {
            "activity_id": None,
            "issue_type": "role_coverage",
            "detail": (
                f"Expected 27 roles but found "
                f"{len(role_counts)}."
            ),
        }
    )

expected_difficulty_counts = {
    "guided": 108,
    "standard": 108,
    "challenge": 108,
}

if dict(
    sorted(
        difficulty_counts.items()
    )
) != expected_difficulty_counts:
    critical_issues.append(
        {
            "activity_id": None,
            "issue_type": (
                "difficulty_coverage"
            ),
            "detail": dict(
                difficulty_counts
            ),
        }
    )

if len(combination_counts) != 81:
    critical_issues.append(
        {
            "activity_id": None,
            "issue_type": (
                "combination_coverage"
            ),
            "detail": (
                f"Expected 81 combinations "
                f"but found "
                f"{len(combination_counts)}."
            ),
        }
    )

incorrect_combination_counts = {
    (
        f"{role_id}|{difficulty}"
    ): count
    for (
        role_id,
        difficulty,
    ), count
    in combination_counts.items()
    if count != 4
}

if incorrect_combination_counts:
    critical_issues.append(
        {
            "activity_id": None,
            "issue_type": (
                "activities_per_combination"
            ),
            "detail": (
                incorrect_combination_counts
            ),
        }
    )


# ------------------------------------------------------------
# Exact duplicate detection
# ------------------------------------------------------------

exact_duplicate_content_groups = [
    {
        "activity_ids": (
            activity_ids
        ),
        "normalised_content": (
            content
        ),
    }
    for content, activity_ids
    in content_lookup.items()
    if len(activity_ids) > 1
]

for duplicate_group in (
    exact_duplicate_content_groups
):
    critical_issues.append(
        {
            "activity_id": None,
            "issue_type": (
                "exact_duplicate_content"
            ),
            "detail": duplicate_group,
        }
    )


duplicate_title_groups = [
    activity_ids
    for activity_ids
    in title_lookup.values()
    if len(activity_ids) > 1
]

for activity_ids in (
    duplicate_title_groups
):
    warnings.append(
        {
            "issue_type": (
                "duplicate_title"
            ),
            "activity_ids": (
                activity_ids
            ),
        }
    )


# ------------------------------------------------------------
# Near-duplicate detection within role and difficulty
# ------------------------------------------------------------

records_by_combination = defaultdict(
    list
)

for record in validated_records:
    key = (
        record["role_id"],
        record["difficulty"],
    )

    activity = record["activity"]

    comparison_text = normalise_text(
        activity["situation"]
        + " "
        + activity[
            "sentence_template"
        ]
    )

    records_by_combination[
        key
    ].append(
        (
            record["activity_id"],
            comparison_text,
        )
    )

near_duplicate_pairs = []

for combination, records in (
    records_by_combination.items()
):
    for first_index in range(
        len(records)
    ):
        for second_index in range(
            first_index + 1,
            len(records)
        ):
            first_id, first_text = (
                records[first_index]
            )

            second_id, second_text = (
                records[second_index]
            )

            similarity = round(
                fuzz.ratio(
                    first_text,
                    second_text
                ),
                2
            )

            if similarity >= 92:
                near_duplicate_pairs.append(
                    {
                        "role_id": (
                            combination[0]
                        ),
                        "difficulty": (
                            combination[1]
                        ),
                        "first_activity_id": (
                            first_id
                        ),
                        "second_activity_id": (
                            second_id
                        ),
                        "similarity": (
                            similarity
                        ),
                    }
                )

for pair in near_duplicate_pairs:
    warnings.append(
        {
            "issue_type": (
                "near_duplicate_content"
            ),
            **pair,
        }
    )


# ------------------------------------------------------------
# Create balanced 27-activity manual sample
# ------------------------------------------------------------

role_ids = sorted(
    role_counts.keys()
)

sample_difficulty_cycle = [
    "guided",
    "standard",
    "challenge",
]

balanced_sample_records = []

for role_index, role_id in enumerate(
    role_ids
):
    selected_difficulty = (
        sample_difficulty_cycle[
            role_index % 3
        ]
    )

    candidate_records = sorted(
        [
            record
            for record in validated_records
            if (
                record["role_id"]
                == role_id
                and record[
                    "difficulty"
                ]
                == selected_difficulty
            )
        ],
        key=lambda record: (
            record["activity_id"]
        )
    )

    selected_variant_index = (
        role_index
        % len(candidate_records)
    )

    balanced_sample_records.append(
        candidate_records[
            selected_variant_index
        ]
    )

sample_difficulty_counts = Counter(
    record["difficulty"]
    for record in (
        balanced_sample_records
    )
)

if len(balanced_sample_records) != 27:
    raise RuntimeError(
        "The balanced manual sample "
        "does not contain 27 records."
    )


# ------------------------------------------------------------
# Save final pool only if critical checks pass
# ------------------------------------------------------------

DETERMINISTIC_AUDIT_PASSED = (
    len(critical_issues) == 0
)

final_pool_sha256 = None

if DETERMINISTIC_AUDIT_PASSED:
    FINAL_POOL = {
        **{
            key: value
            for key, value
            in reviewed_pool.items()
            if key != "activities"
        },
        "dataset_version": (
            "1.2-final"
        ),
        "finalised_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "activity_count": 324,
        "deterministic_audit_passed": (
            True
        ),
        "activities": (
            validated_records
        ),
    }

    with FINAL_POOL_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            FINAL_POOL,
            file,
            indent=2,
            ensure_ascii=False
        )

    final_pool_sha256 = (
        sha256_file(
            FINAL_POOL_FILE
        )
    )


# ------------------------------------------------------------
# Save audit and sample
# ------------------------------------------------------------

QUALITY_AUDIT = {
    "report_name": (
        "drag_and_drop_deterministic_"
        "quality_audit_v1"
    ),
    "created_at_utc": datetime.now(
        timezone.utc
    ).isoformat(),
    "audited_activity_count": len(
        reviewed_records
    ),
    "schema_valid_activity_count": len(
        validated_records
    ),
    "role_count": len(
        role_counts
    ),
    "difficulty_counts": dict(
        sorted(
            difficulty_counts.items()
        )
    ),
    "role_difficulty_combination_count": len(
        combination_counts
    ),
    "unique_skill_count": len(
        skill_usage
    ),
    "critical_issue_count": len(
        critical_issues
    ),
    "warning_count": len(
        warnings
    ),
    "exact_duplicate_content_group_count": len(
        exact_duplicate_content_groups
    ),
    "duplicate_title_group_count": len(
        duplicate_title_groups
    ),
    "near_duplicate_pair_count": len(
        near_duplicate_pairs
    ),
    "critical_issues": (
        critical_issues
    ),
    "warnings": warnings,
    "passed": (
        DETERMINISTIC_AUDIT_PASSED
    ),
    "final_pool_file": (
        str(FINAL_POOL_FILE)
        if DETERMINISTIC_AUDIT_PASSED
        else None
    ),
    "final_pool_sha256": (
        final_pool_sha256
    ),
}

with QUALITY_AUDIT_FILE.open(
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        QUALITY_AUDIT,
        file,
        indent=2,
        ensure_ascii=False
    )

BALANCED_SAMPLE = {
    "created_at_utc": datetime.now(
        timezone.utc
    ).isoformat(),
    "sample_size": len(
        balanced_sample_records
    ),
    "role_count": len(
        {
            record["role_id"]
            for record
            in balanced_sample_records
        }
    ),
    "difficulty_counts": dict(
        sorted(
            sample_difficulty_counts.items()
        )
    ),
    "activities": (
        balanced_sample_records
    ),
}

with BALANCED_SAMPLE_FILE.open(
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        BALANCED_SAMPLE,
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
    "I completed the deterministic "
    "drag-and-drop quality audit."
)

print(
    f"\nI audited "
    f"{len(reviewed_records)}/324 "
    "activities."
)

print(
    f"I found "
    f"{len(critical_issues)} "
    "critical issues."
)

print(
    f"I found "
    f"{len(warnings)} "
    "structural warnings."
)

print(
    f"I found "
    f"{len(exact_duplicate_content_groups)} "
    "exact duplicate content groups."
)

print(
    f"I found "
    f"{len(near_duplicate_pairs)} "
    "near-duplicate pairs at 92% "
    "similarity or higher."
)

print(
    f"I used "
    f"{len(skill_usage)} "
    "unique catalogue skills."
)

print(
    "\nDeterministic audit passed: "
    f"{DETERMINISTIC_AUDIT_PASSED}"
)

print(
    "\nBalanced manual-review sample:"
)

print(
    f"  - activities: "
    f"{len(balanced_sample_records)}"
)

print(
    f"  - roles: "
    f"{len(role_counts)}"
)

for difficulty, count in sorted(
    sample_difficulty_counts.items()
):
    print(
        f"  - {difficulty}: {count}"
    )

print(
    "\nI saved the quality audit to:"
)

print(QUALITY_AUDIT_FILE)

print(
    "\nI saved the balanced sample to:"
)

print(BALANCED_SAMPLE_FILE)

if DETERMINISTIC_AUDIT_PASSED:
    print(
        "\nI saved the final static pool to:"
    )

    print(FINAL_POOL_FILE)

    print(
        "\nFinal pool SHA-256:"
    )

    print(final_pool_sha256)

print(
    "\nSTEP 14 COMPLETE"
)