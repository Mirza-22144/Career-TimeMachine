import psycopg2
import psycopg2.pool

from app.core.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
from app.repositories.interfaces.catalogue_repository import (
    CatalogueItem,
    CatalogueRepository,
)
from app.repositories.memory.memory_catalogue_repository import CATALOGUES

# Tables actually seeded so far (DATA_HANDOVER.md 2.2: role=28, skill=1299,
# role_skill=5629). Every other kind's table is still empty, blocked on the
# decisions in DATA_HANDOVER.md section 6 - those keep using the curated
# mock list until seeded.

_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=5,
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
)


def _query(sql: str, params: tuple = ()) -> list[tuple]:
    conn = _pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        _pool.putconn(conn)


class PostgresCatalogueRepository(CatalogueRepository):
    """Real Cloud SQL data where it's seeded (role, skill, role_skill);
    falls back to the same curated mock lists as MemoryCatalogueRepository
    for kinds whose tables are still empty (DATA_HANDOVER.md section 6)."""

    def get_items(self, kind: str) -> list[CatalogueItem]:
        if kind == "roles":
            rows = _query("SELECT id, label FROM role ORDER BY label")
            return [CatalogueItem(id=r[0], label=r[1]) for r in rows]
        if kind == "skills":
            rows = _query(
                "SELECT id, label, in_demand, hot_technology FROM skill ORDER BY label"
            )
            return [
                CatalogueItem(id=r[0], label=r[1], in_demand=bool(r[2]), hot_technology=bool(r[3]))
                for r in rows
            ]
        return CATALOGUES.get(kind, [])  # still-empty tables -> curated mock

    def get_skills_for_role(self, role_id: str | None) -> list[CatalogueItem]:
        if not role_id:
            return self.get_items("skills")
        rows = _query(
            """
            SELECT s.id, s.label, s.in_demand, s.hot_technology, s.category
            FROM skill s
            JOIN role_skill rs ON rs.skill_id = s.id
            WHERE rs.role_id = %s
            """,
            (role_id,),
        )
        if not rows:
            return self.get_items("skills")  # unmapped role -> full list

        # in_demand/hot_technology alone tie for the large majority of a
        # role's skills, which left the list looking alphabetical (Python
        # buried behind "Active directory"). A category that recurs often
        # among this role's in-demand skills is core to the role (e.g.
        # "Object or component oriented development software" for a
        # developer); a category used by only one skill is usually a
        # one-off O*NET miscategorisation (DATA_HANDOVER.md 7). Breaking
        # ties by that frequency - still real data, nothing invented -
        # surfaces core languages/tools ahead of incidental tools.
        category_counts: dict[str, int] = {}
        for _id, _label, in_demand, hot, category in rows:
            if in_demand and hot and category:
                category_counts[category] = category_counts.get(category, 0) + 1

        def sort_key(row):
            _id, label, in_demand, hot, category = row
            return (not in_demand, not hot, -category_counts.get(category, 0), label)

        return [
            CatalogueItem(id=r[0], label=r[1], in_demand=bool(r[2]), hot_technology=bool(r[3]))
            for r in sorted(rows, key=sort_key)
        ]
