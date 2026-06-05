import logging
import os
import shutil
from typing import List, Optional
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from config import config
from src.embeddings import get_embedding_model

logger = logging.getLogger(__name__)

_store: Optional[FAISS] = None


def build_vector_store(chunks: List[Document]) -> FAISS:
    global _store
    logger.info("Building FAISS index from %d chunks...", len(chunks))
    _store = FAISS.from_documents(chunks, get_embedding_model())
    _store.save_local(config.FAISS_INDEX_PATH)
    logger.info("FAISS index saved.")
    return _store


def add_to_vector_store(chunks: List[Document]) -> FAISS:
    global _store
    if _store is None:
        _store = load_vector_store()
    if _store is None:
        return build_vector_store(chunks)
    _store.add_documents(chunks)
    _store.save_local(config.FAISS_INDEX_PATH)
    return _store


def load_vector_store() -> Optional[FAISS]:
    global _store
    if _store:
        return _store
    if os.path.exists(config.FAISS_INDEX_PATH):
        try:
            _store = FAISS.load_local(
                config.FAISS_INDEX_PATH,
                get_embedding_model(),
                allow_dangerous_deserialization=True,
            )
            logger.info("FAISS index loaded from disk.")
        except Exception as e:
            logger.error("Could not load FAISS index: %s", e)
    return _store


def clear_vector_store():
    global _store
    _store = None
    if os.path.exists(config.FAISS_INDEX_PATH):
        shutil.rmtree(config.FAISS_INDEX_PATH)
    logger.info("Index cleared.")


def similarity_search(query: str, k: int = None) -> List[Document]:
    store = _store or load_vector_store()
    if not store:
        return []
    return store.similarity_search(query, k=k or config.TOP_K_RESULTS)


def get_retriever():
    store = _store or load_vector_store()
    if not store:
        raise RuntimeError("No documents indexed. Please upload a document first.")
    return store.as_retriever(search_kwargs={"k": config.TOP_K_RESULTS})


def is_store_ready() -> bool:
    return _store is not None or os.path.exists(config.FAISS_INDEX_PATH)
