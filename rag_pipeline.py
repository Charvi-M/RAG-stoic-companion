from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os

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
        return generate_stoic_response  # Already built

    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.load_local("faiss_index", embedding_model, allow_dangerous_deserialization=True)

   
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        temperature=0.7,
        api_key=os.getenv("GEMINI_API_KEY")
    )

    retriever = vectorstore.as_retriever(search_type="similarity", k=3)

    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True
    )

    # Build the styling chain
    style_chain = stoic_style_prompt | llm

    return generate_stoic_response


# Final chain logic with stoic formatting
def generate_stoic_response(user_question):
    global qa_chain, style_chain

    result = qa_chain.invoke({"query": user_question})
    base_answer = result.get("result", "").strip()
    sources = result.get("source_documents", [])

    if not base_answer or not sources:
        return (
            "There is no wisdom in speaking beyond what is known. "
            "I must refrain from answering, for no record on this matter exists in the scrolls entrusted to me."
        )

    styled = style_chain.invoke({
        "question": user_question,
        "answer": base_answer
    })

    return styled.content if hasattr(styled, "content") else str(styled)
