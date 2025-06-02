from views.login_view import LoginView
from views.main_view import MainView
from controllers.auth_controller import AuthController
from controllers.remboursement_controller import RemboursementController # NOUVEL IMPORT

class AppController:
    def __init__(self, root_tk_app):
        self.root = root_tk_app
        self.auth_controller = AuthController()
        # self.remboursement_controller = RemboursementController() # Instance unique si partagée ou...
        self.current_user = None
        self.show_login_view()

    def _remboursement_controller_factory(self, nom_utilisateur: str) -> RemboursementController:
        """Crée une instance de RemboursementController avec l'utilisateur actuel."""
        return RemboursementController(nom_utilisateur)


    def show_login_view(self):
        """Affiche la vue de connexion."""
        self.current_user = None
        for widget in self.root.winfo_children():
            widget.destroy()
        self.login_view = LoginView(self.root, self.auth_controller, self.on_login_success)
        self.root.title("Connexion - Gestion Remboursements")

    def on_login_success(self, nom_utilisateur):
        """Appelée lorsque la connexion réussit."""
        self.current_user = nom_utilisateur
        self.show_main_view()

    def show_main_view(self):
        """Affiche la vue principale de l'application."""
        for widget in self.root.winfo_children():
            widget.destroy()
        # Passer une factory ou une instance du contrôleur de remboursement
        self.main_view = MainView(self.root, self.current_user, self.on_logout, self._remboursement_controller_factory)
        self.root.title(f"Gestion Remboursements - {self.current_user}")

    def on_logout(self):
        """Appelée lorsque l'utilisateur se déconnecte."""
        self.show_login_view()