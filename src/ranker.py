# ============================================================
# DOCUMENT RANKING
# ============================================================

def rank_documents(
    documents_with_scores
):

    # FAISS already returns documents
    # ordered by similarity/distance.

    ranked = sorted(
        documents_with_scores,
        key=lambda item: item[1]
    )

    return ranked