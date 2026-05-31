import os
import sys
import hashlib
from loguru import logger
from sentence_transformers import SentenceTransformer
import chromadb

PASTA_CONTAINER = "/converter"
PASTA_TXT = "/converter/txt"
CHROMA_COLLECTION = "onvio_docs"
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200
MODELO_EMBEDDING = "all-MiniLM-L6-v2"

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    level="DEBUG",
    colorize=True,
)


def conectar_chromadb():
    modo = os.environ.get("CHROMA_MODE", "local")

    if modo == "local":
        chroma_path = os.path.join(PASTA_CONTAINER, "chroma_db")
        logger.info(f"ChromaDB modo local: {chroma_path}")
        return chromadb.PersistentClient(path=chroma_path)

    host = os.environ.get("CHROMA_HOST", "localhost")
    port = int(os.environ.get("CHROMA_PORT", "8000"))
    logger.info(f"ChromaDB modo servidor: {host}:{port}")
    return chromadb.HttpClient(host=host, port=port)


def calcular_hash(caminho):
    with open(caminho, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def chunkar_texto(texto):
    chunks = []
    inicio = 0
    while inicio < len(texto):
        fim = inicio + CHUNK_SIZE
        chunk = texto[inicio:fim].strip()
        if chunk:
            chunks.append(chunk)
        inicio = fim - CHUNK_OVERLAP
    return chunks


def buscar_txts(pasta):
    logger.info(f"Varrendo pasta: {pasta}")

    if not os.path.isdir(pasta):
        logger.error(f"Pasta não encontrada: {pasta}")
        sys.exit(1)

    txts = [
        os.path.join(pasta, f)
        for f in os.listdir(pasta)
        if f.lower().endswith(".txt") and os.path.isfile(os.path.join(pasta, f))
    ]

    if not txts:
        logger.warning("Nenhum arquivo .txt encontrado para vetorizar.")
        sys.exit(0)

    logger.info(f"{len(txts)} arquivo(s) .txt encontrado(s).")
    return txts


def indexar(caminho_txt, collection, modelo):
    nome = os.path.basename(caminho_txt)
    hash_atual = calcular_hash(caminho_txt)

    existentes = collection.get(where={"source": nome}, limit=1)

    if existentes["ids"]:
        hash_salvo = existentes["metadatas"][0].get("file_hash", "")
        if hash_salvo == hash_atual:
            logger.debug(f"Sem alterações: {nome} — pulando.")
            return
        logger.info(f"Atualização detectada: {nome} — re-indexando.")
        collection.delete(where={"source": nome})
    else:
        logger.info(f"Novo documento: {nome} — indexando.")

    try:
        with open(caminho_txt, "r", encoding="utf-8") as f:
            texto = f.read()
    except IOError as e:
        logger.error(f"Falha ao ler '{nome}': {e}")
        return

    chunks = chunkar_texto(texto)

    if not chunks:
        logger.warning(f"'{nome}' sem conteúdo após chunking — pulando.")
        return

    logger.info(f"{len(chunks)} chunk(s) gerado(s) para {nome}.")

    ids = [f"{nome}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {"source": nome, "chunk_index": i, "file_hash": hash_atual}
        for i in range(len(chunks))
    ]

    logger.debug(f"Gerando embeddings para {nome}...")
    embeddings = modelo.encode(chunks, show_progress_bar=False).tolist()

    collection.add(ids=ids, documents=chunks, metadatas=metadatas, embeddings=embeddings)
    logger.success(f"'{nome}' indexado com {len(chunks)} chunk(s).")


def main():
    logger.info("Iniciando vetorizador → ChromaDB")

    client = conectar_chromadb()
    collection = client.get_or_create_collection(CHROMA_COLLECTION)
    logger.info(f"Collection: '{CHROMA_COLLECTION}' | Documentos existentes: {collection.count()}")

    logger.info(f"Carregando modelo de embedding: {MODELO_EMBEDDING}")
    modelo = SentenceTransformer(MODELO_EMBEDDING)
    logger.info("Modelo carregado.")

    txts = buscar_txts(PASTA_TXT)

    for txt in txts:
        indexar(txt, collection, modelo)

    logger.info(f"Vetorização finalizada. Total no banco: {collection.count()} chunk(s).")


if __name__ == "__main__":
    main()
