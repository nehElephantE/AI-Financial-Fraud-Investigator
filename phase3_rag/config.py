import os
from dotenv import load_dotenv

load_dotenv()

# Database - Use Railway's MySQL variables
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', os.getenv('DB_HOST', 'mysql')),
    'port': os.getenv('MYSQL_PORT', os.getenv('DB_PORT', '3306')),
    'database': os.getenv('MYSQL_DATABASE', os.getenv('DB_NAME', 'fraud_db')),
    'user': os.getenv('MYSQL_USER', os.getenv('DB_USER', 'fraud_user')),
    'password': os.getenv('MYSQL_PASSWORD', os.getenv('DB_PASSWORD', 'fraud123'))
}

print(f"DB Config: Host={DB_CONFIG['host']}, Database={DB_CONFIG['database']}, User={DB_CONFIG['user']}")

# LLM Configuration - Use template mode for Docker (faster)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
USE_LOCAL_LLM = os.getenv('USE_LOCAL_LLM', 'false').lower() == 'true'
LOCAL_LLM_PATH = os.getenv('LOCAL_LLM_PATH', 'models/phi-2.Q4_K_M.gguf')

# Embeddings
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
CHROMA_PERSIST_DIR = os.getenv('CHROMA_PERSIST_DIR', './chroma_db')

# Paths
MODEL_PATH = 'models/'
os.makedirs(MODEL_PATH, exist_ok=True)