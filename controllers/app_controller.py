from views.login_view import LoginView
from views.main_view import MainView
from controllers.auth_controller import AuthController
from controllers.remboursement_controller import RemboursementController
from models import user_model  # Importé pour obtenir les rôles de l'utilisateur
from tkinter import messagebox  # Importé pour le popup


class AppController:
    def __init__(self, root_tk_app):  #
        self.root = root_tk_app  #
        self.auth_controller = AuthController()  #
        self.current_user = None  #
        self.show_login_view()  #

    def _remboursement_controller_factory(self, nom_utilisateur: str) -> RemboursementController:  #
        return RemboursementController(nom_utilisateur)  #

    def show_login_view(self):  #
        self.current_user = None  #
        for widget in self.root.winfo_children():  #
            widget.destroy()  #
        self.login_view = LoginView(self.root, self.auth_controller, self.on_login_success)  #
        self.root.title("Connexion - Gestion Remboursements")  #

    def _show_admin_warning_popup(self):
        title = "Avertissement - Compte Administrateur"
        message = (
            "Vous êtes connecté en tant qu'Administrateur.\n\n"
            "Ce compte vous confère des droits étendus sur l'application, incluant :\n"
            "  - La capacité d'effectuer toutes les actions des autres utilisateurs.\n"
            "  - La suppression définitive des demandes de remboursement.\n"
            "  - La création, modification et suppression des comptes utilisateurs.\n\n"
            "⚠️ **Responsabilités et Risques** ⚠️\n"
            "  - La suppression de demandes est IRRÉVERSIBLE et efface tous les fichiers associés.\n"
            "  - La modification ou suppression d'utilisateurs peut impacter leur accès et la traçabilité de leurs actions.\n"
            "  - Ne supprimez JAMAIS le compte 'admin' principal et ne lui retirez pas son rôle 'admin', sous peine de perdre l'accès aux fonctions d'administration.\n\n"
            "Veuillez utiliser ces privilèges avec la plus grande prudence et uniquement lorsque cela est nécessaire."
        )
        messagebox.showwarning(title, message, parent=self.root)

    def on_login_success(self, nom_utilisateur):  #
        self.current_user = nom_utilisateur  #

        # Vérifier si l'utilisateur est admin pour afficher l'avertissement
        user_info = user_model.obtenir_info_utilisateur(nom_utilisateur)  #
        is_admin = False
        if user_info:
            user_roles = user_info.get("roles", [])
            if "admin" in user_roles:
                is_admin = True

        if is_admin:
            self._show_admin_warning_popup()

        self.show_main_view()  #

    def show_main_view(self):  #
        for widget in self.root.winfo_children():  #
            widget.destroy()  #
        self.main_view = MainView(  #
            self.root,  #
            self.current_user,  #
            self.on_logout,  #
            self._remboursement_controller_factory,  #
            self.auth_controller  #
        )
        self.root.title(f"Gestion Remboursements - {self.current_user}")  #

    def on_logout(self):  #
        if hasattr(self, 'main_view') and self.main_view:  #
            self.main_view.stop_polling()  #
        self.show_login_view()  #