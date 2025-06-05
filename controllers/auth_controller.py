from models import user_model
from utils import email_utils, password_utils
from config.settings import ROLES_UTILISATEURS, ASSIGNABLE_ROLES


class AuthController:
    def __init__(self):
        pass

    def tenter_connexion(self, nom_utilisateur: str, mot_de_passe_saisi: str) -> str | None:
        info_utilisateur = user_model.obtenir_info_utilisateur(nom_utilisateur)
        if info_utilisateur:
            hachage_stocke = info_utilisateur.get("hashed_password")
            if password_utils.verifier_mdp(mot_de_passe_saisi, hachage_stocke):
                return nom_utilisateur
        return None

    def modifier_mot_de_passe(self, nom_utilisateur: str, ancien_mdp: str, nouveau_mdp: str) -> bool:
        return user_model.modifier_mot_de_passe(nom_utilisateur, ancien_mdp, nouveau_mdp)

    def demarrer_procedure_reset_mdp(self, nom_utilisateur: str) -> tuple[bool, str | None, str | None]:
        info_utilisateur = user_model.obtenir_info_utilisateur(nom_utilisateur)
        if not info_utilisateur or not info_utilisateur.get("email"):
            return False, None, "Utilisateur non trouvé ou email non configuré."

        email_destinataire = info_utilisateur["email"]
        code_reset = user_model.stocker_code_reset_db(nom_utilisateur)

        if not code_reset:
            return False, email_destinataire, "Erreur lors de la génération du code."

        if email_utils.envoyer_email_reset(email_destinataire, nom_utilisateur, code_reset):
            return True, email_destinataire, None
        else:
            print(f"Échec de l'envoi de l'email. Code pour {nom_utilisateur}: {code_reset}")
            return False, email_destinataire, f"L'envoi de l'email a échoué. Code pour test: {code_reset}"

    def verifier_code_et_reinitialiser_mdp(self, nom_utilisateur: str, code_saisi: str, nouveau_mdp: str) -> tuple[
        bool, str | None]:
        if user_model.verifier_et_supprimer_code_reset_db(nom_utilisateur, code_saisi):
            if user_model.reinitialiser_mot_de_passe(nom_utilisateur, nouveau_mdp):
                return True, "Mot de passe réinitialisé avec succès."
            else:
                return False, "Erreur lors de la mise à jour du mot de passe."
        else:
            return False, "Code de réinitialisation invalide ou expiré."

    def get_all_users_for_management(self) -> list[dict]:  #
        """Récupère tous les utilisateurs avec leurs détails pour la gestion (sauf l'admin 'admin')."""
        tous_utilisateurs_data = user_model.obtenir_tous_les_utilisateurs()  # Renommé pour clarté
        liste_utilisateurs = []  #
        for username, data in tous_utilisateurs_data.items():  # Utilisation de la variable correcte
            if username != "admin":  #
                user_info = {  #
                    "login": username,  #
                    "email": data.get("email", "N/A"),  #
                    "roles": data.get("roles", [])  #
                }
                liste_utilisateurs.append(user_info)  #
        return sorted(liste_utilisateurs, key=lambda u: u["login"])  #

    def admin_delete_user(self, nom_utilisateur_a_supprimer: str) -> tuple[bool, str]:  #
        """Supprime un utilisateur (appelé par l'admin)."""
        if nom_utilisateur_a_supprimer == "admin":  #
            return False, "Le compte administrateur principal 'admin' ne peut pas être supprimé."  #

        succes = user_model.supprimer_utilisateur_db(nom_utilisateur_a_supprimer)  #
        if succes:  #
            return True, f"L'utilisateur '{nom_utilisateur_a_supprimer}' a été supprimé avec succès."  #
        else:  #
            return False, f"Impossible de supprimer l'utilisateur '{nom_utilisateur_a_supprimer}' (peut-être non trouvé ou une erreur s'est produite)."  #

    def admin_create_user(self, login: str, email: str, mot_de_passe: str, roles: list[str]) -> tuple[bool, str]:  #
        if not all([login, email, mot_de_passe]):  #
            return False, "Login, email et mot de passe sont requis."  #
        if not login.strip() or not email.strip() or not mot_de_passe.strip():  #
            return False, "Login, email et mot de passe ne peuvent pas être vides."  #
        if login == "admin":  #
            return False, "Le login 'admin' est réservé et ne peut pas être créé."  #
        if user_model.utilisateur_existant(login):  #
            return False, f"Le login '{login}' existe déjà."  #

        valid_roles = sorted(list(set(role for role in roles if role in ASSIGNABLE_ROLES)))  #

        if user_model.ajouter_utilisateur_db(login, mot_de_passe, email, valid_roles):  #
            return True, f"Utilisateur '{login}' créé avec succès."  #
        else:  #
            return False, f"Erreur lors de la création de l'utilisateur '{login}'."  #

    def admin_update_user_details(self, login_original: str, nouveau_login: str, new_email: str, new_roles: list[str],
                                  nouveau_mot_de_passe: str | None) -> tuple[bool, str]:  #
        if not all([login_original, nouveau_login, new_email]):  #
            return False, "Le login original, le nouveau login et le nouvel email sont requis."  #
        if not nouveau_login.strip() or not new_email.strip():  #
            return False, "Le nouveau login et le nouvel email ne peuvent pas être vides."  #

        if login_original == "admin" and nouveau_login != "admin":  #
            return False, "Le login du compte administrateur principal 'admin' ne peut pas être modifié."  #
        if login_original == "admin" and "admin" not in new_roles:  # # Assurer que l'admin garde son rôle "admin"
            new_roles.append("admin")  #
        if nouveau_login == "admin" and login_original != "admin":  #
            return False, "Le login 'admin' est réservé."  #

        if nouveau_login != "admin":  #
            valid_roles = [role for role in new_roles if role in ASSIGNABLE_ROLES]  #
        else:  #
            valid_roles = ["admin"] + [role for role in new_roles if role in ASSIGNABLE_ROLES and role != "admin"]  #
        valid_roles = sorted(list(set(valid_roles)))  #

        return user_model.mettre_a_jour_utilisateur_db(login_original, nouveau_login, new_email, valid_roles,
                                                       nouveau_mot_de_passe)  #

    def get_role_descriptions_with_users(self) -> dict:  #
        """Récupère les descriptions des rôles et y ajoute les utilisateurs actuels pour chaque rôle."""
        descriptions = ROLES_UTILISATEURS.copy()  #
        # CRUCIAL: Définir la variable ici
        tous_utilisateurs_data = user_model.obtenir_tous_les_utilisateurs()

        for role_key in descriptions:  #
            # S'assurer que la clé pour les utilisateurs actuels existe et est une liste
            if "utilisateurs_actuels" not in descriptions[role_key] or not isinstance(
                    descriptions[role_key]["utilisateurs_actuels"], list):
                descriptions[role_key]["utilisateurs_actuels"] = []
            else:  # Vider pour recalculer
                descriptions[role_key]["utilisateurs_actuels"] = []

        # CORRECTION: Utiliser la variable correctement définie
        for username, data in tous_utilisateurs_data.items():  #
            user_actual_roles = data.get("roles", [])  #
            for role in user_actual_roles:  #
                if role in descriptions:  #
                    descriptions[role]["utilisateurs_actuels"].append(username)  #
                # Le rôle 'admin' est déjà une clé dans ROLES_UTILISATEURS, donc pas besoin de elif spécial ici si 'admin' est dans ASSIGNABLE_ROLES ou géré via ROLES_UTILISATEURS

        for role_key in descriptions:  #
            descriptions[role_key]["utilisateurs_actuels"] = sorted(
                list(set(descriptions[role_key]["utilisateurs_actuels"])))  #

        return descriptions  #

    def get_assignable_roles(self) -> list[str]:  #
        return ASSIGNABLE_ROLES  #