import json
import os
import time
import random
import string
from utils.password_utils import generer_hachage_mdp, verifier_mdp
from config.settings import USER_DATA_FILE, RESET_CODES_FILE, ensure_data_dir_exists, ASSIGNABLE_ROLES

ensure_data_dir_exists()


def _charger_fichier_json(chemin_fichier: str) -> dict:  #
    if os.path.exists(chemin_fichier):  #
        try:  #
            with open(chemin_fichier, 'r', encoding='utf-8') as f:  #
                return json.load(f)  #
        except (json.JSONDecodeError, FileNotFoundError):  #
            return {}  #
    return {}  #


def _sauvegarder_fichier_json(chemin_fichier: str, donnees: dict):  #
    with open(chemin_fichier, 'w', encoding='utf-8') as f:  #
        json.dump(donnees, f, indent=4)  #


def obtenir_tous_les_utilisateurs() -> dict:  #
    return _charger_fichier_json(USER_DATA_FILE)  #


def sauvegarder_les_utilisateurs(donnees_utilisateurs: dict):  #
    _sauvegarder_fichier_json(USER_DATA_FILE, donnees_utilisateurs)  #


def ajouter_utilisateur_db(nom_utilisateur: str, mot_de_passe: str, email: str, roles: list[str] | None = None) -> bool:
    """Ajoute un nouvel utilisateur. Retourne True si succès, False si l'utilisateur existe déjà."""
    utilisateurs = obtenir_tous_les_utilisateurs()
    if nom_utilisateur in utilisateurs:
        return False  # L'utilisateur existe déjà

    hachage = generer_hachage_mdp(mot_de_passe)
    user_data = {
        "hashed_password": hachage,
        "email": email,
        "roles": sorted(list(set(roles if roles is not None else [])))  # Assurer des rôles uniques et triés
    }
    utilisateurs[nom_utilisateur] = user_data
    sauvegarder_les_utilisateurs(utilisateurs)
    return True


def mettre_a_jour_utilisateur_db(
        login_original: str,
        nouveau_login: str,  # Peut être le même que l'original
        nouvel_email: str,
        nouveaux_roles: list[str],
        nouveau_mot_de_passe: str | None = None  # Optionnel pour la mise à jour
) -> tuple[bool, str]:
    """Met à jour les informations d'un utilisateur existant, y compris potentiellement son login."""
    utilisateurs = obtenir_tous_les_utilisateurs()

    if login_original not in utilisateurs:
        return False, "Utilisateur original non trouvé."

    # Si le login change et que le nouveau login existe déjà (et n'est pas l'original)
    if login_original != nouveau_login and nouveau_login in utilisateurs:
        return False, f"Le nouveau login '{nouveau_login}' est déjà utilisé par un autre compte."

    user_data = utilisateurs.pop(login_original)  # Retirer l'ancienne entrée si le login change ou pour la reconstruire

    user_data["email"] = nouvel_email
    # Filtrer et valider les rôles pour s'assurer qu'ils sont assignables (sauf si c'est l'admin et qu'il garde son rôle admin)
    valid_roles = []
    if nouveau_login == "admin":  # L'admin doit toujours avoir le rôle admin
        valid_roles.append("admin")
    for role in nouveaux_roles:
        if role in ASSIGNABLE_ROLES and role not in valid_roles:
            valid_roles.append(role)
    user_data["roles"] = sorted(list(set(valid_roles)))

    if nouveau_mot_de_passe:  # Mettre à jour le mot de passe seulement s'il est fourni
        user_data["hashed_password"] = generer_hachage_mdp(nouveau_mot_de_passe)

    utilisateurs[nouveau_login] = user_data  # Ajouter/Remplacer avec le nouveau login
    sauvegarder_les_utilisateurs(utilisateurs)
    return True, f"Utilisateur '{login_original}' mis à jour avec succès (login: '{nouveau_login}')."


def utilisateur_existant(nom_utilisateur: str) -> bool:  #
    utilisateurs = obtenir_tous_les_utilisateurs()  #
    return nom_utilisateur in utilisateurs  #


def obtenir_info_utilisateur(nom_utilisateur: str) -> dict | None:  #
    utilisateurs = obtenir_tous_les_utilisateurs()  #
    return utilisateurs.get(nom_utilisateur)  #


def modifier_mot_de_passe(nom_utilisateur: str, ancien_mdp_saisi: str, nouveau_mdp: str) -> bool:  #
    info_utilisateur = obtenir_info_utilisateur(nom_utilisateur)  #
    if info_utilisateur and verifier_mdp(ancien_mdp_saisi, info_utilisateur.get("hashed_password")):  #
        nouveau_hachage = generer_hachage_mdp(nouveau_mdp)  #
        utilisateurs = obtenir_tous_les_utilisateurs()  #
        utilisateurs[nom_utilisateur]["hashed_password"] = nouveau_hachage  #
        sauvegarder_les_utilisateurs(utilisateurs)  #
        return True  #
    return False  #


def reinitialiser_mot_de_passe(nom_utilisateur: str, nouveau_mdp: str) -> bool:  #
    utilisateurs = obtenir_tous_les_utilisateurs()  #
    if nom_utilisateur in utilisateurs:  #
        nouveau_hachage = generer_hachage_mdp(nouveau_mdp)  #
        utilisateurs[nom_utilisateur]["hashed_password"] = nouveau_hachage  #
        sauvegarder_les_utilisateurs(utilisateurs)  #
        return True  #
    return False  #


def supprimer_utilisateur_db(nom_utilisateur: str) -> bool:  #
    utilisateurs = obtenir_tous_les_utilisateurs()  #
    if nom_utilisateur in utilisateurs:  #
        if nom_utilisateur == "admin":  #
            print("Erreur: Le compte 'admin' principal ne peut pas être supprimé.")  #
            return False  #
        del utilisateurs[nom_utilisateur]  #
        sauvegarder_les_utilisateurs(utilisateurs)  #
        return True  #
    return False  #


def _generer_code_alphanumerique(longueur=5) -> str:  #
    return "".join(random.choices(string.digits, k=longueur))  #


def stocker_code_reset_db(nom_utilisateur: str, duree_validite_sec: int = 300) -> str | None:  #
    codes_actifs = _charger_fichier_json(RESET_CODES_FILE)  #
    code = _generer_code_alphanumerique()  #

    codes_actifs[nom_utilisateur] = {  #
        "code": code,  #
        "expiration": time.time() + duree_validite_sec  #
    }
    _sauvegarder_fichier_json(RESET_CODES_FILE, codes_actifs)  #
    return code  #


def verifier_et_supprimer_code_reset_db(nom_utilisateur: str, code_saisi: str) -> bool:  #
    codes_actifs = _charger_fichier_json(RESET_CODES_FILE)  #
    info_code = codes_actifs.get(nom_utilisateur)  #
    valide = False  #

    if info_code and info_code["code"] == code_saisi:  #
        if time.time() < info_code["expiration"]:  #
            valide = True  #
        else:  #
            print(f"Code de réinitialisation pour {nom_utilisateur} expiré.")  #

    if nom_utilisateur in codes_actifs:  #
        del codes_actifs[nom_utilisateur]  #
        _sauvegarder_fichier_json(RESET_CODES_FILE, codes_actifs)  #

    return valide  #