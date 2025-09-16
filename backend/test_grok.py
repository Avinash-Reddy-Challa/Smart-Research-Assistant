# backend/test_grok.py
import os
from dotenv import load_dotenv
from app.utils.grok_integration import GrokChatModel, GrokEmbeddings

# Load environment variables
load_dotenv()

# Test chat model
def test_chat():
    chat_model = GrokChatModel(
        api_key=os.environ.get("GROK_API_KEY"),
        temperature=0.7
    )
    
    from langchain_core.messages import HumanMessage, SystemMessage
    
    messages = [
        SystemMessage(content="You are a helpful AI assistant."),
        HumanMessage(content="Hello, how are you?")
    ]
    
    response = chat_model.invoke(messages)
    print("Chat Response:", response.content)

# Test embeddings
def test_embeddings():
    embedding_model = GrokEmbeddings(api_key=os.environ.get("GROK_API_KEY"))
    
    texts = ["This is a test document."]
    embeddings = embedding_model.embed_documents(texts)
    
    print(f"Embedding dimensions: {len(embeddings[0])}")
    print(f"First few values: {embeddings[0][:5]}")

if __name__ == "__main__":
    print("Testing Grok Chat model...")
    test_chat()
    
    print("\nTesting Grok Embeddings...")
    test_embeddings()