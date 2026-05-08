import tkinter as tk
from tkinter import messagebox
from frontend.theme import *
from PIL import Image, ImageTk
import io

class ImageViewer(tk.Toplevel):
    """Popup window to display receipt image"""
    def __init__(self, master, image_data, title="Receipt Image"):
        super().__init__(master)
        self.title(title)
        self.configure(bg=BG_DARK)
        self.geometry("600x500")
        self.build(image_data)

    def build(self, image_data):
        tk.Label(self, text="Receipt Image",
                 bg=BG_DARK, fg=ACCENT,
                 font=FONT_HEADING).pack(pady=10)

        try:
            # Convert bytes to image
            if isinstance(image_data, memoryview):
                image_data = bytes(image_data)

            image = Image.open(io.BytesIO(image_data))
            image.thumbnail((550, 400))
            photo = ImageTk.PhotoImage(image)

            label = tk.Label(self, image=photo, bg=BG_DARK)
            label.image = photo  # keep reference
            label.pack(pady=10)

        except Exception as e:
            tk.Label(self, text=f"Cannot display image: {e}",
                     bg=BG_DARK, fg=DANGER,
                     font=FONT_NORMAL).pack(pady=20)

        tk.Button(self, text="Close",
                  command=self.destroy,
                  bg=DANGER, fg=TEXT_WHITE,
                  font=FONT_BUTTON, relief="flat",
                  cursor="hand2").pack(pady=10)