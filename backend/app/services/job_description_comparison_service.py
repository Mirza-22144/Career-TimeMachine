import re
from dataclasses import dataclass, field

from fastapi import HTTPException, status
from rapidfuzz import fuzz

from app.repositories.interfaces.catalogue_repository import CatalogueRepository
from app.repositories.interfaces.job_description_repository import JobDescription, JobDescriptionRepository
from app.repositories.interfaces.profile_repository import Profile, ProfileRepository
from app.services.practice_role_service import OTHER_ROLE_ID
from app.services.role_prediction_service import RolePredictionService

# How many roles the "Which role is closest to this job?" picker offers.
CLOSEST_ROLE_COUNT = 3
# Below this title similarity (0-100) a role is not "close" at all - the
# frontend then shows "We don't have a roadmap for this kind of role yet."
CLOSEST_ROLE_MIN_SCORE = 60
# A small nudge toward roles the prediction model also suggests for her, so
# they win near-ties. Never enough to beat a clearly better title match.
PREDICTED_ROLE_BONUS = 5

_STOPWORDS = {
    "a", "an", "and", "the", "of", "to", "in", "on", "for", "with", "our", "or", "your", "you", "will",
    "be", "is", "are", "as", "at", "by", "from", "that", "this", "work", "help", "skill", "experience",
}


def _stem(word: str) -> str:
    for suffix in ("ing", "ion", "ment", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            word = word[: -len(suffix)]
            break
    return word.rstrip("e")


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9+#.]+", text.casefold())
    return {_stem(word) for word in words if word not in _STOPWORDS and len(word) > 1}


def _normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9+#]", "", text.casefold())


def _lower_first(text: str) -> str:
    """Lower-case the first letter for mid-sentence use, unless the first
    word is an acronym (REST, SQL)."""
    first_word = text.split(" ", 1)[0] if text else ""
    if not text or (len(first_word) > 1 and first_word.isupper()):
        return text
    return text[:1].lower() + text[1:]


@dataclass
class RefreshItem:
    """A requirement that relates to a skill she listed but asks for a
    newer or more specific version of it (Automated testing vs Testing)."""

    requirement: str
    profile_skill: str


@dataclass
class TransferableItem:
    """Something in her profile that relates to a requirement, with one
    sentence explaining the link."""

    experience: str
    relates_to: str
    explanation: str


@dataclass
class JobComparison:
    """Her map for one job (AC 5.2.1). Every requirement appears in one
    group only. No score, percentage or verdict by design."""

    job_description_id: str
    job_title: str | None
    experience_sentence: str | None
    break_start_year: int | None
    skills_bring_back: list[str] = field(default_factory=list)
    worth_refreshing: list[RefreshItem] = field(default_factory=list)
    transferable_experience: list[TransferableItem] = field(default_factory=list)
    skills_could_explore: list[str] = field(default_factory=list)


@dataclass
class RoleOption:
    role_id: str
    role_label: str


@dataclass
class ClosestRoles:
    """AC 5.2.2. exact_role_id is set when the job title is one of our
    roles outright - the picker can be skipped. closest is empty when no
    role is close."""

    job_title: str | None
    exact_role_id: str | None
    closest: list[RoleOption] = field(default_factory=list)
    # The role she already chose for this job description, if any - the
    # picker is skipped when this is set.
    chosen_role_id: str | None = None


class JobDescriptionComparisonService:
    """Compares a saved job description's extracted requirements with the
    profile, and finds the roles closest to its title. Rule-based on real
    data only: exact and partial skill-name matches and shared wording
    between responsibilities - nothing is generated."""

    def __init__(
        self,
        job_descriptions: JobDescriptionRepository,
        profiles: ProfileRepository,
        catalogue: CatalogueRepository,
        predictions: RolePredictionService,
    ) -> None:
        self.job_descriptions = job_descriptions
        self.profiles = profiles
        self.catalogue = catalogue
        self.predictions = predictions

    def compare(self, owner: str, job_description_id: str) -> JobComparison:
        job = self._job(owner, job_description_id)
        profile = self.profiles.get_by_session_token(owner) or Profile(session_token=owner)

        profile_skills = self._labels("skills", profile.skill_ids) + list(profile.custom_skills)
        responsibilities = self._labels("responsibilities", profile.responsibility_ids) + list(
            profile.custom_responsibilities
        )
        by_normalised = {_normalise(label): label for label in profile_skills}

        bring_back: list[str] = []
        refreshing: list[RefreshItem] = []
        unmatched: list[str] = []
        seen: set[str] = set()
        for skill in job.extracted_skills:
            key = _normalise(skill.label)
            if not key or key in seen:
                continue
            seen.add(key)
            if key in by_normalised:
                bring_back.append(by_normalised[key])
                continue
            related = self._related_skill(skill.label, profile_skills)
            if related is not None:
                refreshing.append(RefreshItem(requirement=skill.label, profile_skill=related))
            else:
                unmatched.append(skill.label)

        # Her responsibilities against what the ad asks for: its
        # responsibilities first, then any requirement still unmatched.
        transferable: list[TransferableItem] = []
        # One-word "responsibilities" (Design, Build) are extraction
        # fragments, too vague to say anything relates to them.
        ad_responsibilities = [r for r in job.extracted_responsibilities if len(r.split()) > 1]
        for responsibility in responsibilities:
            target = self._best_overlap(responsibility, ad_responsibilities)
            if target is None:
                target = self._best_overlap(responsibility, unmatched)
                if target is not None:
                    unmatched.remove(target)
            if target is None:
                continue
            transferable.append(
                TransferableItem(
                    experience=responsibility,
                    relates_to=target,
                    explanation=f"{responsibility} relates to {_lower_first(target)}.",
                )
            )

        return JobComparison(
            job_description_id=job.job_description_id,
            job_title=job.role_title_guess,
            experience_sentence=self._experience_sentence(job, profile, bring_back),
            break_start_year=profile.break_started_on.year if profile.break_started_on else None,
            skills_bring_back=bring_back,
            worth_refreshing=refreshing,
            transferable_experience=transferable,
            skills_could_explore=unmatched,
        )

    def closest_roles(self, owner: str, job_description_id: str) -> ClosestRoles:
        job = self._job(owner, job_description_id)
        title = job.role_title_guess
        # A remembered choice only counts while that role still exists.
        role_ids = {role.id for role in self.catalogue.get_items("roles")}
        chosen = job.closest_role_id if job.closest_role_id in role_ids else None
        if not title:
            return ClosestRoles(job_title=None, exact_role_id=None, chosen_role_id=chosen)

        predicted_ids = {
            role.role_id for role in self.predictions.predict_two_for_session(owner).predicted_roles
        }
        exact_role_id = None
        scored: list[tuple[float, RoleOption]] = []
        for role in self.catalogue.get_items("roles"):
            if role.id == OTHER_ROLE_ID:
                continue
            if _normalise(role.label) == _normalise(title):
                exact_role_id = role.id
            score = fuzz.token_set_ratio(title.casefold(), role.label.casefold())
            if score < CLOSEST_ROLE_MIN_SCORE:
                continue
            if role.id in predicted_ids:
                score += PREDICTED_ROLE_BONUS
            scored.append((score, RoleOption(role_id=role.id, role_label=role.label)))

        scored.sort(key=lambda item: (-item[0], item[1].role_label))
        return ClosestRoles(
            job_title=title,
            exact_role_id=exact_role_id,
            closest=[option for _score, option in scored[:CLOSEST_ROLE_COUNT]],
            chosen_role_id=chosen,
        )

    def choose_closest_role(self, owner: str, job_description_id: str, role_id: str) -> None:
        """AC 5.2.2: remember her choice for this job description."""
        valid = {role.id for role in self.catalogue.get_items("roles")} - {OTHER_ROLE_ID}
        if role_id not in valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role_id: {role_id}")
        self._job(owner, job_description_id)  # 404s for an unknown or another owner's id
        self.job_descriptions.set_closest_role(owner, job_description_id, role_id)

    def _job(self, owner: str, job_description_id: str) -> JobDescription:
        job = self.job_descriptions.get_for_owner(owner, job_description_id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "JOB_DESCRIPTION_NOT_FOUND", "message": "Job description not found"},
            )
        return job

    def _labels(self, kind: str, ids: list[str]) -> list[str]:
        labels = {item.id: item.label for item in self.catalogue.get_items(kind)}
        return [labels[item_id] for item_id in ids if item_id in labels]

    def _related_skill(self, requirement: str, profile_skills: list[str]) -> str | None:
        """A profile skill whose words are all contained in the requirement
        (Testing in Automated testing, SQL in SQL databases) or the reverse."""
        requirement_tokens = _tokens(requirement)
        for skill in profile_skills:
            skill_tokens = _tokens(skill)
            if not skill_tokens or not requirement_tokens:
                continue
            if skill_tokens <= requirement_tokens or requirement_tokens <= skill_tokens:
                return skill
        return None

    def _best_overlap(self, text: str, candidates: list[str]) -> str | None:
        """The candidate sharing the most meaningful words with text."""
        text_tokens = _tokens(text)
        best, best_count = None, 0
        for candidate in candidates:
            count = len(text_tokens & _tokens(candidate))
            if count > best_count:
                best, best_count = candidate, count
        return best

    def _experience_sentence(self, job: JobDescription, profile: Profile, bring_back: list[str]) -> str | None:
        """"This role asks for [requirement]. Your profile shows [related
        experience]." - left out when the ad states no years."""
        if job.min_years_experience is None or profile.role_id is None:
            return None
        years = {item.id: item.label for item in self.catalogue.get_items("experience-options")}
        years_label = years.get(profile.years_experience)
        roles = {item.id: item.label for item in self.catalogue.get_items("roles")}
        role_label = roles.get(profile.role_id, profile.role_id)
        if profile.role_id == OTHER_ROLE_ID and profile.role_other_text:
            role_label = profile.role_other_text
        if years_label is None:
            return None

        asked = job.min_years_experience
        sentence = (
            f"This role asks for {asked} {'year' if asked == 1 else 'years'} of experience. "
            f"Your profile shows {years_label} as a {role_label}."
        )
        match = re.match(r"\d+", profile.years_experience or "")
        if match and int(match.group()) < asked and bring_back:
            sentence += f" Your experience with {' and '.join(bring_back[:2])} is worth highlighting."
        return sentence
