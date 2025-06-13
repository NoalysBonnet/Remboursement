import customtkinter as ctk
from tkinter import messagebox

class CommentDialog(ctk.CTkToplevel):
    def __init__(self, master, title: str, prompt: str, is_mandatory: bool = False):
        super().__init__(master)
        self.transient(master)
        self.grab_set()
        self.title(title)
        self.geometry("450x300")
        self.resizable(False, False)

        self._comment = None
        self._is_mandatory = is_mandatory

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        prompt_label_text = f"{prompt}{' (Obligatoire)' if is_mandatory else ' (Optionnel)'}"
        prompt_label = ctk.CTkLabel(main_frame, text=prompt_label_text, wraplength=400, justify="left")
        prompt_label.pack(pady=(0, 10), anchor="w")

        self.comment_textbox = ctk.CTkTextbox(main_frame, height=150)
        self.comment_textbox.pack(expand=True, fill="both")
        self.comment_textbox.focus()

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=(15, 0))

        ctk.CTkButton(button_frame, text="Valider", command=self._on_validate).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Annuler", command=self._on_cancel, fg_color="gray").pack(side="left", padx=10)

    def _on_validate(self):
        comment_text = self.comment_textbox.get("1.0", "end-1c").strip()
        if self._is_mandatory and not comment_text:
            messagebox.showerror("Champ Requis", "Le commentaire est obligatoire pour cette action.", parent=self)
            return

        self._comment = comment_text
        self.destroy()

    def _on_cancel(self):
        self._comment = None
        self.destroy()

    def get_comment(self):
        self.master.wait_window(self)
        return self._comment