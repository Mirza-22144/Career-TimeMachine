from datetime import date

from pydantic import BaseModel, ConfigDict


class MarketDataResponse(BaseModel):
    """Real Australian hiring-demand data for the ANZSCO group a predicted
    role maps to (DB 3.1). Several roles can share one ANZSCO group, so
    anzsco_title and confidence are included deliberately - the frontend
    must label this figure by the group, not present it as ads for the
    user's exact role (see ITERATION-3-PROGRESS.md, DB 3.1's note).

    Ad volume is the 12-month average, rounded into a range
    (ads_range_low/high), never an exact count - per the industry mentor's
    guidance and app/core/vacancy_rounding.py. The 12-month average is used
    rather than the latest single month so this figure and yoy_change_pct
    are computed on the same basis, not mixed."""

    model_config = ConfigDict(from_attributes=True)

    anzsco_code: str
    anzsco_title: str
    confidence: str
    state: str
    latest_month: date
    ads_range_low: int
    ads_range_high: int
    yoy_change_pct: float | None
    source: str = "Jobs and Skills Australia - Internet Vacancy Index"


class RoleExplanationResponse(BaseModel):
    """Why a role was suggested: a plain-language summary, her skills the
    role also lists, and reason codes. No score, percentage or confidence."""

    model_config = ConfigDict(from_attributes=True)

    summary: str
    matched_skills: list[str]
    reason_codes: list[str]


class PredictedRoleWithMarketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role_id: str
    role_label: str
    # None when the role has no ANZSCO mapping yet (e.g. "other") or no
    # vacancy data loaded for it - never a fabricated figure.
    market_data: MarketDataResponse | None
    # None when the explainer could not supply one.
    explanation: RoleExplanationResponse | None = None


class PredictedRolesResponse(BaseModel):
    """BE 3.4: two AI-predicted future roles (AI 3.2), each with real
    market data where available. An empty list means no prediction is
    available yet (no previous role saved, or the model could not produce
    one) - this endpoint never returns exactly one role."""

    model_config = ConfigDict(from_attributes=True)

    predicted_roles: list[PredictedRoleWithMarketResponse]
