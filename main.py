import os
import sys
import wave
import pyaudio
import keyboard
import pyperclip
import requests
import base64
from openai import OpenAI
from dotenv import load_dotenv
import customtkinter as ctk
import threading
import time
from PIL import ImageGrab, Image, ImageTk, UnidentifiedImageError

# Manage the path for the GIF file
if hasattr(sys, '_MEIPASS'):
    gif_path = os.path.join(sys._MEIPASS, 'recording.gif')
else:
    gif_path = os.path.join(os.path.dirname(__file__), 'recording.gif')

load_dotenv()
##########################
#     AUDIO SETTINGS     #
##########################
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1          # mono
RATE = 44100
OUTPUT_FILENAME = "output.wav"

##########################
#    OPENAI API KEY      #
##########################
# Either in the environment variable:
client = OpenAI()

############################################
# 1) MAIN WINDOW                          #
############################################
class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Mouse GPT")
        self.geometry("600x700")

        # Initialize the animation window
        self.init_recording_screen()

    def init_recording_screen(self):
        # Clear old widgets
        for widget in self.winfo_children():
            widget.destroy()

        # Main title
        self.recording_label = ctk.CTkLabel(self, text="Recording in progress...", font=("Helvetica", 20, "bold"))
        self.recording_label.pack(pady=10)

        # Timer
        self.chrono_label = ctk.CTkLabel(self, text="0:00", font=("Helvetica", 16))
        self.chrono_label.pack(pady=5)

        # GIF Animation
        self.gif_label = ctk.CTkLabel(self, text="")
        self.gif_label.pack(pady=10)
        self.is_animating = True
        self.start_gif_animation()

    def start_gif_animation(self):
        try:
            gif_image = Image.open(gif_path)
            self.frames = []
            for frame_index in range(gif_image.n_frames):
                gif_image.seek(frame_index)
                frame = ctk.CTkImage(light_image=gif_image.copy(), size=(200, 200))
                self.frames.append(frame)

            self.current_frame = 0

            def update_frame():
                if self.is_animating and self.gif_label.winfo_exists():
                    self.gif_label.configure(image=self.frames[self.current_frame])
                    self.current_frame = (self.current_frame + 1) % len(self.frames)
                    self.after(100, update_frame)

            update_frame()
        except (FileNotFoundError, UnidentifiedImageError):
            self.recording_label.configure(text="Error: The GIF file is missing or invalid.")

    def start_timer(self):
        start_time = time.time()

        def update_timer():
            if self.chrono_label.winfo_exists():
                elapsed_time = int(time.time() - start_time)
                minutes = elapsed_time // 60
                seconds = elapsed_time % 60
                self.chrono_label.configure(text=f"{minutes}:{seconds:02}")
                self.after(1000, update_timer)

        update_timer()

    def show_result_screen(self, clipboard_content, transcription_text, gpt_response, image_path=None):
        # Stop animation
        self.is_animating = False

        # Clear old widgets
        for widget in self.winfo_children():
            widget.destroy()

        # Containers for sections
        self.clipboard_label = ctk.CTkLabel(self, text="Clipboard Content", font=("Helvetica", 16, "bold"))
        self.clipboard_label.pack(pady=5)

        if image_path:
            # Display the image if detected
            try:
                clipboard_image = Image.open(image_path)
                clipboard_image.thumbnail((400, 400))  # Resize the image
                clipboard_photo = ImageTk.PhotoImage(clipboard_image)

                self.clipboard_image_label = ctk.CTkLabel(self, image=clipboard_photo, text="")
                self.clipboard_image_label.image = clipboard_photo  # Prevent garbage collection
                self.clipboard_image_label.pack(pady=5)
            except Exception as e:
                self.clipboard_text = ctk.CTkTextbox(self, width=580, height=150)
                self.clipboard_text.insert(ctk.END, f"Error displaying image: {e}")
                self.clipboard_text.pack(pady=5)
        else:
            self.clipboard_text = ctk.CTkTextbox(self, width=580, height=150)
            self.clipboard_text.insert(ctk.END, clipboard_content)
            self.clipboard_text.pack(pady=5)

        self.transcript_label = ctk.CTkLabel(self, text="Transcript", font=("Helvetica", 16, "bold"))
        self.transcript_text = ctk.CTkTextbox(self, width=580, height=150)

        self.response_label = ctk.CTkLabel(self, text="ChatGPT Response", font=("Helvetica", 16, "bold"))
        self.response_text = ctk.CTkTextbox(self, width=580, height=200)

        # Place sections
        self.transcript_label.pack(pady=5)
        self.transcript_text.pack(pady=5)
        self.response_label.pack(pady=5)
        self.response_text.pack(pady=5)

        # Fill text areas
        self.transcript_text.insert(ctk.END, transcription_text)
        self.response_text.insert(ctk.END, gpt_response)

############################################
# 2) RECORD AUDIO UNTIL SPACE IS PRESSED  #
############################################
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

############################################
# 3) TRANSCRIBE AUDIO (NEW API)           #
############################################
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

############################################
# 4) SEND AN IMAGE TO GPT-4o              #
############################################
def send_image_to_gpt4o_with_transcript(image_path, transcript):
    """
    Send a base64-encoded image along with the transcribed text to GPT-4o.
    Returns the generated response.
    """
    try:
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": transcript,
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                        },
                    ],
                }
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error sending image: {e}"

############################################
# 5) SEND TEXT TO GPT-4o                  #
############################################
def send_to_gpt4o(prompt_text):
    """
    Send the given text to GPT-4o and return the response.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an assistant helping a user with their tasks."},
                {"role": "user", "content": prompt_text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling GPT-4o: {e}"

############################################
# 6) CHECK CLIPBOARD CONTENT              #
############################################
def process_clipboard_content():
    """
    Check if the clipboard contains an image or text,
    then process accordingly.
    """
    try:
        image = ImageGrab.grabclipboard()
        if isinstance(image, Image.Image):
            image_path = "clipboard_image.png"
            image.save(image_path)
            return image_path, None
        else:
            clipboard_content = pyperclip.paste()
            return None, clipboard_content or "[No content]"
    except Exception as e:
        return None, f"Error: {e}"

############################################
# 7) MAIN CODE                            #
############################################
if __name__ == "__main__":
    # Prevent terminal window when compiling with PyInstaller
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

    app = MainApp()

    def run_main_operations():
        app.start_timer()

        # 1) Check and process clipboard content
        image_path, clipboard_content = process_clipboard_content()

        # 2) Record audio until SPACE is pressed
        record_audio_until_space()

        # 3) Transcribe the audio file using the new approach
        transcription_text = transcribe_audio_with_whisper(OUTPUT_FILENAME)

        # 4) Prepare and send data to GPT-4o
        if image_path:
            gpt_response = send_image_to_gpt4o_with_transcript(image_path, transcription_text)
        else:
            combined_prompt = (
                f"Clipboard content:\n{clipboard_content}\n\n"
                f"Audio transcription:\n{transcription_text}\n"
            )
            gpt_response = send_to_gpt4o(combined_prompt)

        # Display the results on the final screen
        app.show_result_screen(clipboard_content, transcription_text, gpt_response, image_path=image_path)

    threading.Thread(target=run_main_operations, daemon=True).start()
    app.mainloop()
