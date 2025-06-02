# C:\Users\maxen\PycharmProjects\PythonProject\config\settings.py
import os
import configparser

# --- Chemins de base ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Racine du projet PythonProject
DATA_DIR_NAME = "donnees_partagees_mock"
DATA_DIR = os.path.join(BASE_DIR, DATA_DIR_NAME)

# Fichiers de données
USER_DATA_FILE = os.path.join(DATA_DIR, "utilisateurs.json")
RESET_CODES_FILE = os.path.join(DATA_DIR, "codes_reset.json")

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

load_smtp_config() # Charger la config au démarrage

def ensure_data_dir_exists():
    """S'assure que le dossier de données existe, le crée sinon."""
    if not os.path.exists(DATA_DIR):
        try:
            os.makedirs(DATA_DIR)
            print(f"Dossier de données '{DATA_DIR}' créé.")
        except OSError as e:
            print(f"Erreur critique lors de la création du dossier de données '{DATA_DIR}': {e}")
            raise # Propage l'erreur, car c'est critique