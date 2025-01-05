import sys
import os
import time
import customtkinter as ctk
from utils.audio import record_audio_until_space, transcribe_audio_with_whisper
from utils.gpt_client import send_to_gpt4o, send_image_to_gpt4o_with_transcript
from utils.clipboard import process_clipboard_content
from PIL import Image, ImageTk, UnidentifiedImageError


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MouseGPT")
        self.geometry("600x700")

        if hasattr(sys, '_MEIPASS'):
            self.gif_path = os.path.join(sys._MEIPASS, 'assets', 'recording.gif')
        else:
            self.gif_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'recording.gif')

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

        # Blinking text for stopping recording
        self.stop_recording_label = ctk.CTkLabel(self, text="Press SPACE to stop recording", font=("Helvetica", 14))
        self.stop_recording_label.pack(pady=10)
        self.start_blinking_text()

    def start_gif_animation(self):
        try:
            gif_image = Image.open(self.gif_path)
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

    def start_blinking_text(self):
        def toggle_visibility():
            if self.stop_recording_label.winfo_exists():
                current_color = self.stop_recording_label.cget("text_color")
                new_color = "white" if current_color == "red" else "red"
                self.stop_recording_label.configure(text_color=new_color)
                self.after(500, toggle_visibility)
    
        toggle_visibility()

    
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

    def show_clipboard_prompt(self, clipboard_content, transcription_text, image_path):
        # Clear old widgets
        for widget in self.winfo_children():
            widget.destroy()

        # Prompt user for clipboard inclusion
        self.prompt_label = ctk.CTkLabel(self, text="Do you want to include clipboard content in the request?", font=("Helvetica", 16, "bold"))
        self.prompt_label.pack(pady=10)

        self.yes_button = ctk.CTkButton(self, text="Yes", command=lambda: self.process_request(True, clipboard_content, transcription_text, image_path))
        self.yes_button.pack(side="left", padx=20, pady=20)

        self.no_button = ctk.CTkButton(self, text="No", command=lambda: self.process_request(False, clipboard_content, transcription_text, image_path))
        self.no_button.pack(side="right", padx=20, pady=20)

    def process_request(self, include_clipboard, clipboard_content, transcription_text, image_path):
        # Prepare and send data to GPT-4o
        transcription_text_with_context = f"The audio transcription contains the user's request: {transcription_text}"
        if include_clipboard:
            if image_path:
                gpt_response = send_image_to_gpt4o_with_transcript(image_path, transcription_text_with_context)
            else:
                combined_prompt = (
                    f"Clipboard content:\n{clipboard_content}\n\n"
                    f"Audio transcription:\n{transcription_text_with_context}\n"
                )
                gpt_response = send_to_gpt4o(combined_prompt)
        else:
            combined_prompt = (
                f"Audio transcription:\n{transcription_text_with_context}\n"
            )
            gpt_response = send_to_gpt4o(combined_prompt)

        # Show results
        self.show_result_screen(include_clipboard, clipboard_content, transcription_text, gpt_response, image_path)

    def show_result_screen(self, include_clipboard, clipboard_content, transcription_text, gpt_response, image_path):
        # Stop animation
        self.is_animating = False

        # Clear old widgets
        for widget in self.winfo_children():
            widget.destroy()

        if include_clipboard:
            # Display clipboard content if included
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
        self.transcript_label.pack(pady=5)
        self.transcript_text = ctk.CTkTextbox(self, width=580, height=150)
        self.transcript_text.pack(pady=5)
        self.transcript_text.insert(ctk.END, transcription_text)

        self.response_label = ctk.CTkLabel(self, text="ChatGPT Response", font=("Helvetica", 16, "bold"))
        self.response_label.pack(pady=5)

        # Display plain text response
        self.response_text = ctk.CTkTextbox(self, width=580, height=200, wrap="word")
        self.response_text.pack(pady=5)
        self.response_text.insert(ctk.END, gpt_response)
