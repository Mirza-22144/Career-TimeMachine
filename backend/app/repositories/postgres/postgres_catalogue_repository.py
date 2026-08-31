import psycopg2
import psycopg2.pool

from app.core.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_SSLMODE, DB_USER
from app.repositories.interfaces.catalogue_repository import (
    CatalogueItem,
    CatalogueRepository,
)
from app.repositories.memory.memory_catalogue_repository import CATALOGUES

# role, skill, and role_skill are the only tables filled in so far. Every
# other kind's table is still empty, so those keep using the placeholder
# list until the data team fills them in.

# One shared pool of database connections, reused across every request
# instead of opening a new connection each time.
_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=5,
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    sslmode=DB_SSLMODE,
)


# Runs one SQL query and returns all matching rows. Used by every method
# below instead of repeating the connect/cursor/close steps each time.
def _query(sql: str, params: tuple = ()) -> list[tuple]:
    conn = _pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        _pool.putconn(conn)


class PostgresCatalogueRepository(CatalogueRepository):
    """Reads real data from the database for roles and skills; falls back
    to the same placeholder lists as MemoryCatalogueRepository for kinds
    whose tables are still empty."""

    def get_items(self, kind: str) -> list[CatalogueItem]:
        """Return the list for a kind. Roles and skills come from the
        database; everything else falls back to the placeholder list."""
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
        """Return the skills linked to a role, best matches first. Used by
        the skills catalogue endpoint and the skill relevance comparison."""
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

        # in_demand and hot_technology alone are the same for most of a
        # role's skills, which made the list look alphabetical (Python
        # buried behind "Active directory"). A category shared by many of
        # this role's in-demand skills is a good sign it matters for the
        # role (e.g. "Object or component oriented development software"
        # for a developer); a category used by only one skill is usually a
        # data mistake. Sorting by how often a category shows up - still
        # real data, nothing made up - puts core skills near the top.
        category_counts: dict[str, int] = {}
        for _id, _label, in_demand, hot, category in rows:
            if in_demand and hot and category:
                category_counts[category] = category_counts.get(category, 0) + 1

        # In-demand first, then hot, then most common category, then name.
        def sort_key(row):
            _id, label, in_demand, hot, category = row
            return (not in_demand, not hot, -category_counts.get(category, 0), label)

        return [
            CatalogueItem(id=r[0], label=r[1], in_demand=bool(r[2]), hot_technology=bool(r[3]))
            for r in sorted(rows, key=sort_key)
        ]
