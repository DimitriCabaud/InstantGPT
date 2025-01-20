from openai import OpenAI
from dotenv import load_dotenv
import base64
import os

# Charger la clé API OpenAI depuis le fichier .env
load_dotenv()

# Initialiser l'objet client avec la clé API
api_key = os.getenv("OPENAI_API_KEY")
if api_key is None:
    raise ValueError("API key not found. Make sure OPENAI_API_KEY is set in your .env file.")
client = OpenAI(api_key=api_key)


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


def send_to_llm(prompt_text):
    """
    Send the given text to OpenAI and return the response.
    """
    try:
        response = client.chat.completions.create(
            model="o1-preview",
            messages=[
                #{"role": "system", "content": "You are an assistant helping a user with their tasks. Always respond in the language of the user unless otherwise specified."},
                {"role": "user", "content": prompt_text}
            ],
            #temperature=0.7,  # Adjust creativity
            #max_tokens=16384,   # Limit the response length
            top_p=1.0,        # Typical value for full probability
            frequency_penalty=0.0,
            presence_penalty=0.0,
            #reasoning_effort="high"
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling LLM: {e}"