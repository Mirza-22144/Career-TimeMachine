from copy import deepcopy

from app.repositories.interfaces.job_description_repository import (
    JobDescription,
    JobDescriptionRepository,
)


class MemoryJobDescriptionRepository(JobDescriptionRepository):
    """In-memory store for tests and local dev without a database. Keyed by
    (owner_token_hash, job_description_id); copies in and out so a caller
    mutating a returned object can never corrupt stored state."""

    def __init__(self) -> None:
        self._by_owner: dict[str, dict[str, JobDescription]] = {}

    def add(self, job_description: JobDescription) -> JobDescription:
        owner_store = self._by_owner.setdefault(job_description.owner_token_hash, {})
        owner_store[job_description.job_description_id] = deepcopy(job_description)
        return deepcopy(job_description)

    def get_for_owner(self, owner_token_hash: str, job_description_id: str) -> JobDescription | None:
        stored = self._by_owner.get(owner_token_hash, {}).get(job_description_id)
        return deepcopy(stored) if stored is not None else None

    def list_for_owner(self, owner_token_hash: str) -> list[JobDescription]:
        records = list(self._by_owner.get(owner_token_hash, {}).values())
        records.sort(key=lambda jd: jd.created_at or 0, reverse=True)
        return [deepcopy(jd) for jd in records]

    def delete_for_owner(self, owner_token_hash: str, job_description_id: str) -> bool:
        owner_store = self._by_owner.get(owner_token_hash, {})
        if job_description_id not in owner_store:
            return False
        del owner_store[job_description_id]
        return True
