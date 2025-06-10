# utils/password_utils.py
import re
from passlib.context import CryptContext

context_hachage = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generer_hachage_mdp(mot_de_passe: str) -> str:
    return context_hachage.hash(mot_de_passe)


def verifier_mdp(mot_de_passe_saisi: str, hachage_stocke: str) -> bool:
    return context_hachage.verify(mot_de_passe_saisi, hachage_stocke)


def check_password_strength(password: str) -> tuple[int, str]:
    length = len(password)
    score = 0
    feedback = ""

    # Critères
    has_upper = re.search(r'[A-Z]', password) is not None
    has_lower = re.search(r'[a-z]', password) is not None
    has_digit = re.search(r'\d', password) is not None
    has_special = re.search(r'[^A-Za-z0-9]', password) is not None

    # Calcul du score
    if length >= 8:
        score += 1
    if length >= 12:
        score += 1
    if has_upper and has_lower:
        score += 1
    if has_digit:
        score += 1
    if has_special:
        score += 1

    # Attribution du feedback
    if score <= 1:
        feedback = "Très faible"
    elif score == 2:
        feedback = "Faible"
    elif score == 3:
        feedback = "Moyen"
    elif score == 4:
        feedback = "Fort"
    else:
        feedback = "Très fort"

    return score, feedback