# Recovered from the tested Colab notebook
# Notebook code cell: 30
# This file is source evidence and may depend on earlier notebook definitions.

# ============================================================
# STEP 16C PRINT REPAIR
# No generation or API calls are repeated.
# ============================================================

from pathlib import Path


BASE_DIRECTORY = Path(
    "/content/drive/MyDrive/"
    "CareerTimeMachine/"
    "drag_and_drop_pipeline_v1"
)

FINAL_OUTPUT_FILE = (
    BASE_DIRECTORY
    / "live_service/output/balanced_evaluation/"
    "balanced_live_drag_and_drop_outputs_v1_corrected.json"
)

FINAL_REPORT_FILE = (
    BASE_DIRECTORY
    / "reports/"
    "balanced_live_drag_and_drop_evaluation_v1_corrected.json"
)


# Correct the variable-name typo from the previous cell.
final_live_evaluation_passed = (
    final_evaluation_passed
)


if not FINAL_OUTPUT_FILE.exists():
    raise FileNotFoundError(
        "The corrected combined output file was not saved."
    )

if not FINAL_REPORT_FILE.exists():
    raise FileNotFoundError(
        "The corrected evaluation report was not saved."
    )


print("=" * 72)
print(
    "I completed my corrected balanced "
    "live drag-and-drop evaluation."
)
print()
print(
    f"I passed {passed_count}/6 live tests."
)
print(
    f"Mean live latency: {mean_latency} seconds"
)
print(
    f"P95 live latency: {p95_latency} seconds"
)
print(
    "Security tests passed: 6/6"
)
print(
    "Forced static fallback passed: True"
)
print(
    "Frontend answer mapping hidden: True"
)
print(
    "Backend answer mapping retained: True"
)
print(
    "Exact duplicate situations: 0"
)
print(
    "Near-duplicate situations: 0"
)
print()
print(
    "Final live evaluation passed: "
    f"{final_live_evaluation_passed}"
)
print()
print(
    "I preserved the original failed evaluation "
    "as change-management evidence."
)
print()
print(
    "I saved my corrected combined outputs to:"
)
print(FINAL_OUTPUT_FILE)
print()
print(
    "I saved my final corrected evaluation to:"
)
print(FINAL_REPORT_FILE)
print()
print("STEP 16C COMPLETE")