# utils/ui_messages.py
import os
import tkinter
from tkinter import messagebox

def _show_popup(title, message, a_icon):
    """Fonction helper pour afficher une popup sans la fenêtre principale."""
    root = tkinter.Tk()
    root.withdraw()
    messagebox.showinfo(title, message, icon=a_icon)
    root.destroy()

def show_recovery_success(file_path):
    filename = os.path.basename(file_path)
    title = "Récupération de Données Réussie"
    message = (
        f"Le fichier de données '{filename}' a été détecté comme étant endommagé.\n\n"
        "L'application l'a automatiquement restauré à partir de la dernière sauvegarde valide.\n\n"
        "Vous pouvez continuer à travailler. La dernière action effectuée avant l'erreur a peut-être été perdue."
    )
    _show_popup(title, message, a_icon=messagebox.WARNING)

def show_recovery_error(file_path, backup_exists):
    filename = os.path.basename(file_path)
    title = "Erreur Critique de Données"
    if backup_exists:
        message = (
            f"Le fichier de données '{filename}' et sa sauvegarde sont tous les deux illisibles.\n\n"
            "La récupération automatique a échoué. Pour éviter de bloquer l'application, le fichier a été réinitialisé.\n\n"
            "Veuillez contacter le support technique si des données importantes ont été perdues."
        )
    else:
        message = (
            f"Le fichier de données '{filename}' est illisible et aucune sauvegarde n'a pu être trouvée.\n\n"
            "Pour éviter de bloquer l'application, le fichier a été réinitialisé.\n\n"
            "Veuillez contacter le support technique si des données importantes ont été perdues."
        )
    _show_popup(title, message, a_icon=messagebox.ERROR)