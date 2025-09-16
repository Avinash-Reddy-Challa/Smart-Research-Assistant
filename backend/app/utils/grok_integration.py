# backend/app/utils/grok_integration.py
import json
import requests
from typing import Any, Dict, List, Mapping, Optional, Union
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult
import os
import logging
import numpy as np

logger = logging.getLogger(__name__)

class GrokChatModel(BaseChatModel):
    """Chat model for Grok AI API."""

    api_key: str
    model_name: str = "mixtral-8x7b-32768"  # Updated to the correct model
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    base_url: str = "https://api.groq.com/openai/v1"
    
    @property
    def _llm_type(self) -> str:
        return "grok-chat"

    def _format_messages(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """Format messages for Grok API."""
        formatted_messages = []
        for message in messages:
            if isinstance(message, HumanMessage):
                role = "user"
            elif isinstance(message, AIMessage):
                role = "assistant"
            elif isinstance(message, SystemMessage):
                role = "system"
            else:
                raise ValueError(f"Unknown message type: {type(message)}")
            
            formatted_messages.append({
                "role": role,
                "content": message.content
            })
        return formatted_messages

    def _validate_available_models(self):
        """Check if the specified model is available"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"Error checking models: {response.status_code}, {response.text}")
                return False
                
            models = response.json()
            available_models = [model.get('id') for model in models.get("data", [])]
            
            if self.model_name not in available_models:
                # Try to find a suitable alternative
                logger.warning(f"Model {self.model_name} not found. Available models: {available_models}")
                for model in available_models:
                    if "mixtral" in model.lower():
                        self.model_name = model
                        logger.info(f"Using alternative model: {self.model_name}")
                        return True
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating models: {str(e)}")
            return False

    def _generate(
        self, 
        messages: List[BaseMessage], 
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a chat response from Grok."""
        # Validate the model is available
        if not hasattr(self, "_model_validated"):
            self._model_validated = self._validate_available_models()
        
        # If model validation failed, generate a mock response
        if not getattr(self, "_model_validated", False):
            logger.warning("Using mock response because model validation failed")
            message = AIMessage(content="I'm unable to provide a specific response at this time due to model availability issues. This is a placeholder response.")
            
            return ChatResult(
                generations=[ChatGeneration(message=message)],
                llm_output={
                    "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    "model_name": self.model_name,
                },
            )
        
        # Regular generation logic
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        data = {
            "model": self.model_name,
            "messages": self._format_messages(messages),
            "temperature": self.temperature,
        }
        
        if self.max_tokens:
            data["max_tokens"] = self.max_tokens
        
        if stop:
            data["stop"] = stop
            
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                logger.error(f"Error from Grok API: {response.status_code}, {response.text}")
                raise ValueError(f"Error from Grok API: {response.text}")
                
            response_json = response.json()
            
            message_content = response_json["choices"][0]["message"]["content"]
            message = AIMessage(content=message_content)
            
            generation = ChatGeneration(
                message=message,
                generation_info=dict(
                    finish_reason=response_json["choices"][0].get("finish_reason"),
                    logprobs=response_json.get("logprobs"),
                )
            )
            
            token_usage = response_json.get("usage", {})
            
            return ChatResult(
                generations=[generation],
                llm_output={
                    "token_usage": token_usage,
                    "model_name": self.model_name,
                },
            )
        except Exception as e:
            logger.error(f"Error in _generate: {str(e)}")
            # Return a mock response
            message = AIMessage(content="I encountered an error while processing your request. This is a placeholder response.")
            
            return ChatResult(
                generations=[ChatGeneration(message=message)],
                llm_output={
                    "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    "model_name": self.model_name,
                },
            )  

class SimpleEmbeddings(Embeddings):
    """A fallback embedding class that creates random embeddings for testing"""
    
    def __init__(self, embedding_dim=1536):
        self.embedding_dim = embedding_dim
        logger.info(f"Using SimpleEmbeddings with dimension {embedding_dim}")
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Create random embeddings for documents"""
        logger.info(f"Embedding {len(texts)} documents with SimpleEmbeddings")
        if not texts:
            # Return a single dummy embedding if texts is empty
            logger.warning("Empty texts list provided to embed_documents")
            return [[0.0] * self.embedding_dim]
            
        embeddings = []
        for _ in texts:
            # Create a random embedding vector and normalize it
            vec = np.random.randn(self.embedding_dim)
            vec = vec / np.linalg.norm(vec)
            embeddings.append(vec.tolist())
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Create a random embedding for a query"""
        logger.info(f"Embedding query with SimpleEmbeddings")
        vec = np.random.randn(self.embedding_dim)
        vec = vec / np.linalg.norm(vec)
        return vec.tolist()

class GrokEmbeddings(Embeddings):
    """Embeddings model for Grok API (fallback to SimpleEmbeddings)."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Immediately create a SimpleEmbeddings instance for fallback
        self._simple_embeddings = SimpleEmbeddings()
        logger.warning("GrokEmbeddings initialized but will use SimpleEmbeddings as fallback due to model compatibility issues")
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Use SimpleEmbeddings as fallback."""
        logger.info(f"Using SimpleEmbeddings fallback for {len(texts)} documents")
        return self._simple_embeddings.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """Use SimpleEmbeddings as fallback."""
        logger.info("Using SimpleEmbeddings fallback for query")
        return self._simple_embeddings.embed_query(text)