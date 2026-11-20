"""Alembic environment.

There are no SQLAlchemy models: target_metadata is always None and revisions contain
raw SQL via op.execute(). SQLAlchemy Core is used only here as Alembic's runtime.
"""

import sys
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make the server root importable regardless of the caller's working directory.
SERVER_DIR = Path(__file__).resolve().parents[1]
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from config import DB_PATH  # noqa: E402

config = context.config


def _url() -> str:
    """Three slashes = relative path, four = absolute (SQLite URL rules)."""
    return f"sqlite:///{DB_PATH}"


def run_migrations_offline() -> None:
    """Emit SQL without connecting (used by `alembic upgrade head --sql`)."""
    context.configure(
        url=_url(),
        target_metadata=None,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    config.set_main_option("sqlalchemy.url", _url())
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
