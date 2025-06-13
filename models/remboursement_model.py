# models/remboursement_model.py
import os
import datetime
import uuid
import shutil
from . import remboursement_data
from . import remboursement_workflow
from config.settings import REMBOURSEMENTS_ATTACHMENTS_DIR, REMBOURSEMENTS_ARCHIVE_ATTACHMENTS_DIR, STATUT_CREEE, \
    STATUT_PAIEMENT_EFFECTUE, STATUT_ANNULEE


def obtenir_demande_par_id(id_demande: str):
    return remboursement_data.obtenir_demande_par_id_data(id_demande)


def obtenir_toutes_les_demandes(include_archives: bool = False):
    demandes = remboursement_data.charger_toutes_les_demandes_data(include_archives)
    demandes_formatees = []
    for demande_data in demandes:
        demande_data["chemins_factures_stockees"] = demande_data.get("chemins_factures_stockees", [])
        demande_data["chemins_rib_stockes"] = demande_data.get("chemins_rib_stockes", [])
        demande_data["pieces_capture_trop_percu"] = demande_data.get("pieces_capture_trop_percu", [])
        demandes_formatees.append(demande_data)
    return demandes_formatees


def archiver_les_vieilles_demandes() -> int:
    """Parcourt les demandes et archive celles qui sont terminées depuis plus d'un an."""
    count = 0
    douze_mois = datetime.timedelta(days=365)
    now = datetime.datetime.now()

    demandes_actives = remboursement_data.charger_toutes_les_demandes_data(include_archives=False)

    for demande in demandes_actives:
        statut = demande.get("statut")
        if statut in [STATUT_PAIEMENT_EFFECTUE, STATUT_ANNULEE]:
            date_modif_str = demande.get("date_derniere_modification")
            if date_modif_str:
                date_modif = datetime.datetime.fromisoformat(date_modif_str)
                if (now - date_modif) > douze_mois:
                    print(f"Archivage de la demande {demande['id_demande']}...")
                    if remboursement_data.archiver_demande_par_id(demande['id_demande']):
                        count += 1
    return count


def admin_supprimer_archives_anciennes(age_en_annees: int) -> tuple[int, list[str]]:
    demandes_supprimees = 0
    erreurs = []

    cutoff_delta = datetime.timedelta(days=age_en_annees * 365.25)
    date_limite = datetime.datetime.now() - cutoff_delta

    demandes_archivees = [d for d in obtenir_toutes_les_demandes(include_archives=True) if d.get('is_archived')]

    for demande in demandes_archivees:
        date_modif_str = demande.get("date_derniere_modification")
        if date_modif_str:
            date_modif = datetime.datetime.fromisoformat(date_modif_str)
            if date_modif < date_limite:
                id_demande = demande.get("id_demande")
                succes, msg = supprimer_demande_par_id(id_demande)
                if succes:
                    demandes_supprimees += 1
                    print(f"Demande archivée {id_demande} supprimée.")
                else:
                    erreurs.append(f"Erreur suppression {id_demande}: {msg}")
                    print(f"Erreur lors de la suppression de la demande archivée {id_demande}: {msg}")

    return demandes_supprimees, erreurs


archiver_demande_par_id = remboursement_data.archiver_demande_par_id
supprimer_demande_par_id = remboursement_data.supprimer_demande_par_id_data
ajouter_piece_jointe_trop_percu = remboursement_workflow.ajouter_piece_jointe_trop_percu_action
accepter_constat_trop_percu = remboursement_workflow.accepter_constat_trop_percu_action
refuser_constat_trop_percu = remboursement_workflow.refuser_constat_trop_percu_action
annuler_demande = remboursement_workflow.annuler_demande_action
valider_demande_par_validateur = remboursement_workflow.valider_demande_par_validateur_action
refuser_demande_par_validateur = remboursement_workflow.refuser_demande_par_validateur_action
confirmer_paiement_effectue = remboursement_workflow.confirmer_paiement_action
pneri_resoumettre_demande_corrigee = remboursement_workflow.pneri_resoumettre_demande_action
mlupo_resoumettre_constat_corrige = remboursement_workflow.mlupo_resoumettre_constat_action
mlupo_refuser_correction = remboursement_workflow.mlupo_refuser_correction_action


def creer_nouvelle_demande(
        nom: str,
        prenom: str,
        reference_facture: str,
        montant_demande: float,
        chemin_facture_source: str | None,
        chemin_rib_source: str,
        utilisateur_createur: str,
        description: str
) -> dict | None:
    id_unique_demande = f"D{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{str(uuid.uuid4())[:4]}"
    ref_facture_sanitized = remboursement_data._sanitize_directory_name(reference_facture)
    if not ref_facture_sanitized or ref_facture_sanitized in ["ref_inconnue", "ref_invalide"]:
        ref_facture_sanitized = f"demande_{id_unique_demande}"

    dossier_demande_specifique = os.path.join(REMBOURSEMENTS_ATTACHMENTS_DIR, ref_facture_sanitized)
    try:
        os.makedirs(dossier_demande_specifique, exist_ok=True)
    except OSError as e:
        print(f"Erreur critique lors de la création du dossier de demande {dossier_demande_specifique}: {e}")
        return None

    chemins_factures_stockees = []
    if chemin_facture_source:
        base_nom_facture = os.path.basename(chemin_facture_source)
        nom_fichier_facture = f"facture_v1_{ref_facture_sanitized}_{remboursement_data._sanitize_directory_name(base_nom_facture)}"
        chemin_facture_destination = os.path.join(dossier_demande_specifique, nom_fichier_facture)
        try:
            shutil.copy2(chemin_facture_source, chemin_facture_destination)
            chemins_factures_stockees.append(os.path.join(ref_facture_sanitized, nom_fichier_facture))
        except Exception as e:
            print(f"Avertissement : Erreur lors de la copie de la facture (optionnelle) : {e}")

    chemins_rib_stockes = []
    base_nom_rib = os.path.basename(chemin_rib_source)
    nom_fichier_rib = f"RIB_v1_{remboursement_data._sanitize_directory_name(nom)}_{remboursement_data._sanitize_directory_name(prenom)}_{remboursement_data._sanitize_directory_name(base_nom_rib)}"
    chemin_rib_destination = os.path.join(dossier_demande_specifique, nom_fichier_rib)
    try:
        shutil.copy2(chemin_rib_source, chemin_rib_destination)
        chemins_rib_stockes.append(os.path.join(ref_facture_sanitized, nom_fichier_rib))
    except Exception as e:
        print(f"Erreur critique lors de la copie du RIB : {e}")
        if os.path.exists(dossier_demande_specifique) and not os.listdir(dossier_demande_specifique):
            try:
                os.rmdir(dossier_demande_specifique)
            except OSError:
                pass
        return None

    now = datetime.datetime.now()
    now_iso = now.isoformat()
    nouvelle_demande_dict = {
        "id_demande": id_unique_demande,
        "nom": nom.upper() if nom else None,
        "prenom": prenom.title() if prenom else None,
        "reference_facture": reference_facture,
        "reference_facture_dossier": ref_facture_sanitized,
        "description": description,
        "montant_demande": montant_demande,
        "chemins_factures_stockees": chemins_factures_stockees,
        "chemins_rib_stockes": chemins_rib_stockes,
        "statut": STATUT_CREEE,
        "cree_par": utilisateur_createur,
        "date_creation": now_iso,
        "derniere_modification_par": utilisateur_createur,
        "date_derniere_modification": now_iso,
        "historique_statuts": [{
            "statut": STATUT_CREEE,
            "date": now_iso,
            "par": utilisateur_createur,
            "commentaire": description
        }],
        "pieces_capture_trop_percu": [],
        "preuve_paiement_banque": None,
        "date_paiement_effectue": None
    }

    return remboursement_data.creer_demande_data(nouvelle_demande_dict)


def get_chemin_absolu_piece_jointe(chemin_relatif_pj: str | None, is_archived: bool) -> str | None:
    if not chemin_relatif_pj:
        return None
    base_dir = REMBOURSEMENTS_ATTACHMENTS_DIR
    if is_archived:
        # For archived, the path is already absolute to the zip content, handled by archive_utils
        return chemin_relatif_pj

    return os.path.join(base_dir, chemin_relatif_pj)


def get_chemin_absolu_pj_archive_zip(ref_dossier: str) -> str:
    return os.path.join(REMBOURSEMENTS_ARCHIVE_ATTACHMENTS_DIR, f"{ref_dossier}.zip")