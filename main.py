import os
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
from PIL import ImageGrab, Image

load_dotenv()
##########################
#     PARAMÈTRES AUDIO   #
##########################
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1          # mono
RATE = 44100
OUTPUT_FILENAME = "output.wav"

##########################
#   CLÉ API OPENAI       #
##########################
# Soit dans la variable d'environnement :
client = OpenAI()

############################################
# 1) ANIMATION PENDANT L'ENREGISTREMENT   #
############################################
def show_recording_animation():
    """
    Affiche une fenêtre visuellement agréable avec un point rouge animé et un chrono pendant l'enregistrement.
    """
    # Initialiser la fenêtre
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    window = ctk.CTk()
    window.title("Enregistrement en cours")
    window.geometry("400x200")

    # Titre principal
    title_label = ctk.CTkLabel(window, text="🔴 Enregistrement...", font=("Helvetica", 18, "bold"))
    title_label.pack(pady=10)

    # Cadre pour l'animation
    animation_frame = ctk.CTkFrame(window, width=80, height=80, corner_radius=10)
    animation_frame.pack(pady=10)

    canvas = ctk.CTkCanvas(animation_frame, width=50, height=50, bg="#1A1A1A", highlightthickness=0)
    canvas.pack()
    point = canvas.create_oval(10, 10, 40, 40, fill="red")

    # Chronomètre
    chrono_label = ctk.CTkLabel(window, text="0:00", font=("Helvetica", 16))
    chrono_label.pack(pady=10)

    # Animation du point rouge
    def animate_point():
        while True:
            for i in range(5):
                canvas.move(point, 0, 2)
                window.update()
                time.sleep(0.05)
            for i in range(5):
                canvas.move(point, 0, -2)
                window.update()
                time.sleep(0.05)

    # Mise à jour du chronomètre
    def update_timer():
        start_time = time.time()
        while True:
            elapsed_time = int(time.time() - start_time)
            minutes = elapsed_time // 60
            seconds = elapsed_time % 60
            chrono_label.configure(text=f"{minutes}:{seconds:02}")
            time.sleep(1)

    threading.Thread(target=animate_point, daemon=True).start()
    threading.Thread(target=update_timer, daemon=True).start()

    # Lancement de la fenêtre
    window.mainloop()

############################################
# 2) ENREGISTRER L'AUDIO JUSQU'À ESPACE    #
############################################
def record_audio_until_space(output_filename=OUTPUT_FILENAME):
    """
    Enregistre l'audio jusqu'à ce que l'utilisateur appuie sur ESPACE.
    """
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, 
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

    print("=== Enregistrement en cours. Appuyez sur ESPACE pour arrêter. ===")
    frames = []

    # Lancer l'animation dans un thread séparé
    animation_thread = threading.Thread(target=show_recording_animation, daemon=True)
    animation_thread.start()

    while True:
        data = stream.read(CHUNK)
        frames.append(data)
        
        if keyboard.is_pressed('space'):
            print("=== Espace détecté. Arrêt de l'enregistrement. ===")
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
# 3) TRANSCRIRE L'AUDIO (NOUVELLE API)     #
############################################
def transcribe_audio_with_whisper(filename=OUTPUT_FILENAME):
    """
    Utilise l'API Whisper d'OpenAI pour transcrire le fichier audio.
    Retourne la transcription sous forme de texte.
    """
    print("=== Transcription de l'audio via Whisper... ===")

    try:
        with open(filename, "rb") as audio_file:
            # Utilisation de la méthode correcte
            response = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1"
            )
        text = response.text
        print("=== Transcription obtenue ===")
        print(text)
        return text
    except Exception as e:
        print(f"Erreur lors de la transcription : {e}")
        return ""

############################################
# 4) ENVOYER UNE IMAGE À GPT-4o           #
############################################
def send_image_to_gpt4o(image_path):
    """
    Envoie une image encodée en base64 à GPT-4o.
    Retourne la réponse générée.
    """
    print("=== Envoi de l'image à GPT-4o... ===")
    try:
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "What is in this image?",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                        },
                    ],
                }
            ],
        )
        result = response.choices[0].message.content
        print("=== Réponse de GPT-4o ===")
        print(result)
        return result
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'image : {e}")
        return ""

############################################
# 5) ENVOYER TEXTE À GPT-4o              #
############################################
def send_to_gpt4o(prompt_text):
    """
    Envoie le 'prompt_text' à GPT-4o.
    Retourne le texte de la réponse.
    """
    print("=== Envoi à ChatGPT (GPT-4o) ... ===")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Utilisation de GPT-4o
            messages=[
                {"role": "system", "content": "Tu es un assistant qui répond en français."},
                {"role": "user", "content": prompt_text}
            ]
        )
        answer = response.choices[0].message.content
        print("=== Réponse de ChatGPT ===")
        print(answer)
        return answer
    except Exception as e:
        print(f"Erreur lors de l'appel à l'API ChatGPT: {e}")
        return ""

############################################
# 6) VÉRIFIER LE CONTENU DU PRESSE-PAPIERS #
############################################
def process_clipboard_content():
    """
    Vérifie si le presse-papiers contient une image ou du texte,
    puis traite en conséquence.
    """
    try:
        # Tenter de récupérer une image
        image = ImageGrab.grabclipboard()
        if isinstance(image, Image.Image):
            print("=== Image détectée dans le presse-papiers ===")
            image_path = "clipboard_image.png"
            image.save(image_path)  # Sauvegarde temporaire de l'image
            return send_image_to_gpt4o(image_path)
        else:
            # Sinon, traiter comme texte
            clipboard_content = pyperclip.paste()
            print(f"=== Texte détecté dans le presse-papiers ===\n{clipboard_content}\n")
            return clipboard_content
    except Exception as e:
        print(f"Erreur lors de la vérification du presse-papiers : {e}")
        return ""

############################################
# 7) CODE PRINCIPAL                        #
############################################
if __name__ == "__main__":
    # 1) Vérification et traitement du contenu du presse-papiers
    clipboard_content = process_clipboard_content()

    # 2) Enregistrer l'audio jusqu'à la pression de la touche Espace
    record_audio_until_space()

    # 3) Transcrire le fichier audio via la nouvelle approche
    transcription_text = transcribe_audio_with_whisper(OUTPUT_FILENAME)

    # 4) Préparer le texte à envoyer à GPT-4o:
    combined_prompt = (
        f"Contenu du presse-papiers:\n{clipboard_content}\n\n"
        f"Transcription de l'audio:\n{transcription_text}\n"
    )

    # 5) Envoyer à GPT-4o et récupérer la réponse
    gpt4_response = send_to_gpt4o(combined_prompt)

    # 6) Copier la réponse de GPT-4o dans le presse-papiers
    pyperclip.copy(gpt4_response)
    print("=== La réponse de ChatGPT a été copiée dans le presse-papiers. ===")
