import os
import sys
import re
import html

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from groq import Groq


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

SRC_DIR = os.path.join(
    PROJECT_ROOT,
    "src"
)

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(
    os.path.join(
        PROJECT_ROOT,
        ".env"
    )
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Agri Voice Assistant",
    page_icon="🌾",
    layout="centered",
    initial_sidebar_state="collapsed"
)


# ============================================================
# API
# ============================================================

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

if not GROQ_API_KEY:

    st.error(
        "GROQ_API_KEY is not configured."
    )

    st.stop()


groq_client = Groq(
    api_key=GROQ_API_KEY
)


# ============================================================
# EXISTING RAG
# ============================================================

try:

    from rag import ask_agri_assistant

except Exception as error:

    st.error(
        "The agricultural RAG backend could not be loaded."
    )

    with st.expander(
        "Technical details"
    ):

        st.code(
            str(error)
        )

    st.stop()


# ============================================================
# SESSION STATE
# ============================================================

if "language" not in st.session_state:
    st.session_state.language = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "processed_audio" not in st.session_state:
    st.session_state.processed_audio = None


# ============================================================
# LANGUAGE CONFIGURATION
# ============================================================

LANGUAGES = {

    "English": {
        "whisper": "en",
        "speech": "en-IN",
        "instruction":
            "Answer the farmer in English.",
        "placeholder":
            "Ask your agricultural question..."
    },

    "Hindi": {
        "whisper": "hi",
        "speech": "hi-IN",
        "instruction":
            "उत्तर हिंदी भाषा में और देवनागरी लिपि में दें।",
        "placeholder":
            "अपना कृषि प्रश्न पूछें..."
    },

    "Marathi": {
        "whisper": "mr",
        "speech": "mr-IN",
        "instruction":
            "उत्तर मराठी भाषेत आणि देवनागरी लिपीत द्या.",
        "placeholder":
            "तुमचा कृषी प्रश्न विचारा..."
    }
}


# ============================================================
# MINIMAL UI CSS
# ============================================================

st.markdown(
    """
<style>

.block-container {
    max-width: 850px;
    padding-top: 2.5rem;
    padding-bottom: 4rem;
}

.main-title {
    text-align: center;
    font-size: 32px;
    font-weight: 750;
    margin-bottom: 4px;
}

.subtitle {
    text-align: center;
    opacity: 0.70;
    margin-bottom: 28px;
}

.language-box {
    text-align: center;
    margin-bottom: 24px;
}

.answer {
    font-size: 16px;
    line-height: 1.75;
}

.source {
    font-size: 13px;
    opacity: 0.75;
    padding: 6px 0;
}

div[data-testid="stChatInput"] {
    border-radius: 18px;
}

button {
    border-radius: 10px !important;
}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">'
    '🌾 Agri Voice Assistant'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'AI-powered multilingual agricultural advisory'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# LANGUAGE SELECTION
# ============================================================

if st.session_state.language is None:

    st.markdown(
        '<div class="language-box">'
        '<b>Choose your preferred language</b>'
        '</div>',
        unsafe_allow_html=True
    )

    language = st.radio(
        "Language",
        [
            "English",
            "Hindi",
            "Marathi"
        ],
        horizontal=True,
        label_visibility="collapsed"
    )

    st.write("")

    if st.button(
        "Continue",
        type="primary",
        use_container_width=True
    ):

        st.session_state.language = language

        st.session_state.messages = []

        st.rerun()

    st.stop()


# ============================================================
# CURRENT LANGUAGE
# ============================================================

language = st.session_state.language

language_config = LANGUAGES[
    language
]


# ============================================================
# NEW CHAT
# ============================================================

top_left, top_right = st.columns(
    [5, 1]
)

with top_left:

    st.caption(
        f"🌐 {language}"
    )

with top_right:

    if st.button(
        "New",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.session_state.processed_audio = None

        st.rerun()


# ============================================================
# CLEAN ANSWER
# ============================================================

def clean_answer(
    value
):

    if value is None:

        return ""

    text = str(
        value
    ).strip()

    # Remove code fences
    text = re.sub(
        r"```.*?```",
        "",
        text,
        flags=re.DOTALL
    )

    # Remove bold
    text = re.sub(
        r"\*\*(.*?)\*\*",
        r"\1",
        text,
        flags=re.DOTALL
    )

    # Remove italic
    text = re.sub(
        r"\*(.*?)\*",
        r"\1",
        text,
        flags=re.DOTALL
    )

    # Remove markdown headings
    text = re.sub(
        r"(?m)^\s*#+\s*",
        "",
        text
    )

    # Convert markdown bullets
    text = re.sub(
        r"(?m)^\s*[-*]\s*",
        "• ",
        text
    )

    # Remove backticks
    text = text.replace(
        "`",
        ""
    )

    # Remove excessive blank lines
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


# ============================================================
# EXTRACT RAG RESULT
# ============================================================

def extract_result(
    result
):

    if isinstance(
        result,
        dict
    ):

        answer = result.get(
            "answer",
            ""
        )

        sources = result.get(
            "sources",
            []
        )

        return (
            clean_answer(answer),
            sources
        )

    return (
        clean_answer(result),
        []
    )


# ============================================================
# SPEECH CLEANING
# ============================================================

def speech_text(
    text
):

    text = clean_answer(
        text
    )

    # Remove URLs
    text = re.sub(
        r"https?://\S+",
        "",
        text
    )

    # Turn bullets into natural pauses
    text = text.replace(
        "•",
        ". "
    )

    # Remove symbols that TTS should never read
    for symbol in [
        "*",
        "#",
        "`",
        "_",
        "|",
        "~"
    ]:

        text = text.replace(
            symbol,
            ""
        )

    # Remove common UI emojis
    text = re.sub(
        r"[🌾🎤🔊📚⚠️✅❌⭐👉📌]",
        "",
        text
    )

    # Normalize spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# SPEAK ANSWER
# ============================================================

def speak(
    text
):

    text = speech_text(
        text
    )

    if not text:
        return

    # Escape JavaScript template characters
    text = (
        text
        .replace(
            "\\",
            "\\\\"
        )
        .replace(
            "`",
            "\\`"
        )
        .replace(
            "\n",
            " "
        )
    )

    speech_language = (
        language_config["speech"]
    )

    components.html(
        f"""
<script>

const text = `{text}`;

const targetLanguage =
    `{speech_language}`;

function speakAnswer() {{

    window.speechSynthesis.cancel();

    const voices =
        window.speechSynthesis.getVoices();

    let voice = voices.find(
        v =>
            v.lang.toLowerCase()
            === targetLanguage.toLowerCase()
    );

    if (!voice) {{

        const prefix =
            targetLanguage
            .split("-")[0]
            .toLowerCase();

        voice = voices.find(
            v =>
                v.lang
                 .toLowerCase()
                 .startsWith(prefix)
        );

    }}

    const utterance =
        new SpeechSynthesisUtterance(
            text
        );

    utterance.lang =
        targetLanguage;

    utterance.rate =
        0.95;

    utterance.pitch =
        1.0;

    if (voice) {{

        utterance.voice =
            voice;

    }}

    window.speechSynthesis.speak(
        utterance
    );
}}

if (
    window.speechSynthesis
        .getVoices()
        .length === 0
) {{

    window.speechSynthesis.onvoiceschanged =
        speakAnswer;

}} else {{

    speakAnswer();

}}

</script>
""",
        height=1
    )


# ============================================================
# DISPLAY SOURCES
# ============================================================

def show_sources(
    sources
):

    if not sources:
        return

    with st.expander(
        "📚 Sources"
    ):

        seen = set()

        for source in sources:

            if not isinstance(
                source,
                dict
            ):
                continue

            filename = source.get(
                "file",
                "Agricultural document"
            )

            page = source.get(
                "page"
            )

            key = (
                filename,
                page
            )

            if key in seen:
                continue

            seen.add(key)

            if page:

                st.markdown(
                    f'<div class="source">'
                    f'📄 {html.escape(str(filename))}'
                    f' — Page {page}'
                    f'</div>',
                    unsafe_allow_html=True
                )

            else:

                st.markdown(
                    f'<div class="source">'
                    f'📄 {html.escape(str(filename))}'
                    f'</div>',
                    unsafe_allow_html=True
                )


# ============================================================
# ASK RAG
# ============================================================

def ask_rag(
    question
):

    # Keep the actual farmer query clean for retrieval.
    #
    # Language instruction is appended only for the
    # final answer generation.

    language_instruction = (

        "\n\n"
        "ANSWER LANGUAGE REQUIREMENT:\n"
        + language_config["instruction"]
        + "\n"
        "Use simple farmer-friendly language.\n"
        "Do not answer in another language.\n"
        "Do not use Markdown symbols.\n"
        "Do not use *, **, #, backticks or code blocks."
    )

    query = (
        question
        + language_instruction
    )

    result = ask_agri_assistant(
        query
    )

    return extract_result(
        result
    )


# ============================================================
# VOICE TRANSCRIPTION
# ============================================================

def transcribe(
    audio
):

    result = (
        groq_client
        .audio
        .transcriptions
        .create(
            file=(
                "farmer_audio.wav",
                audio.getvalue()
            ),
            model="whisper-large-v3-turbo",
            language=language_config["whisper"],
            response_format="json",
            temperature=0
        )
    )

    return result.text.strip()


# ============================================================
# PROCESS QUESTION
# ============================================================

def process_question(
    question
):

    question = question.strip()

    if not question:
        return

    # --------------------------------------------------------
    # FARMER MESSAGE
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    with st.chat_message(
        "user",
        avatar="👨‍🌾"
    ):

        st.write(
            question
        )

    # --------------------------------------------------------
    # AI RESPONSE
    # --------------------------------------------------------

    with st.chat_message(
        "assistant",
        avatar="🌾"
    ):

        try:

            with st.spinner(
                "🌾 Thinking..."
            ):

                answer, sources = ask_rag(
                    question
                )

            if not answer:

                raise RuntimeError(
                    "RAG returned an empty answer."
                )

            st.markdown(
                f'<div class="answer">'
                f'{html.escape(answer).replace(chr(10), "<br>")}'
                f'</div>',
                unsafe_allow_html=True
            )

            show_sources(
                sources
            )

            speak(
                answer
            )

        except Exception as error:

            if language == "Marathi":

                friendly_error = (
                    "माफ करा, तुमचा कृषी प्रश्न "
                    "प्रक्रिया करता आला नाही. "
                    "कृपया पुन्हा प्रयत्न करा."
                )

            elif language == "Hindi":

                friendly_error = (
                    "माफ कीजिए, आपके कृषि प्रश्न को "
                    "प्रक्रिया नहीं किया जा सका। "
                    "कृपया फिर से प्रयास करें।"
                )

            else:

                friendly_error = (
                    "Sorry, I could not process "
                    "your agricultural question. "
                    "Please try again."
                )

            st.error(
                friendly_error
            )

            with st.expander(
                "Technical details"
            ):

                st.code(
                    str(error)
                )

            answer = friendly_error

            sources = []

    # --------------------------------------------------------
    # SAVE ASSISTANT MESSAGE
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": sources
        }
    )


# ============================================================
# CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    if message["role"] == "user":

        with st.chat_message(
            "user",
            avatar="👨‍🌾"
        ):

            st.write(
                message["content"]
            )

    else:

        with st.chat_message(
            "assistant",
            avatar="🌾"
        ):

            answer = clean_answer(
                message["content"]
            )

            st.markdown(
                f'<div class="answer">'
                f'{html.escape(answer).replace(chr(10), "<br>")}'
                f'</div>',
                unsafe_allow_html=True
            )

            show_sources(
                message.get(
                    "sources",
                    []
                )
            )


# ============================================================
# VOICE INPUT
# ============================================================

st.markdown(
    "##### 🎤 Voice input"
)

audio = st.audio_input(
    "Record your question",
    sample_rate=16000,
    key="voice_input"
)


# ============================================================
# PROCESS VOICE
# ============================================================

if audio is not None:

    audio_id = (
        str(audio.name)
        + "-"
        + str(audio.size)
    )

    if (
        audio_id
        != st.session_state.processed_audio
    ):

        st.session_state.processed_audio = (
            audio_id
        )

        try:

            with st.spinner(
                "🎧 Understanding your voice..."
            ):

                question = transcribe(
                    audio
                )

            if question:

                process_question(
                    question
                )

            else:

                st.warning(
                    "No speech was detected. "
                    "Please try again."
                )

        except Exception as error:

            st.error(
                "Voice recognition failed. "
                "Please try again."
            )

            with st.expander(
                "Technical details"
            ):

                st.code(
                    str(error)
                )


# ============================================================
# TEXT CHAT INPUT
# ============================================================

question = st.chat_input(
    language_config["placeholder"]
)

if question:

    process_question(
        question
    )