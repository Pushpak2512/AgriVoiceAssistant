from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from config import (
    DATA_DIR,
    VECTORSTORE_DIR,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)


# ============================================================
# FIND ALL PDF FILES
# ============================================================

def find_pdf_files():

    pdf_files = list(DATA_DIR.rglob("*.pdf"))

    return pdf_files


# ============================================================
# LOAD PDF DOCUMENTS
# ============================================================

def load_documents():

    documents = []

    pdf_files = find_pdf_files()

    print()
    print("=" * 60)
    print("LOADING AGRICULTURAL DOCUMENTS")
    print("=" * 60)

    if not pdf_files:

        print("No PDF files found.")
        return documents

    for pdf_path in pdf_files:

        print()
        print(f"Loading: {pdf_path}")

        try:

            loader = PyPDFLoader(str(pdf_path))

            docs = loader.load()

            # ------------------------------------------------
            # Add useful metadata
            # ------------------------------------------------

            for doc in docs:

                relative_path = pdf_path.relative_to(DATA_DIR)

                parts = relative_path.parts

                doc.metadata["source_file"] = pdf_path.name

                doc.metadata["source_path"] = str(relative_path)

                doc.metadata["source_type"] = (
                    parts[0] if len(parts) > 0 else "unknown"
                )

                if len(parts) > 1:
                    doc.metadata["category"] = parts[1]
                else:
                    doc.metadata["category"] = "general"

                if len(parts) > 2:
                    doc.metadata["crop"] = parts[2]
                else:
                    doc.metadata["crop"] = "multi_crop"

                doc.metadata["page_number"] = (
                    doc.metadata.get("page", 0) + 1
                )

            documents.extend(docs)

            print(f"Pages loaded: {len(docs)}")

        except Exception as e:

            print(f"ERROR loading {pdf_path}")
            print(e)

    print()
    print("=" * 60)
    print(f"TOTAL DOCUMENT PAGES LOADED: {len(documents)}")
    print("=" * 60)

    return documents


# ============================================================
# SPLIT DOCUMENTS
# ============================================================

def split_documents(documents):

    print()
    print("Splitting documents into chunks...")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=[
            "\n\n",
            "\n",
            "।",
            ".",
            " ",
        ],
    )

    chunks = splitter.split_documents(documents)

    print(f"TOTAL CHUNKS CREATED: {len(chunks)}")

    return chunks


# ============================================================
# CREATE VECTOR DATABASE
# ============================================================

def create_vectorstore(chunks):

    print()
    print("Creating multilingual embeddings...")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={
            "device": "cpu"
        },
        encode_kwargs={
            "normalize_embeddings": True
        },
    )

    print("Creating FAISS vector database...")

    vectorstore = FAISS.from_documents(
        chunks,
        embeddings
    )

    VECTORSTORE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    vectorstore.save_local(
        str(VECTORSTORE_DIR)
    )

    print()
    print("=" * 60)
    print("VECTOR DATABASE CREATED SUCCESSFULLY")
    print("=" * 60)
    print(f"Location: {VECTORSTORE_DIR}")
    print(f"Vectors: {len(chunks)}")
    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    documents = load_documents()

    if not documents:

        print("No documents available.")
        print("Please add PDF files inside data/")
        raise SystemExit(1)

    chunks = split_documents(documents)

    if not chunks:

        print("No chunks were created.")
        raise SystemExit(1)

    create_vectorstore(chunks)