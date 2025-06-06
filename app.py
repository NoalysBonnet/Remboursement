import customtkinter as ctk
from controllers.app_controller import AppController
from config.settings import ensure_data_dir_exists

class MainApplication(ctk.CTk):
    def __init__(self):
        super().__init__()

        ensure_data_dir_exists()

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.title("Application de Gestion")

        initial_width = 1024
        initial_height = 768
        self.geometry(f"{int(initial_width)}x{int(initial_height)}")

        # Tentatives de maximisation de la fenêtre
        self.after(100, self.attempt_maximize)

        self.minsize(800, 600)
        self.app_controller = AppController(self)

    def attempt_maximize(self):
        try:
            self.state('zoomed')
        except ctk.TclError:
            try:
                # Pour certains systèmes (comme Windows)
                self.attributes('-zoomed', True)
            except ctk.TclError:
                try:
                    # Fallback pour d'autres systèmes en définissant la géométrie manuellement
                    screen_width = self.winfo_screenwidth()
                    screen_height = self.winfo_screenheight()
                    self.geometry(f"{screen_width}x{screen_height}+0+0")
                except ctk.TclError:
                    # Si tout échoue, la taille initiale sera utilisée
                    pass

if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()