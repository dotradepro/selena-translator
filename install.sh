#!/usr/bin/env bash
# selena-translator installer — clones, builds, runs, adds desktop icon
set -euo pipefail

REPO="${SELENA_TRANSLATOR_REPO:-https://github.com/dotradepro/selena-translator.git}"
DEST="${SELENA_TRANSLATOR_DEST:-${HOME}/selena-translator}"
PORT="${SELENA_TRANSLATOR_PORT:-8002}"

log() { printf '\033[1;34m[install]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[install]\033[0m %s\n' "$*" >&2; exit 1; }

command -v git >/dev/null || die "git is required"
command -v docker >/dev/null || die "docker is required"

if [ ! -d "$DEST/.git" ]; then
  log "Cloning $REPO → $DEST"
  git clone "$REPO" "$DEST"
else
  log "Updating existing checkout at $DEST"
  git -C "$DEST" pull --ff-only
fi

cd "$DEST"

DOCKER="docker"
if ! docker info >/dev/null 2>&1; then
  log "docker requires sudo on this host"
  DOCKER="sudo docker"
fi

log "Building and starting container on port $PORT"
$DOCKER compose up -d --build

log "Waiting for service to be ready"
for _ in $(seq 1 30); do
  if curl -fsS "http://localhost:${PORT}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

DESKTOP_SRC="$DEST/scripts/selena-translator.desktop"
DESKTOP_APPS="${HOME}/.local/share/applications/selena-translator.desktop"
DESKTOP_LINK="${HOME}/Desktop/selena-translator.desktop"

mkdir -p "${HOME}/.local/share/applications"
install -m 0755 "$DESKTOP_SRC" "$DESKTOP_APPS"
log "Installed application entry: $DESKTOP_APPS"

if [ -d "${HOME}/Desktop" ]; then
  install -m 0755 "$DESKTOP_SRC" "$DESKTOP_LINK"
  log "Installed desktop shortcut: $DESKTOP_LINK"
fi

log "Ready → http://localhost:${PORT}"
