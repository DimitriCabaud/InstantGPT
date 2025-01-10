import time
from ui.main_window import MainApp  # Import de la classe principale
from utils.clipboard import process_clipboard_content  # Import des fonctions utilitaires
from utils.audio import record_audio_until_space, transcribe_audio_with_whisper, OUTPUT_FILENAME
from utils.gpt_client import send_image_to_gpt4o_with_transcript, send_to_gpt4o

import threading

if __name__ == "__main__":
    app = MainApp()

    def run_main_operations():
        app.start_timer()

        # Step 1: Start recording
        app.update_log("Recording started...")
        start_time = time.time()
        record_audio_until_space()
        app.update_log("Recording stopped.")

        # Step 2: Calculate the recording duration
        elapsed_time = int(time.time() - start_time)
        app.update_log(f"Total recording duration: {elapsed_time} seconds")

        # Step 3: Check clipboard content
        app.update_log("Checking clipboard content...")
        image_path, clipboard_content = process_clipboard_content()
        if image_path:
            app.update_log("Clipboard contains an image.")
        elif clipboard_content:
            app.update_log("Clipboard contains text.")
        else:
            app.update_log("Clipboard is empty or invalid.")

        # Step 4: Transcribe the audio
        app.update_log("Transcribing audio...")
        transcription_text = transcribe_audio_with_whisper(OUTPUT_FILENAME)
        if "Error" in transcription_text:
            app.update_log(f"Error during transcription: {transcription_text}")
        else:
            app.update_log("Transcription completed.")

        # Step 5: Display clipboard inclusion options
        app.show_clipboard_prompt(clipboard_content, transcription_text, image_path=image_path)

    threading.Thread(target=run_main_operations, daemon=True).start()
    app.mainloop()
