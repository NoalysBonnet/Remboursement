import os
import configparser
import sys #

def get_application_base_path(): #
    """ Obtient le chemin de base de l'application, que ce soit en mode script ou compilé. """
    if getattr(sys, 'frozen', False): #
        return os.path.dirname(sys.executable) #
    else: #
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__))) #

UNIVERSAL_APP_ROOT_PATH = get_application_base_path() #

APP_DATA_SUBDIR_NAME = "donnees_partagees_mock" #
REMBOURSEMENT_FILES_SUBDIR_NAME = "Demande_Remboursement" #

APP_DATA_DIR = os.path.join(UNIVERSAL_APP_ROOT_PATH, APP_DATA_SUBDIR_NAME) #
REMBOURSEMENT_BASE_DIR = os.path.join(UNIVERSAL_APP_ROOT_PATH, REMBOURSEMENT_FILES_SUBDIR_NAME) #

USER_DATA_FILE = os.path.join(APP_DATA_DIR, "utilisateurs.json") #
RESET_CODES_FILE = os.path.join(APP_DATA_DIR, "codes_reset.json") #
REMBOURSEMENTS_JSON_FILE = os.path.join(APP_DATA_DIR, "remboursements.json") #

CONFIG_EMAIL_FILE = os.path.join(UNIVERSAL_APP_ROOT_PATH, "config", "config_email.ini") #
SMTP_CONFIG = {} #

# LOCK_FILE_EXTENSION = ".lock" # Supprimé

# --- Statuts des demandes de remboursement ---
STATUT_ANNULEE = "0. Demande Annulée" #
STATUT_CREEE = "1. Créée (en attente constat trop-perçu)" #
STATUT_REFUSEE_CONSTAT_TP = "1b. Refusée par Compta. Trésorerie (action P. Neri)" #
STATUT_TROP_PERCU_CONSTATE = "2. Trop-perçu constaté (en attente validation)" #
STATUT_VALIDEE = "3. Validée (en attente de paiement)" #
STATUT_REFUSEE_VALIDATION_CORRECTION_MLUPO = "3b. Refusée - Validation (action M. Lupo)" #
STATUT_PAIEMENT_EFFECTUE = "4. Paiement effectué (Terminée)" #


def load_smtp_config(): #
    """Charge la configuration SMTP depuis config_email.ini."""
    global SMTP_CONFIG #
    if not os.path.exists(CONFIG_EMAIL_FILE): #
        print(f"ATTENTION: Le fichier de configuration email '{CONFIG_EMAIL_FILE}' est manquant.") #
        print("Veuillez créer ce fichier à partir de 'config_email_template.ini' et le remplir.") #
        SMTP_CONFIG = None #
        return #

    config = configparser.ConfigParser() #
    config.read(CONFIG_EMAIL_FILE) #
    if 'SMTP' in config: #
        SMTP_CONFIG = dict(config.items('SMTP')) #
        if 'port' in SMTP_CONFIG: #
            try: #
                SMTP_CONFIG['port'] = int(SMTP_CONFIG['port']) #
            except ValueError: #
                print(f"ATTENTION: Le port SMTP dans '{CONFIG_EMAIL_FILE}' n'est pas un nombre valide.") #
                SMTP_CONFIG = None #
                return #
        for key in ['use_tls', 'use_ssl']: #
            if key in SMTP_CONFIG: #
                SMTP_CONFIG[key] = config.getboolean('SMTP', key) #
    else: #
        print(f"ATTENTION: La section [SMTP] est manquante dans '{CONFIG_EMAIL_FILE}'.") #
        SMTP_CONFIG = None #

def ensure_dir_exists(directory_path: str, dir_description: str): #
    """S'assure qu'un dossier existe, le crée sinon."""
    if not os.path.exists(directory_path): #
        try: #
            os.makedirs(directory_path) #
            print(f"Dossier '{dir_description}' ('{directory_path}') créé.") #
        except OSError as e: #
            print(f"Erreur critique lors de la création du dossier '{dir_description}' ('{directory_path}'): {e}") #

load_smtp_config() #
ensure_dir_exists(APP_DATA_DIR, "de données partagées mock") #
ensure_dir_exists(REMBOURSEMENT_BASE_DIR, "de base des remboursements") #

def ensure_data_dir_exists(): #
     ensure_dir_exists(APP_DATA_DIR, "de données partagées mock") #