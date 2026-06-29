#!/usr/bin/env bash
set -euo pipefail

: "${DASH_USERNAME:?DASH_USERNAME is required}"
: "${DASH_PASSWORD:?DASH_PASSWORD is required}"
DASH_PORT="${DASH_PORT:-9000}"

# Configure auth at runtime — never baked into a layer.
cronitor configure \
    --dash-username "${DASH_USERNAME}" \
    --dash-password "${DASH_PASSWORD}" \
    >/dev/null

# Align crontab paths: dcron on Alpine uses /etc/crontabs/{user},
# but CronitorCLI may expect the Debian-style /var/spool/cron/crontabs path.
# Both paths point to the same directory, so crond and cronitor agree.
mkdir -p /etc/crontabs
mkdir -p /var/spool/cron
ln -sfn /etc/crontabs /var/spool/cron/crontabs

# Start cron daemon in background.
# dcron flags: -b = background, -l 2 = log warnings+errors only.
crond -b -l 2

# Dashboard in foreground as PID 1.
exec cronitor dash --port "${DASH_PORT}"
