import logging
import os
import time
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

from config import config
from src.chunker import chunk_documents, get_chunk_stats
from src.document_loader import load_document
from src.llm_chain import answer_question
from src.retriever import (
    add_to_vector_store, build_vector_store,
    clear_vector_store, is_store_ready,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def status():
    return jsonify({
        "success": True,
        "store_ready": is_store_ready(),
        "model": config.GROQ_MODEL,
    })


@app.route("/api/upload", methods=["POST"])
def upload_document():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded."}), 400

    file = request.files["file"]
    mode = request.form.get("mode", "replace")

    if not file.filename:
        return jsonify({"success": False, "error": "Empty filename."}), 400

    if not allowed_file(file.filename):
        return jsonify({"success": False, "error": "File type not supported. Use PDF, DOCX, TXT, or MD."}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(config.UPLOAD_FOLDER, filename)
    file.save(save_path)

    try:
        t0 = time.time()
        documents = load_document(save_path)

        if not documents:
            return jsonify({"success": False, "error": "Document is empty or unreadable."}), 400

        chunks = chunk_documents(documents)
        stats = get_chunk_stats(chunks)

        if mode == "append":
            add_to_vector_store(chunks)
        else:
            clear_vector_store()
            build_vector_store(chunks)

        elapsed = round(time.time() - t0, 2)
        return jsonify({
            "success": True,
            "filename": filename,
            "pages": len(documents),
            "chunks": stats["count"],
            "avg_chars": stats["avg_chars"],
            "elapsed_s": elapsed,
            "message": f"'{filename}' indexed in {elapsed}s ({stats['count']} chunks).",
        })

    except Exception as e:
        logger.exception("Upload failed: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    if not is_store_ready():
        return jsonify({"success": False, "error": "No documents indexed. Please upload a document first."}), 400

    data = request.get_json(silent=True)
    if not data or not data.get("question", "").strip():
        return jsonify({"success": False, "error": "Please provide a question."}), 400

    question = data["question"].strip()

    try:
        t0 = time.time()
        result = answer_question(question)
        elapsed = round(time.time() - t0, 2)

        return jsonify({
            "success": True,
            "question": question,
            "answer": result["answer"],
            "sources": result["sources"],
            "elapsed_s": elapsed,
        })

    except EnvironmentError as e:
        return jsonify({"success": False, "error": str(e)}), 500
    except Exception as e:
        logger.exception("Chat error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/reset", methods=["POST"])
def reset():
    clear_vector_store()
    return jsonify({"success": True, "message": "Index cleared."})


if __name__ == "__main__":
    logger.info("DocuMind (Groq) starting on http://localhost:%d", config.FLASK_PORT)
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=False)
