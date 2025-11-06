"""Initialise la base de données Project Empathy et charge les données de démonstration."""

from __future__ import annotations

import argparse

from project_empathy.bootstrap import create_schema, seed_demo_data
from project_empathy.config import get_settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialiser la base Project Empathy")
    parser.add_argument(
        "--seed-demo",
        action="store_true",
        help="Insère un restaurant, un menu et des commandes de démonstration.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Réinitialise les données existantes avant l'insertion de la démo.",
    )
    args = parser.parse_args()

    settings = get_settings()
    create_schema()
    print(f"Tables créées sur {settings.database.url}")

    if args.seed_demo:
        created = seed_demo_data(skip_existing=not args.force)
        if created:
            print("Données de démonstration insérées ✔")
        else:
            print("Données déjà présentes – utilisez --force pour les recréer.")


if __name__ == "__main__":
    main()
