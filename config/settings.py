# config/settings.py
import os
import configparser
import sys

def get_application_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UNIVERSAL_APP_ROOT_PATH = get_application_base_path()

APP_DATA_SUBDIR_NAME = "donnees_partagees_mock"
REMBOURSEMENT_FILES_SUBDIR_NAME = "Demande_Remboursement"

APP_DATA_DIR = os.path.join(UNIVERSAL_APP_ROOT_PATH, APP_DATA_SUBDIR_NAME)
REMBOURSEMENT_BASE_DIR = os.path.join(UNIVERSAL_APP_ROOT_PATH, REMBOURSEMENT_FILES_SUBDIR_NAME)

USER_DATA_FILE = os.path.join(APP_DATA_DIR, "utilisateurs.json")
RESET_CODES_FILE = os.path.join(APP_DATA_DIR, "codes_reset.json")
REMBOURSEMENTS_JSON_FILE = os.path.join(APP_DATA_DIR, "remboursements.json")

CONFIG_EMAIL_FILE = os.path.join(UNIVERSAL_APP_ROOT_PATH, "config", "config_email.ini")
SMTP_CONFIG = {}

# --- Statuts des demandes de remboursement ---
STATUT_ANNULEE = "0. Demande Annulée"
STATUT_CREEE = "1. Créée (en attente constat trop-perçu)"
STATUT_REFUSEE_CONSTAT_TP = "1b. Refusée par Compta. Trésorerie (action P. Neri)"
STATUT_TROP_PERCU_CONSTATE = "2. Trop-perçu constaté (en attente validation)"
STATUT_VALIDEE = "3. Validée (en attente de paiement)"
STATUT_REFUSEE_VALIDATION_CORRECTION_MLUPO = "3b. Refusée - Validation (action M. Lupo)"
STATUT_PAIEMENT_EFFECTUE = "4. Paiement effectué (Terminée)"

# --- Rôles Utilisateurs et Descriptions Détaillées ---
ROLES_UTILISATEURS = {
    "demandeur": {
        "description": "Responsable de l'initiation des demandes de remboursement pour les clients.\n"
                       "Actions possibles :\n"
                       "  - Créer une nouvelle demande de remboursement.\n"
                       "  - Joindre la facture du client (optionnel) et le RIB (obligatoire).\n"
                       "  - Rédiger une description initiale de la demande.\n"
                       "  - Annuler une demande qui lui a été retournée après un refus.",
        "utilisateurs_actuels": [] # Sera peuplé dynamiquement
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
        print("Veuillez créer ce fichier à partir de 'config_email_template.ini' et le remplir.")
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

def ensure_dir_exists(directory_path: str, dir_description: str):
    if not os.path.exists(directory_path):
        try:
            os.makedirs(directory_path)
            print(f"Dossier '{dir_description}' ('{directory_path}') créé.")
        except OSError as e:
            print(f"Erreur critique lors de la création du dossier '{dir_description}' ('{directory_path}'): {e}")

load_smtp_config()
ensure_dir_exists(APP_DATA_DIR, "de données partagées mock")
ensure_dir_exists(REMBOURSEMENT_BASE_DIR, "de base des remboursements")

def ensure_data_dir_exists():
     ensure_dir_exists(APP_DATA_DIR, "de données partagées mock")