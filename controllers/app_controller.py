# PythonProject/controllers/app_controller.py
from views.login_view import LoginView
from views.main_view import MainView
from controllers.auth_controller import AuthController
from controllers.remboursement_controller import RemboursementController
from models import user_model 
from tkinter import messagebox

class AppController:
    def __init__(self, ctk_master_frame, true_root_window): # Modifié
        self.ctk_master_frame = ctk_master_frame # Le CTkFrame où l'UI sera construite
        self.true_root_window = true_root_window # La vraie racine Tk (TkinterDnD.Tk ou tkinter.Tk)
        self.auth_controller = AuthController()
        self.current_user = None
        self.show_login_view()

    def _remboursement_controller_factory(self, nom_utilisateur: str) -> RemboursementController:
        return RemboursementController(nom_utilisateur)

    def show_login_view(self):
        self.current_user = None
        for widget in self.ctk_master_frame.winfo_children(): # Nettoyer le frame CTk
            widget.destroy()
        # LoginView est maintenant un enfant du ctk_master_frame.
        # Pour les dialogues (simpledialog, messagebox, CTkToplevel), le parent doit être la vraie fenêtre racine.
        self.login_view = LoginView(self.ctk_master_frame, self.auth_controller, self.on_login_success, self.true_root_window)
        self.true_root_window.title("Connexion - Gestion Remboursements")

    def _show_admin_warning_popup(self):
        title = "Avertissement - Compte Administrateur"
        message = (
            "Vous êtes connecté en tant qu'Administrateur.\n\n" # ... (message identique)
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
        messagebox.showwarning(title, message, parent=self.true_root_window) # Parent est la vraie racine

    def on_login_success(self, nom_utilisateur):
        self.current_user = nom_utilisateur
        user_info = user_model.obtenir_info_utilisateur(nom_utilisateur)
        is_admin = False
        if user_info and "admin" in user_info.get("roles", []):
            is_admin = True
        if is_admin:
            self._show_admin_warning_popup()
        self.show_main_view()

    def show_main_view(self):
        for widget in self.ctk_master_frame.winfo_children(): # Nettoyer le frame CTk
            widget.destroy()
        # MainView est un enfant du ctk_master_frame.
        # Les dialogues créés par MainView utiliseront self.master (qui sera ce ctk_master_frame)
        # ou devront explicitement utiliser self.true_root_window pour les CTkToplevel.
        self.main_view = MainView(
            self.ctk_master_frame, 
            self.current_user,
            self.on_logout,
            self._remboursement_controller_factory,
            self.auth_controller,
            self.true_root_window # Passer la vraie racine
        )
        self.true_root_window.title(f"Gestion Remboursements - {self.current_user}")

    def on_logout(self):
        if hasattr(self, 'main_view') and self.main_view:
            self.main_view.stop_polling()
        self.show_login_view()