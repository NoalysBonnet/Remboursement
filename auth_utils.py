# auth_utils.py
import json
import os
from passlib.context import CryptContext
from config.settings import USER_DATA_FILE
from utils.data_manager import load_json_data, read_modify_write_json

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generer_hachage_mdp(mot_de_passe: str) -> str:
    """Génère un hachage sécurisé pour un mot de passe."""
    return pwd_context.hash(mot_de_passe)


def verifier_mdp(mot_de_passe_saisi: str, hachage_stocke: str) -> bool:
    """Vérifie un mot de passe saisi par rapport à un hachage stocké."""
    return pwd_context.verify(mot_de_passe_saisi, hachage_stocke)


def charger_donnees_utilisateurs() -> dict:
    """Charge les données des utilisateurs depuis le fichier JSON centralisé."""
    return load_json_data(USER_DATA_FILE)


def sauvegarder_donnees_utilisateurs(donnees: dict):
    """Sauvegarde les données des utilisateurs dans le fichier JSON centralisé."""

    def modification(data):
        data.clear()
        data.update(donnees)

    read_modify_write_json(USER_DATA_FILE, modification)


def ajouter_utilisateur_si_necessaire(nom_utilisateur: str, mot_de_passe: str):
    """Ajoute un utilisateur avec son mot de passe haché s'il n'existe pas, ou met à jour son mot de passe."""
    hachage = generer_hachage_mdp(mot_de_passe)

    def modification(donnees):
        donnees[nom_utilisateur] = hachage

    # Cette fonction n'est plus utilisée, mais on la garde au cas où.
    # La gestion des utilisateurs se fait maintenant via user_model.
    # read_modify_write_json(USER_DATA_FILE, modification)
    print(f"Utilisateur '{nom_utilisateur}' ajouté/mis à jour dans {USER_DATA_FILE}")


def recuperer_hachage_utilisateur(nom_utilisateur: str) -> str | None:
    """Récupère le hachage du mot de passe pour un utilisateur donné."""
    donnees = charger_donnees_utilisateurs()
    return donnees.get(nom_utilisateur)