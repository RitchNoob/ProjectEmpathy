"""Command-line helpers for running and bootstrapping Project Empathy."""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import contextmanager
from typing import Iterator, Optional

from sqlalchemy.orm import Session

from .bootstrap import create_schema, seed_demo_data
from .config import ApplicationSettings, get_settings
from .db import SessionLocal
from .models import Restaurant
from .services.statistics import compute_dashboard_stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="empathy", description="Utilitaires Project Empathy")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-db", help="Crée les tables et options de démo")
    init_parser.add_argument("--seed-demo", action="store_true", help="Charge un restaurant de démonstration")
    init_parser.add_argument(
        "--force", action="store_true", help="Écrase les données existantes avant l'insertion de la démo"
    )

    seed_parser = subparsers.add_parser("seed-demo", help="Ajoute les données de démonstration")
    seed_parser.add_argument("--force", action="store_true", help="Réinitialise les données existantes")

    config_parser = subparsers.add_parser("config", help="Affiche la configuration active")
    config_parser.add_argument("--json", action="store_true", help="Retourne la configuration au format JSON")

    stats_parser = subparsers.add_parser("stats", help="Affiche les métriques d'un restaurant")
    stats_parser.add_argument("restaurant_id", type=int, nargs="?", help="Identifiant du restaurant (défaut: premier)")

    server_parser = subparsers.add_parser("runserver", help="Lance l'API FastAPI via Uvicorn")
    server_parser.add_argument("--host", default="0.0.0.0")
    server_parser.add_argument("--port", type=int, default=8000)
    server_parser.add_argument("--reload", action="store_true", help="Active le rechargement auto (développement)")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init-db":
        create_schema()
        print("✅ Tables SQL créées")
        if args.seed_demo:
            _seed_demo(force=args.force)
        return 0

    if args.command == "seed-demo":
        _seed_demo(force=args.force)
        return 0

    if args.command == "config":
        settings = get_settings()
        if args.json:
            print(_settings_to_json(settings))
        else:
            print(_settings_to_pretty_string(settings))
        return 0

    if args.command == "stats":
        return _print_stats(args.restaurant_id)

    if args.command == "runserver":
        return _run_server(args.host, args.port, args.reload)

    parser.print_help()
    return 1


def _seed_demo(*, force: bool) -> None:
    created = seed_demo_data(skip_existing=not force)
    if created:
        print("✅ Données de démonstration prêtes")
    else:
        print("ℹ️  Données déjà présentes (utilisez --force pour les régénérer)")


def _settings_to_json(settings: ApplicationSettings) -> str:
    return settings.model_dump_json(indent=2)


def _settings_to_pretty_string(settings: ApplicationSettings) -> str:
    return settings.model_dump_json(indent=2, ensure_ascii=False)


@contextmanager
def _session_scope() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _print_stats(restaurant_id: Optional[int]) -> int:
    with _session_scope() as session:
        target_id = restaurant_id
        if target_id is None:
            restaurant = session.query(Restaurant).order_by(Restaurant.id.asc()).first()
            if restaurant is None:
                print("Aucun restaurant trouvé. Lancez 'seed-demo' d'abord.")
                return 1
            target_id = restaurant.id
        stats = compute_dashboard_stats(session, target_id)
        print(json.dumps(stats.model_dump(), indent=2, ensure_ascii=False))
    return 0


def _run_server(host: str, port: int, reload: bool) -> int:
    try:
        import uvicorn
    except ImportError:  # pragma: no cover - only triggered when uvicorn absent
        print("Uvicorn est requis pour lancer le serveur: pip install -r requirements.txt", file=sys.stderr)
        return 1

    from .main import app
    create_schema()

    uvicorn.run(app, host=host, port=port, reload=reload)
    return 0


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
