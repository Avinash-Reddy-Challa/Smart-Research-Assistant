# backend/app/config.py
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Get the Grok API key
GROK_API_KEY = os.environ.get("GROK_API_KEY")
if not GROK_API_KEY:
    logger.warning("GROK_API_KEY environment variable is not set. ")