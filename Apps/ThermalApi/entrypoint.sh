#!/bin/sh
set -e
mkdir -p /app/logs
chown 1000:1000 /app/logs
exec gosu appuser "$@"
