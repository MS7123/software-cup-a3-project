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

AGENT_RUN_STEP_COLUMN_DEFINITIONS = {
    "execution_metadata": "JSON NOT NULL DEFAULT '{}'",
}


def ensure_document_columns(database_url: str | None = None) -> None:
    _ensure_columns("documents", DOCUMENT_COLUMN_DEFINITIONS, database_url)


def ensure_agent_run_step_columns(database_url: str | None = None) -> None:
    _ensure_columns("agent_run_steps", AGENT_RUN_STEP_COLUMN_DEFINITIONS, database_url)


def _ensure_columns(table_name: str, definitions: dict[str, str], database_url: str | None = None) -> None:
    engine = get_engine(database_url)
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns(table_name)}
    missing = [
        (name, definition)
        for name, definition in definitions.items()
        if name not in existing
    ]
    if not missing:
        return
    with engine.begin() as connection:
        for name, definition in missing:
            connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {name} {definition}"))
