import wave
import pyaudio
from pynput import keyboard
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load the OpenAI API key from the .env file
load_dotenv()

# Initialize the OpenAI client with the API key
api_key = os.getenv("OPENAI_API_KEY")
if api_key is None:
    raise ValueError("API key not found. Make sure OPENAI_API_KEY is set in your .env file.")
client = OpenAI(api_key=api_key)

# Enhanced audio parameters
CHUNK = 512  # Smaller chunk size for reduced latency
FORMAT = pyaudio.paInt16  # 16-bit audio format
CHANNELS = 2  # Stereo
RATE = 48000  # Higher sampling rate
OUTPUT_FILENAME = "output.wav"

def record_audio_until_space(output_filename=OUTPUT_FILENAME):
    """
    Record audio until the user presses SPACE with improved quality.
    """
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, 
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

    frames = []
    stop_recording = False

    def on_press(key):
        nonlocal stop_recording
        if key == keyboard.Key.space:
            stop_recording = True
            return False

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    print("Recording... Press SPACE to stop.")
    while not stop_recording:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)

    listener.stop()
    stream.stop_stream()
    stream.close()
    audio.terminate()

    with wave.open(output_filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    print(f"Recording saved to {output_filename}")

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

def split_audio_with_wave(file_path, max_size_mb=24):
    """
    Split a WAV audio file into smaller chunks under the max_size_mb size using the wave module.

    Args:
        file_path (str): Path to the input WAV file.
        max_size_mb (int): Maximum size of each chunk in MB.
    Returns:
        list: List of paths to the smaller audio chunks.
    """
    max_size_bytes = max_size_mb * 1024 * 1024  # Convert max size to bytes

    with wave.open(file_path, 'rb') as wav_file:
        params = wav_file.getparams()
        frame_rate = params.framerate
        frame_width = params.sampwidth
        n_channels = params.nchannels

        # Calculate bytes per second
        bytes_per_second = frame_rate * frame_width * n_channels

        # Determine the max number of frames per chunk
        max_frames = max_size_bytes // (frame_width * n_channels)

        chunk_paths = []
        chunk_index = 0

        while wav_file.tell() < wav_file.getnframes():
            chunk_path = f"{os.path.splitext(file_path)[0]}_chunk{chunk_index}.wav"
            with wave.open(chunk_path, 'wb') as chunk_file:
                chunk_file.setparams(params)

                # Write frames for the current chunk
                frames_to_write = min(max_frames, wav_file.getnframes() - wav_file.tell())
                frames = wav_file.readframes(frames_to_write)
                chunk_file.writeframes(frames)

            chunk_paths.append(chunk_path)
            chunk_index += 1

    return chunk_paths
