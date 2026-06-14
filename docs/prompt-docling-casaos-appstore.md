# Prompt: Adicionar Docling Serve ao casaos-appstore

## Contexto do projeto

Você está trabalhando no repositório `casaos-appstore`, um catálogo de apps para ZimaOS/CasaOS. Cada app vive em `Apps/<nome>/docker-compose.yml` com uma seção `x-casaos` que descreve os metadados exibidos na UI do ZimaOS. O formato de referência é o do `bigbeartechworld/big-bear-casaos`.

Na raiz do VS Code estão abertas:
- `casaos-appstore/` — o projeto a modificar
- `LightRAG/` — referência (já tem um app `lightrag` criado neste mesmo appstore)

## Objetivo

Adicionar o **Docling Serve** como app instalável pelo catálogo. O Docling Serve converte documentos (PDF, DOCX, PPTX, etc.) em Markdown via API HTTP. Ele será usado em conjunto com o LightRAG já presente no appstore: uma futura aplicação de orquestração enviará PDFs ao Docling e o Markdown resultante ao LightRAG.

**IMPORTANTE — não criar imagem Docker.** A imagem oficial `ghcr.io/docling-project/docling-serve-cpu:latest` já existe, é mantida pelo projeto e deve ser usada diretamente. NÃO crie Dockerfile nem GitHub Action de build. A tarefa é apenas empacotar a imagem oficial no formato do catálogo.

---

## Tarefa 1 — Analisar o padrão existente

Antes de criar qualquer arquivo:

1. **Leia `casaos-appstore/Apps/lightrag/docker-compose.yml`** — é o app mais recente e segue o padrão exato do repositório. Use-o como template estrutural (nome, formato de volumes com `$AppID` ou path absoluto, formato da seção `x-casaos`, campos usados como `author`, `category`, `tips`, `index`, `store_app_id`).

2. **Confirme o padrão de path de volumes** usado no repositório: é `/DATA/AppData/$AppID/...` ou `/DATA/storage1/AppData/...`? Copie o que o lightrag usa, para manter consistência.

3. **Confirme a categoria** usada em apps similares (Productivity, Utilities, etc.).

---

## Tarefa 2 — Criar `Apps/docling-serve/docker-compose.yml`

Crie o arquivo seguindo o padrão do lightrag. Requisitos funcionais:

### Serviço

- **Imagem:** `ghcr.io/docling-project/docling-serve-cpu:latest` (variante CPU — o ZimaOS alvo não tem GPU exposta ao container)
- **Porta:** `5001:5001`
- **Restart:** `unless-stopped`
- **Container name:** `docling-serve`

### Variáveis de ambiente (com valores padrão funcionais)

```
DOCLING_SERVE_ENABLE_UI=1
DOCLING_SERVE_LOAD_MODELS_AT_BOOT=false
UVICORN_WORKERS=1
DOCLING_NUM_THREADS=4
DOCLING_SERVE_MAX_NUM_PAGES=1000
DOCLING_SERVE_MAX_FILE_SIZE=209715200
```

Justificativa de cada uma (inclua como comentário no compose):
- `DOCLING_SERVE_ENABLE_UI=1` — habilita UI de teste em `/ui` e doc em `/docs`
- `DOCLING_SERVE_LOAD_MODELS_AT_BOOT=false` — não carrega modelos no boot; carrega sob demanda no primeiro request. Mantém o container leve em idle (crítico em hardware com RAM limitada)
- `UVICORN_WORKERS=1` — 1 worker basta para uso de baixa frequência e economiza RAM
- `DOCLING_NUM_THREADS=4` — threads de CPU para parsing
- `DOCLING_SERVE_MAX_NUM_PAGES=1000` — limite de páginas por documento (cobre PDFs grandes de ~300 págs)
- `DOCLING_SERVE_MAX_FILE_SIZE=209715200` — 200 MB por arquivo

### Volumes

```
# cache dos modelos baixados — DEVE persistir, senão rebaixa a cada restart
[path-padrão-do-repo]/docling-serve/cache:/opt/app-root/src/.cache
# pasta de entrada compartilhada com o pipeline (PDFs a converter)
[path-padrão-do-repo]/lightrag/pdfs_raw:/data/input:ro
```

> Ajuste os paths do host conforme o padrão confirmado na Tarefa 1. O segundo volume aponta para a mesma `pdfs_raw` que o pipeline LightRAG usará; é read-only porque o Docling só lê.

### Healthcheck

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:5001/health')"]
  interval: 30s
  timeout: 10s
  start_period: 120s
  retries: 5
```

> `start_period` alto (120s) porque o primeiro carregamento de modelos é lento.

### Seção x-casaos

```yaml
x-casaos:
  architectures:
    - amd64
    - arm64
  main: docling
  author: sergio.sousa
  developer: docling-project
  category: Productivity
  icon: https://raw.githubusercontent.com/docling-project/docling/main/docs/assets/logo.png
  title:
    custom: Docling Serve
    en_us: Docling Serve
  description:
    en_us: |
      Docling Serve is an HTTP API for Docling — a document conversion engine
      that turns PDF, DOCX, PPTX, XLSX, HTML and images into clean Markdown,
      JSON, or HTML.

      Powered by specialized AI models for layout analysis (DocLayNet) and
      table structure recognition (TableFormer), it runs efficiently on
      commodity CPU hardware. Ideal as a parsing backend for RAG pipelines:
      feed it documents, get back structured Markdown ready for indexing.

      Key features:
      - REST API at /v1/convert/source (stable v1)
      - Built-in test UI at /ui and interactive docs at /docs
      - Supports PDF, DOCX, PPTX, XLSX, HTML, images, AsciiDoc, Markdown
      - Optional OCR for scanned documents (EasyOCR, Tesseract, RapidOCR)
      - Table structure extraction and layout-aware parsing
      - Models load on demand to keep idle memory low
  tagline:
    en_us: Document-to-Markdown conversion API for RAG pipelines
  port_map: "5001"
  index: /ui
  store_app_id: docling-serve
  tips:
    before_install:
      en_us: |
        **No configuration required to start** — defaults work out of the box.

        **First request is slow:** with models loading on demand, the very first
        conversion downloads and loads the AI models (DocLayNet, TableFormer).
        This can take 1–2 minutes. Subsequent conversions are fast. The model
        cache persists in a volume, so this only happens once.

        **Memory:** idle footprint is low (models not loaded). During conversion
        it can use up to ~4 GB RAM. Avoid running large batch jobs alongside
        other heavy services.

        **After installation — verify it works:**
        1. Open the test UI at `http://[HOST-IP]:5001/ui` and convert a sample PDF
        2. Or check the API docs at `http://[HOST-IP]:5001/docs`
        3. API test (PDF text, OCR off):
           ```
           curl -X POST 'http://[HOST-IP]:5001/v1/convert/source' \
             -H 'Content-Type: application/json' \
             -d '{"sources":[{"kind":"http","url":"https://arxiv.org/pdf/2501.17887"}],"options":{"to_formats":["md"],"do_ocr":false,"pdf_backend":"dlparse_v2"}}'
           ```

        **Known issue:** the `/v1/convert/file` (multipart) endpoint currently
        ignores OCR parameters and always uses RapidOCR. Use `/v1/convert/source`
        (path/URL based) for reliable OCR control.

        **Pairs with LightRAG:** send PDFs here, get Markdown, then feed the
        Markdown to LightRAG's input directory for indexing.
```

**Preencha/ajuste:**
- `author` — confirme o valor usado no lightrag e use o mesmo
- `category` — confirme a categoria do repo
- paths de volume — use o padrão confirmado na Tarefa 1
- valide que o ícone existe; se a URL retornar 404, substitua por um PNG quadrado hospedado no próprio repo ou outra URL válida

---

## Tarefa 3 — Validação

- [ ] `name:` consistente com o padrão dos outros apps
- [ ] imagem é `ghcr.io/docling-project/docling-serve-cpu:latest` (CPU, não CUDA, não base)
- [ ] porta 5001 mapeada e em `port_map`
- [ ] volume de cache presente (senão rebaixa modelos a cada restart)
- [ ] healthcheck com `start_period` longo
- [ ] seção `x-casaos` com todos os campos que os outros apps usam
- [ ] NENHUM Dockerfile criado, NENHUMA GitHub Action criada

---

## Referências

- Imagem oficial e API: https://github.com/docling-project/docling-serve
- Endpoint estável: `POST /v1/convert/source` na porta 5001
- Variantes de imagem: `docling-serve` (base), `docling-serve-cpu` (CPU), `docling-serve-cu128`/`cu130` (CUDA). Usar **cpu**.
- Path do cache de modelos no container: `/opt/app-root/src/.cache`

---

## Entregável

1. `casaos-appstore/Apps/docling-serve/docker-compose.yml` — completo e validado
2. Breve resumo das decisões e dos placeholders que precisam de revisão manual (author, category, paths, validade do ícone)
