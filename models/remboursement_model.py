import json
import os
import datetime
import uuid  # Pour générer des ID uniques de demande
import shutil
import re  # Pour la sanitization des noms de dossier
from config.settings import REMBOURSEMENT_BASE_DIR, REMBOURSEMENTS_JSON_FILE  #


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
    return []  #


def _sauvegarder_remboursements(remboursements: list):  #
    """Sauvegarde la liste des demandes de remboursement dans le fichier JSON."""
    with open(REMBOURSEMENTS_JSON_FILE, 'w', encoding='utf-8') as f:  #
        json.dump(remboursements, f, indent=4, ensure_ascii=False)  #


def creer_nouvelle_demande(
        nom: str,
        prenom: str,
        reference_facture: str,
        montant_demande: float,
        chemin_facture_source: str | None,  # Peut être None si non fournie
        chemin_rib_source: str,
        utilisateur_createur: str,
        description: str  # Nouveau champ
) -> dict | None:  #
    """Crée et sauvegarde une nouvelle demande de remboursement."""
    demandes = _charger_remboursements()  #

    id_unique_demande = f"D{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{str(uuid.uuid4())[:4]}"  #

    ref_facture_sanitized = _sanitize_directory_name(reference_facture)  #
    if not ref_facture_sanitized or ref_facture_sanitized in ["ref_inconnue", "ref_invalide"]:  #
        ref_facture_sanitized = f"demande_{id_unique_demande}"  #

    dossier_demande_specifique = os.path.join(REMBOURSEMENT_BASE_DIR, ref_facture_sanitized)  #
    os.makedirs(dossier_demande_specifique, exist_ok=True)  #

    # Gestion de la facture (optionnelle)
    chemin_facture_stockee_relatif = None
    nom_fichier_facture = None
    chemin_facture_destination = None
    if chemin_facture_source:
        base_nom_facture = os.path.basename(chemin_facture_source)  #
        nom_fichier_facture = f"facture_{ref_facture_sanitized}_{base_nom_facture}"  #
        chemin_facture_destination = os.path.join(dossier_demande_specifique, nom_fichier_facture)  #
        chemin_facture_stockee_relatif = os.path.join(ref_facture_sanitized, nom_fichier_facture)  #

    # Gestion du RIB (obligatoire)
    base_nom_rib = os.path.basename(chemin_rib_source)  #
    nom_fichier_rib = f"RIB_{_sanitize_directory_name(nom)}_{_sanitize_directory_name(prenom)}_{base_nom_rib}"  #
    chemin_rib_destination = os.path.join(dossier_demande_specifique, nom_fichier_rib)  #
    chemin_rib_stocke_relatif = os.path.join(ref_facture_sanitized, nom_fichier_rib)  #

    try:
        # Copier la facture seulement si elle est fournie
        if chemin_facture_source and chemin_facture_destination:
            shutil.copy2(chemin_facture_source, chemin_facture_destination)  #
        # Copier le RIB (obligatoire)
        shutil.copy2(chemin_rib_source, chemin_rib_destination)  #
    except Exception as e:  #
        print(f"Erreur lors de la copie des pièces jointes : {e}")  #
        try:  #
            if not os.listdir(dossier_demande_specifique):  #
                os.rmdir(dossier_demande_specifique)  #
            # Ne pas supprimer le dossier s'il contient déjà un fichier (ex: RIB copié avant erreur sur facture)
        except OSError:  #
            pass  #
        return None  #

    nouvelle_demande = {
        "id_demande": id_unique_demande,  #
        "nom": nom.upper() if nom else None,  #
        "prenom": prenom.title() if prenom else None,  #
        "reference_facture": reference_facture,  #
        "reference_facture_dossier": ref_facture_sanitized,  #
        "description": description,  # Nouveau champ
        "montant_demande": montant_demande,  #
        "chemin_facture_stockee": chemin_facture_stockee_relatif,  #
        "chemin_rib_stocke": chemin_rib_stocke_relatif,  #
        "statut": "1. Créée par P. Neri",  #
        "cree_par": utilisateur_createur,  #
        "date_creation": datetime.datetime.now().isoformat(),  #
        "derniere_modification_par": utilisateur_createur,  #
        "date_derniere_modification": datetime.datetime.now().isoformat(),  #
        "historique_statuts": [  #
            {  #
                "statut": "1. Créée par P. Neri",  #
                "date": datetime.datetime.now().isoformat(),  #
                "par": utilisateur_createur,  #
                "commentaire": "Demande initialisée."  #
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
                    f_txt.write("\nHistorique des Statuts:\n")  #
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


def get_chemin_absolu_piece_jointe(chemin_relatif_pj: str) -> str | None:  #
    """Construit le chemin absolu vers une pièce jointe à partir de son chemin relatif."""
    if not chemin_relatif_pj:
        return None
    return os.path.join(REMBOURSEMENT_BASE_DIR, chemin_relatif_pj)  #