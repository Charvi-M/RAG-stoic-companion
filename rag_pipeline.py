from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Globals
vectorstore = None
llm = None
retrieval_qa_chain = None
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

        logger.info("Loading embedding model for query-time inference...")
        embedding_model = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L12-v1",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )

        logger.info("Loading vectorstore...")
        vectorstore = FAISS.load_local(
            "faiss_index",
            embeddings=embedding_model,
            allow_dangerous_deserialization=True
        )
        logger.info("Vectorstore loaded successfully")

        logger.info("Initializing LLM...")
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0.7,
            api_key=api_key,
            timeout=30,
            max_retries=2
        )
        logger.info("LLM initialized successfully")

        logger.info("Creating retriever...")
        retriever = vectorstore.as_retriever(search_type="similarity", k=3)

        logger.info("Creating QA chain...")
        retrieval_qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            chain_type="stuff",
            return_source_documents=True
        )

        logger.info("Creating style chain...")
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
        logger.info(f"Processing question: {user_question[:50]}...")

        if retrieval_qa_chain is None or style_chain is None:
            raise RuntimeError("QA chain not properly initialized")

        logger.info("Invoking QA chain...")
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

        logger.info("Sources used:")
        for i, doc in enumerate(sources, 1):
            logger.info(f"[{i}] {doc.metadata.get('source', 'Unknown')} - {doc.page_content[:200].strip()}...")

        logger.info("Applying stoic styling...")
        styled = style_chain.invoke({
            "question": user_question,
            "answer": base_answer
        })

        styled_response = styled.content if hasattr(styled, "content") else str(styled)

        sources_info = "\n\n---\nSources consulted:\n" + "\n".join(
            f"- {doc.metadata.get('source', 'Unknown')}" for doc in sources
        )

        return styled_response + sources_info

    except Exception as e:
        logger.error(f"Error generating stoic response: {str(e)}")
        traceback.print_exc()
        return (
            "The mind encounters obstacles in its pursuit of wisdom. "
            "Let us approach this matter with patience, for even difficulties teach us virtue."
        )


def test_qa_system():
    """Test function to verify the QA system works"""
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
