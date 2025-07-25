from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import traceback
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

qa_chain = None
initialized = False  # for lazy init

def initialize_qa_system():
    """Initialize the QA system only if FAISS index and API key are present."""
    global qa_chain
    try:
        if qa_chain is not None:
            return True

        logger.info("Initializing QA system...")

        # Check if FAISS index files exist
        if not os.path.exists("faiss_index/index.faiss") or not os.path.exists("faiss_index/index.pkl"):
            logger.error("FAISS index files not found in faiss_index/")
            return False

        if not os.getenv("GEMINI_API_KEY"):
            logger.error("GEMINI_API_KEY missing in environment")
            return False

        from rag_pipeline import get_stoic_qa_chain
        qa_func = get_stoic_qa_chain()

        if qa_func is None or not callable(qa_func):
            logger.error("get_stoic_qa_chain returned None or non-callable")
            return False

        qa_chain = qa_func
        logger.info("QA system initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Initialization error: {str(e)}")
        logger.error(traceback.format_exc())
        return False


@app.before_request
def ensure_qa_chain_initialized():
    global initialized
    if not initialized:
        logger.info("Lazy-loading QA system on first request...")
        if initialize_qa_system():
            logger.info("QA chain initialized lazily")
        else:
            logger.warning("QA chain failed to initialize")
        initialized = True

@app.route("/")
def home():
    try:
        return render_template("index.html")
    except Exception as e:
        logger.error(f"Template render error: {str(e)}")
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>Stoic Companion</title></head>
        <body>
            <h1>Stoic Companion - Service Unavailable</h1>
            <p>The template could not be loaded. Please check server logs.</p>
        </body>
        </html>
        ''', 500

@app.route("/health")
def health():
    try:
        health_status = {
            "status": "ok",
            "vectorstore_exists": os.path.exists("faiss_index/index.faiss") and os.path.exists("faiss_index/index.pkl"),
            "env_key_set": bool(os.getenv("GEMINI_API_KEY")),
            "qa_chain_initialized": qa_chain is not None and callable(qa_chain)
        }

        if not health_status["qa_chain_initialized"]:
            health_status["qa_chain_initialized"] = initialize_qa_system()

        if all(health_status.values()):
            return jsonify(health_status), 200
        else:
            health_status["status"] = "degraded"
            return jsonify(health_status), 503
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route("/debug")
def debug_info():
    try:
        debug_data = {
            "vectorstore_exists": os.path.exists("faiss_index/index.faiss"),
            "pkl_exists": os.path.exists("faiss_index/index.pkl"),
            "env_file_exists": os.path.exists(".env"),
            "gemini_key_set": bool(os.getenv("GEMINI_API_KEY")),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "working_directory": os.getcwd(),
            "current_dir_files": [f for f in os.listdir(".") if not f.startswith('.')],
            "qa_chain_status": "initialized" if qa_chain and callable(qa_chain) else "not_initialized"
        }

        debug_data["faiss_files"] = os.listdir("faiss_index") if os.path.exists("faiss_index") else "missing"
        debug_data["template_files"] = os.listdir("templates") if os.path.exists("templates") else "missing"

        return jsonify(debug_data)
    except Exception as e:
        return jsonify({"debug_error": str(e)}), 500

@app.route("/ask", methods=["POST"])
def ask_question():
    global qa_chain
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        question = data.get("question", "").strip()
        if not question:
            return jsonify({"error": "No question provided"}), 400

        logger.info(f"Received question: {question[:50]}...")

        if qa_chain is None or not callable(qa_chain):
            logger.info("QA chain not ready or not callable, initializing...")
            if not initialize_qa_system():
                return jsonify({
                    "error": "QA system unavailable. Please check configuration."
                }), 503

        if not callable(qa_chain):
            logger.error("QA chain is still not callable after init.")
            return jsonify({"error": "QA system misconfiguration. Contact admin."}), 500

        logger.info("Generating answer...")
        answer = qa_chain(question)

        if not answer or not answer.strip():
            answer = "I find myself unable to provide wisdom on this matter. Perhaps you might rephrase your question?"

        logger.info("Answer generated successfully")
        return jsonify({"answer": answer})

    except ImportError as e:
        logger.error(f"Import error: {str(e)}")
        return jsonify({"error": "Missing dependencies"}), 500

    except Exception as e:
        logger.error(f"Error in ask_question: {str(e)}")
        logger.error(traceback.format_exc())

        if "API" in str(e).lower() or "key" in str(e).lower():
            return jsonify({"error": "API configuration issue. Contact administrator."}), 500
        elif "faiss" in str(e).lower() or "vectorstore" in str(e).lower():
            return jsonify({"error": "Knowledge base error. Contact administrator."}), 500
        elif "timeout" in str(e).lower():
            return jsonify({"error": "Request timed out. Try again."}), 408
        else:
            return jsonify({"error": "Unexpected error. Try later."}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("Starting Flask app with lazy QA loading...")
    app.run(host="0.0.0.0", port=port, debug=False)
