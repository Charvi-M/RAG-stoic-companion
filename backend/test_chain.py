from rag_pipeline import get_stoic_qa_chain

qa_chain = get_stoic_qa_chain()

query = "I'm anxious"
response = qa_chain(query)

print("\nSTOIC RESPONSE:\n")
print(response)
