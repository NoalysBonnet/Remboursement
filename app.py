import customtkinter as ctk
from controllers.app_controller import AppController
from config.settings import ensure_data_dir_exists  # Pour créer le dossier de données au démarrage si besoin


class MainApplication(ctk.CTk):
    def __init__(self):
        super().__init__()

        ensure_data_dir_exists()

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.title("Application de Gestion")

        # Définir une taille initiale raisonnable avant la tentative de maximisation.
        # Cela peut aider certains gestionnaires de fenêtres.
        initial_width = 1024  # ou self.winfo_screenwidth() // 1.5
        initial_height = 768  # ou self.winfo_screenheight() // 1.5
        self.geometry(f"{int(initial_width)}x{int(initial_height)}")

        # Forcer Tkinter à traiter les événements de géométrie initiaux
        # avant de tenter la maximisation.
        self.update_idletasks()

        # Fonction pour maximiser la fenêtre
        def attempt_maximize():
            try:
                self.state('zoomed')
                # print("INFO: Tentative de maximisation avec self.state('zoomed')")
            except ctk.TclError:
                try:
                    self.attributes('-zoomed', True)  # Alternative pour certains systèmes Unix
                    # print("INFO: Tentative de maximisation avec self.attributes('-zoomed', True)")
                except ctk.TclError:
                    # Solution de repli : définir la géométrie à la taille de l'écran
                    # Cela ne maximise pas toujours la fenêtre de la même manière (pas d'icône "maximisé")
                    # mais remplit l'écran.
                    try:
                        screen_width = self.winfo_screenwidth()
                        screen_height = self.winfo_screenheight()
                        # Positionner en haut à gauche
                        self.geometry(f"{screen_width}x{screen_height}+0+0")
                        # print(f"INFO: Fenêtre redimensionnée manuellement à {screen_width}x{screen_height}")
                    except ctk.TclError as e_geom:
                        print(f"ERREUR: Impossible de maximiser ou redimensionner la fenêtre: {e_geom}")

        # Retarder légèrement l'appel à la maximisation
        # 50-100ms est souvent suffisant pour que la fenêtre soit prête.
        self.after(100, attempt_maximize)

        # Définir une taille minimale pour que la fenêtre ne devienne pas trop petite si "dé-maximisée"
        self.minsize(800, 600)

        self.app_controller = AppController(self)


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()