# Recovered from the tested Colab notebook
# Notebook code cell: 7
# This file is source evidence and may depend on earlier notebook definitions.

# ============================================================
# CAREERTIMEMACHINE
# ITERATION 3 DRAG-AND-DROP ACTIVITY PIPELINE
# STEP 7: CONNECT SECURELY TO GEMINI
# ============================================================

from pathlib import Path
from datetime import datetime, timezone
from getpass import getpass
import json
import os
import time

from google import genai
from google.genai import types

print(
    "I need my Gemini API key for offline "
    "static generation and live custom-skill testing."
)

print(
    "The key will remain hidden while I type it."
)

print(
    "I will not print it or save it "
    "to Google Drive."
)


# ------------------------------------------------------------
# Locations
# ------------------------------------------------------------

DRAG_DROP_ROOT = Path(
    "/content/drive/MyDrive/CareerTimeMachine/"
    "drag_and_drop_pipeline_v1"
)

REPORT_DIRECTORY = DRAG_DROP_ROOT / "reports"

REPORT_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True
)


# ------------------------------------------------------------
# Read the API key securely
# ------------------------------------------------------------

GEMINI_API_KEY = getpass(
    "\nPaste my Gemini API key and press Enter: "
).strip()

if not GEMINI_API_KEY:
    raise ValueError(
        "A Gemini API key is required."
    )

if len(GEMINI_API_KEY) < 20:
    raise ValueError(
        "The supplied Gemini API key appears "
        "to be incomplete."
    )


# Keep the key only in the current runtime environment.
os.environ["GEMINI_API_KEY"] = (
    GEMINI_API_KEY
)

gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ------------------------------------------------------------
# Discover available Gemini models
# ------------------------------------------------------------

print(
    "\nI am checking the available "
    "Gemini models."
)

available_models = []

try:
    for model_record in (
        gemini_client.models.list()
    ):
        model_name = str(
            getattr(
                model_record,
                "name",
                ""
            )
        ).strip()

        if not model_name:
            continue

        normalised_model_name = (
            model_name.removeprefix(
                "models/"
            )
        )

        if "gemini" in (
            normalised_model_name.casefold()
        ):
            available_models.append(
                normalised_model_name
            )

except Exception as error:
    raise RuntimeError(
        "I could not list the available "
        "Gemini models: "
        f"{type(error).__name__}: {error}"
    ) from error

available_models = sorted(
    set(available_models)
)

if not available_models:
    raise RuntimeError(
        "The API key did not return any "
        "available Gemini models."
    )


# ------------------------------------------------------------
# Select the preferred offline generator
# ------------------------------------------------------------

PREFERRED_GENERATOR_MODELS = [
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
    "gemini-3-flash",
    "gemini-2.5-flash",
]

GEMINI_STATIC_GENERATOR_MODEL = None

for preferred_model in (
    PREFERRED_GENERATOR_MODELS
):
    if preferred_model in available_models:
        GEMINI_STATIC_GENERATOR_MODEL = (
            preferred_model
        )
        break

if GEMINI_STATIC_GENERATOR_MODEL is None:
    flash_candidates = [
        model_name
        for model_name in available_models
        if "flash" in (
            model_name.casefold()
        )
        and "image" not in (
            model_name.casefold()
        )
        and "tts" not in (
            model_name.casefold()
        )
    ]

    if flash_candidates:
        GEMINI_STATIC_GENERATOR_MODEL = (
            flash_candidates[-1]
        )

if GEMINI_STATIC_GENERATOR_MODEL is None:
    raise RuntimeError(
        "I could not find a suitable "
        "Gemini Flash model."
    )


# ------------------------------------------------------------
# Select the preferred live model
# ------------------------------------------------------------

PREFERRED_LIVE_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3-flash-lite-preview",
    "gemini-2.5-flash-lite",
    GEMINI_STATIC_GENERATOR_MODEL,
]

GEMINI_LIVE_GENERATOR_MODEL = None

for preferred_model in (
    PREFERRED_LIVE_MODELS
):
    if preferred_model in available_models:
        GEMINI_LIVE_GENERATOR_MODEL = (
            preferred_model
        )
        break

if GEMINI_LIVE_GENERATOR_MODEL is None:
    GEMINI_LIVE_GENERATOR_MODEL = (
        GEMINI_STATIC_GENERATOR_MODEL
    )


# ------------------------------------------------------------
# Verify the selected offline model
# ------------------------------------------------------------

print(
    "\nI am verifying my Gemini API key "
    "and selected generator."
)

smoke_test_started = time.perf_counter()

try:
    smoke_response = (
        gemini_client.models.generate_content(
            model=(
                GEMINI_STATIC_GENERATOR_MODEL
            ),
            contents=(
                "Return one JSON object containing "
                'exactly {"status":"ready"}.'
            ),
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type=(
                    "application/json"
                ),
            ),
        )
    )

except Exception as error:
    raise RuntimeError(
        "The Gemini connection test failed: "
        f"{type(error).__name__}: {error}"
    ) from error

smoke_test_latency = round(
    time.perf_counter()
    - smoke_test_started,
    4
)

smoke_text = (
    smoke_response.text or ""
).strip()

try:
    smoke_payload = json.loads(
        smoke_text
    )
except json.JSONDecodeError as error:
    raise RuntimeError(
        "Gemini did not return valid JSON "
        "during the connection test."
    ) from error

if smoke_payload != {
    "status": "ready"
}:
    raise RuntimeError(
        "Gemini returned an unexpected "
        "connection-test response: "
        f"{smoke_payload}"
    )


# ------------------------------------------------------------
# Remove the plain key variable
# ------------------------------------------------------------

# The client and environment variable remain available
# during this Colab runtime. The original plain variable
# is removed to reduce accidental exposure.
del GEMINI_API_KEY


# ------------------------------------------------------------
# Save non-secret connection evidence
# ------------------------------------------------------------

flash_models = [
    model_name
    for model_name in available_models
    if "flash" in model_name.casefold()
]

CONNECTION_REPORT = {
    "report_name": (
        "drag_and_drop_gemini_"
        "connection_report_v1"
    ),
    "created_at_utc": datetime.now(
        timezone.utc
    ).isoformat(),
    "connection_succeeded": True,
    "offline_static_generator_model": (
        GEMINI_STATIC_GENERATOR_MODEL
    ),
    "live_generator_model": (
        GEMINI_LIVE_GENERATOR_MODEL
    ),
    "available_gemini_model_count": len(
        available_models
    ),
    "available_flash_model_count": len(
        flash_models
    ),
    "smoke_test_response": (
        smoke_payload
    ),
    "smoke_test_latency_seconds": (
        smoke_test_latency
    ),
    "api_key_printed": False,
    "api_key_saved_to_drive": False,
    "api_key_saved_to_report": False,
}

CONNECTION_REPORT_FILE = (
    REPORT_DIRECTORY
    / "drag_and_drop_gemini_"
      "connection_report_v1.json"
)

with CONNECTION_REPORT_FILE.open(
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        CONNECTION_REPORT,
        file,
        indent=2,
        ensure_ascii=False
    )


# ------------------------------------------------------------
# Report completion
# ------------------------------------------------------------

print(
    "\nI successfully connected to "
    "the Gemini API."
)

print(
    "\nI selected this model for "
    "offline static generation:"
)

print(
    "  - "
    f"{GEMINI_STATIC_GENERATOR_MODEL}"
)

print(
    "\nI selected this model for "
    "live custom-skill generation:"
)

print(
    "  - "
    f"{GEMINI_LIVE_GENERATOR_MODEL}"
)

print(
    "\nI found "
    f"{len(flash_models)} "
    "available Gemini Flash models."
)

print(
    "\nMy connection test took "
    f"{smoke_test_latency:.4f} seconds."
)

print(
    "\nI did not print or save "
    "my API key."
)

print(
    "\nI saved my connection evidence to:"
)

print(CONNECTION_REPORT_FILE)

print(
    "\nSTEP 7 COMPLETE"
)