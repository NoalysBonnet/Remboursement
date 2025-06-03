# models/remboursement_workflow.py
import os
import datetime
import shutil
from . import remboursement_data  # Utiliser l'import relatif
from config.settings import (
    REMBOURSEMENT_BASE_DIR,
    STATUT_CREEE, STATUT_TROP_PERCU_CONSTATE,
    STATUT_REFUSEE_CONSTAT_TP, STATUT_ANNULEE,
    STATUT_VALIDEE, STATUT_REFUSEE_VALIDATION_CORRECTION_MLUPO
)


def _sanitize_directory_name_workflow(name: str) -> str:  # Wrapper pour garder la fonction locale si besoin
    return remboursement_data._sanitize_directory_name(name)


def ajouter_piece_jointe_trop_percu_action(id_demande: str, chemin_pj_source: str, utilisateur: str) -> tuple[
    bool, str, str | None]:
    demande_data_obj = remboursement_data.obtenir_demande_par_id_data(id_demande)
    if not demande_data_obj:
        return False, "Demande non trouvée.", None

    ref_dossier = demande_data_obj.get("reference_facture_dossier")
    if not ref_dossier:
        return False, "Référence de dossier non trouvée pour la demande.", None

    dossier_demande_specifique = os.path.join(REMBOURSEMENT_BASE_DIR, ref_dossier)
    os.makedirs(dossier_demande_specifique, exist_ok=True)

    nom_original_pj = os.path.basename(chemin_pj_source)
    nom_fichier_pj_stockee = f"trop_percu_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{_sanitize_directory_name_workflow(nom_original_pj)}"
    chemin_pj_destination = os.path.join(dossier_demande_specifique, nom_fichier_pj_stockee)

    try:
        shutil.copy2(chemin_pj_source, chemin_pj_destination)
    except Exception as e:
        return False, f"Erreur lors de la copie de la PJ : {e}", None

    chemin_pj_relatif = os.path.join(ref_dossier, nom_fichier_pj_stockee)

    # Mise à jour de la liste des PJ et des timestamps
    current_pjs = demande_data_obj.get("pieces_capture_trop_percu", [])
    current_pjs.append(chemin_pj_relatif)

    updates = {
        "pieces_capture_trop_percu": current_pjs,
        "derniere_modification_par": utilisateur,
        "date_derniere_modification": datetime.datetime.now().isoformat()
    }
    succes_maj = remboursement_data.mettre_a_jour_demande_data(id_demande, updates)
    if succes_maj:
        return True, "Pièce jointe de trop-perçu ajoutée.", chemin_pj_relatif
    else:
        # Tenter de supprimer la PJ copiée si la mise à jour du JSON échoue (pour la cohérence)
        if os.path.exists(chemin_pj_destination): os.remove(chemin_pj_destination)
        return False, "Erreur lors de la mise à jour des données de la demande après copie PJ.", None


def accepter_constat_trop_percu_action(id_demande: str, commentaire: str, utilisateur: str) -> tuple[bool, str]:
    demande_actuelle = remboursement_data.obtenir_demande_par_id_data(id_demande)
    if not demande_actuelle: return False, "Demande non trouvée."
    if demande_actuelle.get("statut") != STATUT_CREEE:
        return False, f"La demande n'est pas au statut '{STATUT_CREEE}'."

    updates = {
        "statut": STATUT_TROP_PERCU_CONSTATE,
        "derniere_modification_par": utilisateur,
        "date_derniere_modification": datetime.datetime.now().isoformat()
    }
    nouvelle_entree_historique = {
        "statut": STATUT_TROP_PERCU_CONSTATE,
        "date": updates["date_derniere_modification"],
        "par": utilisateur,
        "commentaire": commentaire
    }

    succes_maj_demande = remboursement_data.mettre_a_jour_demande_data(id_demande, updates)
    succes_hist = remboursement_data.ajouter_entree_historique_data(id_demande, nouvelle_entree_historique)

    if succes_maj_demande and succes_hist:
        return True, f"Constat de trop-perçu accepté. Statut: '{STATUT_TROP_PERCU_CONSTATE}'."
    return False, "Erreur lors de la mise à jour de la demande pour acceptation du constat."


def refuser_constat_trop_percu_action(id_demande: str, commentaire: str, utilisateur_mlupo: str) -> tuple[bool, str]:
    demande_actuelle = remboursement_data.obtenir_demande_par_id_data(id_demande)
    if not demande_actuelle: return False, "Demande non trouvée."
    if demande_actuelle.get("statut") != STATUT_CREEE:
        return False, f"La demande n'est pas au statut '{STATUT_CREEE}' pour un refus."

    updates = {
        "statut": STATUT_REFUSEE_CONSTAT_TP,
        "derniere_modification_par": utilisateur_mlupo,
        "date_derniere_modification": datetime.datetime.now().isoformat()
    }
    nouvelle_entree_historique = {
        "statut": STATUT_REFUSEE_CONSTAT_TP,
        "date": updates["date_derniere_modification"],
        "par": utilisateur_mlupo,
        "commentaire": commentaire
    }
    succes_maj_demande = remboursement_data.mettre_a_jour_demande_data(id_demande, updates)
    succes_hist = remboursement_data.ajouter_entree_historique_data(id_demande, nouvelle_entree_historique)

    if succes_maj_demande and succes_hist:
        return True, f"Constat refusé. Statut: '{STATUT_REFUSEE_CONSTAT_TP}'."
    return False, "Erreur lors du refus du constat."


def annuler_demande_action(id_demande: str, commentaire: str, utilisateur_annulant: str) -> tuple[bool, str]:
    demande_actuelle = remboursement_data.obtenir_demande_par_id_data(id_demande)
    if not demande_actuelle: return False, "Demande non trouvée."
    if demande_actuelle.get("statut") == STATUT_ANNULEE: return False, "Demande déjà annulée."
    # Idéalement, vérifier si l'utilisateur_annulant est le créateur ou admin, et si statut = STATUT_REFUSEE_CONSTAT_TP

    updates = {
        "statut": STATUT_ANNULEE,
        "derniere_modification_par": utilisateur_annulant,
        "date_derniere_modification": datetime.datetime.now().isoformat()
    }
    nouvelle_entree_historique = {
        "statut": STATUT_ANNULEE,
        "date": updates["date_derniere_modification"],
        "par": utilisateur_annulant,
        "commentaire": commentaire
    }
    succes_maj_demande = remboursement_data.mettre_a_jour_demande_data(id_demande, updates)
    succes_hist = remboursement_data.ajouter_entree_historique_data(id_demande, nouvelle_entree_historique)

    if succes_maj_demande and succes_hist:
        return True, f"Demande annulée. Statut: '{STATUT_ANNULEE}'."
    return False, "Erreur lors de l'annulation de la demande."


def valider_demande_par_validateur_action(id_demande: str, commentaire: str | None, utilisateur_validateur: str) -> \
tuple[bool, str]:
    demande_actuelle = remboursement_data.obtenir_demande_par_id_data(id_demande)
    if not demande_actuelle: return False, "Demande non trouvée."
    if demande_actuelle.get("statut") != STATUT_TROP_PERCU_CONSTATE:
        return False, f"La demande n'est pas au statut '{STATUT_TROP_PERCU_CONSTATE}' attendu pour validation."

    updates = {
        "statut": STATUT_VALIDEE,
        "derniere_modification_par": utilisateur_validateur,
        "date_derniere_modification": datetime.datetime.now().isoformat()
    }
    nouvelle_entree_historique = {
        "statut": STATUT_VALIDEE,
        "date": updates["date_derniere_modification"],
        "par": utilisateur_validateur,
        "commentaire": commentaire if commentaire else "Demande validée par validateur."
    }
    succes_maj_demande = remboursement_data.mettre_a_jour_demande_data(id_demande, updates)
    succes_hist = remboursement_data.ajouter_entree_historique_data(id_demande, nouvelle_entree_historique)

    if succes_maj_demande and succes_hist:
        return True, f"Demande validée. Statut: '{STATUT_VALIDEE}'."
    return False, "Erreur lors de la validation de la demande."


def refuser_demande_par_validateur_action(id_demande: str, commentaire: str, utilisateur_validateur: str) -> tuple[
    bool, str]:
    demande_actuelle = remboursement_data.obtenir_demande_par_id_data(id_demande)
    if not demande_actuelle: return False, "Demande non trouvée."
    if demande_actuelle.get("statut") != STATUT_TROP_PERCU_CONSTATE:
        return False, f"La demande n'est pas au statut '{STATUT_TROP_PERCU_CONSTATE}' attendu pour un refus par validateur."

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
    succes_maj_demande = remboursement_data.mettre_a_jour_demande_data(id_demande, updates)
    succes_hist = remboursement_data.ajouter_entree_historique_data(id_demande, nouvelle_entree_historique)

    if succes_maj_demande and succes_hist:
        return True, f"Demande refusée par validateur. Statut: '{STATUT_REFUSEE_VALIDATION_CORRECTION_MLUPO}'."
    return False, "Erreur lors du refus de la demande par le validateur."