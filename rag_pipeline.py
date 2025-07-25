from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
import os
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()


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
    
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


    db = FAISS.load_local("faiss_index", embedding_model, allow_dangerous_deserialization=True)

    retriever = db.as_retriever()

   
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        temperature=0.7,
        api_key=os.getenv("GEMINI_API_KEY"),
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True 
    )

    #Marcus Aurelius style
    style_chain = stoic_style_prompt | llm
    

    #Return both chained
    def generate_stoic_response(user_question):
        result = qa_chain.invoke({"query": user_question})
        base_answer = result["result"]
        sources = result.get("source_documents", [])
        # for i, doc in enumerate(sources):
        #     print(f"[Source {i+1}]\n{doc.page_content}\n")

    # Check if retrieval returned any sources
        if not sources or not base_answer.strip():
            return (
            "There is no wisdom in speaking beyond what is known. "
            "I must refrain from answering, for no record on this matter exists in the scrolls entrusted to me."
        )

        styled_answer = style_chain.invoke({
        "question": user_question,
        "answer": base_answer
        })

        return styled_answer.content if hasattr(styled_answer, "content") else str(styled_answer)


    return generate_stoic_response
