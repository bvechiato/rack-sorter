DB = "search_eval.db"

UPLOADS_PATH = "service/static/uploads"

CREATE_TABLES_QUERY = """
CREATE TABLE IF NOT EXISTS user_uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    image_path TEXT,
    embedding BLOB,
    model_version TEXT DEFAULT 'v1.0'
);

CREATE TABLE IF NOT EXISTS queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    search_keyword TEXT,
    query_params TEXT,
    FOREIGN KEY (upload_id) REFERENCES user_uploads(id)
);

CREATE TABLE IF NOT EXISTS search_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_id INTEGER,
    title TEXT,
    url TEXT,
    image_url TEXT,
    blob_data TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    model_version TEXT DEFAULT 'v1.0',
    embedding BLOB,
    FOREIGN KEY (query_id) REFERENCES queries(id)
);

CREATE TABLE IF NOT EXISTS clip_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id INTEGER,
    tag_name TEXT,
    score REAL,
    category_type TEXT,
    model_version TEXT DEFAULT 'v1.0',
    FOREIGN KEY (upload_id) REFERENCES user_uploads(id)
);

CREATE TABLE IF NOT EXISTS rerank_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id INTEGER,
    item_url TEXT,
    feedback_type TEXT CHECK(feedback_type IN ('MORE', 'LESS')),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (upload_id) REFERENCES user_uploads(id)
);
"""