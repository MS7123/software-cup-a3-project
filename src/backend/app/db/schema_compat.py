from sqlalchemy import inspect, text

from app.db.session import get_engine


DOCUMENT_COLUMN_DEFINITIONS = {
    "visibility": "VARCHAR(40) NOT NULL DEFAULT 'course'",
    "owner_user_id": "INTEGER",
    "file_name": "VARCHAR(240)",
    "mime_type": "VARCHAR(160)",
    "file_size": "INTEGER",
    "parser_name": "VARCHAR(80)",
}


def ensure_document_columns(database_url: str | None = None) -> None:
    engine = get_engine(database_url)
    inspector = inspect(engine)
    if "documents" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("documents")}
    missing = [
        (name, definition)
        for name, definition in DOCUMENT_COLUMN_DEFINITIONS.items()
        if name not in existing
    ]
    if not missing:
        return
    with engine.begin() as connection:
        for name, definition in missing:
            connection.execute(text(f"ALTER TABLE documents ADD COLUMN {name} {definition}"))
