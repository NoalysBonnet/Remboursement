# models/remboursement_model.py
import os
import datetime
import uuid
import shutil
from . import remboursement_data
from . import remboursement_workflow
from config.settings import REMBOURSEMENT_FILES_DIR, STATUT_CREEE

# Réexporter les fonctions
obtenir_toutes_les_demandes = remboursement_data.charger_toutes_les_demandes_data
supprimer_demande_par_id = remboursement_data.supprimer_demande_par_id_data

ajouter_piece_jointe_trop_percu = remboursement_workflow.ajouter_piece_jointe_trop_percu_action
accepter_constat_trop_percu = remboursement_workflow.accepter_constat_trop_percu_action
refuser_constat_trop_percu = remboursement_workflow.refuser_constat_trop_percu_action
annuler_demande = remboursement_workflow.annuler_demande_action
valider_demande_par_validateur = remboursement_workflow.valider_demande_par_validateur_action
refuser_demande_par_validateur = remboursement_workflow.refuser_demande_par_validateur_action
confirmer_paiement_effectue = remboursement_workflow.confirmer_paiement_action
# Nouvelles actions pour la resoumission après refus
pneri_resoumettre_demande_corrigee = remboursement_workflow.pneri_resoumettre_demande_action
mlupo_resoumettre_constat_corrige = remboursement_workflow.mlupo_resoumettre_constat_action


def creer_nouvelle_demande(
        nom: str,
        prenom: str,
        reference_facture: str,
        montant_demande: float,
        chemin_facture_source: str | None,
        chemin_rib_source: str,
        utilisateur_createur: str,
        description: str
) -> dict | None:  #
    id_unique_demande = f"D{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{str(uuid.uuid4())[:4]}"  #
    ref_facture_sanitized = remboursement_data._sanitize_directory_name(reference_facture)  #
    if not ref_facture_sanitized or ref_facture_sanitized in ["ref_inconnue", "ref_invalide"]:  #
        ref_facture_sanitized = f"demande_{id_unique_demande}"  #

    dossier_demande_specifique = os.path.join(REMBOURSEMENT_FILES_DIR, ref_facture_sanitized)  #
    try:  #
        os.makedirs(dossier_demande_specifique, exist_ok=True)  #
    except OSError as e:  #
        print(f"Erreur critique lors de la création du dossier de demande {dossier_demande_specifique}: {e}")  #
        return None  #

    chemins_factures_stockees = []
    if chemin_facture_source:  #
        # Construire un nom de fichier versionné (v1 pour la première)
        base_nom_facture = os.path.basename(chemin_facture_source)  #
        nom_fichier_facture = f"facture_v1_{ref_facture_sanitized}_{remboursement_data._sanitize_directory_name(base_nom_facture)}"
        chemin_facture_destination = os.path.join(dossier_demande_specifique, nom_fichier_facture)  #
        try:  #
            shutil.copy2(chemin_facture_source, chemin_facture_destination)  #
            chemins_factures_stockees.append(os.path.join(ref_facture_sanitized, nom_fichier_facture))  #
        except Exception as e:  #
            print(f"Avertissement : Erreur lors de la copie de la facture (optionnelle) : {e}")  #

    chemins_rib_stockes = []
    base_nom_rib = os.path.basename(chemin_rib_source)  #
    nom_fichier_rib = f"RIB_v1_{remboursement_data._sanitize_directory_name(nom)}_{remboursement_data._sanitize_directory_name(prenom)}_{remboursement_data._sanitize_directory_name(base_nom_rib)}"
    chemin_rib_destination = os.path.join(dossier_demande_specifique, nom_fichier_rib)  #
    try:  #
        shutil.copy2(chemin_rib_source, chemin_rib_destination)  #
        chemins_rib_stockes.append(os.path.join(ref_facture_sanitized, nom_fichier_rib))  #
    except Exception as e:  #
        print(f"Erreur critique lors de la copie du RIB : {e}")  #
        if os.path.exists(dossier_demande_specifique) and not os.listdir(dossier_demande_specifique):  #
            try:
                os.rmdir(dossier_demande_specifique)  #
            except OSError:
                pass  #
        return None  #

    nouvelle_demande_dict = {  #
        "id_demande": id_unique_demande,  #
        "nom": nom.upper() if nom else None,  #
        "prenom": prenom.title() if prenom else None,  #
        "reference_facture": reference_facture,  #
        "reference_facture_dossier": ref_facture_sanitized,  #
        "description": description,  #
        "montant_demande": montant_demande,  #
        "chemins_factures_stockees": chemins_factures_stockees,  # Modifié en liste
        "chemins_rib_stockes": chemins_rib_stockes,  # Modifié en liste
        "statut": STATUT_CREEE,  #
        "cree_par": utilisateur_createur,  #
        "date_creation": datetime.datetime.now().isoformat(),  #
        "derniere_modification_par": utilisateur_createur,  #
        "date_derniere_modification": datetime.datetime.now().isoformat(),  #
        "historique_statuts": [{  #
            "statut": STATUT_CREEE,  #
            "date": datetime.datetime.now().isoformat(),  #
            "par": utilisateur_createur,  #
            "commentaire": description  #
        }],
        "pieces_capture_trop_percu": [],  # # Déjà une liste
        "preuve_paiement_banque": None,  # Reste None pour l'instant, deviendra une liste si pdiop peut resoumettre
        "date_paiement_effectue": None  #
    }

    return remboursement_data.creer_demande_data(nouvelle_demande_dict)  #


def get_chemin_absolu_piece_jointe(chemin_relatif_pj: str | None) -> str | None:  #
    """Construit le chemin absolu vers une pièce jointe à partir de son chemin relatif."""
    if not chemin_relatif_pj:  #
        return None  #
    return os.path.join(REMBOURSEMENT_FILES_DIR, chemin_relatif_pj)  #