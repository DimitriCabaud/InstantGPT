import wave
import pyaudio
import keyboard
from openai import OpenAI
from dotenv import load_dotenv
import os

# Charger la clé API OpenAI depuis le fichier .env
load_dotenv()

# Initialiser l'objet client avec la clé API
api_key = os.getenv("OPENAI_API_KEY")
if api_key is None:
    raise ValueError("API key not found. Make sure OPENAI_API_KEY is set in your .env file.")
client = OpenAI(api_key=api_key)


CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
OUTPUT_FILENAME = "output.wav"

def record_audio_until_space(output_filename=OUTPUT_FILENAME):
    """
    Record audio until the user presses SPACE.
    """
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, 
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

    frames = []
    while True:
        data = stream.read(CHUNK)
        frames.append(data)
        
        if keyboard.is_pressed('space'):
            break

    stream.stop_stream()
    stream.close()
    audio.terminate()

    with wave.open(output_filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))


def transcribe_audio_with_whisper(filename=OUTPUT_FILENAME):
    """
    Use OpenAI's Whisper API to transcribe the audio file.
    Returns the transcription as text.
    """
    try:
        with open(filename, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1"
            )
        return response.text
    except Exception as e:
        return f"Error during transcription: {e}"