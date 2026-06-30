# OpenSearch

Full-text search and analytics engine for homelab use. Two services: OpenSearch (BM25 search API) + OpenSearch Dashboards (visual query console).

## Upstream

Project: [opensearch-project/OpenSearch](https://github.com/opensearch-project/OpenSearch) — `opensearchproject/opensearch:latest`  
Dashboards: [opensearch-project/OpenSearch-Dashboards](https://github.com/opensearch-project/OpenSearch-Dashboards) — `opensearchproject/opensearch-dashboards:latest`

Apache 2.0. Fork of Elasticsearch 7.10.2 (April 2021), maintained by the OpenSearch Software Foundation under the Linux Foundation since September 2024.

## Features

- **Full-text search** — BM25 relevance ranking, query DSL compatible with pre-2021 Elasticsearch
- **Aggregations & facets** — filter, group, and count documents
- **REST API** — HTTP on port 9200
- **Dashboards** — visual index explorer and Dev Tools query console on port 5601
- **Single-node mode** — no cluster config required for personal use

## Required host setup (before first install)

OpenSearch will not start without this. SSH into the host and run:

```bash
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
```

## Ports

| Port | Service |
|------|---------|
| `5601` | OpenSearch Dashboards (main UI) |
| `9200` | OpenSearch REST API |

## Security

Security plugin is **disabled by default** (`DISABLE_SECURITY_PLUGIN=true`). No TLS, no auth. Sized for homelab behind Tailscale/LAN — do not expose ports 9200 or 5601 publicly.

To re-enable security: remove both `DISABLE_SECURITY_*` env vars, set `OPENSEARCH_INITIAL_ADMIN_PASSWORD` (min 8 chars, upper/lowercase/number/symbol — required since OpenSearch 2.12), switch `OPENSEARCH_HOSTS` to `https://`, update `scheme` in `x-casaos` to `https`.

## Memory

- OpenSearch heap: 1GB fixed (`-Xms1g -Xmx1g`)
- Container limit: 2GB (JVM overhead headroom)
- Dashboards container limit: 1GB
- Combined footprint at rest: ~2–3GB RAM

## Data persistence

`/DATA/AppData/opensearch/data` — index data survives container restarts and upgrades.

## Icon

Uses [selfhst/icons](https://github.com/selfhst/icons) CDN. Verify `opensearch.png` exists before publishing; replace with official project icon if unavailable.
