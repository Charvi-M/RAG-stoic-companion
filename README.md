# Stoic Companion Web App

## Introduction
Stoic Companion is a Retrieval Augmented Generation system that uses Stoic Data from two different sources on the internet and generates Stoic response. The data scraping is done by using BeutifulSoup and the text generation is done by using Gemini LLM. The vectorstore used is FAISS, with all-miniLM embeddings from Huggingface. The UI is created using vanilla HTML, CSS, JS.



## Project Structure

STOIC_COMPANION_RAG/
backend/
├─ data/
│  ├─ daily_stoic_articles.txt
│  ├─ meditations.txt
├─ faiss_index/
│  ├─ index.faiss
│  ├─ index.pkl
├─ app.py
├─ prepare_vectorstore.py
├─ rag_pipeline.py
├─ scraper.py
├─ test_chain.py
frontend/
├─ app.js
├─ index.html
├─ style.css
.env
.gitignore
README.md
requirements.txt

## Project Setup

1. `pip install -r requirements.txt`
2. run scraper.py using `python scraper.py`
3. run prepare_vectorstore.py using `python prepare_vectorstore.py`
4. The above commands should generate necessary data and faiss_index folder
5. run rag_pipeline.py using `python rag_pipeline.py`
6. now run the backend by using command `python app.py` 
7. we are ready to open the index.html file and play with the Stoic Companion

### Sources of data scraping

1. [Meditations by Marcus Aurelius](https://www.gutenberg.org/cache/epub/2680/pg2680-images.html)
2. [Daily Stoic Articles](https://dailystoic.com/all-articles/)
