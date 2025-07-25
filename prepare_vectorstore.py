import os
import gc
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
        print("✓ Vectorstore already exists, skipping build")
        return

    print("Loading text content...")
    # Load raw content
    meditations_text = load_text("data/meditations.txt")
    articles_text = load_text("data/daily_stoic_articles.txt")

    # Wrap in Document objects with metadata
    documents = [
        Document(page_content=meditations_text, metadata={"source": "Meditations"}),
        Document(page_content=articles_text, metadata={"source": "Daily Stoic Articles"})
    ]

    # Clear large text variables to free memory
    del meditations_text, articles_text
    gc.collect()

    print("Splitting documents into chunks...")
    # Use smaller chunks to reduce memory usage
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,  # Reduced from 500
        chunk_overlap=50,  # Reduced from 100
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    split_docs = splitter.split_documents(documents)
    
    # Clear documents to free memory
    del documents
    gc.collect()
    
    print(f"Created {len(split_docs)} document chunks")

    # Limit the number of chunks if too many (memory safety)
    if len(split_docs) > 2000:
        print(f"Too many chunks ({len(split_docs)}), limiting to 2000 for memory safety")
        split_docs = split_docs[:2000]

    
    # Create embeddings with memory optimization
    embedding_model = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L12-v1",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    print("🔍 Building FAISS vectorstore...")
    # Process in smaller batches to avoid memory spikes
    batch_size = 100
    vectorstore = None
    
    for i in range(0, len(split_docs), batch_size):
        batch = split_docs[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(split_docs)-1)//batch_size + 1}")
        
        if vectorstore is None:
            vectorstore = FAISS.from_documents(batch, embedding_model)
        else:
            batch_store = FAISS.from_documents(batch, embedding_model)
            vectorstore.merge_from(batch_store)
            del batch_store
        
        # Force garbage collection after each batch
        gc.collect()

   
    vectorstore.save_local("faiss_index")
    
    # Clean up
    del vectorstore, embedding_model, split_docs
    gc.collect()

    print("Vectorstore saved to ./faiss_index")

if __name__ == "__main__":
    build_vectorstore()