# views/profile_view.py
import os
import shutil
import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image, ImageDraw, ImageFont

from config.settings import PROFILE_PICTURES_DIR
from utils.image_utils import create_circular_image


class ProfileView(ctk.CTkToplevel):
    def __init__(self, master, current_user: str, auth_controller, user_data: dict, on_save_callback):
        super().__init__(master)
        self.transient(master)
        self.grab_set()
        self.title(f"Profil de {current_user}")
        self.geometry("500x650")
        self.resizable(False, False)

        self.current_user = current_user
        self.auth_controller = auth_controller
        self.on_save_callback = on_save_callback

        self.new_profile_pic_source_path = None
        self.profile_pic_rel_path = user_data.get("profile_picture_path")

        main_frame = ctk.CTkFrame(self)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # --- Photo de profil ---
        self.pfp_size = 80
        self.pfp_label = ctk.CTkLabel(main_frame, text="", width=self.pfp_size, height=self.pfp_size)
        self.pfp_label.pack(pady=(10, 5))
        self.load_profile_picture()

        ctk.CTkButton(main_frame, text="Changer de photo", command=self._select_profile_picture).pack(pady=5)

        # --- Informations ---
        ctk.CTkLabel(main_frame, text="Adresse e-mail:", anchor="w").pack(fill="x", padx=20, pady=(15, 2))
        self.email_entry = ctk.CTkEntry(main_frame)
        self.email_entry.insert(0, user_data.get("email", ""))
        self.email_entry.pack(fill="x", padx=20)

        # --- Changer le mot de passe ---
        ctk.CTkLabel(main_frame, text="Ancien mot de passe:", anchor="w").pack(fill="x", padx=20, pady=(15, 2))
        self.old_password_entry = ctk.CTkEntry(main_frame, show="*")
        self.old_password_entry.pack(fill="x", padx=20)

        ctk.CTkLabel(main_frame, text="Nouveau mot de passe (laisser vide pour ne pas changer):", anchor="w").pack(
            fill="x", padx=20, pady=(5, 2))
        self.new_password_entry = ctk.CTkEntry(main_frame, show="*")
        self.new_password_entry.pack(fill="x", padx=20)

        # --- Préférences ---
        ctk.CTkLabel(main_frame, text="Thème de couleur de l'application:", anchor="w").pack(fill="x", padx=20,
                                                                                             pady=(15, 2))
        themes = ["blue", "dark-blue", "green"]
        self.theme_menu = ctk.CTkOptionMenu(main_frame, values=themes)
        self.theme_menu.set(user_data.get("theme_color", "blue"))
        self.theme_menu.pack(fill="x", padx=20)

        ctk.CTkLabel(main_frame, text="Filtre par défaut au démarrage:", anchor="w").pack(fill="x", padx=20,
                                                                                          pady=(15, 2))
        filters = ["Toutes les demandes", "En attente de mon action", "En cours", "Terminées et annulées"]
        self.filter_menu = ctk.CTkOptionMenu(main_frame, values=filters)
        self.filter_menu.set(user_data.get("default_filter", "Toutes les demandes"))
        self.filter_menu.pack(fill="x", padx=20)

        # --- Boutons ---
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=30)
        ctk.CTkButton(button_frame, text="Enregistrer", command=self._save_profile, width=150).pack(side="left",
                                                                                                    padx=10)
        ctk.CTkButton(button_frame, text="Annuler", command=self.destroy, fg_color="gray").pack(side="left", padx=10)

    def load_profile_picture(self):
        pfp_image = None
        if self.profile_pic_rel_path:
            full_path = os.path.join(PROFILE_PICTURES_DIR, self.profile_pic_rel_path)
            if os.path.exists(full_path):
                pfp_image = create_circular_image(full_path, self.pfp_size)

        if pfp_image:
            self.pfp_label.configure(image=pfp_image)
        else:
            pfp_size = self.pfp_size
            placeholder = Image.new('RGBA', (pfp_size, pfp_size), (80, 80, 80, 255))
            draw = ImageDraw.Draw(placeholder)
            try:
                font = ImageFont.truetype("arial", 40)
            except IOError:
                font = ImageFont.load_default()
            draw.text((pfp_size / 2, pfp_size / 2), self.current_user[0].upper(), font=font, anchor="mm")
            ctk_placeholder = ctk.CTkImage(light_image=placeholder, dark_image=placeholder, size=(pfp_size, pfp_size))
            self.pfp_label.configure(image=ctk_placeholder)

    def _select_profile_picture(self):
        filepath = filedialog.askopenfilename(
            title="Choisir une photo de profil",
            filetypes=(("Images", "*.png *.jpg *.jpeg *.gif *.bmp"), ("Tous les fichiers", "*.*"))
        )
        if filepath:
            self.new_profile_pic_source_path = filepath
            pfp_image = create_circular_image(filepath, self.pfp_size)
            if pfp_image:
                self.pfp_label.configure(image=pfp_image)

    def _handle_picture_save(self) -> str | None:
        if not self.new_profile_pic_source_path:
            return self.profile_pic_rel_path

        _, extension = os.path.splitext(self.new_profile_pic_source_path)
        new_filename = f"pfp_{self.current_user}{extension}"
        destination_path = os.path.join(PROFILE_PICTURES_DIR, new_filename)

        try:
            shutil.copy2(self.new_profile_pic_source_path, destination_path)
            return new_filename
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'enregistrer la photo de profil : {e}", parent=self)
            return self.profile_pic_rel_path

    def _save_profile(self):
        new_email = self.email_entry.get().strip()
        old_password = self.old_password_entry.get()
        new_password = self.new_password_entry.get()

        if new_password and not old_password:
            messagebox.showerror("Erreur", "Veuillez entrer votre ancien mot de passe pour le modifier.", parent=self)
            return

        new_pfp_rel_path = self._handle_picture_save()

        updated_prefs = {
            "theme_color": self.theme_menu.get(),
            "default_filter": self.filter_menu.get(),
            "profile_picture_path": new_pfp_rel_path
        }

        success, message = self.auth_controller.update_user_profile(
            login=self.current_user,
            new_email=new_email,
            old_password=old_password if old_password else None,
            new_password=new_password if new_password else None,
            preferences=updated_prefs
        )

        if success:
            messagebox.showinfo("Succès", "Profil mis à jour avec succès.", parent=self)
            if self.on_save_callback:
                self.on_save_callback()
            self.destroy()
        else:
            messagebox.showerror("Erreur", message, parent=self)