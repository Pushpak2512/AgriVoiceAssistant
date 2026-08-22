import queue
import re

import speech_recognition as sr

from rag import stream_agri_assistant
from voice import start_speech_worker


# ============================================================
# LANGUAGE CONFIGURATION
# ============================================================

LANGUAGES = {
    "1": {
        "name": "English",
        "speech_code": "en-IN",
    },

    "2": {
        "name": "Hindi",
        "speech_code": "hi-IN",
    },

    "3": {
        "name": "Marathi",
        "speech_code": "mr-IN",
    }
}


# ============================================================
# LANGUAGE SELECTION
# ============================================================

def choose_language():

    print()
    print("=" * 60)
    print("CHOOSE YOUR PREFERRED LANGUAGE")
    print("=" * 60)

    print("1. English")
    print("2. Hindi")
    print("3. Marathi")

    while True:

        choice = input(
            "\nEnter choice (1/2/3): "
        ).strip()

        if choice in LANGUAGES:

            return LANGUAGES[choice]

        print(
            "Invalid choice. Please enter 1, 2, or 3."
        )


# ============================================================
# SPEECH TO TEXT
# ============================================================

def listen_to_farmer(language):

    recognizer = sr.Recognizer()

    print()
    print("=" * 60)
    print("VOICE INPUT")
    print("=" * 60)

    print(
        "🎤 Please speak your agricultural question..."
    )

    try:

        with sr.Microphone() as source:

            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.5
            )

            print("Listening...")

            audio = recognizer.listen(
                source,
                timeout=10,
                phrase_time_limit=15
            )

        print(
            "🧠 Converting speech to text..."
        )

        text = recognizer.recognize_google(
            audio,
            language=language["speech_code"]
        )

        return text

    except sr.WaitTimeoutError:

        print(
            "No speech detected."
        )

        return None

    except sr.UnknownValueError:

        print(
            "Could not understand the speech."
        )

        return None

    except sr.RequestError as error:

        print(
            "Speech recognition error:"
        )

        print(error)

        return None


# ============================================================
# SENTENCE EXTRACTION
# ============================================================

def extract_complete_sentences(buffer):

    sentences = []

    pattern = r"(.+?[.!?।])(?:\s+|$)"

    while True:

        match = re.search(
            pattern,
            buffer,
            flags=re.DOTALL
        )

        if not match:

            break

        sentence = match.group(
            1
        ).strip()

        if sentence:

            sentences.append(
                sentence
            )

        buffer = buffer[
            match.end():
        ]

    return sentences, buffer


# ============================================================
# PRINT SOURCES
# ============================================================

def print_sources(sources):

    print()
    print("=" * 60)
    print("RETRIEVED VERIFIED SOURCES")
    print("=" * 60)

    if not sources:

        print("No sources retrieved.")

        return

    for index, source in enumerate(
        sources,
        start=1
    ):

        print(
            f"{index}. "
            f"{source['file']} | "
            f"Page: {source['page']} | "
            f"Distance: {source['score']:.4f}"
        )

    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("        AGRI VOICE ASSISTANT")
    print("=" * 60)

    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------

    language = choose_language()

    print()
    print(
        f"Language selected: {language['name']}"
    )

    # --------------------------------------------------------
    # VOICE INPUT
    # --------------------------------------------------------

    question = listen_to_farmer(
        language
    )

    if not question:

        return

    # --------------------------------------------------------
    # RECOGNIZED QUESTION
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("RECOGNIZED FARMER QUESTION")
    print("=" * 60)

    print(question)

    # --------------------------------------------------------
    # RAG
    # --------------------------------------------------------

    print()
    print(
        "🔎 Searching verified agricultural knowledge base..."
    )

    print()
    print("=" * 60)
    print("AGRI ASSISTANT")
    print("=" * 60)

    # --------------------------------------------------------
    # SPEECH QUEUE
    # --------------------------------------------------------

    speech_queue = queue.Queue()

    speech_thread = start_speech_worker(
        speech_queue,
        language["name"]
    )

    # --------------------------------------------------------
    # STREAM RESPONSE
    # --------------------------------------------------------

    text_buffer = ""

    full_answer = ""

    sources = []

    for item in stream_agri_assistant(
        question
    ):

        # ----------------------------------------------------
        # STREAMED TEXT
        # ----------------------------------------------------

        if item["type"] == "token":

            token = item["text"]

            full_answer += token

            print(
                token,
                end="",
                flush=True
            )

            text_buffer += token

            sentences, text_buffer = (
                extract_complete_sentences(
                    text_buffer
                )
            )

            # ------------------------------------------------
            # SEND SENTENCES TO AUDIO QUEUE
            # ------------------------------------------------

            for sentence in sentences:

                speech_queue.put(
                    sentence
                )

        # ----------------------------------------------------
        # SOURCES
        # ----------------------------------------------------

        elif item["type"] == "sources":

            sources = item["sources"]

    # --------------------------------------------------------
    # REMAINING TEXT
    # --------------------------------------------------------

    if text_buffer.strip():

        speech_queue.put(
            text_buffer.strip()
        )

    # --------------------------------------------------------
    # WAIT FOR AUDIO
    # --------------------------------------------------------

    speech_queue.join()

    # Stop worker

    speech_queue.put(
        None
    )

    speech_thread.join(
        timeout=2
    )

    # --------------------------------------------------------
    # SOURCES
    # --------------------------------------------------------

    print()

    print_sources(
        sources
    )

    print()
    print(
        "✅ Voice response completed."
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()