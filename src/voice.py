import asyncio
import io
import queue
import threading

import edge_tts
import sounddevice as sd
import soundfile as sf


# ============================================================
# LANGUAGE → EDGE TTS VOICE
# ============================================================

VOICE_MAP = {
    "English": "en-IN-NeerjaNeural",
    "Hindi": "hi-IN-SwaraNeural",
    "Marathi": "mr-IN-AarohiNeural",
}


# ============================================================
# GENERATE AUDIO IN MEMORY
# ============================================================

async def _generate_audio_bytes(text, voice):

    communicator = edge_tts.Communicate(
        text,
        voice
    )

    audio_buffer = bytearray()

    async for chunk in communicator.stream():

        if chunk["type"] == "audio":

            audio_buffer.extend(
                chunk["data"]
            )

    return bytes(audio_buffer)


# ============================================================
# PLAY AUDIO FROM MEMORY
# ============================================================

def _play_audio(audio_bytes):

    try:

        audio_stream = io.BytesIO(
            audio_bytes
        )

        audio_data, sample_rate = sf.read(
            audio_stream,
            dtype="float32"
        )

        sd.play(
            audio_data,
            sample_rate
        )

        sd.wait()

    except Exception as error:

        print()
        print("Audio playback error:")
        print(error)


# ============================================================
# SPEAK ONE SENTENCE
# ============================================================

def speak_sentence(
    text,
    language
):

    text = text.strip()

    if not text:

        return

    voice = VOICE_MAP.get(
        language,
        VOICE_MAP["English"]
    )

    try:

        audio_bytes = asyncio.run(
            _generate_audio_bytes(
                text,
                voice
            )
        )

        _play_audio(
            audio_bytes
        )

    except Exception as error:

        print()
        print("TTS error:")
        print(error)


# ============================================================
# BACKGROUND SPEECH WORKER
# ============================================================

def start_speech_worker(
    speech_queue,
    language
):

    def worker():

        while True:

            text = speech_queue.get()

            if text is None:

                speech_queue.task_done()

                break

            speak_sentence(
                text,
                language
            )

            speech_queue.task_done()

    thread = threading.Thread(
        target=worker,
        daemon=True
    )

    thread.start()

    return thread