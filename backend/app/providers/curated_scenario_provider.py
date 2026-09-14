"""Curated scenario provider for local development and automated tests.

This is NOT the production AI integration. It returns hand-written scenarios
matched to broad role families so the practice flow can be built and tested
before the AI owner's provider exists. Submitted responses are only read as
text - nothing a user submits is ever executed.
"""

import re
from dataclasses import dataclass
from typing import Any

from app.providers.scenario_provider import (
    FeedbackRequest,
    ScenarioProvider,
    ScenarioProviderError,
    ScenarioRequest,
)


@dataclass(frozen=True)
class CuratedScenario:
    scenario_id: str
    title: str
    workplace_area: str
    situation: str
    task: str
    skills: tuple[str, ...]
    new_skill_focus: str
    why_relevant: str
    guidance: tuple[str, ...]
    reflection_prompts: tuple[str, ...]


CURATED_SCENARIOS: dict[str, tuple[CuratedScenario, ...]] = {
    "software": (
        CuratedScenario(
            scenario_id="software_slow_release",
            title="Slow responses after a release",
            workplace_area="Engineering team desk",
            situation=(
                "Your team shipped an update to the customer orders service this morning. "
                "Support has passed on reports that the order history page now takes more "
                "than ten seconds to load for some customers. The on-call developer is in "
                "another meeting and your lead has asked you to take a first look."
            ),
            task=(
                "Write a short message to your lead describing how you would investigate the "
                "slowdown, what information you would gather first, and how you would keep "
                "customers and the support team informed while you work on it."
            ),
            skills=("Debugging", "Communication", "API design"),
            new_skill_focus="Observability",
            why_relevant=(
                "Modern teams use logs, metrics and traces to see how a service behaves in "
                "production, which makes problems like this faster to locate without guessing."
            ),
            guidance=(
                "Think about what changed in this morning's release.",
                "Consider which logs or monitoring data would show where the time is spent.",
                "Decide who needs an update, and how often.",
            ),
            reflection_prompts=(
                "How would you confirm the release caused the slowdown before rolling anything back?",
                "What would you record so the team can prevent a similar issue next time?",
            ),
        ),
        CuratedScenario(
            scenario_id="software_code_review",
            title="Reviewing a teammate's pull request",
            workplace_area="Code review queue",
            situation=(
                "A newer developer has opened a pull request that adds a discount-code feature "
                "to the checkout. It works in their demo, but it has no automated tests and one "
                "function is over two hundred lines long. They have asked for your review before "
                "the end of the day."
            ),
            task=(
                "Write the review comment you would leave. Explain what you would ask them to "
                "change, what you would praise, and how you would phrase it so the feedback is "
                "useful and encouraging."
            ),
            skills=("Code review", "Testing", "Mentoring"),
            new_skill_focus="Automated testing in CI pipelines",
            why_relevant=(
                "Teams now run tests automatically on every pull request, so reviews can focus "
                "on design and readability while the pipeline catches regressions."
            ),
            guidance=(
                "Start with what the change does well.",
                "Pick the one or two changes that matter most.",
                "Suggest a concrete first test they could add.",
            ),
            reflection_prompts=(
                "Which of your suggestions would do the most to keep checkout reliable?",
                "How might you pair with the developer so they feel confident adding tests next time?",
            ),
        ),
    ),
    "data": (
        CuratedScenario(
            scenario_id="data_dashboard_mismatch",
            title="Two dashboards disagree",
            workplace_area="Analytics team workspace",
            situation=(
                "The sales manager has noticed that last month's revenue is noticeably higher on "
                "the finance dashboard than on the sales dashboard. Both dashboards read from the "
                "company data warehouse, and the manager needs a figure for a board report on Friday."
            ),
            task=(
                "Write a reply to the sales manager explaining how you would find the cause of the "
                "difference, what you would check first, and what you can promise before Friday."
            ),
            skills=("SQL", "Data analysis", "Stakeholder communication"),
            new_skill_focus="Data lineage and documentation",
            why_relevant=(
                "Documenting where each metric comes from and how it is calculated helps teams "
                "trust shared dashboards and resolve differences quickly."
            ),
            guidance=(
                "List the definitions of revenue each dashboard might be using.",
                "Think about filters, date ranges and refunds.",
                "Be clear about what you know now and what you still need to confirm.",
            ),
            reflection_prompts=(
                "How would you make sure both dashboards agree once this is resolved?",
                "What would you tell the manager if the cause is not found before Friday?",
            ),
        ),
    ),
    "quality": (
        CuratedScenario(
            scenario_id="quality_rushed_release",
            title="Testing a rushed release",
            workplace_area="Test planning board",
            situation=(
                "A mobile banking update must go live tomorrow to meet a regulatory deadline. "
                "Development finished a day late, so you have one working day to test changes to "
                "the login screen and the transfer limits feature."
            ),
            task=(
                "Write a short test plan for the day. Explain what you would test first, what you "
                "would leave out, and how you would communicate the remaining risk to the release manager."
            ),
            skills=("Test planning", "Risk assessment", "Communication"),
            new_skill_focus="Risk-based test automation",
            why_relevant=(
                "Automating the highest-risk checks lets teams re-run them on every build, so tight "
                "deadlines rely less on manual testing."
            ),
            guidance=(
                "Rank the changes by how much harm a defect could cause.",
                "Decide which checks must be done by hand today.",
                "Plan how you will report what was not tested.",
            ),
            reflection_prompts=(
                "Which risks would you want the release manager to formally accept?",
                "What would you automate first after this release?",
            ),
        ),
    ),
    "security": (
        CuratedScenario(
            scenario_id="security_phishing_report",
            title="A suspicious email report",
            workplace_area="Security operations desk",
            situation=(
                "Three staff members have forwarded the same email asking them to confirm their "
                "payroll details through a link. One person says they clicked the link before "
                "noticing the sender address looked wrong."
            ),
            task=(
                "Write the first update you would send to your security lead. Include the immediate "
                "steps you would take, what you would ask the person who clicked the link, and how "
                "you would warn other staff."
            ),
            skills=("Incident response", "Risk assessment", "Communication"),
            new_skill_focus="Security automation",
            why_relevant=(
                "Security teams increasingly automate routine steps such as blocking a sender or "
                "resetting credentials, which shortens the time between a report and containment."
            ),
            guidance=(
                "Separate containment steps from investigation steps.",
                "Think about what the person who clicked may have entered.",
                "Keep the staff warning short and calm.",
            ),
            reflection_prompts=(
                "Which step would you take first, and why?",
                "How would you check whether anyone else interacted with the email?",
            ),
        ),
    ),
    "infrastructure": (
        CuratedScenario(
            scenario_id="infrastructure_office_outage",
            title="One office cannot reach a shared system",
            workplace_area="IT service desk",
            situation=(
                "Staff in one office report that they cannot open the shared document system, while "
                "colleagues working from home can. Tickets are arriving quickly and a client meeting "
                "that depends on those documents starts in forty minutes."
            ),
            task=(
                "Describe how you would narrow down the cause, what you would tell the affected staff "
                "right now, and how you would help the client meeting go ahead."
            ),
            skills=("Troubleshooting", "Networking", "Customer service"),
            new_skill_focus="Cloud networking and zero-trust access",
            why_relevant=(
                "Many organisations now reach systems through cloud services and identity-based "
                "access, so understanding those paths helps when only some users are affected."
            ),
            guidance=(
                "Compare what is different between the office and home users.",
                "Think about a workaround for the meeting.",
                "Plan a single, clear status message.",
            ),
            reflection_prompts=(
                "What evidence would tell you whether the fault is local to the office?",
                "How would you record this so the next person can resolve it faster?",
            ),
        ),
    ),
    "general": (
        CuratedScenario(
            scenario_id="general_competing_requests",
            title="Competing requests on a busy morning",
            workplace_area="Team planning board",
            situation=(
                "In your first week back, two managers each ask you to prioritise their request: one "
                "wants a report on system usage for a budget meeting tomorrow, the other wants help "
                "fixing a problem that is blocking five colleagues today."
            ),
            task=(
                "Write a message to both managers explaining how you would prioritise the two "
                "requests, what you would do first, and how you would keep them both informed."
            ),
            skills=("Prioritisation", "Communication", "Problem solving"),
            new_skill_focus="Agile ways of working",
            why_relevant=(
                "Many technology teams plan work in short cycles with a shared, visible backlog, "
                "which makes competing requests easier to discuss openly."
            ),
            guidance=(
                "Weigh how many people are affected and how urgent each request is.",
                "Consider whether either request can be partly delivered.",
                "Be open about the trade-off you are making.",
            ),
            reflection_prompts=(
                "How would you respond if both managers disagreed with your order?",
                "What would make this kind of decision easier next time?",
            ),
        ),
    ),
}

# First match wins, so more specific families come before "software".
_FAMILY_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("security", ("security", "forensics", "penetration")),
    ("data", ("data", "business_intelligence")),
    ("quality", ("quality", "qa_", "test")),
    ("infrastructure", ("network", "support", "administrator", "cloud")),
    ("software", ("software", "developer", "programmer", "engineer", "web")),
)

_SCENARIOS_BY_ID = {
    scenario.scenario_id: scenario
    for family in CURATED_SCENARIOS.values()
    for scenario in family
}


def role_family(role_id: str) -> str:
    """Map a role catalogue id to a curated scenario family."""
    for family, keywords in _FAMILY_KEYWORDS:
        if any(keyword in role_id for keyword in keywords):
            return family
    return "general"


class CuratedScenarioProvider(ScenarioProvider):
    """Development/test provider backed by CURATED_SCENARIOS."""

    def generate_scenario(self, request: ScenarioRequest) -> dict[str, Any]:
        if request.activity_type != "written_response":
            raise ScenarioProviderError("No curated scenarios for this activity type")
        available = [
            scenario
            for scenario in CURATED_SCENARIOS[role_family(request.role_id)]
            if scenario.scenario_id not in request.exclude_scenario_ids
        ]
        if not available:
            raise ScenarioProviderError("No further curated scenarios for this role")
        scenario = available[0]

        # Guided shows every hint, standard one, challenge none.
        hint_count = {"guided": len(scenario.guidance), "standard": 1}.get(request.difficulty, 0)
        task = scenario.task
        if request.difficulty == "challenge":
            task += " Note any assumptions you are making."

        # Scenario skills first, then up to two of the user's own saved skills.
        skills_used = list(scenario.skills)
        for skill in request.skills:
            if len(skills_used) >= len(scenario.skills) + 2:
                break
            if skill.lower() not in {s.lower() for s in skills_used}:
                skills_used.append(skill)

        return {
            "scenario_id": scenario.scenario_id,
            "title": scenario.title,
            "workplace_area": scenario.workplace_area,
            "situation": scenario.situation,
            "task": task,
            "activity_type": "written_response",
            "guidance": list(scenario.guidance[:hint_count]),
            "skills_used": skills_used,
            "new_skill_focus": scenario.new_skill_focus,
        }

    def generate_feedback(self, request: FeedbackRequest) -> dict[str, Any]:
        scenario = _SCENARIOS_BY_ID.get(request.scenario_id)
        if scenario is None:
            raise ScenarioProviderError("Unknown curated scenario")

        text = request.response_text.lower()
        word_count = len(request.response_text.split())

        worked_well = [
            "You set out your own approach to the situation, which is where any real workplace task starts."
        ]
        if word_count >= 60:
            worked_well.append(
                "You explained your thinking in some detail, which helps a team follow and build on your approach."
            )
        mentioned = [
            skill
            for skill in request.skills_used
            if re.search(rf"(?<!\w){re.escape(skill.lower())}(?!\w)", text)
        ]
        if mentioned:
            worked_well.append(
                f"You drew on {mentioned[0]}, connecting the task to experience you already have."
            )

        areas_to_consider = list(scenario.reflection_prompts)
        if word_count < 25:
            areas_to_consider.append(
                "Consider adding a little more detail about the steps you would take and why."
            )

        return {
            "what_worked_well": worked_well,
            "areas_to_consider": areas_to_consider,
            "skill_to_explore": {
                "skill": scenario.new_skill_focus,
                "why_relevant": scenario.why_relevant,
            },
        }
