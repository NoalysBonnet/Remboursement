import os
import datetime
import shutil
from . import remboursement_data
from config.settings import (
    REMBOURSEMENTS_ATTACHMENTS_DIR,
    STATUT_CREEE, STATUT_TROP_PERCU_CONSTATE,
    STATUT_REFUSEE_CONSTAT_TP, STATUT_ANNULEE,
    STATUT_VALIDEE, STATUT_REFUSEE_VALIDATION_CORRECTION_MLUPO,
    STATUT_PAIEMENT_EFFECTUE
)


def _sanitize_directory_name_workflow(name: str) -> str:
    return remboursement_data._sanitize_directory_name(name)


def _ajouter_pj_a_liste(id_demande: str, chemin_pj_source: str, utilisateur: str, type_pj_key: str,
                        prefixe_nom_fichier: str) -> tuple[bool, str, str | None]:
    """Helper pour ajouter une PJ à une liste de PJ d'une demande et la copier."""
    demande_data_obj = remboursement_data.obtenir_demande_par_id_data(id_demande)
    if not demande_data_obj:
        return False, "Demande non trouvée.", None

    ref_dossier = demande_data_obj.get("reference_facture_dossier")
    if not ref_dossier:
        return False, "Référence de dossier non trouvée.", None

    dossier_demande_specifique = os.path.join(REMBOURSEMENTS_ATTACHMENTS_DIR, ref_dossier)
    os.makedirs(dossier_demande_specifique, exist_ok=True)

    base_nom_pj = os.path.basename(chemin_pj_source)

    current_pjs_list = demande_data_obj.get(type_pj_key, [])
    if not isinstance(current_pjs_list, list):
        current_pjs_list = [current_pjs_list] if current_pjs_list else []

    version_index = len(current_pjs_list) + 1

    nom_fichier_pj_stockee = f"{prefixe_nom_fichier}_v{version_index}_{ref_dossier}_{_sanitize_directory_name_workflow(base_nom_pj)}"
    chemin_pj_destination = os.path.join(dossier_demande_specifique, nom_fichier_pj_stockee)

    try:
        shutil.copy2(chemin_pj_source, chemin_pj_destination)
    except Exception as e:
        return False, f"Erreur lors de la copie de la pièce jointe '{base_nom_pj}' ({prefixe_nom_fichier}): {e}", None

    chemin_pj_relatif = os.path.join(ref_dossier, nom_fichier_pj_stockee)

    current_pjs_list.append(chemin_pj_relatif)

    updates = {
        type_pj_key: current_pjs_list,
        "derniere_modification_par": utilisateur,
        "date_derniere_modification": datetime.datetime.now().isoformat()
    }
    succes_maj = remboursement_data.mettre_a_jour_demande_data(id_demande, updates)

    if succes_maj:
        return True, f"Pièce jointe '{base_nom_pj}' (v{version_index}) ajoutée.", chemin_pj_relatif
    else:
        if os.path.exists(chemin_pj_destination):
            try:
                os.remove(chemin_pj_destination)
            except OSError:
                pass
        return False, "Erreur lors de la mise à jour des données de la demande après copie PJ.", None


def ajouter_piece_jointe_trop_percu_action(id_demande: str, chemin_pj_source: str, utilisateur: str) -> tuple[
    bool, str, str | None]:
    return _ajouter_pj_a_liste(id_demande, chemin_pj_source, utilisateur, "pieces_capture_trop_percu", "trop_percu")


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
        nom_patient = f"{demande_actuelle.get('prenom', '')} {demande_actuelle.get('nom', '')}".strip()
        return True, f"Constat accepté pour {nom_patient}."
    return False, "Erreur lors de l'acceptation du constat."


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
        nom_patient = f"{demande_actuelle.get('prenom', '')} {demande_actuelle.get('nom', '')}".strip()
        return True, f"Constat refusé pour {nom_patient}."
    return False, "Erreur lors du refus du constat."


def annuler_demande_action(id_demande: str, commentaire: str, utilisateur_annulant: str) -> tuple[bool, str]:
    demande_actuelle = remboursement_data.obtenir_demande_par_id_data(id_demande)
    if not demande_actuelle: return False, "Demande non trouvée."
    if demande_actuelle.get("statut") == STATUT_ANNULEE: return False, "Demande déjà annulée."

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
        nom_patient = f"{demande_actuelle.get('prenom', '')} {demande_actuelle.get('nom', '')}".strip()
        return True, f"Demande pour {nom_patient} annulée."
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
        "commentaire": commentaire if commentaire and commentaire.strip() else "Demande validée par validateur."
    }
    succes_maj_demande = remboursement_data.mettre_a_jour_demande_data(id_demande, updates)
    succes_hist = remboursement_data.ajouter_entree_historique_data(id_demande, nouvelle_entree_historique)

    if succes_maj_demande and succes_hist:
        nom_patient = f"{demande_actuelle.get('prenom', '')} {demande_actuelle.get('nom', '')}".strip()
        return True, f"Demande pour {nom_patient} validée."
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
        nom_patient = f"{demande_actuelle.get('prenom', '')} {demande_actuelle.get('nom', '')}".strip()
        return True, f"Demande pour {nom_patient} refusée et renvoyée pour correction."
    return False, "Erreur lors du refus de la demande par le validateur."


def confirmer_paiement_action(id_demande: str, utilisateur_pdiop: str, commentaire: str | None) -> tuple[bool, str]:
    demande_actuelle = remboursement_data.obtenir_demande_par_id_data(id_demande)
    if not demande_actuelle:
        return False, "Demande non trouvée."
    if demande_actuelle.get("statut") != STATUT_VALIDEE:
        return False, f"La demande n'est pas au statut '{STATUT_VALIDEE}' pour confirmation du paiement."

    date_paiement = datetime.datetime.now().isoformat()
    updates = {
        "statut": STATUT_PAIEMENT_EFFECTUE,
        "derniere_modification_par": utilisateur_pdiop,
        "date_derniere_modification": date_paiement,
        "date_paiement_effectue": date_paiement,
    }
    nouvelle_entree_historique = {
        "statut": STATUT_PAIEMENT_EFFECTUE,
        "date": date_paiement,
        "par": utilisateur_pdiop,
        "commentaire": commentaire if commentaire and commentaire.strip() else "Paiement effectué."
    }

    succes_maj_demande = remboursement_data.mettre_a_jour_demande_data(id_demande, updates)
    succes_hist = remboursement_data.ajouter_entree_historique_data(id_demande, nouvelle_entree_historique)

    if succes_maj_demande and succes_hist:
        nom_patient = f"{demande_actuelle.get('prenom', '')} {demande_actuelle.get('nom', '')}".strip()
        return True, f"Paiement confirmé pour {nom_patient}."
    return False, "Erreur lors de la confirmation du paiement."


def pneri_resoumettre_demande_action(id_demande: str, nouveau_commentaire: str,
                                     nouveau_chemin_facture_source: str | None,
                                     nouveau_chemin_rib_source: str | None,
                                     utilisateur: str) -> tuple[bool, str]:
    demande_actuelle = remboursement_data.obtenir_demande_par_id_data(id_demande)
    if not demande_actuelle: return False, "Demande non trouvée."
    if demande_actuelle.get("statut") != STATUT_REFUSEE_CONSTAT_TP:
        return False, f"La demande n'est pas au statut '{STATUT_REFUSEE_CONSTAT_TP}'."

    if not nouveau_chemin_facture_source and not nouveau_chemin_rib_source:
        if not nouveau_commentaire or not nouveau_commentaire.strip():
            return False, "Aucune modification fournie. Veuillez ajouter un commentaire ou de nouveaux fichiers."

    if nouveau_chemin_facture_source:
        succes_fact, msg_fact, _ = _ajouter_pj_a_liste(id_demande, nouveau_chemin_facture_source, utilisateur,
                                                       "chemins_factures_stockees", "facture")
        if not succes_fact: return False, msg_fact

    if nouveau_chemin_rib_source:
        succes_rib, msg_rib, _ = _ajouter_pj_a_liste(id_demande, nouveau_chemin_rib_source, utilisateur,
                                                     "chemins_rib_stockes", "RIB")
        if not succes_rib: return False, msg_rib

    updates = {
        "statut": STATUT_CREEE,
        "derniere_modification_par": utilisateur,
        "date_derniere_modification": datetime.datetime.now().isoformat()
    }
    nouvelle_entree_historique = {
        "statut": STATUT_CREEE,
        "date": updates["date_derniere_modification"],
        "par": utilisateur,
        "commentaire": f"Demande corrigée et resoumise: {nouveau_commentaire}"
    }

    succes_maj_demande = remboursement_data.mettre_a_jour_demande_data(id_demande, updates)
    succes_hist = remboursement_data.ajouter_entree_historique_data(id_demande, nouvelle_entree_historique)

    if succes_maj_demande and succes_hist:
        nom_patient = f"{demande_actuelle.get('prenom', '')} {demande_actuelle.get('nom', '')}".strip()
        return True, f"Demande pour {nom_patient} corrigée et resoumise."
    return False, "Erreur lors de la resoumission de la demande corrigée."


def mlupo_resoumettre_constat_action(id_demande: str, nouveau_commentaire: str,
                                     nouveau_chemin_pj_trop_percu_source: str | None,
                                     utilisateur: str) -> tuple[bool, str]:
    demande_actuelle = remboursement_data.obtenir_demande_par_id_data(id_demande)
    if not demande_actuelle: return False, "Demande non trouvée."
    if demande_actuelle.get("statut") != STATUT_REFUSEE_VALIDATION_CORRECTION_MLUPO:
        return False, f"La demande n'est pas au statut '{STATUT_REFUSEE_VALIDATION_CORRECTION_MLUPO}'."

    if not nouveau_chemin_pj_trop_percu_source:
        if not nouveau_commentaire or not nouveau_commentaire.strip():
            return False, "Aucune modification fournie. Veuillez ajouter un commentaire ou un nouveau fichier."

    if nouveau_chemin_pj_trop_percu_source:
        succes_pj, msg_pj, _ = ajouter_piece_jointe_trop_percu_action(id_demande,
                                                                      nouveau_chemin_pj_trop_percu_source,
                                                                      utilisateur)
        if not succes_pj: return False, msg_pj

    updates = {
        "statut": STATUT_TROP_PERCU_CONSTATE,
        "derniere_modification_par": utilisateur,
        "date_derniere_modification": datetime.datetime.now().isoformat()
    }
    nouvelle_entree_historique = {
        "statut": STATUT_TROP_PERCU_CONSTATE,
        "date": updates["date_derniere_modification"],
        "par": utilisateur,
        "commentaire": f"Constat corrigé et resoumis: {nouveau_commentaire}"
    }

    succes_maj_demande = remboursement_data.mettre_a_jour_demande_data(id_demande, updates)
    succes_hist = remboursement_data.ajouter_entree_historique_data(id_demande, nouvelle_entree_historique)

    if succes_maj_demande and succes_hist:
        nom_patient = f"{demande_actuelle.get('prenom', '')} {demande_actuelle.get('nom', '')}".strip()
        return True, f"Constat pour {nom_patient} corrigé et resoumis."
    return False, "Erreur lors de la resoumission du constat corrigé."