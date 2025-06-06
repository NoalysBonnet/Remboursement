import os
import getpass
from models.user_model import (
    obtenir_info_utilisateur,
    ajouter_utilisateur_db,
    mettre_a_jour_utilisateur_db
)
from config.settings import USER_DATA_FILE


def initialiser_utilisateurs():
    print("Configuration interactive des utilisateurs de l'application.")
    print("Ce script va créer ou mettre à jour les comptes utilisateurs.")
    print("Pour les mots de passe, la saisie est masquée pour des raisons de sécurité.")
    print("-" * 60)

    utilisateurs_par_defaut = {
        "p.neri": {"nom_complet": "Philipe Neri", "email": "p.neri@noalys.com", "roles": ["demandeur"]},
        "m.lupo": {"nom_complet": "Marie Lupo", "email": "compta-tresorerie@noalys.com",
                   "roles": ["comptable_tresorerie"]},
        "j.durousset": {"nom_complet": "Juliette Durousset", "email": "j.durousset@noalys.com",
                        "roles": ["validateur_chef"]},
        "p.diop": {"nom_complet": "Pascale Diop", "email": "compta.fourn.natecia@noalys.com",
                   "roles": ["comptable_fournisseur"]},
        "admin": {
            "nom_complet": "Administrateur Système",
            "email": "info.stagiaire.noalys@gmail.com",
            "roles": ["admin", "demandeur", "comptable_tresorerie", "validateur_chef", "comptable_fournisseur",
                      "visualiseur_seul"]
        },
        "b.gonnet": {"nom_complet": "Baptiste Gonnet", "email": "b.gonnet@noalys.com", "roles": ["validateur_chef"]},
        "m.fessy": {"nom_complet": "Morgane Fessy", "email": "m.fessy@noalys.com", "roles": ["visualiseur_seul"]}
    }

    for login, details_defaut in utilisateurs_par_defaut.items():
        nom_complet = details_defaut["nom_complet"]
        email_suggere = details_defaut["email"]
        roles_suggeres = details_defaut["roles"]

        print(f"\n--- Traitement de : {nom_complet} (login: {login}) ---")

        utilisateur_existant = obtenir_info_utilisateur(login)

        if utilisateur_existant:
            print(f"L'utilisateur '{login}' existe déjà. Vérification des informations pour la mise à jour.")
            email_actuel = utilisateur_existant.get("email", email_suggere)
            roles_actuels = utilisateur_existant.get("roles", [])
            print(f"  Email actuel: {email_actuel}")
            print(f"  Rôles actuels: {', '.join(roles_actuels)}")

            email_final_input = input(f"  Nouvel email (laisser vide pour conserver '{email_actuel}'): ")
            email_final = email_final_input.strip() or email_actuel

            roles_final_input = input(
                f"  Nouveaux rôles (séparés par ',', laisser vide pour conserver les rôles actuels): ")
            if roles_final_input.strip():
                roles_final = [role.strip() for role in roles_final_input.split(',') if role.strip()]
            else:
                roles_final = roles_actuels

            mdp = getpass.getpass(f"  Nouveau mot de passe pour '{login}' (laisser vide pour ne pas changer): ")

            succes, message = mettre_a_jour_utilisateur_db(
                login_original=login,
                nouveau_login=login,
                nouvel_email=email_final,
                nouveaux_roles=roles_final,
                nouveau_mot_de_passe=mdp if mdp else None
            )

            if succes:
                print(f"  ✅ SUCCÈS: {message}")
            else:
                print(f"  ❌ ERREUR: {message}")

        else:
            print(f"L'utilisateur '{login}' n'existe pas. Procédure de création.")

            email_final_input = input(f"  Email (par défaut '{email_suggere}'): ")
            email_final = email_final_input.strip() or email_suggere

            roles_final_input = input(f"  Rôles (séparés par ',', par défaut '{','.join(roles_suggeres)}'): ")
            if roles_final_input.strip():
                roles_final = [role.strip() for role in roles_final_input.split(',') if role.strip()]
            else:
                roles_final = roles_suggeres

            mdp = ""
            while not mdp:
                mdp = getpass.getpass(f"  Entrez le mot de passe pour '{login}' (obligatoire pour création): ")
                if not mdp:
                    print("  Le mot de passe ne peut pas être vide pour un nouvel utilisateur.")

            succes = ajouter_utilisateur_db(
                nom_utilisateur=login,
                mot_de_passe=mdp,
                email=email_final,
                roles=roles_final
            )

            if succes:
                print(f"  ✅ SUCCÈS: Utilisateur '{login}' créé.")
            else:
                print(f"  ❌ ERREUR: L'utilisateur '{login}' n'a pas pu être créé.")

    print("\n" + "-" * 60)
    print("Configuration des utilisateurs terminée.")
    chemin_fichier_json = os.path.abspath(USER_DATA_FILE)
    if os.path.exists(chemin_fichier_json):
        print(f"Fichier de données utilisateurs trouvé ici : {chemin_fichier_json}")
    else:
        print(
            f"ATTENTION: Fichier de données non trouvé à {chemin_fichier_json}. Il sera créé à la première modification.")


if __name__ == "__main__":
    initialiser_utilisateurs()