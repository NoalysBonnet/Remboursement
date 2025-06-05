import json
import os
import time
import random
import string
import tempfile
from utils.password_utils import generer_hachage_mdp, verifier_mdp
from config.settings import USER_DATA_FILE, RESET_CODES_FILE, ensure_data_dir_exists, ASSIGNABLE_ROLES

ensure_data_dir_exists()


def _charger_fichier_json(chemin_fichier: str) -> dict:
    if os.path.exists(chemin_fichier):
        try:
            with open(chemin_fichier, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}


def _sauvegarder_fichier_json_atomic(chemin_fichier: str, donnees: dict):
    dir_name = os.path.dirname(chemin_fichier)
    if not os.path.exists(dir_name):
        try:
            os.makedirs(dir_name)
        except OSError as e:
            print(f"Erreur critique lors de la création du dossier pour la sauvegarde atomique '{dir_name}': {e}")
            raise

    temp_file_path = ""
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False,
                                         dir=dir_name,
                                         prefix=os.path.basename(chemin_fichier).replace('.json', '') + '~',
                                         suffix='.json.tmp') as tf:
            json.dump(donnees, tf, indent=4, ensure_ascii=False)
            temp_file_path = tf.name

        os.replace(temp_file_path, chemin_fichier)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde atomique de {chemin_fichier}: {e}")
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                pass
        raise


def obtenir_tous_les_utilisateurs() -> dict:
    return _charger_fichier_json(USER_DATA_FILE)


def sauvegarder_les_utilisateurs(donnees_utilisateurs: dict):
    _sauvegarder_fichier_json_atomic(USER_DATA_FILE, donnees_utilisateurs)


def ajouter_utilisateur_db(nom_utilisateur: str, mot_de_passe: str, email: str, roles: list[str] | None = None) -> bool:
    utilisateurs = obtenir_tous_les_utilisateurs()
    if nom_utilisateur in utilisateurs:
        return False

    hachage = generer_hachage_mdp(mot_de_passe)
    user_data = {
        "hashed_password": hachage,
        "email": email,
        "roles": sorted(list(set(roles if roles is not None else [])))
    }
    utilisateurs[nom_utilisateur] = user_data
    sauvegarder_les_utilisateurs(utilisateurs)
    return True


def mettre_a_jour_utilisateur_db(
        login_original: str,
        nouveau_login: str,
        nouvel_email: str,
        nouveaux_roles: list[str],
        nouveau_mot_de_passe: str | None = None
) -> tuple[bool, str]:
    utilisateurs = obtenir_tous_les_utilisateurs()

    if login_original not in utilisateurs:
        return False, "Utilisateur original non trouvé."

    if login_original != nouveau_login and nouveau_login in utilisateurs:
        return False, f"Le nouveau login '{nouveau_login}' est déjà utilisé par un autre compte."

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
    sauvegarder_les_utilisateurs(utilisateurs)
    return True, f"Utilisateur '{login_original}' mis à jour avec succès (login: '{nouveau_login}')."


def utilisateur_existant(nom_utilisateur: str) -> bool:
    utilisateurs = obtenir_tous_les_utilisateurs()
    return nom_utilisateur in utilisateurs


def obtenir_info_utilisateur(nom_utilisateur: str) -> dict | None:
    utilisateurs = obtenir_tous_les_utilisateurs()
    return utilisateurs.get(nom_utilisateur)


def modifier_mot_de_passe(nom_utilisateur: str, ancien_mdp_saisi: str, nouveau_mdp: str) -> bool:
    info_utilisateur = obtenir_info_utilisateur(nom_utilisateur)
    if info_utilisateur and verifier_mdp(ancien_mdp_saisi, info_utilisateur.get("hashed_password")):
        nouveau_hachage = generer_hachage_mdp(nouveau_mdp)
        utilisateurs = obtenir_tous_les_utilisateurs()
        utilisateurs[nom_utilisateur]["hashed_password"] = nouveau_hachage
        sauvegarder_les_utilisateurs(utilisateurs)
        return True
    return False


def reinitialiser_mot_de_passe(nom_utilisateur: str, nouveau_mdp: str) -> bool:
    utilisateurs = obtenir_tous_les_utilisateurs()
    if nom_utilisateur in utilisateurs:
        nouveau_hachage = generer_hachage_mdp(nouveau_mdp)
        utilisateurs[nom_utilisateur]["hashed_password"] = nouveau_hachage
        sauvegarder_les_utilisateurs(utilisateurs)
        return True
    return False


def supprimer_utilisateur_db(nom_utilisateur: str) -> bool:
    utilisateurs = obtenir_tous_les_utilisateurs()
    if nom_utilisateur in utilisateurs:
        if nom_utilisateur == "admin":
            print("Erreur: Le compte 'admin' principal ne peut pas être supprimé.")
            return False
        del utilisateurs[nom_utilisateur]
        sauvegarder_les_utilisateurs(utilisateurs)
        return True
    return False


def _generer_code_alphanumerique(longueur=5) -> str:
    return "".join(random.choices(string.digits, k=longueur))


def stocker_code_reset_db(nom_utilisateur: str, duree_validite_sec: int = 300) -> str | None:
    codes_actifs = _charger_fichier_json(RESET_CODES_FILE)
    code = _generer_code_alphanumerique()

    codes_actifs[nom_utilisateur] = {
        "code": code,
        "expiration": time.time() + duree_validite_sec
    }
    _sauvegarder_fichier_json_atomic(RESET_CODES_FILE, codes_actifs)
    return code


def verifier_et_supprimer_code_reset_db(nom_utilisateur: str, code_saisi: str) -> bool:
    codes_actifs = _charger_fichier_json(RESET_CODES_FILE)
    info_code = codes_actifs.get(nom_utilisateur)
    valide = False

    if info_code and info_code["code"] == code_saisi:
        if time.time() < info_code["expiration"]:
            valide = True
        else:
            print(f"Code de réinitialisation pour {nom_utilisateur} expiré.")

    if nom_utilisateur in codes_actifs:
        del codes_actifs[nom_utilisateur]
        _sauvegarder_fichier_json_atomic(RESET_CODES_FILE, codes_actifs)

    return valide