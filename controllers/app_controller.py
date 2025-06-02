# C:\Users\maxen\PycharmProjects\PythonProject\controllers\app_controller.py
import customtkinter as ctk
from views.login_view import LoginView
from views.main_view import MainView
from controllers.auth_controller import AuthController

class AppController:
    def __init__(self, root_tk_app):
        self.root = root_tk_app
        self.auth_controller = AuthController()
        self.current_user = None
        self.show_login_view()

    def show_login_view(self):
        """Affiche la vue de connexion."""
        self.current_user = None # Réinitialiser l'utilisateur lors du retour à la connexion
        # Nettoyer la fenêtre racine avant d'afficher une nouvelle vue principale
        for widget in self.root.winfo_children():
            widget.destroy()
        self.login_view = LoginView(self.root, self.auth_controller, self.on_login_success)
        self.root.title("Connexion - Gestion Remboursements")
        self.root.geometry("400x420") # Ajusté pour les boutons

    def on_login_success(self, nom_utilisateur):
        """Appelée lorsque la connexion réussit."""
        self.current_user = nom_utilisateur
        self.show_main_view()

    def show_main_view(self):
        """Affiche la vue principale de l'application."""
        # Nettoyer la fenêtre racine
        for widget in self.root.winfo_children():
            widget.destroy()
        self.main_view = MainView(self.root, self.current_user, self.on_logout)
        self.root.title(f"Gestion Remboursements - {self.current_user}")
        self.root.geometry("900x700")

    def on_logout(self):
        """Appelée lorsque l'utilisateur se déconnecte."""
        # Logique de déconnexion ici si nécessaire (ex: nettoyage de session)
        self.show_login_view()