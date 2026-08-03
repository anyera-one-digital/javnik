#!/bin/sh
set -e

# Named media volume may be created as root; app runs as appuser.
mkdir -p \
  /app/media/avatars \
  /app/media/customers \
  /app/media/services/covers \
  /app/media/services/portfolio \
  /app/media/landing \
  /app/staticfiles

if [ "$(id -u)" = "0" ]; then
  chown -R appuser:appuser /app/media /app/staticfiles || true
  exec gosu appuser "$@"
fi

exec "$@"
