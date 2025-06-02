# C:\Users\maxen\PycharmProjects\PythonProject\app.py
import customtkinter as ctk
from controllers.app_controller import AppController
from config.settings import ensure_data_dir_exists  # Pour créer le dossier de données au démarrage si besoin


class MainApplication(ctk.CTk):
    def __init__(self):
        super().__init__()

        ensure_data_dir_exists()  # S'assurer que le dossier de données existe

        ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

        self.title("Application de Gestion")  # Titre initial, sera changé par les vues
        self.geometry("400x400")  # Géométrie initiale, sera changée par les vues

        self.app_controller = AppController(self)  # Passer la fenêtre racine au contrôleur


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()