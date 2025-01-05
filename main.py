from ui.main_window import MainApp  # Import de la classe principale
from utils.clipboard import process_clipboard_content  # Import des fonctions utilitaires
from utils.audio import record_audio_until_space, transcribe_audio_with_whisper, OUTPUT_FILENAME
from utils.gpt_client import send_image_to_gpt4o_with_transcript, send_to_gpt4o

import threading

if __name__ == "__main__":
    app = MainApp()

    def run_main_operations():
        app.start_timer()

        # Étape 1 : Vérifiez et traitez le contenu du presse-papier
        image_path, clipboard_content = process_clipboard_content()

        # Étape 2 : Enregistrez l'audio jusqu'à ce que l'utilisateur appuie sur ESPACE
        record_audio_until_space()

        # Étape 3 : Transcrivez le fichier audio
        transcription_text = transcribe_audio_with_whisper(OUTPUT_FILENAME)

        # Étape 4 : Affichez l'invite pour inclure ou non le contenu du presse-papier
        app.show_clipboard_prompt(clipboard_content, transcription_text, image_path=image_path)

    threading.Thread(target=run_main_operations, daemon=True).start()
    app.mainloop()
