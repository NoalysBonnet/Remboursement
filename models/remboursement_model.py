import json
import os
import datetime
import uuid  #
import shutil
import re  #
from config.settings import (  #
    REMBOURSEMENT_BASE_DIR,
    REMBOURSEMENTS_JSON_FILE,
    LOCK_FILE_EXTENSION,
    STATUT_CREEE,  #
    STATUT_TROP_PERCU_CONSTATE,  #
    STATUT_REFUSEE_CONSTAT_TP,  #
    STATUT_ANNULEE,  #
    STATUT_VALIDEE,  # Nouveau statut importé
    STATUT_REFUSEE_VALIDATION_CORRECTION_MLUPO  # Nouveau statut importé
)


def _sanitize_directory_name(name: str) -> str:  #
    """Nettoie une chaîne pour l'utiliser comme nom de dossier valide."""
    if not name:  #
        return "ref_inconnue"  #
    name = name.replace('/', '_').replace('\\', '_').replace(':', '_')  #
    name = "".join(c if c.isalnum() or c in ['_', '-'] else '_' for c in name)  #
    name = name.strip('.')  #
    name = re.sub(r'[_.-]+', '_', name)  #
    if not name:  #
        return "ref_invalide"  #
    return name  #


def _charger_remboursements() -> list:  #
    """Charge la liste des demandes de remboursement depuis le fichier JSON."""
    if os.path.exists(REMBOURSEMENTS_JSON_FILE):  #
        try:  #
            with open(REMBOURSEMENTS_JSON_FILE, 'r', encoding='utf-8') as f:  #
                return json.load(f)  #
        except (json.JSONDecodeError, FileNotFoundError):  #
            return []  #
        except Exception as e:  #
            print(f"Erreur inattendue lors du chargement de {REMBOURSEMENTS_JSON_FILE}: {e}")  #
            return []  #
    return []  #


def _sauvegarder_remboursements(remboursements: list):  #
    """Sauvegarde la liste des demandes de remboursement dans le fichier JSON."""
    try:  #
        with open(REMBOURSEMENTS_JSON_FILE, 'w', encoding='utf-8') as f:  #
            json.dump(remboursements, f, indent=4, ensure_ascii=False)  #
    except Exception as e:  #
        print(f"Erreur inattendue lors de la sauvegarde de {REMBOURSEMENTS_JSON_FILE}: {e}")  #


def creer_nouvelle_demande(
        nom: str,
        prenom: str,
        reference_facture: str,
        montant_demande: float,
        chemin_facture_source: str | None,  #
        chemin_rib_source: str,
        utilisateur_createur: str,
        description: str  #
) -> dict | None:  #
    demandes = _charger_remboursements()  #

    id_unique_demande = f"D{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{str(uuid.uuid4())[:4]}"  #

    ref_facture_sanitized = _sanitize_directory_name(reference_facture)  #
    if not ref_facture_sanitized or ref_facture_sanitized in ["ref_inconnue", "ref_invalide"]:  #
        ref_facture_sanitized = f"demande_{id_unique_demande}"  #

    dossier_demande_specifique = os.path.join(REMBOURSEMENT_BASE_DIR, ref_facture_sanitized)  #
    os.makedirs(dossier_demande_specifique, exist_ok=True)  #

    chemin_facture_stockee_relatif = None  #
    nom_fichier_facture = None  #
    chemin_facture_destination = None  #
    if chemin_facture_source:  #
        base_nom_facture = os.path.basename(chemin_facture_source)  #
        nom_fichier_facture = f"facture_{ref_facture_sanitized}_{base_nom_facture}"  #
        chemin_facture_destination = os.path.join(dossier_demande_specifique, nom_fichier_facture)  #
        chemin_facture_stockee_relatif = os.path.join(ref_facture_sanitized, nom_fichier_facture)  #

    base_nom_rib = os.path.basename(chemin_rib_source)  #
    nom_fichier_rib = f"RIB_{_sanitize_directory_name(nom)}_{_sanitize_directory_name(prenom)}_{base_nom_rib}"  #
    chemin_rib_destination = os.path.join(dossier_demande_specifique, nom_fichier_rib)  #
    chemin_rib_stocke_relatif = os.path.join(ref_facture_sanitized, nom_fichier_rib)  #

    try:  #
        if chemin_facture_source and chemin_facture_destination:  #
            shutil.copy2(chemin_facture_source, chemin_facture_destination)  #
        shutil.copy2(chemin_rib_source, chemin_rib_destination)  #
    except Exception as e:  #
        print(f"Erreur lors de la copie des pièces jointes : {e}")  #
        try:  #
            if not os.listdir(dossier_demande_specifique):  #
                os.rmdir(dossier_demande_specifique)  #
        except OSError:  #
            pass  #
        return None  #

    nouvelle_demande = {  #
        "id_demande": id_unique_demande,  #
        "nom": nom.upper() if nom else None,  #
        "prenom": prenom.title() if prenom else None,  #
        "reference_facture": reference_facture,  #
        "reference_facture_dossier": ref_facture_sanitized,  #
        "description": description,  #
        "montant_demande": montant_demande,  #
        "chemin_facture_stockee": chemin_facture_stockee_relatif,  #
        "chemin_rib_stocke": chemin_rib_stocke_relatif,  #
        "statut": STATUT_CREEE,  #
        "cree_par": utilisateur_createur,  #
        "date_creation": datetime.datetime.now().isoformat(),  #
        "derniere_modification_par": utilisateur_createur,  #
        "date_derniere_modification": datetime.datetime.now().isoformat(),  #
        "historique_statuts": [  #
            {  #
                "statut": STATUT_CREEE,  #
                "date": datetime.datetime.now().isoformat(),  #
                "par": utilisateur_createur,  #
                "commentaire": description  #
            }
        ],
        "pieces_capture_trop_percu": [],  #
        "preuve_paiement_banque": None  #
    }
    demandes.append(nouvelle_demande)  #
    _sauvegarder_remboursements(demandes)  #

    nom_fichier_info_txt = "informations_demande.txt"  #
    chemin_fichier_info_txt = os.path.join(dossier_demande_specifique, nom_fichier_info_txt)  #
    try:  #
        with open(chemin_fichier_info_txt, 'w', encoding='utf-8') as f_txt:  #
            f_txt.write(f"Informations pour la demande: {id_unique_demande}\n")  #
            f_txt.write("=" * 40 + "\n")  #
            for cle, valeur in nouvelle_demande.items():  #
                if cle == "historique_statuts":  #
                    f_txt.write("\nHistorique des Statuts et Commentaires:\n")  #
                    if isinstance(valeur, list) and valeur:  #
                        for item_hist in valeur:  #
                            f_txt.write(f"  - Statut: {item_hist.get('statut', 'N/A')}\n")  #
                            f_txt.write(f"    Date: {item_hist.get('date', 'N/A')}\n")  #
                            f_txt.write(f"    Par: {item_hist.get('par', 'N/A')}\n")  #
                            f_txt.write(f"    Commentaire: {item_hist.get('commentaire', 'N/A')}\n")  #
                            f_txt.write("-" * 20 + "\n")  #
                    else:  #
                        f_txt.write("  Aucun historique disponible.\n")  #
                elif isinstance(valeur, list):  #
                    f_txt.write(
                        f"{cle.replace('_', ' ').title()}: {', '.join(map(str, valeur)) if valeur else 'N/A'}\n")  #
                else:  #
                    f_txt.write(f"{cle.replace('_', ' ').title()}: {valeur if valeur is not None else 'N/A'}\n")  #
            f_txt.write("\n" + "=" * 40 + "\n")  #
            f_txt.write(f"Fichier généré le: {datetime.datetime.now().isoformat()}\n")  #
        print(f"Fichier d'information '{chemin_fichier_info_txt}' créé avec succès.")  #
    except IOError as e:  #
        print(f"Erreur lors de la création du fichier d'information '{chemin_fichier_info_txt}': {e}")  #

    return nouvelle_demande  #


def obtenir_toutes_les_demandes() -> list:  #
    """Retourne toutes les demandes de remboursement."""
    return _charger_remboursements()  #


def get_chemin_absolu_piece_jointe(chemin_relatif_pj: str | None) -> str | None:  #
    """Construit le chemin absolu vers une pièce jointe à partir de son chemin relatif."""
    if not chemin_relatif_pj:  #
        return None  #
    return os.path.join(REMBOURSEMENT_BASE_DIR, chemin_relatif_pj)  #


def supprimer_demande_par_id(id_demande_a_supprimer: str) -> tuple[bool, str]:  #
    """Supprime une demande et son dossier associé."""
    demandes = _charger_remboursements()  #
    demande_a_supprimer_trouvee = None  #
    nouvelle_liste_demandes = []  #

    for demande in demandes:  #
        if demande.get("id_demande") == id_demande_a_supprimer:  #
            demande_a_supprimer_trouvee = demande  #
        else:  #
            nouvelle_liste_demandes.append(demande)  #

    if not demande_a_supprimer_trouvee:  #
        return False, f"Demande ID {id_demande_a_supprimer} non trouvée."  #

    _sauvegarder_remboursements(nouvelle_liste_demandes)  #

    ref_dossier = demande_a_supprimer_trouvee.get("reference_facture_dossier")  #
    if ref_dossier:  #
        chemin_dossier_demande = os.path.join(REMBOURSEMENT_BASE_DIR, ref_dossier)  #
        chemin_fichier_verrou = get_lock_file_path(ref_dossier)  #
        if os.path.exists(chemin_fichier_verrou):  #
            try:  #
                os.remove(chemin_fichier_verrou)  #
            except OSError as e:  #
                print(f"Avertissement: Impossible de supprimer le fichier verrou {chemin_fichier_verrou}: {e}")  #

        if os.path.exists(chemin_dossier_demande) and os.path.isdir(chemin_dossier_demande):  #
            try:  #
                shutil.rmtree(chemin_dossier_demande)  #
                print(f"Dossier {chemin_dossier_demande} supprimé avec succès.")  #
            except OSError as e:  #
                print(f"Erreur lors de la suppression du dossier {chemin_dossier_demande}: {e}")  #
                return True, f"Demande ID {id_demande_a_supprimer} supprimée, mais échec de la suppression du dossier {ref_dossier}."  #

    return True, f"Demande ID {id_demande_a_supprimer} supprimée avec succès."  #


def get_lock_file_path(reference_facture_dossier: str) -> str:  #
    """Retourne le chemin complet du fichier de verrou pour une demande."""
    return os.path.join(REMBOURSEMENT_BASE_DIR, reference_facture_dossier,
                        f"{reference_facture_dossier}{LOCK_FILE_EXTENSION}")  #


def is_demande_locked(reference_facture_dossier: str) -> str | None:  #
    """
    Vérifie si une demande est verrouillée.
    Retourne le nom de l'utilisateur qui a verrouillé si c'est le cas, sinon None.
    Un verrou est considéré comme expiré après un certain temps (ex: 1 heure).
    """  #
    lock_file = get_lock_file_path(reference_facture_dossier)  #
    lock_timeout_seconds = 3600  # 1 heure

    if os.path.exists(lock_file):  #
        try:  #
            with open(lock_file, 'r', encoding='utf-8') as f:  #
                content = f.readlines()  #
                if len(content) >= 2:  #
                    locked_by_user = content[0].strip()  #
                    lock_time_str = content[1].strip()  #
                    lock_time = datetime.datetime.fromisoformat(lock_time_str)  #

                    if datetime.datetime.now() - lock_time < datetime.timedelta(seconds=lock_timeout_seconds):  #
                        return locked_by_user  #
                    else:  #
                        print(f"Verrou expiré pour {reference_facture_dossier} (par {locked_by_user}). Suppression.")  #
                        os.remove(lock_file)  #
                        return None  #
                else:  #
                    os.remove(lock_file)  #
                    return None  #
        except Exception as e:  #
            print(f"Erreur lors de la lecture du fichier de verrou {lock_file}: {e}")  #
            try:  #
                os.remove(lock_file)  #
            except OSError:  #
                pass  #
            return None  #
    return None  #


def lock_demande(reference_facture_dossier: str, username: str) -> bool:  #
    """Tente de verrouiller une demande pour modification."""
    current_locker = is_demande_locked(reference_facture_dossier)  #
    if current_locker and current_locker != username:  #
        print(f"Demande {reference_facture_dossier} déjà verrouillée par {current_locker}.")  #
        return False  #

    lock_file = get_lock_file_path(reference_facture_dossier)  #
    try:  #
        os.makedirs(os.path.dirname(lock_file), exist_ok=True)  #
        with open(lock_file, 'w', encoding='utf-8') as f:  #
            f.write(f"{username}\n")  #
            f.write(f"{datetime.datetime.now().isoformat()}\n")  #
        return True  #
    except IOError as e:  #
        print(f"Impossible de créer le fichier de verrou {lock_file}: {e}")  #
        return False  #


def unlock_demande(reference_facture_dossier: str, username_unlocking: str) -> bool:  #
    """Déverrouille une demande. Seul l'utilisateur ayant verrouillé (ou un admin) devrait pouvoir le faire."""
    lock_file = get_lock_file_path(reference_facture_dossier)  #
    locked_by_user = None  #
    if os.path.exists(lock_file):  #
        try:  #
            with open(lock_file, 'r', encoding='utf-8') as f:  #
                content = f.readlines()  #
                if len(content) >= 1:  #
                    locked_by_user = content[0].strip()  #
        except Exception:  #
            pass  #

        if username_unlocking == "admin" or locked_by_user == username_unlocking or locked_by_user is None:  #
            try:  #
                os.remove(lock_file)  #
                return True  #
            except OSError as e:  #
                print(f"Impossible de supprimer le fichier de verrou {lock_file}: {e}")  #
                return False  #
        else:  #
            print(
                f"Tentative de déverrouillage de {reference_facture_dossier} par {username_unlocking} alors qu'il est verrouillé par {locked_by_user}.")  #
            return False  #
    return True  #


def _modifier_demande_par_id(id_demande: str, updates: dict) -> tuple[bool, str]:  #
    """Modifie une demande existante avec les données fournies dans `updates`."""
    demandes = _charger_remboursements()  #
    demande_trouvee = False  #
    for i, demande in enumerate(demandes):  #
        if demande.get("id_demande") == id_demande:  #
            # Avant d'appliquer les updates, ajouter l'ancienne entrée de statut/commentaire à l'historique si elle n'y est pas déjà
            # (pour garder une trace de l'état avant cette modification spécifique)
            # Cette logique peut devenir complexe, pour l'instant, on met à jour directement.
            # Les actions spécifiques comme "accepter", "refuser" gèrent leur propre entrée d'historique.
            demandes[i].update(updates)  #
            demande_trouvee = True  #
            break  #

    if not demande_trouvee:  #
        return False, "Demande non trouvée pour modification."  #

    _sauvegarder_remboursements(demandes)  #
    return True, "Demande modifiée avec succès."  #


def ajouter_piece_jointe_trop_percu(id_demande: str, chemin_pj_source: str, utilisateur: str) -> tuple[
    bool, str, str | None]:  #
    """Ajoute une pièce jointe (preuve de trop-perçu) à une demande existante."""
    demandes = _charger_remboursements()  #
    demande_trouvee = None  #
    demande_index = -1  #

    for i, d in enumerate(demandes):  #
        if d.get("id_demande") == id_demande:  #
            demande_trouvee = d  #
            demande_index = i  #
            break  #

    if not demande_trouvee:  #
        return False, "Demande non trouvée.", None  #

    ref_dossier = demande_trouvee.get("reference_facture_dossier")  #
    if not ref_dossier:  #
        return False, "Référence de dossier non trouvée pour la demande.", None  #

    dossier_demande_specifique = os.path.join(REMBOURSEMENT_BASE_DIR, ref_dossier)  #
    os.makedirs(dossier_demande_specifique, exist_ok=True)  #

    nom_original_pj = os.path.basename(chemin_pj_source)  #
    nom_fichier_pj_stockee = f"trop_percu_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{_sanitize_directory_name(nom_original_pj)}"  #
    chemin_pj_destination = os.path.join(dossier_demande_specifique, nom_fichier_pj_stockee)  #

    try:  #
        shutil.copy2(chemin_pj_source, chemin_pj_destination)  #
    except Exception as e:  #
        return False, f"Erreur lors de la copie de la pièce jointe de trop-perçu : {e}", None  #

    chemin_pj_relatif = os.path.join(ref_dossier, nom_fichier_pj_stockee)  #

    if "pieces_capture_trop_percu" not in demande_trouvee:  #
        demande_trouvee["pieces_capture_trop_percu"] = []  #
    demande_trouvee["pieces_capture_trop_percu"].append(chemin_pj_relatif)  #

    # Pas de changement de statut ici, juste l'ajout de PJ. Le statut change avec le commentaire.
    demande_trouvee["derniere_modification_par"] = utilisateur  #
    demande_trouvee["date_derniere_modification"] = datetime.datetime.now().isoformat()  #

    demandes[demande_index] = demande_trouvee  #
    _sauvegarder_remboursements(demandes)  #

    return True, "Pièce jointe de trop-perçu ajoutée avec succès.", chemin_pj_relatif  #


def accepter_constat_trop_percu(id_demande: str, commentaire: str, utilisateur: str) -> tuple[
    bool, str]:  # Renommé et simplifié
    """Action lorsque m.lupo accepte et constate le trop-perçu (PJ déjà ajoutée séparément)."""
    updates = {  #
        "statut": STATUT_TROP_PERCU_CONSTATE,  #
        "derniere_modification_par": utilisateur,  #
        "date_derniere_modification": datetime.datetime.now().isoformat()  #
    }
    nouvelle_entree_historique = {  #
        "statut": STATUT_TROP_PERCU_CONSTATE,  #
        "date": updates["date_derniere_modification"],  #
        "par": utilisateur,  #
        "commentaire": commentaire  #
    }

    demandes = _charger_remboursements()  #
    demande_trouvee = False  #
    for i, demande in enumerate(demandes):  #
        if demande.get("id_demande") == id_demande:  #
            if demande.get("statut") != STATUT_CREEE:  #
                return False, f"La demande n'est pas au statut '{STATUT_CREEE}' attendu."  #
            demandes[i].update(updates)  #
            if "historique_statuts" not in demandes[i]: demandes[i]["historique_statuts"] = []  #
            demandes[i]["historique_statuts"].append(nouvelle_entree_historique)  #
            demande_trouvee = True  #
            break  #

    if not demande_trouvee:  #
        return False, "Demande non trouvée."  #

    _sauvegarder_remboursements(demandes)  #
    return True, f"Constat de trop-perçu accepté. Statut mis à jour à '{STATUT_TROP_PERCU_CONSTATE}'."  #


def refuser_constat_trop_percu(id_demande: str, commentaire: str, utilisateur_mlupo: str) -> tuple[bool, str]:  #
    """Action lorsque m.lupo refuse le constat de trop-perçu."""
    updates = {  #
        "statut": STATUT_REFUSEE_CONSTAT_TP,  #
        "derniere_modification_par": utilisateur_mlupo,  #
        "date_derniere_modification": datetime.datetime.now().isoformat()  #
    }
    nouvelle_entree_historique = {  #
        "statut": STATUT_REFUSEE_CONSTAT_TP,  #
        "date": updates["date_derniere_modification"],  #
        "par": utilisateur_mlupo,  #
        "commentaire": commentaire  #
    }

    demandes = _charger_remboursements()  #
    demande_trouvee = False  #
    for i, demande in enumerate(demandes):  #
        if demande.get("id_demande") == id_demande:  #
            if demande.get("statut") != STATUT_CREEE:  #
                return False, f"La demande n'est pas au statut '{STATUT_CREEE}' attendu pour un refus."  #
            demandes[i].update(updates)  #
            if "historique_statuts" not in demandes[i]: demandes[i]["historique_statuts"] = []  #
            demandes[i]["historique_statuts"].append(nouvelle_entree_historique)  #
            demande_trouvee = True  #
            break  #

    if not demande_trouvee:  #
        return False, "Demande non trouvée."  #

    _sauvegarder_remboursements(demandes)  #
    return True, f"Constat de trop-perçu refusé. Demande renvoyée pour action. Statut: '{STATUT_REFUSEE_CONSTAT_TP}'."  #


def annuler_demande(id_demande: str, commentaire: str, utilisateur_annulant: str) -> tuple[bool, str]:  #
    """Action lorsque p.neri (ou admin) annule une demande (souvent après un refus)."""
    updates = {  #
        "statut": STATUT_ANNULEE,  #
        "derniere_modification_par": utilisateur_annulant,  #
        "date_derniere_modification": datetime.datetime.now().isoformat()  #
    }
    nouvelle_entree_historique = {  #
        "statut": STATUT_ANNULEE,  #
        "date": updates["date_derniere_modification"],  #
        "par": utilisateur_annulant,  #
        "commentaire": commentaire  #
    }

    demandes = _charger_remboursements()  #
    demande_trouvee = False  #
    for i, demande in enumerate(demandes):  #
        if demande.get("id_demande") == id_demande:  #
            if demande.get("statut") == STATUT_ANNULEE:  #
                return False, "La demande est déjà annulée."  #

            demandes[i].update(updates)  #
            if "historique_statuts" not in demandes[i]: demandes[i]["historique_statuts"] = []  #
            demandes[i]["historique_statuts"].append(nouvelle_entree_historique)  #
            demande_trouvee = True  #
            break  #

    if not demande_trouvee:  #
        return False, "Demande non trouvée."  #

    _sauvegarder_remboursements(demandes)  #
    return True, f"Demande annulée avec succès. Statut: '{STATUT_ANNULEE}'."  #


# --- Fonctions pour l'étape de j.durousset (validation) ---
def valider_demande_par_validateur(id_demande: str, commentaire: str | None, utilisateur_validateur: str) -> tuple[
    bool, str]:
    """Action lorsque j.durousset/b.gonnet valide la demande."""
    updates = {
        "statut": STATUT_VALIDEE,
        "derniere_modification_par": utilisateur_validateur,
        "date_derniere_modification": datetime.datetime.now().isoformat()
    }
    nouvelle_entree_historique = {
        "statut": STATUT_VALIDEE,
        "date": updates["date_derniere_modification"],
        "par": utilisateur_validateur,
        "commentaire": commentaire if commentaire else "Demande validée."
    }

    demandes = _charger_remboursements()
    demande_trouvee = False
    for i, demande in enumerate(demandes):
        if demande.get("id_demande") == id_demande:
            if demande.get("statut") != STATUT_TROP_PERCU_CONSTATE:
                return False, f"La demande n'est pas au statut '{STATUT_TROP_PERCU_CONSTATE}' attendu pour validation."
            demandes[i].update(updates)
            if "historique_statuts" not in demandes[i]: demandes[i]["historique_statuts"] = []
            demandes[i]["historique_statuts"].append(nouvelle_entree_historique)
            demande_trouvee = True
            break

    if not demande_trouvee:
        return False, "Demande non trouvée."

    _sauvegarder_remboursements(demandes)
    return True, f"Demande validée. Statut mis à jour à '{STATUT_VALIDEE}'."


def refuser_demande_par_validateur(id_demande: str, commentaire: str, utilisateur_validateur: str) -> tuple[bool, str]:
    """Action lorsque j.durousset/b.gonnet refuse la demande, la renvoyant à m.lupo."""
    updates = {
        "statut": STATUT_REFUSEE_VALIDATION_CORRECTION_MLUPO,
        "derniere_modification_par": utilisateur_validateur,
        "date_derniere_modification": datetime.datetime.now().isoformat()
    }
    nouvelle_entree_historique = {
        "statut": STATUT_REFUSEE_VALIDATION_CORRECTION_MLUPO,
        "date": updates["date_derniere_modification"],
        "par": utilisateur_validateur,
        "commentaire": commentaire
    }

    demandes = _charger_remboursements()
    demande_trouvee = False
    for i, demande in enumerate(demandes):
        if demande.get("id_demande") == id_demande:
            if demande.get("statut") != STATUT_TROP_PERCU_CONSTATE:
                return False, f"La demande n'est pas au statut '{STATUT_TROP_PERCU_CONSTATE}' attendu pour un refus par validateur."
            demandes[i].update(updates)
            if "historique_statuts" not in demandes[i]: demandes[i]["historique_statuts"] = []
            demandes[i]["historique_statuts"].append(nouvelle_entree_historique)
            demande_trouvee = True
            break

    if not demande_trouvee:
        return False, "Demande non trouvée."

    _sauvegarder_remboursements(demandes)
    return True, f"Demande refusée par validateur. Renvoyée pour correction à Compta. Trésorerie. Statut: '{STATUT_REFUSEE_VALIDATION_CORRECTION_MLUPO}'."