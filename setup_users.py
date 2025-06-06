# setup_users.py
import os
import getpass
import sys
from config.settings import IS_DEPLOYMENT_MODE, SHARED_DATA_BASE_PATH, APP_DATA_JSON_DIR, USER_DATA_FILE
from models.user_model import (
    obtenir_info_utilisateur,
    ajouter_utilisateur_db,
    mettre_a_jour_utilisateur_db
)


def initialiser_environnement():
    print("=" * 60)
    print("--- SCRIPT D'INITIALISATION DE L'ENVIRONNEMENT DE L'APPLICATION ---")
    print("=" * 60)

    # 1. Affiche le mode de fonctionnement actuel (local ou réseau)
    if IS_DEPLOYMENT_MODE:
        print("\n[!] MODE DÉPLOIEMENT RÉSEAU DÉTECTÉ [!]")
        print(f"Le script va opérer sur le dossier partagé :\n    {SHARED_DATA_BASE_PATH}")
    else:
        print("\n[!] MODE DÉVELOPPEMENT LOCAL DÉTECTÉ [!]")
        print(f"Le script va opérer sur le dossier local :\n    {SHARED_DATA_BASE_PATH}")

    # La création des dossiers est déjà gérée à l'import de settings.py
    print("\nStructure des dossiers prête.")

    # 2. Demande une confirmation à l'utilisateur pour la sécurité
    try:
        consent = input("\nÊtes-vous sûr de vouloir continuer et potentiellement modifier les données ? (o/n) : ")
    except KeyboardInterrupt:
        print("\nOpération annulée.")
        sys.exit()
    if consent.lower() != 'o':
        print("Opération annulée par l'utilisateur.")
        sys.exit()

    # 3. Gère l'ancien fichier de données s'il existe
    obsolete_file = os.path.join(APP_DATA_JSON_DIR, 'remboursements.json')
    if os.path.exists(obsolete_file):
        print("\n[AVERTISSEMENT] L'ancien fichier de données 'remboursements.json' a été trouvé.")
        print("Ce fichier n'est plus utilisé et peut être archivé ou supprimé.")
        try:
            action = input("Voulez-vous (a)rchiver (en .old), (s)upprimer ou (i)gnorer ce fichier ? (a/s/i) : ")
            if action.lower() == 'a':
                os.rename(obsolete_file, obsolete_file + '.old')
                print("-> Fichier archivé avec succès en 'remboursements.json.old'.")
            elif action.lower() == 's':
                os.remove(obsolete_file)
                print("-> Fichier supprimé avec succès.")
            else:
                print("-> Fichier ignoré.")
        except KeyboardInterrupt:
            print("\nOpération annulée.")
            sys.exit()

    print("\n--- Configuration des comptes utilisateurs ---")
    print("Ce script va créer ou mettre à jour les comptes utilisateurs.")
    print("Pour les mots de passe, la saisie est masquée pour des raisons de sécurité.")

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
            print(f"L'utilisateur '{login}' existe déjà. Mise à jour possible.")
            mdp = getpass.getpass(f"  Nouveau mot de passe pour '{login}' (laisser vide pour ne pas changer): ")
            if mdp:
                succes, message = mettre_a_jour_utilisateur_db(login, login, utilisateur_existant['email'],
                                                               utilisateur_existant['roles'], mdp)
                if succes:
                    print(f"  ✅ SUCCÈS: Mot de passe mis à jour pour '{login}'.")
                else:
                    print(f"  ❌ ERREUR: {message}")
            else:
                print("  Mot de passe non modifié.")
        else:
            print(f"L'utilisateur '{login}' n'existe pas. Création...")
            mdp = ""
            while not mdp:
                mdp = getpass.getpass(f"  Entrez le mot de passe pour '{login}' (obligatoire pour création): ")
                if not mdp:
                    print("  Le mot de passe ne peut pas être vide pour un nouvel utilisateur.")

            succes = ajouter_utilisateur_db(
                nom_utilisateur=login,
                mot_de_passe=mdp,
                email=email_suggere,
                roles=roles_suggeres
            )
            if succes:
                print(f"  ✅ SUCCÈS: Utilisateur '{login}' créé.")
            else:
                print(f"  ❌ ERREUR: L'utilisateur '{login}' n'a pas pu être créé.")

    print("\n" + "=" * 60)
    print("Configuration des utilisateurs terminée.")
    print(f"Le fichier des utilisateurs se trouve ici : {os.path.abspath(USER_DATA_FILE)}")
    print("=" * 60)


if __name__ == "__main__":
    initialiser_environnement()