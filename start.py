"""Point d'entrée simplifié pour lancer Project Empathy en mode clé en main."""

from __future__ import annotations

import sys

from project_empathy.cli import main


if __name__ == "__main__":
    arguments = ["launch", *sys.argv[1:]]
    raise SystemExit(main(arguments))
