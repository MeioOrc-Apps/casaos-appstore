# Cronmaster

Visual cron job manager with Docker container control. Web UI for scheduling any shell task, editing crontabs in real time, and triggering docker start/stop via socket.

## Upstream

Project: [fccview/cronmaster](https://github.com/fccview/cronmaster) — `ghcr.io/fccview/cronmaster:latest`

This app store only packages the Docker image for 1-click install on ZimaOS/CasaOS.

## Features

- **Cron editor** — human-readable syntax, live validation
- **Log streaming** — real-time output per job
- **Script editor** — create and manage Bash scripts via UI
- **Docker control** — docker start/stop as cron jobs via socket
- **Auth** — password-protected dashboard (`AUTH_PASSWORD`)

## Security notice

Cronmaster requires `privileged: true` and `pid: host` to edit the host crontab in real time. This is a design constraint of the tool, not configurable.

- Do not expose port 3013 directly to the internet
- Deploy only on trusted networks (LAN / Tailscale)
- Change `AUTH_PASSWORD` before first use

## Default port

`3013` → `http://HOST:3013`

## Icon

Upstream icon not yet available on selfhst/icons CDN. Field left blank pending upstream addition.
