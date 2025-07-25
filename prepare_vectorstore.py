import os
import gc
from fastembed.embedding import TextEmbedding
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.embeddings import Embeddings
from fastembed.embedding import TextEmbedding

class FastEmbedLangChainWrapper(Embeddings):
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model = TextEmbedding(model_name=model_name)

    def embed_documents(self, texts):
        return list(self.model.embed(texts))

    def embed_query(self, text):
        return next(self.model.embed([text]))


def load_text(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()



def build_vectorstore():
    if os.path.exists("faiss_index/index.faiss"):
        print("Vectorstore already exists, skipping build")
        return

    #Load and wrap documents
    meditations_text = load_text("data/meditations.txt")
    articles_text = load_text("data/daily_stoic_articles.txt")
    documents = [
        Document(page_content=meditations_text, metadata={"source": "Meditations"}),
        Document(page_content=articles_text, metadata={"source": "Daily Stoic Articles"})
    ]

    
    del meditations_text, articles_text
    gc.collect()

    #Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    split_docs = splitter.split_documents(documents)

    del documents
    gc.collect()

    if len(split_docs) > 2000:
        split_docs = split_docs[:2000]

    
    embedding_model = FastEmbedLangChainWrapper(model_name="BAAI/bge-small-en-v1.5")

    
    batch_size = 100
    vectorstore = None

    for i in range(0, len(split_docs), batch_size):
        batch = split_docs[i:i + batch_size]
        print(f"Processing batch {i // batch_size + 1}/{(len(split_docs) - 1) // batch_size + 1}")

        if vectorstore is None:
            vectorstore = FAISS.from_documents(batch, embedding_model)
        else:
            batch_store = FAISS.from_documents(batch, embedding_model)
            vectorstore.merge_from(batch_store)
            del batch_store

        gc.collect()

    vectorstore.save_local("faiss_index")
    del vectorstore, embedding_model, split_docs
    gc.collect()
    print("Vectorstore saved to ./faiss_index")

if __name__ == "__main__":
    build_vectorstore()
