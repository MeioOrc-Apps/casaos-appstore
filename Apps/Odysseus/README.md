# Odysseus

Self-hosted AI workspace — versão self-hosted da experiência de UI tipo ChatGPT/Claude, rodando no seu próprio hardware, com seus próprios dados.

## Upstream

Projeto original: [pewdiepie-archdaemon/odysseus](https://github.com/pewdiepie-archdaemon/odysseus)

Este app store **não** é o projeto Odysseus — apenas empacota a imagem Docker pra instalação 1-clique no ZimaOS/CasaOS.

## Funcionalidades

- **Chat** — qualquer modelo local ou API (vLLM, llama.cpp, Ollama, OpenRouter, OpenAI)
- **Agent** — ferramentas, MCP, web, files, shell, skills, memory
- **Cookbook** — escaneia hardware, recomenda modelos, 1-click download e serve
- **Deep Research** — runs multi-step que coletam, leem e sintetizam fontes em relatório visual
- **Compare** — compara modelos lado a lado, teste cego
- **Documents** — editor multi-tab com markdown/HTML/CSV + AI edits/suggestions
- **Memory / Skills** — memória persistente via ChromaDB + fastembed
- **Email** — inbox IMAP/SMTP com AI triage (urgência, auto-tag, auto-summary, drafts)
- **Notes & Tasks** — notas com reminders, todo, tasks agendadas (ntfy/browser/email)
- **Calendar** — local-first com sync CalDAV (Radicale, Nextcloud, Apple, Fastmail)
- **PWA** — funciona em mobile

## Pipeline de build

A imagem `sergiosjs/odysseus:latest` no Docker Hub é construída automaticamente via [.github/workflows/build-odysseus.yml](../../.github/workflows/build-odysseus.yml):

- Clone shallow do branch `main` do upstream
- Build multi-arch (`linux/amd64`, `linux/arm64`) com Buildx + QEMU
- Push pra Docker Hub com tags `:latest` e `:sha-<commit>`

Triggers:
- Push pra `main` do casaos-appstore (mudanças em `Apps/Odysseus/**`)
- Manual via `workflow_dispatch`
- Schedule semanal (segunda 04:00 UTC) — pega updates do upstream

## Serviços bundled

| Serviço | Imagem | Propósito |
|---|---|---|
| `odysseus` | `sergiosjs/odysseus:latest` | API + UI principal (porta 7000) |
| `chromadb` | `chromadb/chroma:latest` | Vector store pra memory/skills |
| `searxng` | `searxng/searxng:2026.5.31-7159b8aed` | Web search self-hosted |
| `ntfy` | `binwiederhier/ntfy` | Push notifications (interno) |

## Pós-instalação

1. **Primeiro login** — admin password gerada no boot. Pegue via:
   ```bash
   docker compose logs odysseus | grep -i password
   ```
2. **LLM** — Settings → conecta Ollama do host via `http://host.docker.internal:11434/v1`
3. **Phone push** — pra usar ntfy no celular, expõe porta 8091 e configura `NTFY_BASE_URL` pra IP/domain do ZimaOS

## Volumes

Tudo persistido em `/DATA/AppData/odysseus/`:
- `data/` — SQLite, sessões, configs
- `logs/` — logs da app
- `ssh/` — SSH keys do Cookbook (remote serve)
- `huggingface/` — cache de modelos baixados
- `local/` — Python CLIs instaladas via Cookbook (vLLM, llama-cpp, etc.)
- `searxng/` — config searxng (gerada no primeiro boot)
- `chromadb/` — vector store
- `ntfy/` — cache ntfy

## Licença

Odysseus é distribuído sob a licença do projeto upstream. Consulte [LICENSE](https://github.com/pewdiepie-archdaemon/odysseus/blob/main/LICENSE).
