from PIL import ImageGrab, Image as PILImage
import pyperclip

def process_clipboard_content():
    """
    Check if the clipboard contains an image or text,
    then process accordingly.
    """
    try:
        image = ImageGrab.grabclipboard()
        if isinstance(image, PILImage.Image):
            image_path = "clipboard_image.png"
            image.save(image_path)
            return image_path, None
        else:
            clipboard_content = pyperclip.paste()
            return None, clipboard_content or "[No content]"
    except Exception as e:
        return None, f"Error: {e}"
