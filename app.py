import customtkinter as ctk
from controllers.app_controller import AppController
from config.settings import ensure_data_dir_exists
import logging
import os
import sys
import tkinter  # Importation pour tkinter.TclError

# --- Configuration du Logging ---
log_file_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(
    os.path.abspath(__file__))
log_file_path = os.path.join(log_file_dir, "app_gestion_remboursements.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(module)s.%(funcName)s:%(lineno)d] - %(message)s',
    handlers=[logging.FileHandler(log_file_path, encoding='utf-8', mode='a'), logging.StreamHandler()]
)
logging.info("Début du logging pour l'application.")

# --- Importation et Initialisation de TkinterDnD2 ---
TkinterDnD = None
dnd_ready = False
try:
    from tkinterdnd2 import \
        TkinterDnD as TkinterDnD_Class  # Renommer pour éviter conflit si TkinterDnD est déjà un nom de variable

    TkinterDnD = TkinterDnD_Class  # Le rendre accessible globalement si l'import réussit
    dnd_ready = True
    logging.info("Module TkinterDnD2 (classe TkinterDnD) importé avec succès.")
except ImportError:
    logging.warning("IMPORT ERROR: TkinterDnD2 non trouvé. Le glisser-déposer sera désactivé.")
except Exception as e_imp:
    logging.error(f"Erreur inattendue lors de l'import de TkinterDnD2: {e_imp}", exc_info=True)


class MainApplication:  # N'hérite plus de ctk.CTk ni de TkinterDnD.Tk directement ici
    def __init__(self):
        self.root = None
        self.dnd_initialized_successfully = False

        if dnd_ready and TkinterDnD is not None:
            try:
                # La fenêtre racine EST une TkinterDnD.Tk()
                self.root = TkinterDnD.Tk()
                self.dnd_initialized_successfully = True
                logging.info("Fenêtre racine créée avec TkinterDnD.Tk().")

                # Test immédiat si les commandes tkdnd sont chargées
                version = self.root.tk.call('package', 'require', 'tkdnd')
                logging.info(f"Version du package Tcl tkdnd chargée : {version}. Le DnD devrait être fonctionnel.")

            except tkinter.TclError as e_pkg:
                logging.error(
                    f"ÉCHEC CRITIQUE du chargement du package Tcl 'tkdnd': {e_pkg}. Le DnD ne fonctionnera PAS.",
                    exc_info=True)
                self.dnd_initialized_successfully = False
                # Fallback vers une fenêtre Tkinter standard si TkinterDnD.Tk() échoue au chargement du package Tcl
                if self.root:
                    try:
                        self.root.destroy()
                    except:
                        pass
                self.root = tkinter.Tk()  # Fenêtre Tkinter de base
                logging.warning(
                    "Fallback vers une racine tkinter.Tk() standard car TkinterDnD a échoué à charger son package Tcl.")
            except Exception as e_dnd_root:
                logging.error(f"Erreur lors de la création de la racine TkinterDnD.Tk(): {e_dnd_root}", exc_info=True)
                self.dnd_initialized_successfully = False
                if self.root:
                    try:
                        self.root.destroy()
                    except:
                        pass
                self.root = tkinter.Tk()
                logging.warning("Fallback vers une racine tkinter.Tk() standard.")
        else:
            # Si TkinterDnD n'est pas disponible, créer une racine Tkinter standard
            # CustomTkinter a besoin d'une racine Tkinter pour y attacher ses fonctionnalités de theming etc.
            self.root = tkinter.Tk()  # Ctk.CTk() aurait fait ça aussi.
            logging.info("TkinterDnD non disponible, création d'une racine tkinter.Tk() standard.")

        # Appliquer les configurations et le theming CustomTkinter à la fenêtre racine
        # CTk s'attend à ce que sa racine soit une instance de tkinter.Tk (ce que TkinterDnD.Tk est aussi)
        try:
            # Initialiser les aspects CustomTkinter sur la racine existante
            # Cela n'est pas fait en héritant de ctk.CTk directement pour la classe MainApplication,
            # mais en utilisant la racine créée (soit TkinterDnD.Tk, soit tkinter.Tk) comme maître pour les widgets CTk.
            # Les fonctions globales de CTk pour le thème s'appliqueront.
            ctk.set_appearance_mode("System")
            ctk.set_default_color_theme("blue")
            self.root.title("Application de Gestion")  # Définir le titre sur la racine

            # Créer un CTkFrame principal qui remplira la fenêtre racine
            # C'est ce frame qui deviendra le "master" pour le reste de l'interface CTk.
            self.ctk_root_frame = ctk.CTkFrame(self.root, fg_color="transparent")
            self.ctk_root_frame.pack(expand=True, fill="both")

        except Exception as e_ctk_setup:
            logging.error(f"Erreur lors de la configuration de CustomTkinter sur la racine: {e_ctk_setup}",
                          exc_info=True)
            # Si cela échoue, l'application risque de ne pas avoir l'apparence CTk.
            # On pourrait choisir de quitter ou de continuer avec une UI potentiellement dégradée.
            if not isinstance(self.root, tkinter.Tk):  # S'assurer qu'on a au moins une racine Tk
                self.root = tkinter.Tk()
                self.root.title("Erreur - App Gestion")
            # Afficher l'erreur dans la fenêtre elle-même
            error_label = tkinter.Label(self.root,
                                        text=f"Erreur initialisation CTk: {e_ctk_setup}\nConsultez les logs.",
                                        foreground="red", font=("Arial", 16))
            error_label.pack(padx=20, pady=20, expand=True, fill="both")
            self.root.geometry("600x200")
            return  # Arrêter l'initialisation de l'UI si CTk ne peut pas être configuré

        ensure_data_dir_exists()

        initial_width = 1024
        initial_height = 768
        self.root.geometry(f"{int(initial_width)}x{int(initial_height)}")
        self.root.update_idletasks()

        def attempt_maximize():
            try:
                self.root.state('zoomed')
            except tkinter.TclError:  # Utiliser tkinter.TclError ici
                try:
                    self.root.attributes('-zoomed', True)
                except tkinter.TclError:
                    try:
                        screen_width = self.root.winfo_screenwidth()
                        screen_height = self.root.winfo_screenheight()
                        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
                    except tkinter.TclError as e_geom:
                        logging.error(f"Impossible de maximiser ou redimensionner: {e_geom}", exc_info=True)

        self.root.after(100, attempt_maximize)
        self.root.minsize(800, 600)

        # L'AppController prend maintenant le CTkFrame principal comme "root" pour l'UI
        self.app_controller = AppController(self.ctk_root_frame,
                                            self.root)  # Passer aussi la vraie racine pour les Toplevels

    def mainloop(self):
        if self.root:
            self.root.mainloop()


if __name__ == "__main__":
    app = MainApplication()
    # La vérification du package tkdnd est maintenant faite dans __init__
    # Si dnd_initialized_successfully est False après __init__, le DnD ne fonctionnera pas.
    # Le logger aura déjà indiqué le succès ou l'échec du chargement du package Tcl tkdnd.
    if hasattr(app, 'root') and app.root:  # Vérifier si la racine a été créée
        app.mainloop()
    else:
        logging.critical("La fenêtre racine de l'application n'a pas pu être créée. Fermeture.")