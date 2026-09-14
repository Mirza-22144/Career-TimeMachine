"""Curated scenario provider for local development and automated tests.

This is NOT the production AI integration. It returns hand-written scenarios
matched to broad role families so the practice flow can be built and tested
before the AI owner's provider exists. Each scenario can be served as a
single-selection multiple-choice activity (active in Iteration 2) or as a
written-response activity (kept for later iterations). Submitted answers are
only read as data - nothing a user submits is ever executed.
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
class CuratedOption:
    """One multiple-choice approach and the reflective notes shown when it is
    selected. No option is marked correct: each is a plausible workplace
    approach with its own trade-offs."""

    option_id: str
    text: str
    may_help: str
    trade_off: str
    consider: str


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
    decision_prompt: str
    options: tuple[CuratedOption, ...]


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
            decision_prompt="What would you do first to investigate the slowdown?",
            options=(
                CuratedOption(
                    option_id="software_slow_release_a",
                    text=(
                        "Compare this morning's release changes with the monitoring data for "
                        "the order history page"
                    ),
                    may_help=(
                        "Linking the timing of the slowdown to specific changes can narrow "
                        "the search quickly and gives your lead evidence rather than guesses."
                    ),
                    trade_off=(
                        "Reading through the changes and dashboards takes time while "
                        "customers are still waiting, so support may need a holding update "
                        "first."
                    ),
                    consider=(
                        "If the monitoring data is incomplete, how would you find out where "
                        "the time is being spent?"
                    ),
                ),
                CuratedOption(
                    option_id="software_slow_release_b",
                    text="Roll back this morning's release straight away, then investigate",
                    may_help=(
                        "Rolling back can restore normal service for customers quickly, which "
                        "reduces the impact while the cause is found."
                    ),
                    trade_off=(
                        "A rollback also removes any fixes or features in the release, and "
                        "the slowdown may turn out to have a different cause."
                    ),
                    consider=(
                        "Who would you check with before rolling back, and how would you "
                        "confirm afterwards that it helped?"
                    ),
                ),
                CuratedOption(
                    option_id="software_slow_release_c",
                    text=(
                        "Post an update for support and customers, then start gathering "
                        "information"
                    ),
                    may_help=(
                        "Communicating early keeps support and customers informed and reduces "
                        "repeated questions while you work."
                    ),
                    trade_off=(
                        "An update without any findings yet may raise questions you cannot "
                        "answer, and the investigation starts a little later."
                    ),
                    consider=(
                        "How often would you update support, and what would each update "
                        "include?"
                    ),
                ),
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
            decision_prompt="What would you focus on first in your review?",
            options=(
                CuratedOption(
                    option_id="software_code_review_a",
                    text=(
                        "Ask for automated tests that cover the main discount-code cases "
                        "before approving"
                    ),
                    may_help=(
                        "Tests protect checkout from future changes and give the developer a "
                        "clear, concrete next step."
                    ),
                    trade_off=(
                        "Adding tests may push the change past the end of the day, which "
                        "could affect anyone waiting for the feature."
                    ),
                    consider=(
                        "Which one or two test cases would you suggest first so the request "
                        "feels manageable?"
                    ),
                ),
                CuratedOption(
                    option_id="software_code_review_b",
                    text="Suggest splitting the long function into smaller, named parts",
                    may_help=(
                        "Smaller functions are easier to read, review and change, which helps "
                        "the whole team maintain checkout."
                    ),
                    trade_off=(
                        "Restructuring working code carries its own risk when there are no "
                        "tests to show that behaviour has not changed."
                    ),
                    consider=(
                        "Would you ask for this now, or record it as a follow-up once tests "
                        "are in place?"
                    ),
                ),
                CuratedOption(
                    option_id="software_code_review_c",
                    text=(
                        "Approve it with comments so the feature ships today, and pair on "
                        "improvements next week"
                    ),
                    may_help=(
                        "This respects the deadline and offers the developer support, which "
                        "can build their confidence."
                    ),
                    trade_off=(
                        "Checkout changes without tests reach customers, and follow-up work "
                        "can be displaced by new priorities."
                    ),
                    consider=(
                        "What would you need in place to feel comfortable releasing checkout "
                        "changes without tests?"
                    ),
                ),
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
            decision_prompt="What would you check first to explain the difference?",
            options=(
                CuratedOption(
                    option_id="data_dashboard_mismatch_a",
                    text="Compare how each dashboard defines and filters revenue",
                    may_help=(
                        "Differences in definitions, such as refunds or date ranges, often "
                        "explain mismatched figures and are quick to confirm."
                    ),
                    trade_off=(
                        "If the definitions match, you will still need to trace the "
                        "underlying data, so this may be only the first step."
                    ),
                    consider=(
                        "Who owns each dashboard definition, and how would you agree on one "
                        "for the board report?"
                    ),
                ),
                CuratedOption(
                    option_id="data_dashboard_mismatch_b",
                    text=(
                        "Run your own query against the warehouse to produce an independent "
                        "figure"
                    ),
                    may_help=(
                        "An independent query gives you a figure you understand fully and can "
                        "explain to the manager."
                    ),
                    trade_off=(
                        "A third figure can add confusion if it does not match either "
                        "dashboard and its assumptions are not documented."
                    ),
                    consider=(
                        "How would you document your query so others can check how the figure "
                        "was produced?"
                    ),
                ),
                CuratedOption(
                    option_id="data_dashboard_mismatch_c",
                    text=(
                        "Suggest the manager uses the finance figure for now, since finance "
                        "owns revenue reporting"
                    ),
                    may_help=(
                        "This gives the manager a figure to work with before Friday and "
                        "follows an existing ownership line."
                    ),
                    trade_off=(
                        "The underlying difference remains unexplained, and the sales "
                        "dashboard may keep showing a conflicting figure."
                    ),
                    consider=(
                        "What caveat, if any, would you include alongside the figure in the "
                        "board report?"
                    ),
                ),
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
            decision_prompt="How would you plan the single day of testing?",
            options=(
                CuratedOption(
                    option_id="quality_rushed_release_a",
                    text=(
                        "Test the transfer limits feature first, since a defect there could "
                        "affect customers' money"
                    ),
                    may_help=(
                        "Ranking by potential harm puts your limited time where a defect "
                        "would affect customers most."
                    ),
                    trade_off=(
                        "Login changes get less attention, and a login problem could stop "
                        "customers reaching the app at all."
                    ),
                    consider=(
                        "How would you record which login checks were not done so the release "
                        "manager can decide?"
                    ),
                ),
                CuratedOption(
                    option_id="quality_rushed_release_b",
                    text="Split the day evenly between the login screen and transfer limits",
                    may_help="Even coverage means neither change goes out completely untested.",
                    trade_off=(
                        "Neither area may get deep enough testing to find less obvious "
                        "defects in a high-risk feature."
                    ),
                    consider="Which specific checks would you drop from each area to fit the time?",
                ),
                CuratedOption(
                    option_id="quality_rushed_release_c",
                    text=(
                        "Ask the release manager whether the deadline allows releasing only "
                        "the lower-risk change"
                    ),
                    may_help=(
                        "Raising options early lets the people who own the risk make an "
                        "informed decision."
                    ),
                    trade_off=(
                        "The conversation takes time away from testing, and the regulatory "
                        "deadline may leave no room to change the plan."
                    ),
                    consider=(
                        "What information would the release manager need from you to decide "
                        "quickly?"
                    ),
                ),
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
            decision_prompt="What would you do first?",
            options=(
                CuratedOption(
                    option_id="security_phishing_report_a",
                    text=(
                        "Help the person who clicked reset their password and review their "
                        "account activity"
                    ),
                    may_help=(
                        "Containing the one known exposure quickly limits what an attacker "
                        "could do with any details entered."
                    ),
                    trade_off=(
                        "While you focus on one account, other staff may still receive and "
                        "click the email."
                    ),
                    consider=(
                        "What would you ask the person about what they entered after clicking "
                        "the link?"
                    ),
                ),
                CuratedOption(
                    option_id="security_phishing_report_b",
                    text="Block the sender and remove the email from all mailboxes",
                    may_help="Removing the email stops further clicks across the organisation.",
                    trade_off=(
                        "It does not address the account that may already be exposed, so that "
                        "step still needs to follow quickly."
                    ),
                    consider=(
                        "How would you find out whether anyone else clicked before the email "
                        "was removed?"
                    ),
                ),
                CuratedOption(
                    option_id="security_phishing_report_c",
                    text="Send a short warning to all staff about the email",
                    may_help=(
                        "A clear warning helps staff avoid the link and report similar "
                        "messages."
                    ),
                    trade_off=(
                        "A company-wide message takes time to approve and send, and some "
                        "staff will read it after clicking."
                    ),
                    consider=(
                        "How would you keep the warning short and calm so it does not cause "
                        "alarm?"
                    ),
                ),
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
            decision_prompt="What would you do first?",
            options=(
                CuratedOption(
                    option_id="infrastructure_office_outage_a",
                    text=(
                        "Compare the office network path with the home connections to narrow "
                        "down the fault"
                    ),
                    may_help=(
                        "Comparing what works with what does not can quickly show whether the "
                        "fault is in the office network."
                    ),
                    trade_off=(
                        "Diagnosis takes time, and office staff still cannot work while you "
                        "investigate."
                    ),
                    consider="Which quick checks would tell you most about the office connection?",
                ),
                CuratedOption(
                    option_id="infrastructure_office_outage_b",
                    text=(
                        "Set up a workaround, such as a mobile hotspot, so the client meeting "
                        "can go ahead"
                    ),
                    may_help=(
                        "Protecting the client meeting reduces the most visible business "
                        "impact in the next forty minutes."
                    ),
                    trade_off=(
                        "A workaround may bypass normal security controls and does not fix "
                        "the problem for other staff."
                    ),
                    consider="What security checks would the workaround need before it is used?",
                ),
                CuratedOption(
                    option_id="infrastructure_office_outage_c",
                    text="Send a status message to the affected office before investigating",
                    may_help=(
                        "A clear message reduces duplicate tickets and lets staff plan around "
                        "the outage."
                    ),
                    trade_off=(
                        "Without findings yet, the message can only say that the issue is "
                        "being looked at."
                    ),
                    consider="When would you send the next update, and what would trigger it?",
                ),
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
            decision_prompt="How would you prioritise the two requests?",
            options=(
                CuratedOption(
                    option_id="general_competing_requests_a",
                    text="Start with the problem blocking five colleagues, then work on the report",
                    may_help=(
                        "Unblocking several people today reduces the overall impact on the "
                        "team."
                    ),
                    trade_off="The report may be rushed or late for tomorrow's budget meeting.",
                    consider="How would you check that the report can still be ready in time?",
                ),
                CuratedOption(
                    option_id="general_competing_requests_b",
                    text="Ask both managers to agree the order together",
                    may_help=(
                        "A shared decision makes the trade-off visible and avoids you "
                        "choosing between managers alone."
                    ),
                    trade_off=(
                        "Arranging the conversation takes time while five colleagues remain "
                        "blocked."
                    ),
                    consider="What would you do if the managers could not be reached quickly?",
                ),
                CuratedOption(
                    option_id="general_competing_requests_c",
                    text=(
                        "Split your time, starting with a quick fix attempt before returning "
                        "to the report"
                    ),
                    may_help=(
                        "Making some progress on both keeps each manager informed and their "
                        "work moving."
                    ),
                    trade_off=(
                        "Switching between tasks can slow both down, and neither may be "
                        "finished soon."
                    ),
                    consider=(
                        "How long would you give the quick fix before switching back to the "
                        "report?"
                    ),
                ),
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
        if request.activity_type not in ("multiple_choice", "written_response"):
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

        # Scenario skills first, then up to two of the user's own saved skills.
        skills_used = list(scenario.skills)
        for skill in request.skills:
            if len(skills_used) >= len(scenario.skills) + 2:
                break
            if skill.lower() not in {s.lower() for s in skills_used}:
                skills_used.append(skill)

        content: dict[str, Any] = {
            "scenario_id": scenario.scenario_id,
            "title": scenario.title,
            "workplace_area": scenario.workplace_area,
            "situation": scenario.situation,
            "activity_type": request.activity_type,
            "guidance": list(scenario.guidance[:hint_count]),
            "skills_used": skills_used,
            "new_skill_focus": scenario.new_skill_focus,
        }
        if request.activity_type == "multiple_choice":
            content["task"] = scenario.decision_prompt
            content["options"] = [{"option_id": option.option_id, "text": option.text} for option in scenario.options]
        else:
            content["task"] = scenario.task
            if request.difficulty == "challenge":
                content["task"] += " Note any assumptions you are making."
        return content

    def generate_feedback(self, request: FeedbackRequest) -> dict[str, Any]:
        scenario = _SCENARIOS_BY_ID.get(request.scenario_id)
        if scenario is None:
            raise ScenarioProviderError("Unknown curated scenario")
        if request.activity_type == "multiple_choice":
            return self._multiple_choice_feedback(scenario, request)
        if request.activity_type == "written_response" and request.response_text is not None:
            return self._written_feedback(scenario, request)
        raise ScenarioProviderError("Unsupported feedback request")

    def _multiple_choice_feedback(self, scenario: CuratedScenario, request: FeedbackRequest) -> dict[str, Any]:
        """Reflect on the selected approach: why it may help, its trade-offs
        and what else to consider. No option is ever labelled correct."""
        option = next((o for o in scenario.options if o.option_id == request.selected_option_id), None)
        if option is None:
            raise ScenarioProviderError("Unknown curated option")
        return {
            "what_worked_well": [option.may_help],
            "trade_offs": [option.trade_off],
            "areas_to_consider": [
                option.consider,
                "The other options could suit a different deadline, team or level of risk, so think about "
                "when you might choose one of them instead.",
            ],
            "skill_to_explore": {
                "skill": scenario.new_skill_focus,
                "why_relevant": scenario.why_relevant,
            },
        }

    def _written_feedback(self, scenario: CuratedScenario, request: FeedbackRequest) -> dict[str, Any]:
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
