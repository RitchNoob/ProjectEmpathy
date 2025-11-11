"""Command-line helpers for running and bootstrapping Project Empathy."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional, Sequence

from sqlalchemy.orm import Session

from .bootstrap import SeedResult, create_schema, seed_demo_data
from .config import ApplicationSettings, get_settings
from .db import SessionLocal
from .models import Restaurant
from .services.auth import issue_api_token
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

    launch_parser = subparsers.add_parser(
        "launch",
        help="Démarre automatiquement l'API, le front-end et charge la démo (clé en main)",
    )
    launch_parser.add_argument("--host", default="127.0.0.1", help="Hôte pour l'API FastAPI")
    launch_parser.add_argument("--port", type=int, default=8000, help="Port pour l'API FastAPI")
    launch_parser.add_argument(
        "--frontend-host",
        default="127.0.0.1",
        help="Hôte pour le serveur web du tableau de bord",
    )
    launch_parser.add_argument(
        "--frontend-port",
        type=int,
        default=5173,
        help="Port du tableau de bord",
    )
    launch_parser.add_argument(
        "--reseed",
        action="store_true",
        help="Réinitialise les données de démonstration avant le lancement",
    )
    launch_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="N'ouvre pas automatiquement le navigateur",
    )

    token_parser = subparsers.add_parser("create-token", help="Génère une clé API pour un restaurant")
    token_parser.add_argument("restaurant_id", type=int, help="Identifiant du restaurant")
    token_parser.add_argument("--name", default="Clé API", help="Nom lisible de la clé")

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

    if args.command == "launch":
        return _launch_stack(
            host=args.host,
            port=args.port,
            frontend_host=args.frontend_host,
            frontend_port=args.frontend_port,
            reseed=args.reseed,
            open_browser=not args.no_browser,
        )

    if args.command == "create-token":
        return _create_token(args.restaurant_id, args.name)

    parser.print_help()
    return 1


def _seed_demo(*, force: bool) -> None:
    result = seed_demo_data(skip_existing=not force)
    if result.created:
        print("✅ Données de démonstration prêtes")
        if result.api_key:
            print(f"🔑 Clé API de démonstration: {result.api_key}")
            print("➡️  Elle est également sauvegardée dans data/demo_api_key.txt")
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


def _create_token(restaurant_id: int, name: str) -> int:
    with _session_scope() as session:
        restaurant = session.get(Restaurant, restaurant_id)
        if restaurant is None:
            print("Restaurant introuvable", file=sys.stderr)
            return 1
        _, api_key = issue_api_token(session, restaurant, name)
        print(f"🔑 Nouvelle clé API pour {restaurant.name}: {api_key}")
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


@dataclass
class ManagedProcess:
    name: str
    command: Sequence[str]
    cwd: Path
    process: subprocess.Popen | None = None


def _launch_stack(
    *,
    host: str,
    port: int,
    frontend_host: str,
    frontend_port: int,
    reseed: bool,
    open_browser: bool,
) -> int:
    try:
        import uvicorn  # noqa: F401  # pragma: no cover - import guard for runtime env
    except ImportError:
        print(
            "Uvicorn est requis pour lancer le serveur tout-en-un. Exécutez 'pip install -r requirements.txt'.",
            file=sys.stderr,
        )
        return 1

    print("🚀 Préparation de l'environnement Project Empathy...")
    create_schema()
    seed_result = seed_demo_data(skip_existing=not reseed)
    api_key = _obtain_demo_api_key(seed_result)
    if seed_result.created:
        print("✅ Données de démonstration chargées")
    else:
        print("ℹ️ Données existantes détectées. Utilisez --reseed pour les régénérer.")

    if api_key:
        print(f"🔑 Clé API de démonstration: {api_key}")
    else:
        print("⚠️ Impossible de déterminer la clé API de démonstration. Générez-en une via 'create-token'.")

    project_root = _project_root()
    frontend_dir = project_root / "dashboard"
    _write_frontend_config(frontend_dir, api_url=f"http://{host}:{port}", api_key=api_key, restaurant_id=seed_result.restaurant_id)
    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "project_empathy.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    frontend_cmd = [
        sys.executable,
        "-m",
        "http.server",
        str(frontend_port),
        "--bind",
        frontend_host,
    ]

    processes = [
        ManagedProcess(name="API", command=backend_cmd, cwd=project_root),
        ManagedProcess(name="Dashboard", command=frontend_cmd, cwd=frontend_dir),
    ]

    _start_processes(processes)
    _install_signal_handlers(processes)

    url = f"http://{frontend_host}:{frontend_port}" if frontend_host not in ("0.0.0.0", "::") else f"http://127.0.0.1:{frontend_port}"

    if open_browser:
        threading.Thread(target=_open_browser_after_delay, args=(url,), daemon=True).start()

    print("")
    print("🌐 Tableau de bord:", url)
    print(f"📞 API FastAPI: http://{host}:{port}")
    print("Appuyez sur Ctrl+C pour arrêter l'application.")

    try:
        while True:
            for managed in processes:
                proc = managed.process
                if proc is None:
                    continue
                code = proc.poll()
                if code is not None:
                    print(f"❌ Le service {managed.name} s'est arrêté (code {code}).", file=sys.stderr)
                    _terminate_processes(processes)
                    return code or 1
            time.sleep(0.5)
    except KeyboardInterrupt:  # pragma: no cover - runtime behaviour
        print("\nArrêt demandé, fermeture des services...")
        _terminate_processes(processes)
        return 0


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _write_frontend_config(frontend_dir: Path, *, api_url: str, api_key: Optional[str], restaurant_id: Optional[int]) -> None:
    frontend_dir.mkdir(parents=True, exist_ok=True)
    config = {
        "apiBaseUrl": api_url,
    }
    if restaurant_id is not None:
        config["restaurantId"] = restaurant_id
    if api_key:
        config["apiKey"] = api_key
    config_path = frontend_dir / "runtime-config.json"
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def _start_processes(processes: Sequence[ManagedProcess]) -> None:
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(_project_root() / "src"))
    for managed in processes:
        managed.process = subprocess.Popen(
            managed.command,
            cwd=str(managed.cwd),
            env=env,
            text=True,
            start_new_session=True,
        )
        print(f"▶️  {managed.name} lancé ({' '.join(map(str, managed.command))})")


def _install_signal_handlers(processes: Sequence[ManagedProcess]) -> None:
    def _handler(signum, _frame):  # pragma: no cover - signal handling during runtime
        print(f"\nSignal {signum} reçu, arrêt en cours...")
        _terminate_processes(processes)
        sys.exit(0)

    for sig_name in ("SIGINT", "SIGTERM"):
        if hasattr(signal, sig_name):
            signal.signal(getattr(signal, sig_name), _handler)


def _terminate_processes(processes: Sequence[ManagedProcess]) -> None:
    deadline = time.time() + 10
    for managed in processes:
        proc = managed.process
        if proc is not None and proc.poll() is None:
            proc.terminate()

    while time.time() < deadline:
        if all(managed.process is None or managed.process.poll() is not None for managed in processes):
            break
        time.sleep(0.2)

    for managed in processes:
        proc = managed.process
        if proc is not None and proc.poll() is None:
            proc.kill()


def _open_browser_after_delay(url: str, delay: float = 3.0) -> None:
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception:  # pragma: no cover - safety net for exotic environments
        pass


def _obtain_demo_api_key(seed_result: SeedResult) -> Optional[str]:
    if seed_result.api_key:
        _persist_demo_api_key(seed_result.api_key)
        return seed_result.api_key

    key = _load_demo_api_key()
    if key:
        return key

    if seed_result.restaurant_id is None:
        return None

    with _session_scope() as session:
        restaurant = session.get(Restaurant, seed_result.restaurant_id)
        if restaurant is None:
            return None
        _, api_key = issue_api_token(session, restaurant, "Tableau de bord (auto)")
        if api_key:
            _persist_demo_api_key(api_key)
        return api_key


def _load_demo_api_key() -> Optional[str]:
    settings = get_settings()
    target = settings.storage.data_dir / "demo_api_key.txt"
    if not target.exists():
        return None
    content = target.read_text(encoding="utf-8").strip()
    return content or None


def _persist_demo_api_key(api_key: str) -> None:
    settings = get_settings()
    target = settings.storage.data_dir / "demo_api_key.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(api_key, encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
