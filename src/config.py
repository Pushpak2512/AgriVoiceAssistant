from pathlib import Path
import os
import warnings

from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# REDUCE NON-CRITICAL HUGGING FACE WARNINGS
# ============================================================

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

warnings.filterwarnings(
    "ignore",
    message="You are sending unauthenticated requests to the HF Hub.*"
)


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

VECTORSTORE_DIR = BASE_DIR / "vectorstore"


# ============================================================
# GROQ
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

LLM_MODEL = "openai/gpt-oss-120b"


# ============================================================
# MULTILINGUAL EMBEDDING MODEL
# ============================================================

EMBEDDING_MODEL = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)


# ============================================================
# RAG PARAMETERS
# ============================================================

CHUNK_SIZE = 800

CHUNK_OVERLAP = 150

TOP_K = 5