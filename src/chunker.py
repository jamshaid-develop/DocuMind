import logging
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import config

logger = logging.getLogger(__name__)


def chunk_documents(documents: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
    logger.info("Chunked into %d pieces", len(chunks))
    return chunks


def get_chunk_stats(chunks: List[Document]) -> dict:
    if not chunks:
        return {"count": 0, "avg_chars": 0}
    sizes = [len(c.page_content) for c in chunks]
    return {"count": len(chunks), "avg_chars": round(sum(sizes) / len(sizes))}
