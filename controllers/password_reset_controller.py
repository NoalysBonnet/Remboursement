class PasswordResetController:
    def __init__(self, auth_controller):
        """
        Initialise le contrôleur pour la réinitialisation de mot de passe.
        :param auth_controller: L'instance du contrôleur d'authentification principal.
        """
        self.auth_controller = auth_controller

    def request_password_reset(self, username: str) -> tuple[bool, str]:
        """
        Gère la demande initiale de réinitialisation de mot de passe.
        Retourne un tuple (succès, message_pour_la_vue).
        """
        success, email_sent_to, message = self.auth_controller.demarrer_procedure_reset_mdp(username)

        if success:
            return True, f"Un code a été envoyé à l'adresse e-mail associée à '{username}'."
        else:
            # Gérer le cas de test où le code est affiché au lieu d'être envoyé
            if message and "Code pour test:" in message:
                return True, f"L'envoi d'email a échoué (mode test), mais vous pouvez procéder.\n{message}"
            return False, message or "Impossible de démarrer la procédure de réinitialisation."

    def reset_password(self, username: str, code: str, new_password: str) -> tuple[bool, str]:
        """
        Tente de finaliser la réinitialisation avec le code et le nouveau mot de passe.
        """
        return self.auth_controller.verifier_code_et_reinitialiser_mdp(username, code, new_password)