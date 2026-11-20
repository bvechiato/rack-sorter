"""baseline schema

Revision ID: 0001
Revises:
Create Date: 2026-11-20

The five tables that previously came from model.repository.constants.CREATE_TABLES_QUERY.
Alembic is now the only owner of the SQLite schema.
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE user_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            image_path TEXT,
            embedding BLOB,
            model_version TEXT DEFAULT 'v1.0'
        )
    """)
    op.execute("""
        CREATE TABLE queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            search_keyword TEXT,
            query_params TEXT,
            FOREIGN KEY (upload_id) REFERENCES user_uploads(id)
        )
    """)
    op.execute("""
        CREATE TABLE search_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_id INTEGER,
            title TEXT,
            url TEXT,
            image_url TEXT,
            blob_data TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            model_version TEXT DEFAULT 'v1.0',
            embedding BLOB,
            clip_embedding BLOB,
            FOREIGN KEY (query_id) REFERENCES queries(id)
        )
    """)
    op.execute("""
        CREATE TABLE clip_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_id INTEGER,
            tag_name TEXT,
            score REAL,
            category_type TEXT,
            model_version TEXT DEFAULT 'v1.0',
            FOREIGN KEY (upload_id) REFERENCES user_uploads(id)
        )
    """)
    op.execute("""
        CREATE TABLE rerank_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_id INTEGER,
            item_url TEXT,
            feedback_type TEXT CHECK(feedback_type IN ('MORE', 'LESS')),
            concept TEXT,
            aesthetic TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (upload_id) REFERENCES user_uploads(id)
        )
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS rerank_feedback")
    op.execute("DROP TABLE IF EXISTS clip_tags")
    op.execute("DROP TABLE IF EXISTS search_items")
    op.execute("DROP TABLE IF EXISTS queries")
    op.execute("DROP TABLE IF EXISTS user_uploads")
