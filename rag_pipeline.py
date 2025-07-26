import os
import logging
import traceback
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from fastembed.embedding import TextEmbedding  
from langchain_core.embeddings import Embeddings

class FastEmbedLangChainWrapper(Embeddings):
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model = TextEmbedding(model_name=model_name)

    def embed_documents(self, texts):
        return list(self.model.embed(texts))

    def embed_query(self, text):
        return next(self.model.embed([text]))



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


load_dotenv()

#Globals
vectorstore = None
llm = None
retrieval_qa_chain = None
style_chain = None


stoic_style_prompt = PromptTemplate(
    input_variables=["question", "answer"],
    template="""
Question: {question}

Philosophical Insight: "{answer}"

Respond like Marcus Aurelius writing in his *Meditations*. Use stoic reasoning, introspection, and morality. Avoid modern language. Be concise and reflective. If the answer is not found in the retrieved philosophical texts, respond with humility and say that the information is not known.

Your response:
"""
)

def get_stoic_qa_chain():
    global vectorstore, llm, retrieval_qa_chain, style_chain

    if retrieval_qa_chain is not None:
        logger.info("QA chain already initialized")
        return generate_stoic_response

    try:
        logger.info("Initializing QA chain...")

        if not os.path.exists("faiss_index/index.faiss"):
            logger.error("Vectorstore not found.")
            return None

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            return None

        
        embedder = FastEmbedLangChainWrapper(model_name="BAAI/bge-small-en-v1.5")


        
        vectorstore = FAISS.load_local(
            "faiss_index", embeddings=embedder, allow_dangerous_deserialization=True
        )
        logger.info("Vectorstore loaded successfully")

        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            temperature=0.7,
            api_key=api_key,
            timeout=30,
            max_retries=2
        )
        logger.info("LLM initialized successfully")

        
        retriever = vectorstore.as_retriever(search_type="similarity", k=3)

        
        retrieval_qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            chain_type="stuff",
            return_source_documents=True
        )

        
        style_chain = stoic_style_prompt | llm

        logger.info("QA chain initialization completed successfully")
        return generate_stoic_response

    except Exception as e:
        logger.error(f"Error during QA initialization: {str(e)}")
        traceback.print_exc()
        return None


def generate_stoic_response(user_question):
    global retrieval_qa_chain, style_chain

    try:
        

        if retrieval_qa_chain is None or style_chain is None:
            raise RuntimeError("QA chain not properly initialized")

        
        result = retrieval_qa_chain.invoke({"query": user_question})
        base_answer = result.get("result", "").strip()
        sources = result.get("source_documents", [])

        logger.info(f"QA chain returned {len(sources)} source documents")

        if not base_answer or not sources:
            logger.info("No relevant sources found")
            return (
                "There is no wisdom in speaking beyond what is known. "
                "I must refrain from answering, for no record on this matter exists in the scrolls entrusted to me."
            )

        
        styled = style_chain.invoke({
            "question": user_question,
            "answer": base_answer
        })

        styled_response = styled.content if hasattr(styled, "content") else str(styled)


        return styled_response 


    except Exception as e:
        logger.error(f"Error generating stoic response: {str(e)}")
        traceback.print_exc()
        return (
            "The mind encounters obstacles in its pursuit of wisdom. "
            "Let us approach this matter with patience, for even difficulties teach us virtue."
        )


def test_qa_system():
    try:
        logger.info("Testing QA system...")
        qa_func = get_stoic_qa_chain()
        if not qa_func:
            logger.error("QA system initialization failed")
            return False

        test_response = qa_func("What is virtue?")

        if test_response and len(test_response.strip()) > 0:
            logger.info("QA system test passed")
            return True
        else:
            logger.error("QA system test failed - empty response")
            return False

    except Exception as e:
        logger.error(f"QA system test failed: {str(e)}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if test_qa_system():
        print("RAG system is working correctly")
    else:
        print("RAG system test failed")
