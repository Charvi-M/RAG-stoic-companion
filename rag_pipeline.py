from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load secrets from .env
load_dotenv()

# Global singletons (cached between requests)
vectorstore = None
llm = None
qa_chain = None
style_chain = None

# Marcus Aurelius-style prompt
stoic_style_prompt = PromptTemplate(
    input_variables=["question", "answer"],
    template="""
Question: {question}

Philosophical Insight: "{answer}"

Respond as if you are Marcus Aurelius writing in his *Meditations*. Use stoic reasoning, self-addressed reflection, and moral instruction. Avoid modern language. Be concise, reflective, and moral. If the answer is not found in the retrieved philosophical texts, respond with humility and say that the information is not known.

Your response:
"""
)

def get_stoic_qa_chain():
    global vectorstore, llm, qa_chain, style_chain

    if qa_chain is not None:
        logger.info("QA chain already initialized")
        return generate_stoic_response  # Already built

    try:
        logger.info("Initializing QA chain...")
        
        # Check if vectorstore exists
        if not os.path.exists("faiss_index/index.faiss"):
            raise FileNotFoundError("Vectorstore not found. Please run prepare_vectorstore.py first.")
        
        # Check API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        logger.info("Loading vectorstore...")
        # No embedding model is loaded at runtime!
        vectorstore = FAISS.load_local("faiss_index", embeddings=None, allow_dangerous_deserialization=True)
        logger.info("Vectorstore loaded successfully")

        logger.info("Initializing LLM...")
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",  # Updated model name for better availability
            temperature=0.7,
            api_key=api_key,
            timeout=30,  # Add timeout to prevent hanging
            max_retries=2  # Add retry logic
        )
        logger.info("LLM initialized successfully")

        logger.info("Creating retriever...")
        retriever = vectorstore.as_retriever(search_type="similarity", k=3)

        logger.info("Creating QA chain...")
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            chain_type="stuff",
            return_source_documents=True
        )

        logger.info("Creating style chain...")
        style_chain = stoic_style_prompt | llm
        
        logger.info("QA chain initialization completed successfully")
        return generate_stoic_response
        
    except FileNotFoundError as e:
        logger.error(f"Vectorstore file not found: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during QA chain initialization: {str(e)}")
        raise

def generate_stoic_response(user_question):
    global qa_chain, style_chain

    try:
        logger.info(f"Processing question: {user_question[:50]}...")
        
        if qa_chain is None or style_chain is None:
            raise RuntimeError("QA chain not properly initialized")
        
        logger.info("Invoking QA chain...")
        result = qa_chain.invoke({"query": user_question})
        base_answer = result.get("result", "").strip()
        sources = result.get("source_documents", [])

        logger.info(f"QA chain returned {len(sources)} source documents")

        if not base_answer or not sources:
            logger.info("No relevant sources found, returning default response")
            return (
                "There is no wisdom in speaking beyond what is known. "
                "I must refrain from answering, for no record on this matter exists in the scrolls entrusted to me."
            )

        logger.info("Applying stoic styling...")
        styled = style_chain.invoke({
            "question": user_question,
            "answer": base_answer
        })

        response = styled.content if hasattr(styled, "content") else str(styled)
        logger.info("Response generated successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error generating stoic response: {str(e)}")
        # Return a fallback response in stoic style
        return (
            "The mind encounters obstacles in its pursuit of wisdom. "
            "Let us approach this matter with patience, for even difficulties teach us virtue."
        )

def test_qa_system():
    """Test function to verify the QA system works"""
    try:
        logger.info("Testing QA system...")
        qa_func = get_stoic_qa_chain()
        test_response = qa_func("What is virtue?")
        
        if test_response and len(test_response.strip()) > 0:
            logger.info("QA system test passed")
            return True
        else:
            logger.error("QA system test failed - empty response")
            return False
            
    except Exception as e:
        logger.error(f"QA system test failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Test the system when run directly
    if test_qa_system():
        print("RAG system is working correctly")
    else:
        print("RAG system test failed")