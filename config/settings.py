import os
import configparser

# --- Chemins de base ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Racine du projet PythonProject
DATA_DIR_NAME = "donnees_partagees_mock"
DATA_DIR = os.path.join(BASE_DIR, DATA_DIR_NAME)

# --- Nouveau chemin pour les dossiers de remboursement ---
REMBOURSEMENT_DIR_NAME = "Demande_Remboursement"
REMBOURSEMENT_BASE_DIR = os.path.join(BASE_DIR, REMBOURSEMENT_DIR_NAME)

# Fichiers de données
USER_DATA_FILE = os.path.join(DATA_DIR, "utilisateurs.json")
RESET_CODES_FILE = os.path.join(DATA_DIR, "codes_reset.json")
# Le fichier JSON des remboursements reste dans DATA_DIR
REMBOURSEMENTS_JSON_FILE = os.path.join(DATA_DIR, "remboursements.json")


# --- Configuration Email ---
CONFIG_EMAIL_FILE = os.path.join(BASE_DIR, "config", "config_email.ini")
SMTP_CONFIG = {}

def load_smtp_config():
    """Charge la configuration SMTP depuis config_email.ini."""
    global SMTP_CONFIG
    if not os.path.exists(CONFIG_EMAIL_FILE):
        print(f"ATTENTION: Le fichier de configuration email '{CONFIG_EMAIL_FILE}' est manquant.")
        print("Veuillez créer ce fichier à partir de 'config_email_template.ini' et le remplir.")
        SMTP_CONFIG = None # Indique que la config n'a pas pu être chargée
        return

    config = configparser.ConfigParser()
    config.read(CONFIG_EMAIL_FILE)
    if 'SMTP' in config:
        SMTP_CONFIG = dict(config.items('SMTP'))
        # Conversion du port en entier et ssl/tls en booléen
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
    """S'assure qu'un dossier existe, le crée sinon."""
    if not os.path.exists(directory_path):
        try:
            os.makedirs(directory_path)
            print(f"Dossier '{dir_description}' ('{directory_path}') créé.")
        except OSError as e:
            print(f"Erreur critique lors de la création du dossier '{dir_description}' ('{directory_path}'): {e}")
            raise # Propage l'erreur, car c'est critique

# Charger la config email et s'assurer que les dossiers existent au démarrage
load_smtp_config()
ensure_dir_exists(DATA_DIR, "de données partagées mock")
ensure_dir_exists(REMBOURSEMENT_BASE_DIR, "de base des remboursements")

# Pour l'utiliser dans app.py par exemple, on peut garder une fonction spécifique si besoin
def ensure_data_dir_exists(): # Reste pour compatibilité si ensure_dir_exists n'est pas appelé directement
    ensure_dir_exists(DATA_DIR, "de données partagées mock")