import os
from dotenv import load_dotenv

load_dotenv()

# AWS / Bedrock
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v1"
LLM_MODEL_ID = "amazon.titan-text-express-v1"

# Chunking
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

# Retrieval
RETRIEVER_K = 5

# Paths
INDEXES_DIR = "indexes"
DATA_DIR = "data"
