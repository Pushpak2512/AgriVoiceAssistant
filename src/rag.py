from langchain_groq import ChatGroq

from config import GROQ_API_KEY, LLM_MODEL
from retriever import retrieve_documents


# ============================================================
# GROQ LLM
# ============================================================

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=LLM_MODEL,
    temperature=0,
)


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are a responsible agricultural advisory assistant.

SAFETY RULE:

Use ONLY information supported by the retrieved
agricultural documents.

Never invent agricultural recommendations.

Do not transfer a recommendation from one crop to another
unless the retrieved document explicitly supports doing so.

Do not invent pesticide names, pesticide doses, fertilizer
doses, irrigation quantities, timings, or disease treatments.

If the documents do not contain crop-specific information,
say that clearly.

IMPORTANT RESPONSE FORMAT:

Give a SHORT farmer-friendly answer.

Maximum 4 short bullet points.

Do not create large tables.

Do not repeat the source document contents.

After the useful recommendations, add one short limitation
sentence if necessary.

Answer in the same language as the farmer's question.
"""


# ============================================================
# BUILD RETRIEVED CONTEXT
# ============================================================

def build_context(results):

    context_parts = []

    sources = []

    for doc, score in results:

        source_file = doc.metadata.get(
            "source_file",
            "Unknown"
        )

        page = doc.metadata.get(
            "page_number",
            "Unknown"
        )

        content = doc.page_content.strip()

        context_parts.append(
            f"""
SOURCE: {source_file}
PAGE: {page}

{content}
"""
        )

        sources.append(
            {
                "file": source_file,
                "page": page,
                "score": float(score)
            }
        )

    return "\n\n".join(context_parts), sources


# ============================================================
# STREAMING RAG
# ============================================================

def stream_agri_assistant(question):

    results = retrieve_documents(
        question,
        k=6
    )

    if not results:

        yield {
            "type": "token",
            "text": (
                "I could not find relevant information "
                "in the verified agricultural sources."
            )
        }

        yield {
            "type": "sources",
            "sources": []
        }

        return

    context, sources = build_context(
        results
    )

    prompt = f"""
{SYSTEM_PROMPT}

VERIFIED AGRICULTURAL SOURCES:

{context}

==================================================

FARMER QUESTION:

{question}

==================================================

Answer the farmer using ONLY the verified information above.

Keep the response concise.

Maximum 4 short bullet points.

Do not use a table.
"""

    # --------------------------------------------------------
    # STREAM LLM RESPONSE
    # --------------------------------------------------------

    for chunk in llm.stream(prompt):

        text = chunk.content

        if text:

            yield {
                "type": "token",
                "text": text
            }

    # --------------------------------------------------------
    # SOURCES AFTER RESPONSE
    # --------------------------------------------------------

    yield {
        "type": "sources",
        "sources": sources
    }


# ============================================================
# NON-STREAMING VERSION
# ============================================================

def ask_agri_assistant(question):

    answer_parts = []

    sources = []

    for item in stream_agri_assistant(question):

        if item["type"] == "token":

            answer_parts.append(
                item["text"]
            )

        elif item["type"] == "sources":

            sources = item["sources"]

    return {
        "answer": "".join(answer_parts),
        "sources": sources
    }