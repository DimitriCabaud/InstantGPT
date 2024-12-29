import os
import wave
import pyaudio
import keyboard
import pyperclip
import requests
from openai import OpenAI
from dotenv import load_dotenv
import tkinter as tk
import threading
import time

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
    window = tk.Tk()
    window.title("Enregistrement en cours")
    window.geometry("300x150")
    window.configure(bg="#2C2F33")

    # Titre
    title_label = tk.Label(window, text="🔴 Enregistrement...", fg="white", bg="#2C2F33", font=("Helvetica", 16, "bold"))
    title_label.pack(pady=10)

    # Animation de point rouge
    canvas = tk.Canvas(window, width=50, height=50, bg="#2C2F33", highlightthickness=0)
    canvas.pack()
    point = canvas.create_oval(10, 10, 40, 40, fill="red")

    # Chrono
    chrono_label = tk.Label(window, text="0:00", fg="white", bg="#2C2F33", font=("Helvetica", 14))
    chrono_label.pack(pady=10)

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

    def update_timer():
        start_time = time.time()
        while True:
            elapsed_time = int(time.time() - start_time)
            minutes = elapsed_time // 60
            seconds = elapsed_time % 60
            chrono_label.config(text=f"{minutes}:{seconds:02}")
            time.sleep(1)

    threading.Thread(target=animate_point, daemon=True).start()
    threading.Thread(target=update_timer, daemon=True).start()

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
# 4) ENVOYER TEXTE À GPT-4o              #
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
# 5) CODE PRINCIPAL                        #
############################################
if __name__ == "__main__":
    # 1) Récupération du contenu du presse-papiers (avant l’enregistrement)
    clipboard_before = pyperclip.paste()
    print(f"=== Contenu actuel du presse-papiers ===\n{clipboard_before}\n")

    # 2) Enregistrer l'audio jusqu'à la pression de la touche Espace
    record_audio_until_space()

    # 3) Transcrire le fichier audio via la nouvelle approche
    transcription_text = transcribe_audio_with_whisper(OUTPUT_FILENAME)

    # 4) Préparer le texte à envoyer à GPT-4o:
    combined_prompt = (
        f"Contenu du presse-papiers:\n{clipboard_before}\n\n"
        f"Transcription de l'audio:\n{transcription_text}\n"
    )

    # 5) Envoyer à GPT-4o et récupérer la réponse
    gpt4_response = send_to_gpt4o(combined_prompt)

    # 6) Copier la réponse de GPT-4o dans le presse-papiers
    pyperclip.copy(gpt4_response)
    print("=== La réponse de ChatGPT a été copiée dans le presse-papiers. ===")
