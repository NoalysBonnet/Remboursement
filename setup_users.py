# C:\Users\maxen\PycharmProjects\PythonProject\setup_users.py
from models.user_model import ajouter_ou_mettre_a_jour_utilisateur_db, obtenir_info_utilisateur
from config.settings import USER_DATA_FILE  # Pour afficher le chemin
import os


def initialiser_utilisateurs():
    print("Configuration des utilisateurs initiaux...")

    utilisateurs_a_creer = {
        "p.neri": {"nom_complet": "Philipe Neri", "email": "p.neri@noalys.com"},
        "m.compta": {"nom_complet": "Marie Compta", "email": "compta-tresorerie@noalys.com"},
        "j.durousset": {"nom_complet": "Juliette Durousset", "email": "j.durousset@noalys.com"},
        "p.compta.fourn": {"nom_complet": "Pascale Compta Fourn", "email": "compta.fourn.natecia@noalys.com"},
        "admin.stagiaire": {"nom_complet": "Admin Stagiaire", "email": "info.stagiaire.noalys@gmail.com"}
        # Votre compte admin
    }

    for login, details in utilisateurs_a_creer.items():
        nom_complet = details["nom_complet"]
        email_suggere = details["email"]

        utilisateur_existant = obtenir_info_utilisateur(login)
        if utilisateur_existant:
            print(f"\nL'utilisateur {nom_complet} (login: {login}) existe déjà.")
            modifier = input("  Voulez-vous mettre à jour son mot de passe et email ? (o/N): ").lower()
            if modifier != 'o':
                continue

        print(f"\nConfiguration pour {nom_complet} (login: {login})")
        email_utilisateur = input(
            f"  Email (actuel/suggéré: {utilisateur_existant['email'] if utilisateur_existant else email_suggere}): ") or \
                            (utilisateur_existant['email'] if utilisateur_existant else email_suggere)

        mdp = input(f"  Entrez le mot de passe pour {login}: ")
        if not mdp and not utilisateur_existant:  # Mdp requis pour un nouvel utilisateur
            print(f"  Mot de passe requis pour un nouvel utilisateur {login}. Utilisateur non ajouté.")
            continue
        if not mdp and utilisateur_existant:  # Si pas de mdp, on garde l'ancien
            print(f"  Pas de changement de mot de passe pour {login}.")
            # Si vous voulez juste maj l'email sans changer de mdp, il faudrait une logique plus fine
            # Pour l'instant, si le mdp est vide, on ne fait rien pour simplifier.
            # ou utiliser l'ancien hash si on veut juste maj l'email:
            # mdp_pour_db = None # Indiquerait de ne pas changer le hash
            # mais ajouter_ou_mettre_a_jour_utilisateur_db attend un mdp pour le hacher
            # Donc pour l'instant, il faut entrer un mdp pour mettre à jour, même si c'est l'ancien.
            if input(
                    "  Confirmer la mise à jour sans changer le mot de passe ? (nécessite de retaper l'ancien ou un nouveau) (o/N): ").lower() != 'o':
                continue
            mdp = input(f"  Veuillez retaper l'ancien mot de passe ou un nouveau pour {login}: ")

        if mdp and email_utilisateur:  # mdp peut être vide si on garde l'ancien (pas encore implémenté)
            ajouter_ou_mettre_a_jour_utilisateur_db(login, mdp, email_utilisateur)
            print(f"  Utilisateur '{login}' configuré avec l'email '{email_utilisateur}'.")
        elif not mdp and utilisateur_existant:
            print(f"  Aucun nouveau mot de passe fourni pour {login}, les informations n'ont pas été mises à jour.")
        else:
            print(f"  Informations (mot de passe ou email) manquantes pour {login}. Utilisateur non ajouté/modifié.")

    print("\nConfiguration terminée.")
    chemin_fichier_json = os.path.abspath(USER_DATA_FILE)
    print(f"Le fichier utilisateurs devrait se trouver ici : {chemin_fichier_json}")
    if os.path.exists(chemin_fichier_json):
        print("Le fichier utilisateurs.json a été trouvé/créé.")
    else:
        print("ATTENTION: Le fichier utilisateurs.json n'a pas été trouvé. Vérifiez les chemins et permissions.")


if __name__ == "__main__":
    initialiser_utilisateurs()