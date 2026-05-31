# knowledge-indexer

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Docker-ready-2496ED?style=flat&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/ChromaDB-vector_store-FF6B35?style=flat" alt="ChromaDB">
  <img src="https://img.shields.io/badge/Embedding-all--MiniLM--L6--v2-8A2BE2?style=flat" alt="Embedding Model">
</p>
 
<p align="center">
  Pipeline de ingestão de documentos para RAG. Converte arquivos de múltiplos formatos em texto e os indexa em um banco vetorial <a href="https://www.trychroma.com/">ChromaDB</a>, pronto para uso em sistemas de Retrieval-Augmented Generation.
</p>

---

## Visão geral

```
Documentos (PDF, DOCX, XLSX...)
        │
        ▼
   [ main.py ]  ──────────────────────→  /converter/txt/*.txt
  Conversão para TXT
        │
        ▼
 [ vectorize.py ]  ──────────────────→  ChromaDB  (collection: onvio_docs)
  Chunking + Embedding + Indexação
```

Os dois scripts são independentes e podem ser executados separadamente ou em sequência via Docker.

---

## Formatos suportados

| Formato | Extensão |
|---------|----------|
| PDF | `.pdf` |
| Word | `.docx` |
| Excel | `.xlsx` |
| CSV | `.csv` |
| PowerPoint | `.pptx` |
| HTML | `.html` `.htm` |

---

## Quick start

### Pré-requisitos

- Python 3.12+ **ou** Docker

### Com Python

```bash
# 1. Instale as dependências
pip install -r requirements.txt

# 2. Coloque seus documentos em /converter e execute o pipeline
python main.py && python vectorize.py
```

### Com Docker

```bash
# Build da imagem
docker build -t knowledge-indexer .

# Execução — substitua o caminho pela pasta com seus documentos
docker run --rm \
  -v /caminho/para/seus/documentos:/converter \
  knowledge-indexer
```

### Com Dev Container (VS Code)

1. Instale a extensão **Dev Containers**
2. Em `.devcontainer/devcontainer.json`, configure o campo `source` no mount com o caminho da pasta de documentos
3. `Ctrl+Shift+P` → **Reopen in Container**

---

## Como funciona

### Etapa 1 — Conversão (`main.py`)

Varre `/converter`, detecta o formato de cada arquivo automaticamente e gera um `.txt` correspondente em `/converter/txt/`.

```bash
python main.py
```

### Etapa 2 — Vetorização (`vectorize.py`)

Lê os `.txt`, divide em chunks de **2000 caracteres** (overlap de 200), gera embeddings com `all-MiniLM-L6-v2` e indexa no ChromaDB.

```bash
python vectorize.py
```

> O modelo de embedding (~90 MB) é baixado automaticamente na primeira execução.

---

## Deduplicação automática

O `vectorize.py` detecta alterações via hash MD5 e evita reprocessamento desnecessário:

| Situação | Comportamento |
|----------|--------------|
| Arquivo novo | Indexa normalmente |
| Arquivo sem alterações | Pula — já indexado |
| Arquivo modificado | Remove chunks antigos e re-indexa |

---

## Configuração do ChromaDB

Por padrão o banco é criado localmente em `/converter/chroma_db/`. Para usar um servidor remoto, configure as variáveis de ambiente:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `CHROMA_MODE` | `local` | `local` ou `server` |
| `CHROMA_HOST` | `localhost` | Host do servidor (modo `server`) |
| `CHROMA_PORT` | `8000` | Porta do servidor (modo `server`) |

```bash
# Exemplo — servidor remoto
CHROMA_MODE=server CHROMA_HOST=192.168.1.100 CHROMA_PORT=8000 python vectorize.py
```

#### Subir um servidor ChromaDB com Docker Compose

```yaml
services:
  chromadb:
    image: chromadb/chroma
    ports:
      - "8000:8000"
    volumes:
      - ./chroma_data:/chroma/chroma
    restart: always
```

> Para acessar fora da rede local, é necessário VPN ou IP público exposto.

---

## Integração com chatbot (RAG)

Este projeto cuida da **ingestão**. O chatbot que consome os dados deve:

1. Usar o **mesmo modelo de embedding** (`all-MiniLM-L6-v2`) para vetorizar as perguntas
2. Conectar ao ChromaDB na collection `onvio_docs`
3. Realizar busca por similaridade e passar os trechos relevantes ao LLM

> O LLM que gera as respostas (GPT-4, Claude, Llama, etc.) é independente dos embeddings — use qualquer um.
