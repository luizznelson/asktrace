"""Small durable state store. No questions, IP addresses or credentials are persisted."""

import time
from contextlib import contextmanager

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from asktrace.connections import connect


@contextmanager
def locked_state(root, key):
    with connect(root, "state", row_factory=dict_row) as db:
        db.execute("SET LOCAL statement_timeout = '5s'")
        db.execute("SET LOCAL lock_timeout = '2s'")
        db.execute(
            "INSERT INTO asktrace.runtime_state (name, value) VALUES (%s, '{}'::jsonb) "
            "ON CONFLICT (name) DO NOTHING",
            (key,),
        )
        state = db.execute(
            "SELECT value FROM asktrace.runtime_state WHERE name=%s FOR UPDATE", (key,)
        ).fetchone()["value"]
        yield state
        db.execute("UPDATE asktrace.runtime_state SET value=%s WHERE name=%s", (Jsonb(state), key))


def read_health(root):
    with connect(root, "state", row_factory=dict_row) as db:
        row = db.execute(
            "SELECT value FROM asktrace.runtime_state WHERE name='provider-health'"
        ).fetchone()
        return row["value"] if row else {}


def write_health(root, state):
    # Merge cooldowns monotonically: one worker cannot erase a later observed wait.
    with locked_state(root, "provider-health") as previous:
        for key, record in state.items():
            if record["not_before"] >= previous.get(key, {}).get("not_before", 0):
                previous[key] = record


def reserve(root, ai, daily_ai_limit, now=None):
    """Global request budget shared across instances/restarts, not per browser token."""
    current = time.time() if now is None else now
    day, minute = int(current // 86400), int(current // 60)
    with locked_state(root, "public-budget") as state:
        if state.get("day") != day:
            state.update(day=day, daily=0, ai=0)
        if state.get("minute") != minute:
            state.update(minute=minute, minute_count=0)
        if state["minute_count"] >= 30 or state["daily"] >= 2000:
            return False
        if ai and state["ai"] >= daily_ai_limit:
            return False
        state["minute_count"] += 1
        state["daily"] += 1
        state["ai"] += int(ai)
        return True
