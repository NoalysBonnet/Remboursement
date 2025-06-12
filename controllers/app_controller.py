# controllers/app_controller.py
import customtkinter as ctk
import os
import sys
from tkinter import messagebox
from views.login_view import LoginView
from views.main_view import MainView
from controllers.auth_controller import AuthController
from controllers.remboursement_controller import RemboursementController
from models import user_model


class AppController:
    def __init__(self, root_tk_app):
        self.root = root_tk_app
        self.auth_controller = AuthController()
        self.remboursement_controller = None
        self.current_user = None
        self.login_view = None
        self.main_view = None

        self._run_startup_tasks()

        self.show_login_view()

    def _run_startup_tasks(self):
        print("Lancement des tâches de démarrage (archivage...).")
        rc_temp = RemboursementController(utilisateur_actuel="system")
        rc_temp.archive_old_requests()
        print("Tâches de démarrage terminées.")

    def _remboursement_controller_factory(self, nom_utilisateur: str) -> RemboursementController:
        if self.remboursement_controller is None:
            self.remboursement_controller = RemboursementController(nom_utilisateur)
        else:
            self.remboursement_controller.utilisateur_actuel = nom_utilisateur
        return self.remboursement_controller

    def show_login_view(self):
        self.current_user = None
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        if self.main_view:
            self.main_view.destroy()
            self.main_view = None

        self.login_view = LoginView(self.root, self.auth_controller, self.on_login_success)
        self.root.title("Connexion - Gestion Remboursements")

    def _show_admin_warning_popup(self):
        title = "⚠️ AVERTISSEMENT - COMPTE ADMINISTRATEUR ⚠️"
        message = (
            "Vous êtes connecté en tant qu'Administrateur.\n\n"
            "Ce compte vous confère des privilèges étendus sur l'application, incluant la capacité d'effectuer toutes les actions et de gérer les utilisateurs.\n\n"
            "**RESPONSABILITÉS ET RISQUES CRITIQUES :**\n\n"
            "1.  **Suppression de Demandes :** Cette action est **IRRÉVERSIBLE**.\n\n"
            "2.  **Gestion des Utilisateurs :** La modification ou la suppression d'un compte a un impact direct sur la traçabilité des actions.\n\n"
            "3.  **Compte 'admin' :** Ne supprimez **JAMAIS** le compte 'admin' principal et ne lui retirez pas son rôle."
        )
        messagebox.showwarning(title, message, parent=self.root)

    def on_login_success(self, nom_utilisateur):
        self.current_user = nom_utilisateur
        user_info = user_model.obtenir_info_utilisateur(nom_utilisateur)

        is_admin = False
        user_theme = "blue"
        user_appearance_mode = "Dark"

        if user_info:
            user_roles = user_info.get("roles", [])
            user_theme = user_info.get("theme_color", "blue")
            user_appearance_mode = user_info.get("appearance_mode", "Dark")
            if "admin" in user_roles:
                is_admin = True

        ctk.set_appearance_mode(user_appearance_mode)
        ctk.set_default_color_theme(user_theme)

        self.show_main_view()

        if is_admin:
            self.root.after(200, self._show_admin_warning_popup)

    def show_main_view(self):
        if self.login_view:
            self.root.focus_set()
            self.login_view.destroy()
            self.login_view = None

        self.main_view = MainView(
            self.root,
            self.current_user,
            self,
            self._remboursement_controller_factory
        )
        self.root.title(f"Gestion Remboursements - {self.current_user}")

    def request_restart(self, reason: str):
        if messagebox.askyesno("Redémarrage Requis",
                               f"{reason}\n\nUn redémarrage de l'application est nécessaire pour appliquer tous les changements.\nVoulez-vous redémarrer maintenant ?"):
            self.on_logout(restart=True)

    def on_logout(self, restart=False):
        if self.main_view:
            self.main_view.stop_polling()

        if restart:
            try:
                python = sys.executable
                os.execl(python, python, *sys.argv)
            except Exception as e:
                print(f"Erreur lors de la tentative de redémarrage : {e}")
                messagebox.showinfo("Redémarrage Manuel Requis",
                                    "Le redémarrage automatique a échoué. Veuillez fermer et relancer l'application manuellement.",
                                    parent=self.root)
        else:
            self.show_login_view()