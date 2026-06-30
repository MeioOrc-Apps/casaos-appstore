# CasaOS / ZimaOS Custom App Store

Este repositório serve como uma App Store customizada para o CasaOS e ZimaOS. Ele centraliza todos os aplicativos pessoais para que possam ser instalados e atualizados com 1 clique diretamente pela interface do sistema.

## 🚀 Como instalar esta App Store no seu ZimaOS

1. Abra a **App Store** na interface do seu ZimaOS/CasaOS.
2. No canto superior direito da janela da App Store, clique no botão **Add Source** (Adicionar Fonte).
3. Cole o link do arquivo `.zip` da branch principal deste repositório:
   ```text
   https://github.com/MeioOrc-Apps/casaos-appstore/archive/refs/heads/main.zip
   ```
4. Clique em **Add**.
5. Pronto! Agora você verá uma nova categoria na sua loja contendo os aplicativos deste repositório.

---

## 🗂️ Aplicativos disponíveis

| App | Categoria | Porta | Descrição |
| --- | --- | --- | --- |
| **Art Catalog** | Media | `5173` | Catálogo pessoal de arte e moodboard. |
| **Odysseus** | Productivity | `7000` | Workspace AI self-hosted: chat, agentes, pesquisa profunda, memória, e-mail e notas. |
| **LightRAG** | Productivity | `9621` | Motor de RAG com grafo de conhecimento sobre os seus documentos. |
| **Docling Serve** | Productivity | `5001` | API de conversão de documentos (PDF/DOCX/PPTX/…) para Markdown — backend de parsing para pipelines RAG. |
| **RAG Orchestrator** | Productivity | `8080` | Pipeline de ingestão automática de documentos para LightRAG. Monitora pastas, converte e indexa no schedule. |
| **Thermal API** | Utilities | `8666` | API de monitoramento de temperatura CPU com análise de tendência. Proxy para controle PWM de cooler via ESP32. |
| **Cronmaster** | Utilities | `3013` | Gerenciador visual de cron jobs com editor de scripts Bash e controle de containers Docker via socket. |
| **OpenSearch** | Productivity | `5601` / `9200` | Motor de busca full-text (BM25) com interface visual via Dashboards. Fork open-source do Elasticsearch, Apache 2.0. |

---

## 📦 Como adicionar um novo aplicativo à loja

Para adicionar um novo app (ex: `SaveState`), siga esta estrutura:

1. Crie uma nova pasta dentro do diretório `Apps/` com o nome do aplicativo (sem espaços).
   ```bash
   mkdir -p Apps/SaveState
   ```
2. Coloque o arquivo `docker-compose.yml` do aplicativo dentro dessa pasta.
   * **Importante:** O arquivo `docker-compose.yml` **precisa** conter o bloco `x-casaos` no final, com as informações de título, ícone, categoria, etc.
3. (Opcional) Se quiser que o app apareça na aba de recomendados, adicione o nome da pasta dele no arquivo `recommend-list.json`.
4. Faça o commit e o push para a branch `main`:
   ```bash
   git add .
   git commit -m "feat: add SaveState app"
   git push origin main
   ```
5. O ZimaOS sincronizará a loja automaticamente em segundo plano (ou você pode forçar recarregando a página da App Store).

---

## 🔄 Como lançar uma atualização de um aplicativo

Quando você lançar uma versão nova de um aplicativo (ex: mudou a imagem Docker do `ArtCatalog` para a `v0.1.8`), você precisa atualizar a loja para que o ZimaOS mostre o botão de "Update".

1. Abra o arquivo `Apps/NomeDoApp/docker-compose.yml` neste repositório.
2. Altere a tag da imagem Docker para a nova versão.
   ```yaml
   services:
     api:
       image: sergiosjs/art-catalog-api:1.1.0 # <-- Atualize a tag aqui
   ```
3. Faça o commit e o push:
   ```bash
   git add Apps/ArtCatalog/docker-compose.yml
   git commit -m "chore(art-catalog): bump version to v0.1.8"
   git push origin main
   ```
4. O ZimaOS detectará a mudança no arquivo `docker-compose.yml` e exibirá um aviso vermelho de **Update** no ícone do aplicativo no seu painel!
