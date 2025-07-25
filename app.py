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

qa_chain = None  # Global cached QA chain

def initialize_qa_system():
    """Initialize the QA system with proper error handling"""
    global qa_chain
    try:
        if qa_chain is None:
            logger.info("Initializing QA system...")
            
            # Check if vectorstore exists before importing
            if not os.path.exists("faiss_index/index.faiss"):
                logger.error("Vectorstore not found at faiss_index/index.faiss")
                return False
                
            # Check if environment variables are set
            if not os.getenv("GEMINI_API_KEY"):
                logger.error("GEMINI_API_KEY not found in environment variables")
                return False
            
            from rag_pipeline import get_stoic_qa_chain  
            qa_chain = get_stoic_qa_chain()
            logger.info("QA system initialized successfully")
        return True
    except ImportError as e:
        logger.error(f"Import error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize QA system: {str(e)}")
        logger.error(traceback.format_exc())
        return False

@app.route("/")
def home():
    try:
        return render_template("index.html")
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}")
        # Fallback to simple HTML if template fails
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
    """Enhanced health check"""
    try:
        health_status = {
            "status": "ok",
            "vectorstore_exists": os.path.exists("faiss_index/index.faiss"),
            "env_key_set": bool(os.getenv("GEMINI_API_KEY")),
            "qa_chain_initialized": qa_chain is not None
        }
        
        # Try to initialize QA system if not already done
        if not health_status["qa_chain_initialized"]:
            health_status["qa_chain_initialized"] = initialize_qa_system()
        
        # Determine overall health
        if all([
            health_status["vectorstore_exists"],
            health_status["env_key_set"],
            health_status["qa_chain_initialized"]
        ]):
            return jsonify(health_status), 200
        else:
            health_status["status"] = "degraded"
            return jsonify(health_status), 503
            
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route("/debug")
def debug_info():
    """Debug endpoint to check system status"""
    try:
        debug_data = {
            "vectorstore_exists": os.path.exists("faiss_index/index.faiss"),
            "env_file_exists": os.path.exists(".env"),
            "gemini_key_set": bool(os.getenv("GEMINI_API_KEY")),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "working_directory": os.getcwd(),
            "current_dir_files": [f for f in os.listdir(".") if not f.startswith('.')],
            "qa_chain_status": "initialized" if qa_chain else "not_initialized"
        }
        
        if os.path.exists("faiss_index"):
            debug_data["faiss_files"] = os.listdir("faiss_index")
        else:
            debug_data["faiss_files"] = "directory_not_found"
            
        if os.path.exists("templates"):
            debug_data["template_files"] = os.listdir("templates")
        else:
            debug_data["template_files"] = "templates_directory_not_found"
        
        return jsonify(debug_data)
    except Exception as e:
        return jsonify({"debug_error": str(e)}), 500

@app.route("/ask", methods=["POST"])
def ask_question():
    global qa_chain
    
    try:
        # Get and validate request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        question = data.get("question", "").strip()
        if not question:
            return jsonify({"error": "No question provided"}), 400

        logger.info(f"Received question: {question[:50]}...")

        # Initialize QA system if needed
        if qa_chain is None:
            logger.info("QA chain not initialized, attempting to initialize...")
            if not initialize_qa_system():
                return jsonify({
                    "error": "QA system unavailable. Please check server configuration and try again."
                }), 503

        # Generate answer
        logger.info("Generating answer...")
        answer = qa_chain(question)
        
        if not answer or not answer.strip():
            answer = "I find myself unable to provide wisdom on this matter. Perhaps you might rephrase your question?"
        
        logger.info("Answer generated successfully")
        return jsonify({"answer": answer})
        
    except ImportError as e:
        error_msg = f"Import error: {str(e)}"
        logger.error(error_msg)
        return jsonify({"error": "System dependencies unavailable"}), 500
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in ask_question: {error_msg}")
        logger.error(traceback.format_exc())
        
        # Provide user-friendly error messages
        if "API" in error_msg or "key" in error_msg.lower():
            return jsonify({"error": "API configuration issue. Please contact administrator."}), 500
        elif "vectorstore" in error_msg.lower() or "faiss" in error_msg.lower():
            return jsonify({"error": "Knowledge base unavailable. Please contact administrator."}), 500
        elif "timeout" in error_msg.lower():
            return jsonify({"error": "Request timed out. Please try again."}), 408
        else:
            return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

@app.before_first_request
def startup():
    """Initialize QA system on first request"""
    logger.info("Application starting up...")
    if not initialize_qa_system():
        logger.warning("QA system failed to initialize on startup")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    
    # Try to initialize QA system on startup
    logger.info("Starting Flask application...")
    if initialize_qa_system():
        logger.info("QA system initialized successfully on startup")
    else:
        logger.warning("QA system failed to initialize on startup - will retry on first request")
    
    app.run(host="0.0.0.0", port=port, debug=False)