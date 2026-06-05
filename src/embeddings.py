import logging
from functools import lru_cache
from langchain_huggingface import HuggingFaceEmbeddings
from config import config

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_embedding_model() -> HuggingFaceEmbeddings:
    logger.info("Loading embedding model: %s", config.EMBEDDING_MODEL)
    model = HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    logger.info("Embedding model ready.")
    return model
