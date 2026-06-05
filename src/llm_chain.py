import logging
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from config import config
from src.retriever import get_retriever

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """You are DocuMind, an expert document analyst.
Use ONLY the context below to answer the question.
If the answer is not found in the context, say "I couldn't find that information in the uploaded documents."
Be clear, accurate, and mention which part of the document supports your answer.

Context:
{context}

Question: {question}

Answer:"""

PROMPT = PromptTemplate(
    template=PROMPT_TEMPLATE,
    input_variables=["context", "question"]
)


def build_qa_chain() -> RetrievalQA:
    if not config.GROQ_API_KEY:
        raise EnvironmentError(
            "GROQ_API_KEY not set. Add it to your .env file. "
            "Get free key at: console.groq.com"
        )

    llm = ChatGroq(
        api_key=config.GROQ_API_KEY,
        model_name=config.GROQ_MODEL,
        temperature=0.2,
        max_tokens=1024,
    )

    retriever = get_retriever()

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT},
    )

    logger.info("QA chain ready with Groq model: %s", config.GROQ_MODEL)
    return chain


def answer_question(question: str) -> dict:
    chain = build_qa_chain()
    result = chain.invoke({"query": question})

    answer = result.get("result", "No answer generated.")
    source_docs = result.get("source_documents", [])

    seen = set()
    sources = []
    for doc in source_docs:
        key = (doc.metadata.get("source"), doc.metadata.get("page"))
        if key not in seen:
            seen.add(key)
            sources.append({
                "source": doc.metadata.get("source", "Unknown"),
                "page": doc.metadata.get("page"),
                "excerpt": doc.page_content[:250].replace("\n", " ") + "…",
            })

    return {"answer": answer, "sources": sources}
