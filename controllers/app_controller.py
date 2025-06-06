from views.login_view import LoginView
from views.main_view import MainView
from controllers.auth_controller import AuthController
from controllers.remboursement_controller import RemboursementController
from models import user_model
from tkinter import messagebox


class AppController:
    def __init__(self, root_tk_app):
        self.root = root_tk_app
        self.auth_controller = AuthController()
        self.current_user = None
        self.show_login_view()

    def _remboursement_controller_factory(self, nom_utilisateur: str) -> RemboursementController:
        return RemboursementController(nom_utilisateur)

    def show_login_view(self):
        self.current_user = None
        for widget in self.root.winfo_children():
            widget.destroy()
        self.login_view = LoginView(self.root, self.auth_controller, self.on_login_success)
        self.root.title("Connexion - Gestion Remboursements")

    def _show_admin_warning_popup(self):
        title = "⚠️ AVERTISSEMENT - COMPTE ADMINISTRATEUR ⚠️"
        message = (
            "Vous êtes connecté en tant qu'Administrateur.\n\n"
            "Ce compte vous confère des privilèges étendus sur l'application, incluant la capacité d'effectuer toutes les actions et de gérer les utilisateurs.\n\n"
            "**RESPONSABILITÉS ET RISQUES CRITIQUES :**\n\n"
            "1.  **Suppression de Demandes :** Cette action est **IRRÉVERSIBLE**. Elle efface définitivement la demande et tous les fichiers associés du serveur. Ne l'utilisez qu'en cas de certitude absolue.\n\n"
            "2.  **Gestion des Utilisateurs :** La modification ou la suppression d'un compte utilisateur a un impact direct sur sa capacité à travailler et sur la traçabilité de ses actions.\n\n"
            "3.  **Compte 'admin' :** Ne supprimez **JAMAIS** le compte 'admin' principal et ne lui retirez pas son rôle, sous peine de bloquer définitivement l'accès aux fonctions d'administration.\n\n"
            "Veuillez utiliser ces privilèges avec la plus grande prudence."
        )
        messagebox.showwarning(title, message, parent=self.root)

    def on_login_success(self, nom_utilisateur):
        self.current_user = nom_utilisateur

        user_info = user_model.obtenir_info_utilisateur(nom_utilisateur)
        is_admin = False
        if user_info:
            user_roles = user_info.get("roles", [])
            if "admin" in user_roles:
                is_admin = True

        self.show_main_view()

        if is_admin:
            self.root.after(200, self._show_admin_warning_popup)

    def show_main_view(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.main_view = MainView(
            self.root,
            self.current_user,
            self.on_logout,
            self._remboursement_controller_factory,
            self.auth_controller
        )
        self.root.title(f"Gestion Remboursements - {self.current_user}")

    def on_logout(self):
        if hasattr(self, 'main_view') and self.main_view:
            self.main_view.stop_polling()
        self.show_login_view()