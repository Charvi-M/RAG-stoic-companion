import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

def load_text(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def build_vectorstore():
    # Skip if already exists
    if os.path.exists("faiss_index/index.faiss"):
        return


    # Load raw content
    meditations_text = load_text("data/meditations.txt")
    articles_text = load_text("data/daily_stoic_articles.txt")

    # Wrap in Document objects with metadata
    documents = [
        Document(page_content=meditations_text, metadata={"source": "Meditations"}),
        Document(page_content=articles_text, metadata={"source": "Daily Stoic Articles"})
    ]

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    split_docs = splitter.split_documents(documents)

    # Create embeddings
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # Create vectorstore
    vectorstore = FAISS.from_documents(split_docs, embedding_model)
    vectorstore.save_local("faiss_index")

    print(" Vectorstore saved to ./faiss_index")

if __name__ == "__main__":
    build_vectorstore()
