"""Initialise la base de données Project Empathy."""

from project_empathy.config import get_settings
from project_empathy.db import Base, get_engine
from project_empathy import models  # noqa: F401  # Import side effects to register models


def main() -> None:
    settings = get_settings()
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print(f"Tables créées sur {settings.database.url}")


if __name__ == "__main__":
    main()
