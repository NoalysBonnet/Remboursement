# auth_utils.py
import json
import os
from passlib.context import CryptContext

# --- Configuration pour le développement local ---
# Chemin de base de votre projet
CHEMIN_BASE_PROJET = r"C:\Users\maxen\PycharmProjects\PythonProject"
# Nom du dossier qui simulera le partage réseau
NOM_DOSSIER_MOCK = "donnees_partagees_mock"
# Chemin complet vers le dossier mock
DOSSIER_PARTAGE_LOCAL = os.path.join(CHEMIN_BASE_PROJET, NOM_DOSSIER_MOCK)

# Variable principale utilisée par le reste du code
DOSSIER_PARTAGE = DOSSIER_PARTAGE_LOCAL  # POUR LE DÉVELOPPEMENT LOCAL
# Pour le déploiement final, vous changerez cette ligne pour :
# DOSSIER_PARTAGE = r"\\192.168.197.43\Commun\REMBOURSEMENT"

NOM_FICHIER_UTILISATEURS = os.path.join(DOSSIER_PARTAGE, "utilisateurs.json")
# --- Fin de la configuration pour le développement local ---

# Contexte pour le hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generer_hachage_mdp(mot_de_passe: str) -> str:
    """Génère un hachage sécurisé pour un mot de passe."""
    return pwd_context.hash(mot_de_passe)


def verifier_mdp(mot_de_passe_saisi: str, hachage_stocke: str) -> bool:
    """Vérifie un mot de passe saisi par rapport à un hachage stocké."""
    return pwd_context.verify(mot_de_passe_saisi, hachage_stocke)


def charger_donnees_utilisateurs() -> dict:
    """Charge les données des utilisateurs depuis le fichier JSON."""
    if not os.path.exists(DOSSIER_PARTAGE):
        try:
            os.makedirs(DOSSIER_PARTAGE)
            print(f"Dossier '{DOSSIER_PARTAGE}' créé.")
        except OSError as e:
            print(f"Erreur lors de la création du dossier '{DOSSIER_PARTAGE}': {e}")
            return {}  # Retourne un dict vide si la création échoue

    if os.path.exists(NOM_FICHIER_UTILISATEURS):
        try:
            with open(NOM_FICHIER_UTILISATEURS, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}


def sauvegarder_donnees_utilisateurs(donnees: dict):
    """Sauvegarde les données des utilisateurs dans le fichier JSON."""
    if not os.path.exists(DOSSIER_PARTAGE):
        try:
            os.makedirs(DOSSIER_PARTAGE)
        except OSError as e:
            print(f"Erreur lors de la création du dossier pour la sauvegarde '{DOSSIER_PARTAGE}': {e}")
            return  # Ne pas sauvegarder si le dossier ne peut être créé

    with open(NOM_FICHIER_UTILISATEURS, 'w', encoding='utf-8') as f:
        json.dump(donnees, f, indent=4)


def ajouter_utilisateur_si_necessaire(nom_utilisateur: str, mot_de_passe: str):
    """Ajoute un utilisateur avec son mot de passe haché s'il n'existe pas, ou met à jour son mot de passe."""
    donnees = charger_donnees_utilisateurs()
    hachage = generer_hachage_mdp(mot_de_passe)
    donnees[nom_utilisateur] = hachage
    sauvegarder_donnees_utilisateurs(donnees)
    print(f"Utilisateur '{nom_utilisateur}' ajouté/mis à jour dans {NOM_FICHIER_UTILISATEURS}")


def recuperer_hachage_utilisateur(nom_utilisateur: str) -> str | None:
    """Récupère le hachage du mot de passe pour un utilisateur donné."""
    donnees = charger_donnees_utilisateurs()
    return donnees.get(nom_utilisateur)