# models/user_model.py
import os
import time
import random
import string
from utils.password_utils import generer_hachage_mdp, verifier_mdp
from config.settings import USER_DATA_FILE, RESET_CODES_FILE, ASSIGNABLE_ROLES
from utils.data_manager import read_modify_write_json, load_json_data

def obtenir_tous_les_utilisateurs() -> dict:
    return load_json_data(USER_DATA_FILE)


def sauvegarder_les_utilisateurs(donnees_utilisateurs: dict):
    def modification(data: dict):
        data.clear()
        data.update(donnees_utilisateurs)

    read_modify_write_json(USER_DATA_FILE, modification)


def ajouter_utilisateur_db(nom_utilisateur: str, mot_de_passe: str, email: str, roles: list[str] | None = None) -> bool:
    def modification(utilisateurs: dict) -> bool:
        if nom_utilisateur in utilisateurs:
            return False

        hachage = generer_hachage_mdp(mot_de_passe)
        user_data = {
            "hashed_password": hachage,
            "email": email,
            "roles": sorted(list(set(roles if roles is not None else [])))
        }
        utilisateurs[nom_utilisateur] = user_data
        return True

    return read_modify_write_json(USER_DATA_FILE, modification)


def mettre_a_jour_utilisateur_db(
        login_original: str,
        nouveau_login: str,
        nouvel_email: str,
        nouveaux_roles: list[str],
        nouveau_mot_de_passe: str | None = None
) -> tuple[bool, str]:
    result = {"success": False, "message": ""}

    def modification(utilisateurs: dict) -> bool:
        if login_original not in utilisateurs:
            result["message"] = "Utilisateur original non trouvé."
            return False

        if login_original != nouveau_login and nouveau_login in utilisateurs:
            result["message"] = f"Le nouveau login '{nouveau_login}' est déjà utilisé par un autre compte."
            return False

        user_data = utilisateurs.pop(login_original)

        user_data["email"] = nouvel_email
        valid_roles = []
        if nouveau_login == "admin":
            valid_roles.append("admin")
        for role in nouveaux_roles:
            if role in ASSIGNABLE_ROLES and role not in valid_roles:
                valid_roles.append(role)
        user_data["roles"] = sorted(list(set(valid_roles)))

        if nouveau_mot_de_passe:
            user_data["hashed_password"] = generer_hachage_mdp(nouveau_mot_de_passe)

        utilisateurs[nouveau_login] = user_data
        result["success"] = True
        result["message"] = f"Utilisateur '{login_original}' mis à jour avec succès (login: '{nouveau_login}')."
        return True

    read_modify_write_json(USER_DATA_FILE, modification)
    return result["success"], result["message"]


def utilisateur_existant(nom_utilisateur: str) -> bool:
    utilisateurs = obtenir_tous_les_utilisateurs()
    return nom_utilisateur in utilisateurs


def obtenir_info_utilisateur(nom_utilisateur: str) -> dict | None:
    utilisateurs = obtenir_tous_les_utilisateurs()
    return utilisateurs.get(nom_utilisateur)


def modifier_mot_de_passe(nom_utilisateur: str, ancien_mdp_saisi: str, nouveau_mdp: str) -> bool:
    def modification(utilisateurs: dict) -> bool:
        info_utilisateur = utilisateurs.get(nom_utilisateur)
        if info_utilisateur and verifier_mdp(ancien_mdp_saisi, info_utilisateur.get("hashed_password")):
            nouveau_hachage = generer_hachage_mdp(nouveau_mdp)
            utilisateurs[nom_utilisateur]["hashed_password"] = nouveau_hachage
            return True
        return False

    return read_modify_write_json(USER_DATA_FILE, modification)


def reinitialiser_mot_de_passe(nom_utilisateur: str, nouveau_mdp: str) -> bool:
    def modification(utilisateurs: dict) -> bool:
        if nom_utilisateur in utilisateurs:
            nouveau_hachage = generer_hachage_mdp(nouveau_mdp)
            utilisateurs[nom_utilisateur]["hashed_password"] = nouveau_hachage
            return True
        return False

    return read_modify_write_json(USER_DATA_FILE, modification)


def supprimer_utilisateur_db(nom_utilisateur: str) -> bool:
    def modification(utilisateurs: dict) -> bool:
        if nom_utilisateur in utilisateurs:
            if nom_utilisateur == "admin":
                print("Erreur: Le compte 'admin' principal ne peut pas être supprimé.")
                return False
            del utilisateurs[nom_utilisateur]
            return True
        return False

    return read_modify_write_json(USER_DATA_FILE, modification)


def _generer_code_alphanumerique(longueur=5) -> str:
    return "".join(random.choices(string.digits, k=longueur))


def stocker_code_reset_db(nom_utilisateur: str, duree_validite_sec: int = 300) -> str | None:
    code = _generer_code_alphanumerique()

    def modification(codes_actifs: dict) -> bool:
        codes_actifs[nom_utilisateur] = {
            "code": code,
            "expiration": time.time() + duree_validite_sec
        }
        return True

    read_modify_write_json(RESET_CODES_FILE, modification)
    return code


def verifier_et_supprimer_code_reset_db(nom_utilisateur: str, code_saisi: str) -> bool:
    valide = [False]

    def modification(codes_actifs: dict) -> bool:
        info_code = codes_actifs.get(nom_utilisateur)

        if info_code and info_code["code"] == code_saisi:
            if time.time() < info_code["expiration"]:
                valide[0] = True
            else:
                print(f"Code de réinitialisation pour {nom_utilisateur} expiré.")

        if nom_utilisateur in codes_actifs:
            del codes_actifs[nom_utilisateur]

        return True

    read_modify_write_json(RESET_CODES_FILE, modification)
    return valide[0]