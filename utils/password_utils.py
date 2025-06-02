# C:\Users\maxen\PycharmProjects\PythonProject\utils\password_utils.py
from passlib.context import CryptContext

# Contexte pour le hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generer_hachage_mdp(mot_de_passe: str) -> str:
    """Génère un hachage sécurisé pour un mot de passe."""
    return pwd_context.hash(mot_de_passe)

def verifier_mdp(mot_de_passe_saisi: str, hachage_stocke: str) -> bool:
    """Vérifie un mot de passe saisi par rapport à un hachage stocké."""
    if not hachage_stocke:
        return False
    return pwd_context.verify(mot_de_passe_saisi, hachage_stocke)