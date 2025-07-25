from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from rag_pipeline import get_stoic_qa_chain


app = Flask(__name__)
CORS(app)

#Load RAG pipeline
qa_chain = get_stoic_qa_chain()  

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.get_json()
    question = data.get("question", "")
    
    if not question.strip():
        return jsonify({"error": "No question provided"}), 400
    
    try:
        answer = qa_chain(question) 
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
