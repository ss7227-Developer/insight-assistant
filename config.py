import os
from dotenv import load_dotenv

load_dotenv()

# Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Chunking
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

# Retrieval
RETRIEVER_K = 5

# Paths
INDEXES_DIR = "indexes"
DATA_DIR = "data"
