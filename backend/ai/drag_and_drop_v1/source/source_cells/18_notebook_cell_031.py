# Recovered from the tested Colab notebook
# Notebook code cell: 31
# This file is source evidence and may depend on earlier notebook definitions.

# ============================================================
# STEP 17
# Save the complete notebook and create a backend handover
# checkpoint containing the final data, contracts and evidence.
# ============================================================

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from google.colab import _message


BASE_DIRECTORY = Path(
    "/content/drive/MyDrive/"
    "CareerTimeMachine/"
    "drag_and_drop_pipeline_v1"
)

HANDOVER_DIRECTORY = (
    BASE_DIRECTORY
    / "backend_handover_v1"
)

DATA_DIRECTORY = (
    HANDOVER_DIRECTORY
    / "data"
)

EXAMPLE_DIRECTORY = (
    HANDOVER_DIRECTORY
    / "examples"
)

REPORT_DIRECTORY = (
    HANDOVER_DIRECTORY
    / "reports"
)

SOURCE_DIRECTORY = (
    HANDOVER_DIRECTORY
    / "source"
)

for directory in [
    HANDOVER_DIRECTORY,
    DATA_DIRECTORY,
    EXAMPLE_DIRECTORY,
    REPORT_DIRECTORY,
    SOURCE_DIRECTORY,
]:
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )


print(
    "I am creating my drag-and-drop "
    "backend handover checkpoint."
)


# ------------------------------------------------------------
# 1. Save the complete Colab notebook
# ------------------------------------------------------------

print(
    "I am retrieving my complete Colab notebook."
)

notebook_response = (
    _message.blocking_request(
        "get_ipynb",
        timeout_sec=120,
    )
)

if (
    not isinstance(notebook_response, dict)
    or "ipynb" not in notebook_response
):
    raise RuntimeError(
        "Colab did not return the current notebook."
    )

complete_notebook = notebook_response["ipynb"]

NOTEBOOK_FILE = (
    SOURCE_DIRECTORY
    / "drag_and_drop_pipeline_v1_complete.ipynb"
)

with NOTEBOOK_FILE.open(
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        complete_notebook,
        file,
        indent=1,
        ensure_ascii=False,
    )

print(
    "I saved my complete notebook."
)


# ------------------------------------------------------------
# 2. Copy required final data and evidence
# ------------------------------------------------------------

files_to_copy = [
    (
        BASE_DIRECTORY
        / "output/"
        "drag_and_drop_activity_pool_v1_final.json",
        DATA_DIRECTORY
        / "drag_and_drop_activity_pool_v1_final.json",
        True,
    ),
    (
        BASE_DIRECTORY
        / "data/"
        "drag_and_drop_ai_response_schema_v1.json",
        DATA_DIRECTORY
        / "drag_and_drop_ai_response_schema_v1.json",
        True,
    ),
    (
        BASE_DIRECTORY
        / "data/"
        "drag_and_drop_static_record_schema_v1.json",
        DATA_DIRECTORY
        / "drag_and_drop_static_record_schema_v1.json",
        True,
    ),
    (
        BASE_DIRECTORY
        / "data/"
        "drag_and_drop_backend_contract_v1.json",
        DATA_DIRECTORY
        / "drag_and_drop_backend_contract_v1.json",
        True,
    ),
    (
        BASE_DIRECTORY
        / "reports/"
        "dependency_environment_report_v1.json",
        REPORT_DIRECTORY
        / "dependency_environment_report_v1.json",
        True,
    ),
    (
        BASE_DIRECTORY
        / "reports/"
        "drag_and_drop_generation_summary_v1_324.json",
        REPORT_DIRECTORY
        / "drag_and_drop_generation_summary_v1_324.json",
        True,
    ),
    (
        BASE_DIRECTORY
        / "reports/"
        "drag_and_drop_full_gemini_judge_report_v1_324.json",
        REPORT_DIRECTORY
        / "drag_and_drop_full_gemini_judge_report_v1_324.json",
        True,
    ),
    (
        BASE_DIRECTORY
        / "reports/"
        "drag_and_drop_targeted_revision_report_v1.json",
        REPORT_DIRECTORY
        / "drag_and_drop_targeted_revision_report_v1.json",
        True,
    ),
    (
        BASE_DIRECTORY
        / "reports/"
        "drag_and_drop_deterministic_quality_audit_v1.json",
        REPORT_DIRECTORY
        / "drag_and_drop_deterministic_quality_audit_v1.json",
        True,
    ),
    (
        BASE_DIRECTORY
        / "reports/"
        "live_drag_and_drop_smoke_test_report_v1.json",
        REPORT_DIRECTORY
        / "live_drag_and_drop_smoke_test_report_v1.json",
        True,
    ),
    (
        BASE_DIRECTORY
        / "reports/"
        "balanced_live_drag_and_drop_evaluation_v1.json",
        REPORT_DIRECTORY
        / "balanced_live_drag_and_drop_evaluation_v1_pre_correction.json",
        True,
    ),
    (
        BASE_DIRECTORY
        / "reports/"
        "live_drag_and_drop_quality_correction_v1.json",
        REPORT_DIRECTORY
        / "live_drag_and_drop_quality_correction_v1.json",
        True,
    ),
    (
        BASE_DIRECTORY
        / "reports/"
        "balanced_live_drag_and_drop_evaluation_v1_corrected.json",
        REPORT_DIRECTORY
        / "balanced_live_drag_and_drop_evaluation_v1_corrected.json",
        True,
    ),
    (
        BASE_DIRECTORY
        / "reports/"
        "drag_and_drop_gemini_3_8_judge_smoke_test_v1.json",
        REPORT_DIRECTORY
        / "drag_and_drop_gemini_3_8_judge_smoke_test_v1.json",
        True,
    ),
    (
        BASE_DIRECTORY
        / "reports/"
        "drag_and_drop_qwen_review_diagnostic_v1.json",
        REPORT_DIRECTORY
        / "drag_and_drop_qwen_review_diagnostic_v1.json",
        False,
    ),
]

copied_files = []

for (
    source_file,
    destination_file,
    required,
) in files_to_copy:
    if not source_file.exists():
        if required:
            raise FileNotFoundError(
                "A required handover file is missing: "
                f"{source_file}"
            )

        print(
            "OPTIONAL FILE NOT FOUND:"
        )
        print(
            f"  - {source_file.name}"
        )
        continue

    shutil.copy2(
        source_file,
        destination_file,
    )

    copied_files.append(
        destination_file
    )


print(
    f"I copied {len(copied_files)} data "
    "and evidence files."
)


# ------------------------------------------------------------
# 3. Create the formal live request/response contract
# ------------------------------------------------------------

live_contract = {
    "contract_name": (
        "Iteration 3 live custom-skill "
        "drag-and-drop activity"
    ),
    "contract_version": "1.0",
    "activity_type": "drag_and_drop",
    "request": {
        "role_id": "string",
        "skills": [
            "string",
        ],
        "years_experience": (
            "string or null"
        ),
        "responsibilities": [
            "string",
        ],
        "difficulty": (
            "guided | standard | challenge"
        ),
        "activity_type": "drag_and_drop",
    },
    "response": {
        "title": "string",
        "situation": "string",
        "sentence_template": (
            "string containing {blank_1}, "
            "{blank_2} and {blank_3}"
        ),
        "blanks": [
            {
                "blank_id": "blank_1",
            },
            {
                "blank_id": "blank_2",
            },
            {
                "blank_id": "blank_3",
            },
        ],
        "options": [
            {
                "option_id": "string",
                "text": "string",
                "fits_blank_id": (
                    "blank identifier or null"
                ),
            },
        ],
        "feedback_by_option": {
            "option_id": {
                "what_to_improve": (
                    "string or null"
                ),
                "why": "string",
            },
        },
        "skills_used": [
            "string",
        ],
        "guidance": [
            "string",
        ],
    },
    "invariants": [
        "Exactly three blanks are required.",
        "Exactly five options are required.",
        (
            "Exactly three options contain a "
            "fits_blank_id."
        ),
        (
            "Exactly two options have a null "
            "fits_blank_id."
        ),
        (
            "Every option has constructive "
            "feedback."
        ),
        (
            "No correct, wrong, score or pass/fail "
            "field is returned."
        ),
        (
            "The backend removes fits_blank_id "
            "before sending options to the frontend."
        ),
    ],
    "runtime": {
        "live_model": (
            "gemini-3.5-flash-lite"
        ),
        "maximum_live_attempts": 2,
        "fallback": (
            "One matching validated static "
            "activity selected from four available "
            "role-difficulty activities."
        ),
        "api_key_environment_variable": (
            "GEMINI_API_KEY"
        ),
    },
}

CONTRACT_FILE = (
    HANDOVER_DIRECTORY
    / "live_drag_and_drop_contract_v1.json"
)

with CONTRACT_FILE.open(
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        live_contract,
        file,
        indent=2,
        ensure_ascii=False,
    )


# ------------------------------------------------------------
# 4. Save request and response examples
# ------------------------------------------------------------

example_request = {
    "role_id": "software_developer",
    "skills": [
        "Stakeholder communication",
    ],
    "years_experience": "4",
    "responsibilities": [
        "Reviewed junior developers' code",
    ],
    "difficulty": "guided",
    "activity_type": "drag_and_drop",
}

EXAMPLE_REQUEST_FILE = (
    EXAMPLE_DIRECTORY
    / "example_live_drag_and_drop_request.json"
)

with EXAMPLE_REQUEST_FILE.open(
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        example_request,
        file,
        indent=2,
        ensure_ascii=False,
    )


SMOKE_OUTPUT_FILE = (
    BASE_DIRECTORY
    / "live_service/output/"
    "live_drag_and_drop_smoke_test_v1.json"
)

with SMOKE_OUTPUT_FILE.open(
    "r",
    encoding="utf-8",
) as file:
    smoke_output = json.load(file)


def find_activity(value):
    if isinstance(value, dict):
        required_fields = {
            "title",
            "situation",
            "sentence_template",
            "blanks",
            "options",
            "feedback_by_option",
        }

        if required_fields.issubset(
            value.keys()
        ):
            return value

        for nested_value in value.values():
            result = find_activity(
                nested_value
            )

            if result is not None:
                return result

    elif isinstance(value, list):
        for item in value:
            result = find_activity(item)

            if result is not None:
                return result

    return None


example_response = find_activity(
    smoke_output
)

if example_response is None:
    raise RuntimeError(
        "I could not recover the tested live "
        "example response."
    )

EXAMPLE_RESPONSE_FILE = (
    EXAMPLE_DIRECTORY
    / "example_live_drag_and_drop_response.json"
)

with EXAMPLE_RESPONSE_FILE.open(
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        example_response,
        file,
        indent=2,
        ensure_ascii=False,
    )


# ------------------------------------------------------------
# 5. Create deployment and handover notes
# ------------------------------------------------------------

readme_text = """# Iteration 3 Drag-and-Drop AI

This handover contains the AI assets for the Iteration 3
drag-and-drop workplace communication activity.

## Static activities

The final static pool contains 324 validated activities:

- 27 roles
- 3 difficulty levels
- 4 activities per role and difficulty combination
- 3 blanks per activity
- 5 options per activity
- 3 intended placements
- 2 constructive distractors

## Live custom-skill generation

When a relevant custom skill is supplied, the live service uses:

- role ID
- custom skills
- years of experience
- responsibilities
- difficulty

The live generator uses gemini-3.5-flash-lite. It makes a maximum
of two generation attempts. If generation or validation fails,
the backend serves a matching validated static activity.

## Quality assurance

Static content was generated with gemini-3.5-flash and reviewed
with the separate gemini-3.8-flash model. The final static pool
passed deterministic schema and duplicate checks.

The corrected balanced live evaluation passed 6/6 tests.
The input-security suite passed 6/6 tests, and the forced static
fallback passed.

The original 4/6 live result is retained alongside the corrected
6/6 result as change-management evidence.

## Frontend security

The backend must retain fits_blank_id for evaluation but remove it
from the options returned to the frontend. The user must not
receive the intended answer mapping before submission.

## Secrets

No Gemini API key is included in this handover. The backend must
read the key from the GEMINI_API_KEY deployment environment
variable.
"""

README_FILE = (
    HANDOVER_DIRECTORY
    / "README.md"
)

README_FILE.write_text(
    readme_text,
    encoding="utf-8",
)


deployment_text = """# Model and Service Deployment

## Required environment variable

Set the Gemini API key as a backend secret:

GEMINI_API_KEY=<deployment secret>

Never commit the API key to Git or include it in frontend code.

## Models

Offline static generation:
- gemini-3.5-flash

Independent offline quality review:
- gemini-3.8-flash

Live custom-skill generation:
- gemini-3.5-flash-lite

The static-generation and review models are not required for
normal production requests. Production requires only the live
model and the validated static fallback pool.

## Runtime flow

1. Validate and sanitise the request.
2. Generate a live activity when a relevant custom skill exists.
3. Validate the exact response schema.
4. Apply the professional-plausibility gate.
5. Retry once if validation fails.
6. Serve a matching static fallback if both attempts fail.
7. Remove fits_blank_id before sending options to the frontend.
8. Retain the mapping on the backend for answer evaluation.
"""

DEPLOYMENT_FILE = (
    HANDOVER_DIRECTORY
    / "MODEL_DEPLOYMENT.md"
)

DEPLOYMENT_FILE.write_text(
    deployment_text,
    encoding="utf-8",
)


# ------------------------------------------------------------
# 6. Create checkpoint manifest
# ------------------------------------------------------------

def calculate_sha256(file_path):
    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            sha256.update(block)

    return sha256.hexdigest()


handover_files = sorted(
    file_path
    for file_path in HANDOVER_DIRECTORY.rglob("*")
    if file_path.is_file()
)

manifest_entries = []

for file_path in handover_files:
    manifest_entries.append(
        {
            "relative_path": str(
                file_path.relative_to(
                    HANDOVER_DIRECTORY
                )
            ),
            "size_bytes": (
                file_path.stat().st_size
            ),
            "sha256": calculate_sha256(
                file_path
            ),
        }
    )

manifest = {
    "handover_name": (
        "Career TimeMachine Iteration 3 "
        "drag-and-drop AI checkpoint"
    ),
    "created_at_utc": datetime.now(
        timezone.utc
    ).isoformat(),
    "status": (
        "checkpoint_before standalone "
        "service export"
    ),
    "static_activity_count": 324,
    "role_count": 27,
    "difficulty_count": 3,
    "live_evaluation_passed": True,
    "live_tests_passed": "6/6",
    "security_tests_passed": "6/6",
    "forced_fallback_passed": True,
    "contains_api_key": False,
    "file_count": len(manifest_entries),
    "files": manifest_entries,
}

MANIFEST_FILE = (
    HANDOVER_DIRECTORY
    / "drag_and_drop_handover_checkpoint_manifest_v1.json"
)

with MANIFEST_FILE.open(
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        manifest,
        file,
        indent=2,
        ensure_ascii=False,
    )


print("\n" + "=" * 72)
print(
    "I created my drag-and-drop backend "
    "handover checkpoint."
)
print()
print(
    "I saved my complete Colab notebook to:"
)
print(NOTEBOOK_FILE)
print()
print(
    "I copied my final 324-activity pool."
)
print(
    "I copied my schemas, contracts, examples "
    "and evaluation evidence."
)
print(
    "I documented the Gemini deployment secret "
    "without storing the API key."
)
print()
print(
    "I saved my handover checkpoint to:"
)
print(HANDOVER_DIRECTORY)
print()
print(
    "Checkpoint file count: "
    f"{len(manifest_entries)}"
)
print()
print("STEP 17 COMPLETE")