from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from config import (
    VECTORSTORE_DIR,
    EMBEDDING_MODEL,
    TOP_K,
)

from query_processor import (
    expand_query,
    detect_crop,
)


# ============================================================
# EMBEDDINGS
# ============================================================

@lru_cache(maxsize=1)
def get_embeddings():

    print()
    print("=" * 60)
    print("LOADING EMBEDDING MODEL")
    print("=" * 60)
    print(
        f"Embedding model: {EMBEDDING_MODEL}"
    )

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={
            "device": "cpu"
        },
        encode_kwargs={
            "normalize_embeddings": True
        },
    )

    print("Embedding model loaded successfully.")

    return embeddings


# ============================================================
# LOAD VECTOR DATABASE
# ============================================================

@lru_cache(maxsize=1)
def load_vectorstore():

    print()
    print("=" * 60)
    print("LOADING FAISS VECTOR DATABASE")
    print("=" * 60)
    print(
        f"Vectorstore: {VECTORSTORE_DIR}"
    )

    embeddings = get_embeddings()

    vectorstore = FAISS.load_local(
        str(VECTORSTORE_DIR),
        embeddings,
        allow_dangerous_deserialization=True
    )

    print("FAISS vector database loaded successfully.")

    return vectorstore


# ============================================================
# CROP KEYWORDS
# ============================================================

CROP_KEYWORDS = {

    "soybean": [

        "soybean",
        "soyabean",
        "soy",
        "सोयाबीन",
        "सोयाबीन",
        "सॉयाबीन",
        "सोयाबीनचे",
        "सोयाबीनची",

    ],

    "cotton": [

        "cotton",
        "kapas",
        "कापूस",
        "कापसाचे",
        "कापसाची",
        "कपास",

    ],

    "tomato": [

        "tomato",
        "टमाटर",
        "टोमॅटो",
        "टोमॅटोचे",
        "टोमॅटोची",

    ],

    "onion": [

        "onion",
        "कांदा",
        "कांद्याचे",
        "कांद्याची",
        "प्याज",
        "प्याज़",

    ],

}


# ============================================================
# DETECT CROP IN DOCUMENT
# ============================================================

def document_matches_crop(
    document,
    crop
):

    if not crop:

        return False

    text = (

        document.page_content
        + " "
        + str(
            document.metadata
        )

    ).lower()

    keywords = CROP_KEYWORDS.get(
        crop,
        []
    )

    for keyword in keywords:

        if keyword.lower() in text:

            return True

    return False


# ============================================================
# RETRIEVE DOCUMENTS
# ============================================================

def retrieve_documents(
    query,
    k=10
):

    # --------------------------------------------------------
    # LOAD CACHED VECTOR DATABASE
    # --------------------------------------------------------

    vectorstore = load_vectorstore()

    # --------------------------------------------------------
    # DETECT CROP
    # --------------------------------------------------------

    crop = detect_crop(
        query
    )

    # --------------------------------------------------------
    # EXPAND QUERY
    # --------------------------------------------------------

    expanded_query = expand_query(
        query
    )

    print()
    print("=" * 60)
    print("AGRICULTURAL RETRIEVAL")
    print("=" * 60)

    print(
        f"Original query: {query}"
    )

    print(
        f"Expanded query: {expanded_query}"
    )

    if crop:

        print(
            f"🌱 Detected crop: {crop}"
        )

    else:

        print(
            "🌱 Crop: not explicitly detected"
        )

    print(
        "🔎 Searching agricultural knowledge base..."
    )

    # --------------------------------------------------------
    # RETRIEVE MORE DOCUMENTS THAN REQUIRED
    #
    # We retrieve 20 candidates first so that the
    # crop-aware reranking has enough documents to work with.
    # --------------------------------------------------------

    results = (
        vectorstore
        .similarity_search_with_score(
            expanded_query,
            k=20
        )
    )

    print(
        f"Retrieved candidates: {len(results)}"
    )

    # --------------------------------------------------------
    # CROP-AWARE RERANKING
    # --------------------------------------------------------

    if crop:

        crop_results = []

        other_results = []

        for document, score in results:

            if document_matches_crop(
                document,
                crop
            ):

                crop_results.append(
                    (
                        document,
                        score
                    )
                )

            else:

                other_results.append(
                    (
                        document,
                        score
                    )
                )

        # ----------------------------------------------------
        # Crop-specific documents receive priority.
        # ----------------------------------------------------

        results = (

            crop_results
            +
            other_results

        )

        print(
            f"Crop-specific matches: "
            f"{len(crop_results)}"
        )

    # --------------------------------------------------------
    # RETURN TOP K
    # --------------------------------------------------------

    final_results = results[:k]

    print(
        f"Returning top {len(final_results)} documents."
    )

    print(
        "=" * 60
    )

    return final_results