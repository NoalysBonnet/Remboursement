from models import user_model
from utils import email_utils, password_utils # password_utils n'est pas directmt utilisé ici, mais par user_model

class AuthController:
    def __init__(self):
        pass # Pas d'état spécifique pour ce contrôleur pour l'instant

    def tenter_connexion(self, nom_utilisateur: str, mot_de_passe_saisi: str) -> str | None:
        """Tente de connecter l'utilisateur. Retourne le nom d'utilisateur si succès, None sinon."""
        info_utilisateur = user_model.obtenir_info_utilisateur(nom_utilisateur)
        if info_utilisateur:
            hachage_stocke = info_utilisateur.get("hashed_password")
            if password_utils.verifier_mdp(mot_de_passe_saisi, hachage_stocke):
                return nom_utilisateur
        return None

    def modifier_mot_de_passe(self, nom_utilisateur: str, ancien_mdp: str, nouveau_mdp: str) -> bool:
        """Gère la modification du mot de passe."""
        return user_model.modifier_mot_de_passe(nom_utilisateur, ancien_mdp, nouveau_mdp)

    def demarrer_procedure_reset_mdp(self, nom_utilisateur: str) -> tuple[bool, str | None, str | None]:
        """
        Démarre la procédure de reset.
        Retourne (succès_envoi_email, email_utilisateur, message_erreur_ou_code_pour_test).
        En production, le code ne serait pas retourné ici.
        """
        info_utilisateur = user_model.obtenir_info_utilisateur(nom_utilisateur)
        if not info_utilisateur or not info_utilisateur.get("email"):
            return False, None, "Utilisateur non trouvé ou email non configuré."

        email_destinataire = info_utilisateur["email"]
        code_reset = user_model.stocker_code_reset_db(nom_utilisateur)

        if not code_reset: # Ne devrait pas arriver si la génération fonctionne
             return False, email_destinataire, "Erreur lors de la génération du code."

        if email_utils.envoyer_email_reset(email_destinataire, nom_utilisateur, code_reset):
            return True, email_destinataire, None # Succès, pas de message d'erreur
        else:
            # Pour le développement, si l'email échoue, on retourne le code pour pouvoir tester
            print(f"Échec de l'envoi de l'email. Code pour {nom_utilisateur}: {code_reset}")
            return False, email_destinataire, f"L'envoi de l'email a échoué. Code pour test: {code_reset}"


    def verifier_code_et_reinitialiser_mdp(self, nom_utilisateur: str, code_saisi: str, nouveau_mdp: str) -> tuple[bool, str | None]:
        """Vérifie le code et réinitialise le mdp si valide. Retourne (succès, message_erreur_ou_succès)"""
        if user_model.verifier_et_supprimer_code_reset_db(nom_utilisateur, code_saisi):
            if user_model.reinitialiser_mot_de_passe(nom_utilisateur, nouveau_mdp):
                return True, "Mot de passe réinitialisé avec succès."
            else:
                return False, "Erreur lors de la mise à jour du mot de passe." # Ne devrait pas arriver
        else:
            return False, "Code de réinitialisation invalide ou expiré."