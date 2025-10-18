"""Typer CLI for Project Empathy."""

from __future__ import annotations

from pathlib import Path

import typer

from .analyze import analyze_articles
from .clean import clean_articles
from .config import AppConfig, load_config, write_default_config
from .db import init_db
from .export import export_outputs
from .logging_utils import get_logger
from .scrape import crawl as crawl_pipeline
from .translate import translate_articles
from .utils import ensure_directory

app = typer.Typer(help="Project Empathy data pipeline")
LOGGER = get_logger("cli")


def _load_config(path: Path) -> AppConfig:
    if not path.exists():
        raise typer.BadParameter(f"Config file not found: {path}")
    return load_config(path)


@app.command()
def init(config_path: Path = typer.Option(Path("config.yaml"), help="Configuration file path")) -> None:
    """Initialize configuration and environment templates."""

    if config_path.exists():
        typer.echo(f"Config file already exists at {config_path}")
    else:
        write_default_config(config_path)
        typer.echo(f"Created config at {config_path}")
    env_path = Path(".env")
    if env_path.exists():
        typer.echo(".env already exists")
    else:
        example_env = Path(".env.example")
        env_path.write_text(example_env.read_text(encoding="utf-8"), encoding="utf-8")
        typer.echo("Created .env from example")
    ensure_directory(Path("data"))
    ensure_directory(Path("outputs"))


@app.command()
def crawl(config: Path = typer.Option(Path("config.yaml"), help="Config path")) -> None:
    """Fetch articles from configured sources."""

    app_config = _load_config(config)
    crawl_pipeline(app_config)


@app.command()
def clean(config: Path = typer.Option(Path("config.yaml"), help="Config path")) -> None:
    """Clean raw articles."""

    app_config = _load_config(config)
    clean_articles(app_config)


@app.command()
def translate(config: Path = typer.Option(Path("config.yaml"), help="Config path")) -> None:
    """Translate articles to English."""

    app_config = _load_config(config)
    translate_articles(app_config)


@app.command()
def analyze(config: Path = typer.Option(Path("config.yaml"), help="Config path")) -> None:
    """Run analysis pipeline."""

    app_config = _load_config(config)
    analyze_articles(app_config)


@app.command()
def export(config: Path = typer.Option(Path("config.yaml"), help="Config path")) -> None:
    """Export results to CSV and HTML report."""

    app_config = _load_config(config)
    export_outputs(app_config)


@app.command(name="all")
def run_all(config: Path = typer.Option(Path("config.yaml"), help="Config path")) -> None:
    """Run entire pipeline sequentially."""

    app_config = _load_config(config)
    init_db(app_config.storage.database_path)
    crawl_pipeline(app_config)
    clean_articles(app_config)
    translate_articles(app_config)
    analyze_articles(app_config)
    export_outputs(app_config)


if __name__ == "__main__":  # pragma: no cover
    app()
