# backend/test_grok_models.py
import os
import requests
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def list_grok_models():
    """List available models from Grok API"""
    api_key = os.environ.get("GROK_API_KEY")
    if not api_key:
        logger.error("GROK_API_KEY environment variable not set")
        return
        
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Error: {response.status_code}, {response.text}")
            return
            
        models = response.json()
        logger.info("Available models:")
        for model in models.get("data", []):
            logger.info(f"ID: {model.get('id')}, Created: {model.get('created')}")
            
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")

if __name__ == "__main__":
    list_grok_models()