# config/settings.py
import os
import configparser
import sys

def get_application_base_path():
    """ Obtient le chemin de base de l'application, fonctionne pour le dev et pour l'exécutable PyInstaller. """
    if getattr(sys, 'frozen', False):
        # Si l'application est 'gelée' (par PyInstaller), le chemin est le dossier temporaire _MEIPASS
        return sys._MEIPASS
    else:
        # En mode développement, c'est le dossier racine du projet
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

APP_ROOT_PATH = get_application_base_path()

# --- CONFIGURATION DES CHEMINS DE DONNÉES ---
# MODE DÉPLOIEMENT (à décommenter pour créer l'EXE)
#SHARED_DATA_BASE_PATH = "\\\\192.168.197.43\\Commun\\REMBOURSEMENT"

# MODE DÉVELOPPEMENT LOCAL (à commenter pour créer l'EXE)
SHARED_DATA_BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "donnees_partagees_mock")


# Détermine automatiquement si l'application est en mode déploiement ou développement
IS_DEPLOYMENT_MODE = not SHARED_DATA_BASE_PATH.startswith(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# --- FIN DE LA CONFIGURATION DES CHEMINS ---


# Sous-dossiers et fichiers de données, construits à partir du chemin de base
APP_DATA_JSON_DIR = os.path.join(SHARED_DATA_BASE_PATH, "data_json")
REMBOURSEMENTS_ATTACHMENTS_DIR = os.path.join(SHARED_DATA_BASE_PATH, "Demande_Remboursement_Fichiers")
REMBOURSEMENTS_JSON_DIR = os.path.join(SHARED_DATA_BASE_PATH, "Demande_Remboursement_Data")

USER_DATA_FILE = os.path.join(APP_DATA_JSON_DIR, "utilisateurs.json")
RESET_CODES_FILE = os.path.join(APP_DATA_JSON_DIR, "codes_reset.json")


# --- Configuration Email (ne change pas) ---
CONFIG_EMAIL_FILE = os.path.join(APP_ROOT_PATH, "config", "config_email.ini")
SMTP_CONFIG = {}


# --- Statuts des demandes de remboursement (ne change pas) ---
STATUT_ANNULEE = "0. Demande Annulée"
STATUT_CREEE = "1. Créée (en attente constat trop-perçu)"
STATUT_REFUSEE_CONSTAT_TP = "1b. Refusée par Compta. Trésorerie (action P. Neri)"
STATUT_TROP_PERCU_CONSTATE = "2. Trop-perçu constaté (en attente validation)"
STATUT_VALIDEE = "3. Validée (en attente de paiement)"
STATUT_REFUSEE_VALIDATION_CORRECTION_MLUPO = "3b. Refusée - Validation (action M. Lupo)"
STATUT_PAIEMENT_EFFECTUE = "4. Paiement effectué (Terminée)"

# --- Rôles Utilisateurs et Descriptions Détaillées (ne change pas) ---
ROLES_UTILISATEURS = {
    "demandeur": {
        "description": "Responsable de l'initiation des demandes de remboursement pour les clients.\n"
                       "Actions possibles :\n"
                       "  - Créer une nouvelle demande de remboursement.\n"
                       "  - Joindre la facture du client (optionnel) et le RIB (obligatoire).\n"
                       "  - Rédiger une description initiale de la demande.\n"
                       "  - Annuler une demande qui lui a été retournée après un refus.",
        "utilisateurs_actuels": []
    },
    "comptable_tresorerie": {
        "description": "Chargé de vérifier le trop-perçu sur les comptes de l'hôpital.\n"
                       "Actions possibles :\n"
                       "  - Consulter les demandes en attente de constat.\n"
                       "  - Ajouter une pièce jointe (capture d'écran du trop-perçu, preuve comptable).\n"
                       "  - Ajouter un commentaire.\n"
                       "  - Accepter le constat et envoyer la demande pour validation.\n"
                       "  - Refuser le constat (avec commentaire) et renvoyer la demande au demandeur initial (P. Neri).\n"
                       "  - Corriger et resoumettre un constat après un refus de la validation.",
        "utilisateurs_actuels": []
    },
    "validateur_chef": {
        "description": "Valide les demandes après le constat du trop-perçu.\n"
                       "Actions possibles :\n"
                       "  - Consulter les demandes avec trop-perçu constaté.\n"
                       "  - Vérifier la capture d'écran du trop-perçu et la présence du RIB.\n"
                       "  - Ajouter un commentaire (optionnel pour validation, obligatoire pour refus).\n"
                       "  - Valider la demande et l'envoyer pour paiement.\n"
                       "  - Refuser la validation (avec commentaire) et renvoyer la demande au comptable trésorerie (M. Lupo) pour correction.",
        "utilisateurs_actuels": []
    },
    "comptable_fournisseur": {
        "description": "Effectue le paiement final des demandes validées.\n"
                       "Actions possibles :\n"
                       "  - Consulter les demandes validées et en attente de paiement.\n"
                       "  - Confirmer que le paiement a été effectué.\n"
                       "  - Ajouter un commentaire (optionnel) lors de la confirmation du paiement.",
        "utilisateurs_actuels": []
    },
    "visualiseur_seul": {
        "description": "Peut uniquement consulter la liste des demandes et leurs détails.\n"
                       "Actions possibles :\n"
                       "  - Voir toutes les demandes et leur statut actuel.\n"
                       "  - Consulter les pièces jointes (factures, RIBs, preuves de trop-perçu).\n"
                       "  - Ne peut effectuer aucune action de modification ou de changement de statut.",
        "utilisateurs_actuels": []
    },
    "admin": {
        "description": "Dispose de tous les droits des autres rôles, plus des droits d'administration spécifiques.\n"
                       "Actions possibles (en plus des autres rôles) :\n"
                       "  - Supprimer n'importe quelle demande de remboursement.\n"
                       "  - Gérer les comptes utilisateurs (créer, modifier, supprimer - sauf son propre compte 'admin').\n"
                       "  - Assigner/Modifier les rôles des autres utilisateurs.",
        "utilisateurs_actuels": []
    }
}
ASSIGNABLE_ROLES = ["demandeur", "comptable_tresorerie", "validateur_chef", "comptable_fournisseur", "visualiseur_seul"]


def load_smtp_config():
    global SMTP_CONFIG
    if not os.path.exists(CONFIG_EMAIL_FILE):
        print(f"ATTENTION: Le fichier de configuration email '{CONFIG_EMAIL_FILE}' est manquant.")
        SMTP_CONFIG = None
        return

    config = configparser.ConfigParser()
    config.read(CONFIG_EMAIL_FILE)
    if 'SMTP' in config:
        SMTP_CONFIG = dict(config.items('SMTP'))
        if 'port' in SMTP_CONFIG:
            try:
                SMTP_CONFIG['port'] = int(SMTP_CONFIG['port'])
            except ValueError:
                print(f"ATTENTION: Le port SMTP dans '{CONFIG_EMAIL_FILE}' n'est pas un nombre valide.")
                SMTP_CONFIG = None
                return
        for key in ['use_tls', 'use_ssl']:
            if key in SMTP_CONFIG:
                SMTP_CONFIG[key] = config.getboolean('SMTP', key)
    else:
        print(f"ATTENTION: La section [SMTP] est manquante dans '{CONFIG_EMAIL_FILE}'.")
        SMTP_CONFIG = None

def ensure_shared_dirs_exist():
    """Crée les dossiers de données sur le chemin partagé s'ils n'existent pas."""
    if not SHARED_DATA_BASE_PATH:
        print("ERREUR: Le chemin de base des données partagées n'est pas configuré dans settings.py")
        return

    if not os.path.exists(SHARED_DATA_BASE_PATH):
        if IS_DEPLOYMENT_MODE:
            return
        else:
            try:
                os.makedirs(SHARED_DATA_BASE_PATH)
                print(f"Dossier racine des données locales créé : '{SHARED_DATA_BASE_PATH}'")
            except OSError as e:
                print(f"Erreur critique lors de la création du dossier racine local '{SHARED_DATA_BASE_PATH}': {e}")
                return

    ensure_dir_exists(APP_DATA_JSON_DIR, "des fichiers de configuration JSON")
    ensure_dir_exists(REMBOURSEMENTS_ATTACHMENTS_DIR, "des pièces jointes de remboursement")
    ensure_dir_exists(REMBOURSEMENTS_JSON_DIR, "des données de remboursement")

def ensure_dir_exists(directory_path: str, dir_description: str):
    if not os.path.exists(directory_path):
        try:
            os.makedirs(directory_path)
            print(f"Dossier '{dir_description}' ('{directory_path}') créé.")
        except OSError as e:
            print(f"Erreur critique lors de la création du dossier '{dir_description}' ('{directory_path}'): {e}")

# Initialisation
load_smtp_config()
ensure_shared_dirs_exist()

def ensure_data_dir_exists():
     ensure_shared_dirs_exist()