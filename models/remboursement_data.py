# models/remboursement_data.py
import os
import datetime
import shutil
import re
import json
from pydantic import ValidationError

from config.settings import REMBOURSEMENTS_ATTACHMENTS_DIR, REMBOURSEMENTS_JSON_DIR, REMBOURSEMENTS_ARCHIVE_JSON_DIR, \
    REMBOURSEMENTS_ARCHIVE_ATTACHMENTS_DIR
from utils.data_manager import read_modify_write_json, _save_json_atomically
from utils.ui_messages import show_recovery_success, show_recovery_error
from .schemas import Remboursement


def _sanitize_directory_name(name: str) -> str:
    if not name: return "ref_inconnue"
    base_name, ext = os.path.splitext(name)
    sanitized_base_name = base_name.replace('/', '_').replace('\\', '_').replace(':', '_')
    sanitized_base_name = "".join(c if c.isalnum() or c in ['_', '-'] else '_' for c in sanitized_base_name)
    sanitized_base_name = sanitized_base_name.strip('.')
    sanitized_base_name = re.sub(r'[_.-]+', '_', sanitized_base_name)
    if not sanitized_base_name:
        sanitized_base_name = "fichier_inconnu"
    if ext:
        sanitized_ext = "".join(c if c.isalnum() else "" for c in ext.lower())
        if sanitized_ext:
            ext = "." + sanitized_ext
        else:
            ext = ""
    return sanitized_base_name + ext


def _load_and_validate_demande(file_path: str) -> dict | None:
    """Charge et valide un unique fichier JSON de demande, avec mécanisme de récupération."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            validated_model = Remboursement.model_validate(data)
            return validated_model.model_dump()
    except (json.JSONDecodeError, ValidationError, IOError) as e:
        print(f"ALERTE: Fichier de demande invalide ou corrompu détecté : {file_path}. Erreur : {e}")
        backup_path = file_path + ".bak"
        if os.path.exists(backup_path):
            try:
                print(f"Tentative de restauration depuis {backup_path}...")
                shutil.copy2(backup_path, file_path)
                with open(file_path, 'r', encoding='utf-8') as f_bak:
                    data_bak = json.load(f_bak)
                    validated_data = Remboursement.model_validate(data_bak).model_dump()
                print("Restauration réussie.")
                show_recovery_success(file_path)
                return validated_data
            except (json.JSONDecodeError, ValidationError, IOError):
                print(f"ERREUR: Le fichier de backup {backup_path} est aussi invalide.")
                show_recovery_error(file_path, backup_exists=True)
                return None
        else:
            print("ERREUR: Aucun fichier de backup trouvé.")
            show_recovery_error(file_path, backup_exists=False)
            return None
    return None


def charger_toutes_les_demandes_data(include_archives: bool = False) -> list:
    demandes = []

    def read_from_dir(directory, is_archived_flag):
        if not os.path.exists(directory):
            return []
        loaded_demandes = []
        for filename in os.listdir(directory):
            if filename.endswith('.json') and not filename.endswith('.bak'):
                file_path = os.path.join(directory, filename)
                demande_data = _load_and_validate_demande(file_path)
                if demande_data:
                    demande_data['is_archived'] = is_archived_flag
                    loaded_demandes.append(demande_data)
        return loaded_demandes

    demandes.extend(read_from_dir(REMBOURSEMENTS_JSON_DIR, is_archived_flag=False))
    if include_archives:
        demandes.extend(read_from_dir(REMBOURSEMENTS_ARCHIVE_JSON_DIR, is_archived_flag=True))

    return demandes


def creer_demande_data(nouvelle_demande_dict: dict) -> dict | None:
    id_demande = nouvelle_demande_dict.get("id_demande")
    if not id_demande:
        return None

    file_path = os.path.join(REMBOURSEMENTS_JSON_DIR, f"{id_demande}.json")
    try:
        _save_json_atomically(file_path, nouvelle_demande_dict)
    except IOError as e:
        print(f"Erreur critique lors de la sauvegarde de la nouvelle demande {id_demande}: {e}")
        return None

    ref_dossier = nouvelle_demande_dict.get("reference_facture_dossier")
    if ref_dossier:
        dossier_demande_specifique = os.path.join(REMBOURSEMENTS_ATTACHMENTS_DIR, ref_dossier)
        nom_fichier_info_txt = "informations_demande.txt"
        chemin_fichier_info_txt = os.path.join(dossier_demande_specifique, nom_fichier_info_txt)
        try:
            with open(chemin_fichier_info_txt, 'w', encoding='utf-8') as f_txt:
                f_txt.write(json.dumps(nouvelle_demande_dict, indent=4, ensure_ascii=False, default=str))
        except IOError as e:
            print(f"Erreur lors de la création du fichier d'information '{chemin_fichier_info_txt}': {e}")

    return nouvelle_demande_dict


def obtenir_demande_par_id_data(id_demande: str) -> dict | None:
    file_path_active = os.path.join(REMBOURSEMENTS_JSON_DIR, f"{id_demande}.json")
    if os.path.exists(file_path_active):
        demande = _load_and_validate_demande(file_path_active)
        if demande:
            demande['is_archived'] = False
        return demande

    file_path_archive = os.path.join(REMBOURSEMENTS_ARCHIVE_JSON_DIR, f"{id_demande}.json")
    if os.path.exists(file_path_archive):
        demande = _load_and_validate_demande(file_path_archive)
        if demande:
            demande['is_archived'] = True
        return demande

    return None


def mettre_a_jour_demande_data(id_demande: str, updates: dict) -> bool:
    file_path = os.path.join(REMBOURSEMENTS_JSON_DIR, f"{id_demande}.json")
    if not os.path.exists(file_path):
        return False

    def modification(demande: dict) -> bool:
        for cle, valeur in updates.items():
            if cle in ["chemins_factures_stockees", "chemins_rib_stockes",
                       "pieces_capture_trop_percu"] and isinstance(valeur, str):
                if cle not in demande or not isinstance(demande[cle], list):
                    demande[cle] = []
                demande[cle].append(valeur)
            else:
                demande[cle] = valeur
        demande["date_derniere_modification"] = datetime.datetime.now().isoformat()
        return True

    return read_modify_write_json(file_path, modification)


def ajouter_entree_historique_data(id_demande: str, nouvelle_entree: dict) -> bool:
    file_path = os.path.join(REMBOURSEMENTS_JSON_DIR, f"{id_demande}.json")
    if not os.path.exists(file_path):
        return False

    def modification(demande: dict) -> bool:
        demande["historique_statuts"].append(nouvelle_entree)
        return True

    return read_modify_write_json(file_path, modification)


def supprimer_demande_par_id_data(id_demande_a_supprimer: str) -> tuple[bool, str]:
    demande_a_supprimer = obtenir_demande_par_id_data(id_demande_a_supprimer)
    if not demande_a_supprimer:
        return False, f"Demande ID {id_demande_a_supprimer} non trouvée."

    is_archived = demande_a_supprimer.get('is_archived', False)
    json_dir = REMBOURSEMENTS_ARCHIVE_JSON_DIR if is_archived else REMBOURSEMENTS_JSON_DIR
    attachment_dir = REMBOURSEMENTS_ARCHIVE_ATTACHMENTS_DIR if is_archived else REMBOURSEMENTS_ATTACHMENTS_DIR

    file_path = os.path.join(json_dir, f"{id_demande_a_supprimer}.json")
    backup_path = file_path + ".bak"

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(backup_path):
            os.remove(backup_path)
    except OSError as e:
        return False, f"Erreur lors de la suppression des fichiers de données : {e}"

    ref_dossier = demande_a_supprimer.get("reference_facture_dossier")
    if ref_dossier:
        chemin_dossier_demande = os.path.join(attachment_dir, ref_dossier)
        if os.path.exists(chemin_dossier_demande):
            try:
                shutil.rmtree(chemin_dossier_demande)
            except OSError as e:
                return True, f"Données supprimées, mais échec de la suppression du dossier de PJ : {e}."

    return True, f"Demande ID {id_demande_a_supprimer} et ses fichiers associés supprimés avec succès."


def archiver_demande_par_id(id_demande: str) -> bool:
    demande_data = obtenir_demande_par_id_data(id_demande)
    if not demande_data:
        return False

    source_json_path = os.path.join(REMBOURSEMENTS_JSON_DIR, f"{id_demande}.json")
    dest_json_path = os.path.join(REMBOURSEMENTS_ARCHIVE_JSON_DIR, f"{id_demande}.json")
    source_bak_path = source_json_path + ".bak"
    dest_bak_path = dest_json_path + ".bak"
    bak_moved = False

    if os.path.exists(source_json_path):
        try:
            shutil.move(source_json_path, dest_json_path)
        except Exception as e:
            print(f"Erreur archivage JSON demande {id_demande}: {e}")
            return False

    if os.path.exists(source_bak_path):
        try:
            shutil.move(source_bak_path, dest_bak_path)
            bak_moved = True
        except Exception as e:
            print(f"Erreur archivage fichier .bak demande {id_demande}: {e}")
            if os.path.exists(dest_json_path):
                shutil.move(dest_json_path, source_json_path)
            return False

    ref_dossier = demande_data.get("reference_facture_dossier")
    if ref_dossier:
        source_attachment_path = os.path.join(REMBOURSEMENTS_ATTACHMENTS_DIR, ref_dossier)
        dest_attachment_path = os.path.join(REMBOURSEMENTS_ARCHIVE_ATTACHMENTS_DIR, ref_dossier)
        if os.path.exists(source_attachment_path):
            try:
                shutil.move(source_attachment_path, dest_attachment_path)
            except Exception as e:
                print(f"Erreur archivage PJ demande {id_demande}: {e}")
                if os.path.exists(dest_json_path):
                    shutil.move(dest_json_path, source_json_path)
                if bak_moved and os.path.exists(dest_bak_path):
                    shutil.move(dest_bak_path, source_bak_path)
                return False
    return True