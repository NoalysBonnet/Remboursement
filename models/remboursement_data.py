# models/remboursement_data.py
import os
import datetime
import shutil
import re
import json
from config.settings import REMBOURSEMENTS_ATTACHMENTS_DIR, REMBOURSEMENTS_JSON_DIR
from utils.data_manager import read_modify_write_json, load_json_data, _save_json_atomically


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


def charger_toutes_les_demandes_data() -> list:
    demandes = []
    if not os.path.exists(REMBOURSEMENTS_JSON_DIR):
        return []
    for filename in os.listdir(REMBOURSEMENTS_JSON_DIR):
        if filename.endswith('.json'):
            file_path = os.path.join(REMBOURSEMENTS_JSON_DIR, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    demandes.append(json.load(f))
            except (IOError, json.JSONDecodeError) as e:
                print(f"Erreur lors de la lecture du fichier de demande {filename}: {e}")
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
                f_txt.write(json.dumps(nouvelle_demande_dict, indent=4, ensure_ascii=False))
        except IOError as e:
            print(f"Erreur lors de la création du fichier d'information '{chemin_fichier_info_txt}': {e}")

    return nouvelle_demande_dict


def obtenir_demande_par_id_data(id_demande: str) -> dict | None:
    file_path = os.path.join(REMBOURSEMENTS_JSON_DIR, f"{id_demande}.json")
    if not os.path.exists(file_path):
        return None
    return load_json_data(file_path)


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
        if "historique_statuts" not in demande or not isinstance(demande["historique_statuts"], list):
            demande["historique_statuts"] = []
        demande["historique_statuts"].append(nouvelle_entree)
        return True

    return read_modify_write_json(file_path, modification)


def supprimer_demande_par_id_data(id_demande_a_supprimer: str) -> tuple[bool, str]:
    demande_a_supprimer = obtenir_demande_par_id_data(id_demande_a_supprimer)
    if not demande_a_supprimer:
        return False, f"Demande ID {id_demande_a_supprimer} non trouvée."

    file_path = os.path.join(REMBOURSEMENTS_JSON_DIR, f"{id_demande_a_supprimer}.json")
    backup_path = file_path + ".bak"

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(backup_path):
            os.remove(backup_path)
    except OSError as e:
        return False, f"Erreur lors de la suppression des fichiers de données pour la demande {id_demande_a_supprimer}: {e}"

    ref_dossier = demande_a_supprimer.get("reference_facture_dossier")
    if ref_dossier:
        chemin_dossier_demande = os.path.join(REMBOURSEMENTS_ATTACHMENTS_DIR, ref_dossier)
        if os.path.exists(chemin_dossier_demande) and os.path.isdir(chemin_dossier_demande):
            try:
                shutil.rmtree(chemin_dossier_demande)
                print(f"Dossier {chemin_dossier_demande} supprimé avec succès.")
            except OSError as e:
                print(f"Erreur lors de la suppression du dossier {chemin_dossier_demande}: {e}")
                return True, f"Données de la demande ID {id_demande_a_supprimer} supprimées, mais échec de la suppression du dossier de pièces jointes."

    return True, f"Demande ID {id_demande_a_supprimer} et ses fichiers associés supprimés avec succès."