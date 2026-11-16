"""Small helpers for the SQLite access pattern used by every repository.

Centralising the connection here keeps the ``PRAGMA``/``row_factory`` setup in one
place and avoids leaked connections when a repository forgets to ``close()``.
"""

import sqlite3
from contextlib import contextmanager

from . import constants


@contextmanager
def db_connection():
    """Yield a connection with named-column rows; commit on clean exit, rollback on error."""
    conn = sqlite3.connect(constants.DB)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
