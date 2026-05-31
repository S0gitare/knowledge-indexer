# knowledge-indexer

Conversor de documentos para texto e vetores. Transforma arquivos de múltiplos formatos em `.txt` e os indexa em um banco vetorial [ChromaDB](https://www.trychroma.com/) para uso em sistemas de RAG (Retrieval-Augmented Generation).

---

## Formatos suportados

| Formato | Extensão | → TXT | → ChromaDB |
|---------|----------|-------|------------|
| PDF | `.pdf` | ✅ | ✅ |
| Word | `.docx` | ✅ | ✅ |
| Excel | `.xlsx` | ✅ | ✅ |
| CSV | `.csv` | ✅ | ✅ |
| PowerPoint | `.pptx` | ✅ | ✅ |
| HTML | `.html` `.htm` | ✅ | ✅ |

---

## Arquitetura

```
/converter/
├── documento.pdf   ┐
├── manual.docx     ├─→ main.py ──→ txt/documento.txt ──→ vectorize.py ──→ ChromaDB
├── planilha.xlsx   ┘              txt/manual.txt
├── txt/                (gerado automaticamente pelo main.py)
└── chroma_db/          (gerado automaticamente no modo local)
```

Os dois scripts são independentes e podem ser executados separadamente:
- `main.py` — converte arquivos para `.txt`
- `vectorize.py` — lê os `.txt` e indexa no ChromaDB

---

## Requisitos

- Python 3.12+
- Docker (opcional, para uso com Dev Container)

---

## Instalação

```bash
pip install -r requirements.txt
```

---

## Uso

### 1. Conversão para TXT

Coloque os arquivos na pasta `/converter` e execute:

```bash
python main.py
```

O script varre a pasta, detecta automaticamente o formato de cada arquivo e gera um `.txt` correspondente no mesmo diretório.

### 2. Vetorização para ChromaDB

Após a conversão, execute:

```bash
python vectorize.py
```

O script lê os arquivos `.txt`, divide em chunks de 2000 caracteres (com overlap de 200), gera embeddings e indexa no ChromaDB.

> O modelo de embedding utilizado é `all-MiniLM-L6-v2` (Sentence Transformers), baixado automaticamente na primeira execução (~90MB).

---

## Variáveis de ambiente

### `vectorize.py`

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `CHROMA_MODE` | `local` | Modo de conexão com o ChromaDB (`local` ou `server`) |
| `CHROMA_HOST` | `localhost` | Host do servidor ChromaDB (somente no modo `server`) |
| `CHROMA_PORT` | `8000` | Porta do servidor ChromaDB (somente no modo `server`) |

---

## Modos do ChromaDB

### Modo local (desenvolvimento)

Por padrão, o ChromaDB é criado localmente em `/converter/chroma_db/`. Nenhuma configuração adicional é necessária.

```bash
python vectorize.py
# ou explicitamente:
CHROMA_MODE=local python vectorize.py
```

### Modo servidor (produção)

Para conectar em um servidor ChromaDB remoto (ex: container Docker na empresa):

```bash
CHROMA_MODE=server CHROMA_HOST=192.168.1.100 CHROMA_PORT=8000 python vectorize.py
```

Nesse modo, os documentos são enviados diretamente ao servidor — sem geração de banco local.

#### Exemplo de servidor ChromaDB com Docker

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

> Para acessar o servidor fora da rede local, é necessário estar conectado à VPN da empresa ou ter o servidor exposto com IP público.

---

## Deduplicação e atualização

O `vectorize.py` detecta automaticamente alterações nos arquivos via hash MD5:

| Situação | Comportamento |
|----------|--------------|
| Arquivo novo | Indexa normalmente |
| Arquivo sem alterações | Pula (já indexado) |
| Arquivo atualizado | Remove chunks antigos e re-indexa |

---

## Integração com chatbot (RAG)

Este projeto gera e mantém o banco vetorial. O chatbot que consume esses dados deve:

1. Usar o **mesmo modelo de embedding** (`all-MiniLM-L6-v2`) para vetorizar as perguntas dos usuários
2. Conectar ao ChromaDB (local ou servidor) na collection `onvio_docs`
3. Realizar busca por similaridade e passar os trechos relevantes ao LLM

> O modelo de embedding precisa ser idêntico nos dois lados. O LLM que gera as respostas (GPT-4, Claude, Llama, etc.) pode ser qualquer um — ele é independente dos embeddings.

---

## Dev Container

O projeto inclui configuração para [Dev Containers](https://containers.dev/) no VS Code. Para abrir:

1. Instale a extensão **Dev Containers** no VS Code
2. Abra o arquivo `.devcontainer/devcontainer.json` e configure o campo `source` no mount com o caminho da pasta onde estão seus documentos (PDF, DOCX, etc.) — essa é a pasta que o script vai varrer e processar
3. Abra a pasta do projeto
4. `Ctrl+Shift+P` → **Reopen in Container**
