from sqlalchemy import Engine, inspect, text


def ensure_session_behavioral_columns(engine: Engine) -> None:
    """Add nullable inference columns to an existing local SQLite database."""
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    if "sessions" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("sessions")}
    additions = {
        "behavioural_model_status": "VARCHAR(64)",
        "fusion_log10_estimated_guesses": "FLOAT",
    }
    with engine.begin() as connection:
        for column_name, column_type in additions.items():
            if column_name not in existing:
                connection.execute(
                    text(f"ALTER TABLE sessions ADD COLUMN {column_name} {column_type}")
                )
