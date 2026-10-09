# Recovered from the tested Colab notebook
# Notebook code cell: 1
# This file is source evidence and may depend on earlier notebook definitions.

# ============================================================
# CAREERTIMEMACHINE
# ITERATION 3 DRAG-AND-DROP ACTIVITY PIPELINE
# STEP 1: CONNECT DRIVE AND CREATE THE WORKSPACE
# ============================================================

from google.colab import drive
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import platform

print("I am connecting to Google Drive.")

drive.mount(
    "/content/drive",
    force_remount=False
)

print("\nI successfully connected to Google Drive.")


# ------------------------------------------------------------
# Workspace locations
# ------------------------------------------------------------

PROJECT_ROOT = Path(
    "/content/drive/MyDrive/CareerTimeMachine"
)

DRAG_DROP_ROOT = (
    PROJECT_ROOT
    / "drag_and_drop_pipeline_v1"
)

DATA_DIRECTORY = DRAG_DROP_ROOT / "data"
RAW_OUTPUT_DIRECTORY = DRAG_DROP_ROOT / "raw_outputs"
CHECKPOINT_DIRECTORY = DRAG_DROP_ROOT / "checkpoints"
OUTPUT_DIRECTORY = DRAG_DROP_ROOT / "output"
REPORT_DIRECTORY = DRAG_DROP_ROOT / "reports"
LIVE_SERVICE_DIRECTORY = DRAG_DROP_ROOT / "live_service"
MODEL_DIRECTORY = DRAG_DROP_ROOT / "models"
BACKEND_HANDOVER_DIRECTORY = (
    DRAG_DROP_ROOT
    / "backend_handover_v1"
)

WORKSPACE_DIRECTORIES = [
    PROJECT_ROOT,
    DRAG_DROP_ROOT,
    DATA_DIRECTORY,
    RAW_OUTPUT_DIRECTORY,
    CHECKPOINT_DIRECTORY,
    OUTPUT_DIRECTORY,
    REPORT_DIRECTORY,
    LIVE_SERVICE_DIRECTORY,
    MODEL_DIRECTORY,
    BACKEND_HANDOVER_DIRECTORY,
]

for directory in WORKSPACE_DIRECTORIES:
    directory.mkdir(
        parents=True,
        exist_ok=True
    )


# ------------------------------------------------------------
# Confirm the processing environment
# ------------------------------------------------------------

try:
    import torch

    CUDA_AVAILABLE = torch.cuda.is_available()

    if CUDA_AVAILABLE:
        PROCESSING_DEVICE = torch.cuda.get_device_name(0)
        GPU_MEMORY_GB = round(
            torch.cuda.get_device_properties(0).total_memory
            / (1024 ** 3),
            2
        )
    else:
        PROCESSING_DEVICE = "cpu"
        GPU_MEMORY_GB = None

except Exception as error:
    CUDA_AVAILABLE = False
    PROCESSING_DEVICE = "unknown"
    GPU_MEMORY_GB = None

    print(
        "I could not inspect the GPU:",
        type(error).__name__,
        str(error)
    )


# ------------------------------------------------------------
# Final project scope
# ------------------------------------------------------------

SUPPORTED_ROLE_COUNT = 27

DIFFICULTY_LEVELS = [
    "guided",
    "standard",
    "challenge",
]

STATIC_ACTIVITIES_PER_COMBINATION = 4

ROLE_DIFFICULTY_COMBINATIONS = (
    SUPPORTED_ROLE_COUNT
    * len(DIFFICULTY_LEVELS)
)

EXPECTED_STATIC_ACTIVITY_COUNT = (
    ROLE_DIFFICULTY_COMBINATIONS
    * STATIC_ACTIVITIES_PER_COMBINATION
)

BLANKS_PER_ACTIVITY = 3
OPTIONS_PER_ACTIVITY = 5
INTENDED_OPTIONS_PER_ACTIVITY = 3
DISTRACTOR_OPTIONS_PER_ACTIVITY = 2

EXPECTED_TOTAL_BLANKS = (
    EXPECTED_STATIC_ACTIVITY_COUNT
    * BLANKS_PER_ACTIVITY
)

EXPECTED_TOTAL_OPTIONS = (
    EXPECTED_STATIC_ACTIVITY_COUNT
    * OPTIONS_PER_ACTIVITY
)


# ------------------------------------------------------------
# Save the agreed pipeline configuration
# ------------------------------------------------------------

PIPELINE_CONFIGURATION = {
    "project": "CareerTimeMachine",
    "iteration": 3,
    "pipeline_name": (
        "drag_and_drop_activity_pipeline_v1"
    ),
    "created_at_utc": datetime.now(
        timezone.utc
    ).isoformat(),
    "python_version": platform.python_version(),
    "processing_device": PROCESSING_DEVICE,
    "cuda_available": CUDA_AVAILABLE,
    "gpu_memory_gb": GPU_MEMORY_GB,
    "static_generation": {
        "role_count": SUPPORTED_ROLE_COUNT,
        "difficulty_levels": DIFFICULTY_LEVELS,
        "activities_per_role_difficulty": (
            STATIC_ACTIVITIES_PER_COMBINATION
        ),
        "role_difficulty_combinations": (
            ROLE_DIFFICULTY_COMBINATIONS
        ),
        "expected_activity_count": (
            EXPECTED_STATIC_ACTIVITY_COUNT
        ),
        "blanks_per_activity": BLANKS_PER_ACTIVITY,
        "options_per_activity": OPTIONS_PER_ACTIVITY,
        "intended_options_per_activity": (
            INTENDED_OPTIONS_PER_ACTIVITY
        ),
        "distractor_options_per_activity": (
            DISTRACTOR_OPTIONS_PER_ACTIVITY
        ),
        "expected_total_blanks": (
            EXPECTED_TOTAL_BLANKS
        ),
        "expected_total_options": (
            EXPECTED_TOTAL_OPTIONS
        ),
    },
    "live_generation": {
        "enabled_for_relevant_custom_skills": True,
        "uses_role_id": True,
        "uses_skills": True,
        "uses_years_experience": True,
        "uses_responsibilities": True,
        "uses_difficulty": True,
        "maximum_generation_attempts": 2,
        "fallback": (
            "matching pre-generated activity"
        ),
        "rag_enabled": False,
    },
    "activity_contract": {
        "activity_type": "drag_and_drop",
        "required_blank_count": 3,
        "required_option_count": 5,
        "required_intended_option_count": 3,
        "required_distractor_count": 2,
        "feedback_required_for_every_option": True,
        "private_answer_field": "fits_blank_id",
        "supportive_feedback_only": True,
    },
    "generation_design": {
        "offline_generator": (
            "Gemini structured generation"
        ),
        "independent_reviewer": (
            "Qwen2.5-3B-Instruct"
        ),
        "deterministic_validation": True,
        "checkpointing": True,
        "manual_balanced_review": True,
    },
    "security": {
        "api_key_saved_to_drive": False,
        "api_key_saved_to_output": False,
        "answer_mapping_must_not_reach_frontend": True,
        "user_input_treated_as_untrusted": True,
    },
}

CONFIGURATION_FILE = (
    DRAG_DROP_ROOT
    / "drag_and_drop_pipeline_configuration_v1.json"
)

with CONFIGURATION_FILE.open(
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        PIPELINE_CONFIGURATION,
        file,
        indent=2,
        ensure_ascii=False
    )


# ------------------------------------------------------------
# Verify the saved configuration
# ------------------------------------------------------------

configuration_bytes = (
    CONFIGURATION_FILE.read_bytes()
)

CONFIGURATION_SHA256 = hashlib.sha256(
    configuration_bytes
).hexdigest()

if not CONFIGURATION_FILE.exists():
    raise RuntimeError(
        "The pipeline configuration was not saved."
    )

if EXPECTED_STATIC_ACTIVITY_COUNT != 324:
    raise RuntimeError(
        "The expected static activity count is incorrect."
    )

if EXPECTED_TOTAL_BLANKS != 972:
    raise RuntimeError(
        "The expected blank count is incorrect."
    )

if EXPECTED_TOTAL_OPTIONS != 1620:
    raise RuntimeError(
        "The expected option count is incorrect."
    )


# ------------------------------------------------------------
# Report completion
# ------------------------------------------------------------

print(
    "\nI created my Iteration 3 drag-and-drop workspace."
)

print(
    "\nI will create "
    f"{EXPECTED_STATIC_ACTIVITY_COUNT} "
    "validated static activities:"
)

print(
    f"  - {SUPPORTED_ROLE_COUNT} roles"
)

print(
    f"  - {len(DIFFICULTY_LEVELS)} "
    "difficulty levels"
)

print(
    "  - "
    f"{STATIC_ACTIVITIES_PER_COMBINATION} "
    "activities for every role and difficulty combination"
)

print(
    f"  - {EXPECTED_TOTAL_BLANKS} total blanks"
)

print(
    f"  - {EXPECTED_TOTAL_OPTIONS} total options"
)

print(
    "\nEach activity will contain:"
)

print(
    "  - 3 blanks"
)

print(
    "  - 5 draggable options"
)

print(
    "  - 3 intended placements"
)

print(
    "  - 2 constructive distractors"
)

print(
    "  - feedback for every option"
)

print(
    "\nFor a relevant custom skill, the live service "
    "will use the user's role, skill, years of "
    "experience, responsibilities and difficulty."
)

print(
    "If live generation fails validation twice, "
    "the backend will serve a matching static activity."
)

print(
    "\nI will not store the Gemini API key "
    "in Google Drive."
)

print(
    "\nI saved my configuration to:"
)

print(CONFIGURATION_FILE)

print(
    "\nConfiguration SHA-256:"
)

print(CONFIGURATION_SHA256)

print("\nSTEP 1 COMPLETE")