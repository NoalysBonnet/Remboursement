# utils/image_utils.py
from PIL import Image, ImageDraw, ImageOps
import customtkinter as ctk

def create_circular_image(image_path: str, size: int) -> ctk.CTkImage | None:
    try:
        img = Image.open(image_path).convert("RGBA")
    except (IOError, FileNotFoundError):
        return None

    # Redimensionner et centrer l'image pour qu'elle soit carrée
    img = ImageOps.fit(img, (size, size), Image.Resampling.LANCZOS)

    # Créer un masque circulaire
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)

    # Appliquer le masque
    img.putalpha(mask)

    return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))