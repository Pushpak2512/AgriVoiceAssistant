import os
import tempfile
import requests

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
from groq import Groq

from rag import ask_agri_assistant


# ============================================================
# LOAD .ENV
# ============================================================

load_dotenv()


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

TWILIO_ACCOUNT_SID = os.getenv(
    "TWILIO_ACCOUNT_SID"
)

TWILIO_AUTH_TOKEN = os.getenv(
    "TWILIO_AUTH_TOKEN"
)

TWILIO_API_KEY_SID = os.getenv(
    "TWILIO_API_KEY_SID"
)

TWILIO_API_KEY_SECRET = os.getenv(
    "TWILIO_API_KEY_SECRET"
)

TWILIO_WHATSAPP_NUMBER = os.getenv(
    "TWILIO_WHATSAPP_NUMBER"
)


# ============================================================
# GROQ CLIENT
# ============================================================

groq_client = Groq(
    api_key=GROQ_API_KEY
)


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)


# ============================================================
# USER LANGUAGE MEMORY
# ============================================================

user_languages = {}


# ============================================================
# SUPPORTED LANGUAGES
# ============================================================

LANGUAGES = {

    "1": {
        "name": "English",
        "code": "en"
    },

    "2": {
        "name": "Hindi",
        "code": "hi"
    },

    "3": {
        "name": "Marathi",
        "code": "mr"
    }

}


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return (
        "AgriVoiceAssistant WhatsApp "
        "server is running."
    )


# ============================================================
# CONFIGURATION CHECK
# ============================================================

def check_configuration():

    missing = []

    if not GROQ_API_KEY:
        missing.append(
            "GROQ_API_KEY"
        )

    if not TWILIO_ACCOUNT_SID:
        missing.append(
            "TWILIO_ACCOUNT_SID"
        )

    if not TWILIO_AUTH_TOKEN:
        missing.append(
            "TWILIO_AUTH_TOKEN"
        )

    if missing:

        raise RuntimeError(
            "Missing .env variables: "
            + ", ".join(missing)
        )


# ============================================================
# DOWNLOAD WHATSAPP AUDIO
# ============================================================

def download_whatsapp_audio(
    media_url
):

    print()
    print("=" * 60)
    print("DOWNLOADING WHATSAPP VOICE MESSAGE")
    print("=" * 60)

    # --------------------------------------------------------
    # Show which credentials are being used
    # --------------------------------------------------------

    print(
        "Twilio Account SID:",
        TWILIO_ACCOUNT_SID[:6] + "..."
    )

    print(
        "Twilio Auth Token:",
        "LOADED"
        if TWILIO_AUTH_TOKEN
        else "MISSING"
    )

    # --------------------------------------------------------
    # IMPORTANT
    #
    # WhatsApp media is downloaded using:
    #
    # Account SID + Auth Token
    #
    # --------------------------------------------------------

    response = requests.get(

        media_url,

        auth=(

            TWILIO_ACCOUNT_SID,

            TWILIO_AUTH_TOKEN

        ),

        timeout=30

    )

    print(
        "Twilio media response:",
        response.status_code
    )

    # --------------------------------------------------------
    # Show response if authentication fails
    # --------------------------------------------------------

    if response.status_code != 200:

        print()
        print(
            "Twilio media download failed."
        )

        print(
            "Response:",
            response.text[:500]
        )

    response.raise_for_status()

    # --------------------------------------------------------
    # Save temporary OGG file
    # --------------------------------------------------------

    temporary_file = (
        tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".ogg"
        )
    )

    temporary_file.write(
        response.content
    )

    temporary_file.close()

    print(
        "Audio downloaded successfully."
    )

    print(
        "Temporary file:",
        temporary_file.name
    )

    return temporary_file.name


# ============================================================
# SPEECH TO TEXT
# ============================================================

def speech_to_text(
    audio_path,
    language_code
):

    print()
    print("=" * 60)
    print("CONVERTING SPEECH TO TEXT")
    print("=" * 60)

    print(
        "Selected language:",
        language_code
    )

    # --------------------------------------------------------
    # Read audio
    # --------------------------------------------------------

    with open(
        audio_path,
        "rb"
    ) as audio_file:

        audio_bytes = audio_file.read()

    # --------------------------------------------------------
    # Groq Whisper
    # --------------------------------------------------------

    transcription = (

        groq_client
        .audio
        .transcriptions
        .create(

            file=(

                "voice_message.ogg",

                audio_bytes

            ),

            model=(
                "whisper-large-v3-turbo"
            ),

            language=language_code,

            response_format="json",

            temperature=0.0

        )

    )

    text = (
        transcription.text
        .strip()
    )

    print()
    print("=" * 60)
    print("RECOGNIZED FARMER QUESTION")
    print("=" * 60)

    print(text)

    return text


# ============================================================
# SEND LANGUAGE MENU
# ============================================================

def send_language_menu():

    return (

        "🌾 *Agri Voice Assistant*\n\n"

        "Choose your preferred language:\n\n"

        "1️⃣ English\n"
        "2️⃣ हिंदी\n"
        "3️⃣ मराठी\n\n"

        "Reply with *1*, *2*, or *3*."

    )


# ============================================================
# WHATSAPP WEBHOOK
# ============================================================

@app.route(
    "/whatsapp",
    methods=["POST"]
)
def whatsapp():

    # --------------------------------------------------------
    # Incoming sender
    # --------------------------------------------------------

    sender = request.form.get(
        "From",
        "Unknown"
    )

    # --------------------------------------------------------
    # Text body
    # --------------------------------------------------------

    message = request.form.get(
        "Body",
        ""
    ).strip()

    # --------------------------------------------------------
    # Media
    # --------------------------------------------------------

    media_url = request.form.get(
        "MediaUrl0"
    )

    media_type = request.form.get(
        "MediaContentType0"
    )

    num_media = request.form.get(
        "NumMedia",
        "0"
    )

    # --------------------------------------------------------
    # Terminal logging
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("WHATSAPP MESSAGE RECEIVED")
    print("=" * 60)

    print(
        "From:",
        sender
    )

    print(
        "Message:",
        message
    )

    print(
        "Number of media:",
        num_media
    )

    print(
        "Media URL:",
        media_url
    )

    print(
        "Media type:",
        media_type
    )

    response = MessagingResponse()

    # ========================================================
    # START / HI
    # ========================================================

    if message.lower() in [

        "hi",
        "hello",
        "hey",
        "start"

    ]:

        # Clear previous selection

        user_languages.pop(
            sender,
            None
        )

        response.message(
            send_language_menu()
        )

        return str(response)

    # ========================================================
    # LANGUAGE SELECTION
    # ========================================================

    if message in LANGUAGES:

        selected = LANGUAGES[
            message
        ]

        user_languages[
            sender
        ] = selected

        print()
        print(
            "Language selected:",
            selected["name"]
        )

        if message == "1":

            reply = (

                "✅ *English selected.*\n\n"

                "🎤 Now send your "
                "agricultural question "
                "as a voice message."

            )

        elif message == "2":

            reply = (

                "✅ *हिंदी चुनी गई है।*\n\n"

                "🎤 अब अपना कृषि प्रश्न "
                "वॉइस मैसेज में भेजें।"

            )

        else:

            reply = (

                "✅ *मराठी निवडली आहे.*\n\n"

                "🎤 आता तुमचा कृषी प्रश्न "
                "वॉइस मेसेज म्हणून पाठवा."

            )

        response.message(
            reply
        )

        return str(response)

    # ========================================================
    # VOICE MESSAGE
    # ========================================================

    if media_url:

        print()
        print("=" * 60)
        print("🎤 VOICE MESSAGE DETECTED")
        print("=" * 60)

        audio_path = None

        try:

            # ------------------------------------------------
            # Get selected language
            # ------------------------------------------------

            selected_language = (
                user_languages.get(
                    sender
                )
            )

            if not selected_language:

                response.message(

                    "⚠️ Please select your "
                    "preferred language first.\n\n"

                    + send_language_menu()

                )

                return str(response)

            language_code = (
                selected_language[
                    "code"
                ]
            )

            print(
                "Selected language:",
                selected_language[
                    "name"
                ]
            )

            # ------------------------------------------------
            # Download audio
            # ------------------------------------------------

            audio_path = (
                download_whatsapp_audio(
                    media_url
                )
            )

            # ------------------------------------------------
            # Speech → Text
            # ------------------------------------------------

            question = (
                speech_to_text(
                    audio_path,
                    language_code
                )
            )

            # ------------------------------------------------
            # Validate transcription
            # ------------------------------------------------

            if not question:

                response.message(

                    "❌ I could not understand "
                    "your voice message.\n\n"

                    "Please speak clearly and "
                    "try again."

                )

                return str(response)

            # ------------------------------------------------
            # RAG
            # ------------------------------------------------

            print()
            print("=" * 60)
            print(
                "🔎 SEARCHING VERIFIED "
                "AGRICULTURAL KNOWLEDGE BASE"
            )
            print("=" * 60)

            answer = (
                ask_agri_assistant(
                    question
                )
            )

            # ------------------------------------------------
            # Print answer
            # ------------------------------------------------

            print()
            print("=" * 60)
            print("🌾 AGRI ASSISTANT")
            print("=" * 60)

            print(answer)

            # ------------------------------------------------
            # Send text answer to WhatsApp
            # ------------------------------------------------

            response.message(

                "🌾 *Agri Voice Assistant*\n\n"

                + str(answer)

            )

            return str(response)

        # ====================================================
        # ERROR
        # ====================================================

        except Exception as error:

            print()
            print("=" * 60)
            print("❌ VOICE PROCESSING ERROR")
            print("=" * 60)

            print(
                type(error).__name__,
                ":",
                str(error)
            )

            response.message(

                "❌ Sorry, I could not process "
                "your voice message.\n\n"

                "Please try sending it again."

            )

            return str(response)

        finally:

            # ------------------------------------------------
            # Delete temporary audio
            # ------------------------------------------------

            if audio_path:

                try:

                    if os.path.exists(
                        audio_path
                    ):

                        os.remove(
                            audio_path
                        )

                        print(
                            "Temporary audio deleted."
                        )

                except Exception:

                    pass

    # ========================================================
    # FALLBACK
    # ========================================================

    response.message(

        "🎤 Please send your agricultural "
        "question as a voice message."

    )

    return str(response)


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print(
        "🌾 AGRI VOICE ASSISTANT "
        "- WHATSAPP SERVER"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # Validate configuration
    # --------------------------------------------------------

    try:

        check_configuration()

    except Exception as error:

        print()
        print(
            "❌ CONFIGURATION ERROR"
        )

        print(
            str(error)
        )

        raise SystemExit(1)

    # --------------------------------------------------------
    # Display safe credential status
    # --------------------------------------------------------

    print(
        "Twilio Account SID:",
        TWILIO_ACCOUNT_SID[:6] + "..."
    )

    print(
        "Twilio Auth Token:",
        "LOADED"
    )

    print(
        "Twilio API Key:",
        (
            TWILIO_API_KEY_SID[:6] + "..."
            if TWILIO_API_KEY_SID
            else "NOT USED"
        )
    )

    print(
        "Twilio API Secret:",
        (
            "LOADED"
            if TWILIO_API_KEY_SECRET
            else "NOT USED"
        )
    )

    print(
        "WhatsApp Number:",
        (
            TWILIO_WHATSAPP_NUMBER
            if TWILIO_WHATSAPP_NUMBER
            else "NOT SET"
        )
    )

    print(
        "Groq API Key:",
        "LOADED"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # Start Flask
    # --------------------------------------------------------

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=False

    )