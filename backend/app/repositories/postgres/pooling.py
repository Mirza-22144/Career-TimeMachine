"""Shared care for pooled database connections.

The database is remote, and a connection left idle for a few minutes can be
dropped by the server or by something in between without either end being
told. The pool would then hand out a dead connection and every request
would fail ("server closed the connection unexpectedly") until the app was
restarted. Two things prevent that:

- KEEPALIVE asks the operating system to keep idle connections alive and to
  notice dead ones.
- checkout() tests a connection that has sat idle before handing it out,
  and quietly replaces it if it is dead. The test costs one round trip, so
  it is only made after an idle spell, never on a busy connection.
"""

import threading
import time

import psycopg2

# Passed to every ThreadedConnectionPool (libpq connection parameters).
KEEPALIVE = {"keepalives": 1, "keepalives_idle": 30, "keepalives_interval": 10, "keepalives_count": 3}

# A connection used more recently than this is trusted without a test.
IDLE_SECONDS_BEFORE_TEST = 20.0
# Enough attempts to work through a pool whose every connection has died.
_MAX_ATTEMPTS = 12

_last_used: dict[int, float] = {}
_lock = threading.Lock()


def checkout(pool):
    """Return a live connection from the pool."""
    conn = pool.getconn()
    for _ in range(_MAX_ATTEMPTS):
        with _lock:
            last_used = _last_used.get(id(conn))
        # Never seen before means the pool has just opened it.
        if last_used is None or time.monotonic() - last_used < IDLE_SECONDS_BEFORE_TEST:
            return conn
        try:
            # Autocommit so the test leaves no transaction open behind it.
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
            return conn
        except psycopg2.Error:
            with _lock:
                _last_used.pop(id(conn), None)
            pool.putconn(conn, close=True)
            conn = pool.getconn()
    return conn


def release(pool, conn) -> None:
    """Give a connection back, discarding it if it has died."""
    if getattr(conn, "closed", 0):
        with _lock:
            _last_used.pop(id(conn), None)
        pool.putconn(conn, close=True)
        return
    with _lock:
        _last_used[id(conn)] = time.monotonic()
    pool.putconn(conn)


def rollback_quietly(conn) -> None:
    """Roll back after a failed statement so the pool doesn't hand the
    connection out mid-transaction. A connection that has died cannot be
    rolled back; that must not hide the error that is already being raised."""
    try:
        conn.rollback()
    except psycopg2.Error:
        pass
