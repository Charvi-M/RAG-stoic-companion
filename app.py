from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

qa_chain = None  # Global cached QA chain

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/health")
def health():
    return "ok", 200

@app.route("/ask", methods=["POST"])
def ask_question():
    global qa_chain
    data = request.get_json()
    question = data.get("question", "")

    if not question.strip():
        return jsonify({"error": "No question provided"}), 400

    try:
        if qa_chain is None:
            from rag_pipeline import get_stoic_qa_chain  
            qa_chain = get_stoic_qa_chain()              

        answer = qa_chain(question)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
