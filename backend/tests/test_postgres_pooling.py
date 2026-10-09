"""A connection the database dropped while idle must be replaced, not
handed to a request (which would fail until the app was restarted)."""

import psycopg2

from app.repositories.postgres import pooling


class Cursor:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def execute(self, sql, params=None):
        self.conn.statements.append(sql)
        if self.conn.dead:
            self.conn.closed = 1
            raise psycopg2.OperationalError("server closed the connection unexpectedly")

    def fetchone(self):
        return (1,)


class Conn:
    def __init__(self, dead=False):
        self.dead = dead
        self.closed = 0
        self.autocommit = False
        self.statements = []

    def cursor(self):
        return Cursor(self)

    def rollback(self):
        if self.closed:
            raise psycopg2.InterfaceError("connection already closed")


class Pool:
    def __init__(self, *conns):
        self.free = list(conns)
        self.closed = []

    def getconn(self):
        return self.free.pop(0)

    def putconn(self, conn, close=False):
        if close:
            self.closed.append(conn)
        else:
            self.free.append(conn)


def _make_idle(conn, monkeypatch):
    """As if the connection was last used a long time ago."""
    monkeypatch.setitem(pooling._last_used, id(conn), pooling.time.monotonic() - 3600)


def test_a_connection_that_died_while_idle_is_replaced(monkeypatch):
    dead, alive = Conn(dead=True), Conn()
    pool = Pool(dead, alive)
    _make_idle(dead, monkeypatch)

    conn = pooling.checkout(pool)

    assert conn is alive
    assert pool.closed == [dead]


def test_an_idle_connection_that_is_still_alive_is_reused(monkeypatch):
    conn = Conn()
    pool = Pool(conn)
    _make_idle(conn, monkeypatch)

    assert pooling.checkout(pool) is conn
    assert conn.statements == ["SELECT 1"]
    assert pool.closed == []


def test_a_recently_used_or_new_connection_is_not_tested():
    new, recent = Conn(), Conn()
    pool = Pool(recent)
    pooling.release(pool, pooling.checkout(pool))

    assert pooling.checkout(pool) is recent
    assert pooling.checkout(Pool(new)) is new
    assert recent.statements == [] and new.statements == []


def test_a_dead_connection_is_discarded_on_release_and_rollback_does_not_raise():
    conn = Conn()
    conn.closed = 1
    pool = Pool()

    pooling.rollback_quietly(conn)
    pooling.release(pool, conn)

    assert pool.closed == [conn] and pool.free == []
