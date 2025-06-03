from models.user_model import ajouter_ou_mettre_a_jour_utilisateur_db, obtenir_info_utilisateur  #
from config.settings import USER_DATA_FILE  #
import os


def initialiser_utilisateurs():  #
    print("Configuration des utilisateurs initiaux...")  #

    # Définition des utilisateurs avec leurs emails et rôles par défaut
    utilisateurs_par_defaut = {
        "p.neri": {"nom_complet": "Philipe Neri", "email": "p.neri@noalys.com", "roles": ["demandeur"]},  #
        "m.lupo": {"nom_complet": "Marie Lupo", "email": "compta-tresorerie@noalys.com",
                   "roles": ["comptable_tresorerie"]},  # Renommé et email mis à jour si besoin
        "j.durousset": {"nom_complet": "Juliette Durousset", "email": "j.durousset@noalys.com",
                        "roles": ["validateur_chef"]},  #
        "p.diop": {"nom_complet": "Pascale Diop", "email": "compta.fourn.natecia@noalys.com",
                   "roles": ["comptable_fournisseur"]},  # Renommé et email mis à jour si besoin
        "admin": {
            "nom_complet": "Administrateur Système",
            "email": "info.stagiaire.noalys@gmail.com",  # Email corrigé
            "roles": [
                "admin",
                "demandeur",
                "comptable_tresorerie",
                "validateur_chef",
                "comptable_fournisseur",
                "visualiseur_seul"
            ]
        },
        "b.gonnet": {"nom_complet": "Baptiste Gonnet", "email": "b.gonnet@noalys.com", "roles": ["validateur_chef"]},
        # Nouvel utilisateur
        "m.fessy": {"nom_complet": "Morgane Fessy", "email": "m.fessy@noalys.com", "roles": ["visualiseur_seul"]}
        # Nouvel utilisateur
    }

    for login, details_defaut in utilisateurs_par_defaut.items():  #
        nom_complet = details_defaut["nom_complet"]  #
        email_suggere = details_defaut["email"]  #
        roles_suggeres = details_defaut["roles"]  #

        utilisateur_existant = obtenir_info_utilisateur(login)  #

        email_a_utiliser = email_suggere
        roles_a_utiliser = roles_suggeres

        if utilisateur_existant:  #
            print(f"\nL'utilisateur {nom_complet} (login: {login}) existe déjà.")  #
            email_a_utiliser = utilisateur_existant.get("email", email_suggere)  #
            roles_a_utiliser = utilisateur_existant.get("roles", roles_suggeres)  #

            modifier = input(
                f"  Email actuel: {email_a_utiliser}, Rôles actuels: {roles_a_utiliser}. Mettre à jour mot de passe, email et rôles ? (o/N): ").lower()  #
            if modifier != 'o':  #
                continue  #
        else:
            print(f"\nCréation du nouvel utilisateur {nom_complet} (login: {login}).")

        print(f"Configuration pour {nom_complet} (login: {login})")  #

        email_input = input(f"  Email (laisser vide pour '{email_a_utiliser}'): ")  #
        email_final = email_input or email_a_utiliser  #

        # Pour la modification interactive des rôles :
        roles_input_str = input(f"  Rôles (séparés par virgule, laisser vide pour '{','.join(roles_a_utiliser)}'): ")
        if roles_input_str.strip():
            roles_final = [role.strip() for role in roles_input_str.split(',') if role.strip()]
        else:
            roles_final = roles_a_utiliser

        mdp = input(f"  Entrez le mot de passe pour {login} (laisser vide si existant et non modifié): ")  #

        if not mdp and not utilisateur_existant:  #
            print(f"  Mot de passe requis pour un nouvel utilisateur {login}. Utilisateur non ajouté.")  #
            continue  #

        ajouter_ou_mettre_a_jour_utilisateur_db(login, mdp if mdp else None, email_final, roles_final)  #
        print(f"  Utilisateur '{login}' configuré avec l'email '{email_final}' et rôles {roles_final}.")  #

    print("\nConfiguration terminée.")  #
    chemin_fichier_json = os.path.abspath(USER_DATA_FILE)  #
    print(f"Le fichier utilisateurs devrait se trouver ici : {chemin_fichier_json}")  #
    if os.path.exists(chemin_fichier_json):  #
        print("Le fichier utilisateurs.json a été trouvé/créé.")  #
    else:  #
        print("ATTENTION: Le fichier utilisateurs.json n'a pas été trouvé. Vérifiez les chemins et permissions.")  #


if __name__ == "__main__":  #
    initialiser_utilisateurs()  #