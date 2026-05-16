import os
from dotenv import load_dotenv

load_dotenv()

# Database - Use environment variables for Docker
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'mysql'),
    'port': os.getenv('DB_PORT', '3306'),
    'database': os.getenv('DB_NAME', 'fraud_db'),
    'user': os.getenv('DB_USER', 'fraud_user'),
    'password': os.getenv('DB_PASSWORD', 'fraud123')
}

# LLM Configuration - Use template mode for Docker (faster)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
USE_LOCAL_LLM = os.getenv('USE_LOCAL_LLM', 'false').lower() == 'true'  # Default to false for Docker
LOCAL_LLM_PATH = os.getenv('LOCAL_LLM_PATH', 'models/phi-2.Q4_K_M.gguf')

# Embeddings
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
CHROMA_PERSIST_DIR = os.getenv('CHROMA_PERSIST_DIR', './chroma_db')

# Paths
MODEL_PATH = 'models/'
os.makedirs(MODEL_PATH, exist_ok=True)