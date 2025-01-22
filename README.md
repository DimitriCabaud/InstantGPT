# ![flash.ico](assets/flash.ico){width=32} InstantGPT

InstantGPT is an interactive application designed to provide direct access to OpenAI models from your mouse or a keyboard shortcut. The goal is to enable rapid interactions with OpenAI's models, far faster than the web application or even the ChatGPT Desktop app. By using a shortcut or a click, users can record audio, access clipboard content, process the audio for transcription, and send the transcript along with clipboard content (text or image) to OpenAI models for contextual analysis. This application also distinguishes between user transcriptions and OpenAI model responses. Additionally, it provides access to OpenAI's voice transcription model, Whisper, which is not available in the standard ChatGPT Desktop app.

## Features

- **Direct Access to OpenAI Models**: Interact with OpenAI models directly using a mouse click or keyboard shortcut.
- **Audio Recording**: Records audio until the SPACE key is pressed and saves it as a WAV file.
- **Clipboard Processing**: Detects clipboard content (image or text) and processes it for further use.
- **Audio Transcription**: Utilizes OpenAI's Whisper API to transcribe recorded audio into text.
- **Image and Text Analysis**: Sends images and transcriptions to OpenAI's GPT-4.0 API for analysis.
- **Interactive GUI**: User-friendly interface for displaying results, including clipboard content, transcription, and OpenAI model responses.
- **Productivity Enhancement**: Aims to save time and streamline workflows by offering faster interactions with OpenAI models.
- **Automated Recording**: Automatically starts recording audio as soon as the program is launched, until the SPACE key is pressed.

## Installation

### Prerequisites

- **Python 3.9+**

### Dependencies:

- `pyaudio`
- `keyboard`
- `pyperclip`
- `requests`
- `pillow`
- `customtkinter`
- `python-dotenv`
- `openai`

### Setup

1. Clone the repository:

   ```bash
   git clone <repository_url>
   cd <repository_folder>
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up the environment file:

   - Create a `.env` file in the root directory.
   - Add your OpenAI API key:

     ```env
     OPENAI_API_KEY=your_openai_api_key
     ```

4. Place the `recording.gif` file in the same directory as the script or in the application bundle for distribution.

## Executable Version

A precompiled executable version of InstantGPT is available in the `DIST` folder. To use this executable, ensure that a `.env` file is placed in the same directory as the executable before running it. This file must contain the OpenAI API key with the variable name `OPENAI_API_KEY` in uppercase, formatted as follows:

```env
OPENAI_API_KEY=your_openai_api_key
```

Users have the option to either use the precompiled executable or recompile the project themselves. The project was compiled using PyInstaller.

## Usage

### Run the Application

To launch the application, execute:

```bash
python main.py
```

### Functionality Overview

#### Recording Audio:

- The application starts recording audio automatically when launched.
- Press **SPACE** to stop recording.

#### Clipboard Content:

- If an image is detected in the clipboard, it will be processed and displayed.
- If text is detected, it will be analyzed and displayed.

#### Transcription:

- The recorded audio file is transcribed using OpenAI's Whisper API.

#### OpenAI Model Integration:

- Sends clipboard content and transcription to OpenAI's GPT-4.0 API for contextual responses.
- Uses GPT-4.0 for image analysis and the GPT-3.5-turbo (0.1 model) for other tasks.
- Displays the response in the GUI.

## Code Structure

### Main Application (GUI):

- **`MainApp`**: The primary class for GUI management.
- **`init_recording_screen`**: Initializes the recording interface.
- **`show_result_screen`**: Displays the final result interface.

### Audio Handling:

- **`record_audio_until_space`**: Captures audio until SPACE is pressed.

### API Interaction:

- **`transcribe_audio_with_whisper`**: Transcribes audio using OpenAI's Whisper API.
- **`send_image_to_gpt4o_with_transcript`**: Sends image and text data to GPT-4.0.
- **`send_to_gpt4o`**: Sends text prompts to OpenAI's GPT-3.5-turbo.

### Clipboard Handling:

- **`process_clipboard_content`**: Checks and processes clipboard content for images or text.

### Utility Functions:

- Handles image processing, base64 encoding, and error handling.

## Known Issues

- Missing `recording.gif` will result in an error during the animation setup.
- Clipboard image handling depends on the OS clipboard functionality.

## Contributing

1. Fork the repository.
2. Create a feature branch:

   ```bash
   git checkout -b feature-name
   ```

3. Commit changes:

   ```bash
   git commit -m "Description of changes"
   ```

4. Push to the branch:

   ```bash
   git push origin feature-name
   ```

5. Create a pull request.

## License

This project is licensed under the **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)** License. You are free to share and adapt the material for non-commercial purposes, provided appropriate credit is given. See the [CC BY-NC 4.0 license](https://creativecommons.org/licenses/by-nc/4.0/) for more details.
