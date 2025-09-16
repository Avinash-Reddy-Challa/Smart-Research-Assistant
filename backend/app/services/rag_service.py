# backend/app/services/rag_service.py
import os
import logging
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from app.services.document_processor import document_processor
from app.utils.grok_integration import GrokChatModel


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        try:
            # Try to use Grok chat model
            self.llm = GrokChatModel(
                api_key=os.environ.get("GROK_API_KEY"),
                model_name="llama-3.1-8b-instant",  # Updated to a model likely available
                temperature=0.1
            )
            logger.info("Using GrokChatModel")
        except Exception as e:
            logger.error(f"Failed to initialize GrokChatModel: {str(e)}")
            # No fallback needed as GrokChatModel has its own internal fallback
            
        self.qa_prompt_template = """
        You are a helpful AI research assistant. Use the following pieces of context to answer the question at the end.
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        Keep the answer concise and accurate. Only provide information that is directly supported by the context.
        
        Context:
        {context}
        
        Question: {question}
        
        Answer:
        """
    
    def get_answer(self, question, include_sources=True):
        """Generate an answer for the given question using RAG"""
        # Get relevant documents
        logger.info(f"Getting relevant documents for: {question}")
        relevant_docs = document_processor.get_relevant_documents(question)
        
        if not relevant_docs:
            logger.warning("No relevant documents found")
            return {
                "answer": "I don't have enough information to answer that question. Please upload relevant documents first.",
                "sources": []
            }
        
        # Format context for the prompt
        context_text = "\n\n".join([doc.page_content for doc in relevant_docs])
        logger.info(f"Found {len(relevant_docs)} relevant documents")
        
        # Try to use the LLM chain, but provide fallbacks
        try:
            # Create prompt
            prompt = PromptTemplate(
                template=self.qa_prompt_template,
                input_variables=["context", "question"]
            )
            
            # Create chain
            chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=document_processor.vector_store.as_retriever(),
                chain_type_kwargs={"prompt": prompt}
            )
            
            # Get answer
            logger.info("Invoking LLM chain")
            result = chain.invoke({"query": question})
            answer = result["result"]
            logger.info("Got answer from LLM")
        except Exception as e:
            logger.error(f"Error in RAG chain: {str(e)}", exc_info=True)
            
            # Create a more helpful fallback response based on the documents
            snippets = [doc.page_content[:150] + "..." for doc in relevant_docs[:2]]
            doc_names = list(set([doc.metadata.get("source", "Unknown") for doc in relevant_docs]))
            
            if "summarize" in question.lower():
                answer = f"Here's a summary based on the document(s): {', '.join(doc_names)}\n\n"
                answer += "• The document contains information that would be summarized here.\n"
                answer += "• This is a placeholder summary because the AI model couldn't process the request.\n"
                answer += f"• Some content from the document: \"{snippets[0]}\"\n"
            else:
                answer = f"Based on the document(s): {', '.join(doc_names)}\n\n"
                answer += f"I found information related to your question, but couldn't process it fully. Here are some relevant excerpts:\n\n"
                for i, snippet in enumerate(snippets):
                    answer += f"{i+1}. {snippet}\n\n"
                answer += "Try asking a more specific question about this content."
        
        # Format sources if requested
        sources = []
        if include_sources:
            seen_sources = set()
            for doc in relevant_docs:
                source = doc.metadata.get("source", "Unknown")
                page = doc.metadata.get("page", 0)
                source_key = f"{source}-{page}"
                if source_key not in seen_sources:
                    sources.append({
                        "source": source,
                        "page": page,
                        "snippet": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                    })
                    seen_sources.add(source_key)
        
        return {
            "answer": answer,
            "sources": sources
        }
    
# Create a singleton instance
rag_service = RAGService()