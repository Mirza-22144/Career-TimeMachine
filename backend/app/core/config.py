import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

_BACKEND_DIR = Path(__file__).resolve().parents[2]

DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_SSLMODE = os.environ.get("DB_SSLMODE", "prefer")

# Comma-separated list of frontend origins allowed to call this API. Local
# dev origins are always included; add the deployed frontend URL through
# the CORS_ORIGINS env var (see DEPLOYMENT.md) rather than editing code.
_extra_origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173", *_extra_origins]

# True once real connection details are present, so the app can fall back
# to the in-memory repositories when they're not (e.g. a fresh checkout with
# no .env yet).
HAS_DATABASE = all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD])

# How long to wait for the workplace-scenario provider before returning a
# controlled "scenario unavailable" error instead.
SCENARIO_PROVIDER_TIMEOUT_SECONDS = float(os.environ.get("SCENARIO_PROVIDER_TIMEOUT_SECONDS", "10"))

# Iteration 3 practice activity: four pre-written questions, plus one live
# question about a skill she typed in herself. The live one is generated
# with Gemini (AI team's reflective_mcq_v3); without a key the static
# fallback question is used instead. 8 seconds is AC 4.4.6's limit.
QUESTIONS_PER_ACTIVITY = int(os.environ.get("QUESTIONS_PER_ACTIVITY", "4"))
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
LIVE_QUESTION_TIMEOUT_SECONDS = float(os.environ.get("LIVE_QUESTION_TIMEOUT_SECONDS", "8"))

# Local GLiNER model directory for job-description extraction (see
# backend/ai/job_description_extraction/MODEL_DEPLOYMENT.md) - too large for
# Git, never committed. Defaults to backend/models/gliner_small_v2_5, a
# gitignored path; override with JOB_DESCRIPTION_MODEL_DIR if it lives
# somewhere else. HAS_JOB_DESCRIPTION_MODEL reflects whether it is actually
# present on disk right now, so the app can fall back cleanly when it is
# not (a fresh checkout, or an environment that hasn't pulled it yet).
JOB_DESCRIPTION_MODEL_DIR = Path(
    os.environ.get("JOB_DESCRIPTION_MODEL_DIR", str(_BACKEND_DIR / "models" / "gliner_small_v2_5"))
)
HAS_JOB_DESCRIPTION_MODEL = JOB_DESCRIPTION_MODEL_DIR.is_dir()

# How long to wait for the job-description extraction provider (a local NLP
# model, real latency unlike the catalogue/role-prediction providers) before
# returning a controlled "couldn't extract" error instead.
JOB_DESCRIPTION_PROVIDER_TIMEOUT_SECONDS = float(
    os.environ.get("JOB_DESCRIPTION_PROVIDER_TIMEOUT_SECONDS", "20")
)
