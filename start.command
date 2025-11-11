#!/bin/bash
set -euo pipefail

cleanup() {
  status=$?
  trap - EXIT
  if [ $status -ne 0 ]; then
    echo ""
    echo "❌ Le script s'est terminé avec le code $status."
  fi
  echo ""
  read -n 1 -s -r -p "Appuyez sur une touche pour fermer cette fenêtre."
  exit $status
}

trap cleanup EXIT

# Permet de lancer Project Empathy en un double-clic sur macOS
# - installe (ou réutilise) un environnement virtuel Python 3
# - installe les dépendances nécessaires
# - démarre le serveur clé en main via start.py

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "❌ Python 3 est requis pour exécuter Project Empathy." >&2
  echo "Installez-le depuis https://www.python.org/downloads/ puis relancez ce script." >&2
  trap - EXIT
  echo ""
  read -n 1 -s -r -p "Appuyez sur une touche pour fermer cette fenêtre."
  exit 1
fi

VENV_DIR="$SCRIPT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
  echo "🐍 Création d'un environnement virtuel Python (.venv)..."
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

PYTHON_IN_VENV="$(command -v python)"

echo "📦 Installation des dépendances (requirements.txt)..."
"$PYTHON_IN_VENV" -m pip install --upgrade pip >/dev/null
"$PYTHON_IN_VENV" -m pip install -r requirements.txt

echo "🚀 Lancement de Project Empathy (appuyez sur Ctrl+C pour arrêter)..."
"$PYTHON_IN_VENV" start.py
