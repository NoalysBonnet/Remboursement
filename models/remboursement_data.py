# models/remboursement_data.py
import os
import datetime
import shutil
import re
from config.settings import REMBOURSEMENT_FILES_DIR, REMBOURSEMENTS_JSON_FILE
from utils.data_manager import read_modify_write_json, load_json_data


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
    return load_json_data(REMBOURSEMENTS_JSON_FILE)


def sauvegarder_toutes_les_demandes_data(remboursements: list):
    def modification(data):
        data.clear()
        data.extend(remboursements)

    read_modify_write_json(REMBOURSEMENTS_JSON_FILE, modification)


def creer_demande_data(nouvelle_demande_dict: dict) -> dict | None:
    def modification(demandes: list):
        demandes.append(nouvelle_demande_dict)

    read_modify_write_json(REMBOURSEMENTS_JSON_FILE, modification)

    ref_dossier = nouvelle_demande_dict.get("reference_facture_dossier")
    id_unique_demande = nouvelle_demande_dict.get("id_demande")
    if ref_dossier and id_unique_demande:
        dossier_demande_specifique = os.path.join(REMBOURSEMENT_FILES_DIR, ref_dossier)
        nom_fichier_info_txt = "informations_demande.txt"
        chemin_fichier_info_txt = os.path.join(dossier_demande_specifique, nom_fichier_info_txt)
        try:
            with open(chemin_fichier_info_txt, 'w', encoding='utf-8') as f_txt:
                f_txt.write(f"Informations pour la demande: {id_unique_demande}\n")
                f_txt.write("=" * 40 + "\n")
                for cle, valeur in nouvelle_demande_dict.items():
                    if cle == "historique_statuts":
                        f_txt.write("\nHistorique des Statuts et Commentaires:\n")
                        if isinstance(valeur, list) and valeur:
                            for item_hist in valeur:
                                f_txt.write(f"  - Statut: {item_hist.get('statut', 'N/A')}\n")
                                f_txt.write(f"    Date: {item_hist.get('date', 'N/A')}\n")
                                f_txt.write(f"    Par: {item_hist.get('par', 'N/A')}\n")
                                f_txt.write(f"    Commentaire: {item_hist.get('commentaire', 'N/A')}\n")
                                f_txt.write("-" * 20 + "\n")
                        else:
                            f_txt.write("  Aucun historique disponible.\n")
                    elif isinstance(valeur, list):
                        f_txt.write(f"{cle.replace('_', ' ').title()}:\n")
                        if valeur:
                            for item_path in valeur:
                                f_txt.write(f"  - {item_path}\n")
                        else:
                            f_txt.write("  N/A\n")
                    else:
                        f_txt.write(f"{cle.replace('_', ' ').title()}: {valeur if valeur is not None else 'N/A'}\n")
                f_txt.write("\n" + "=" * 40 + "\n")
                f_txt.write(f"Fichier généré le: {datetime.datetime.now().isoformat()}\n")
            print(f"Fichier d'information '{chemin_fichier_info_txt}' créé avec succès.")
        except IOError as e:
            print(f"Erreur lors de la création du fichier d'information '{chemin_fichier_info_txt}': {e}")

    return nouvelle_demande_dict


def obtenir_demande_par_id_data(id_demande: str) -> dict | None:
    demandes = charger_toutes_les_demandes_data()
    for demande in demandes:
        if demande.get("id_demande") == id_demande:
            return demande
    return None


def mettre_a_jour_demande_data(id_demande: str, updates: dict) -> bool:
    def modification(demandes: list) -> bool:
        demande_trouvee_et_maj = False
        for i, demande in enumerate(demandes):
            if demande.get("id_demande") == id_demande:
                for cle, valeur in updates.items():
                    if cle in ["chemins_factures_stockees", "chemins_rib_stockes",
                               "pieces_capture_trop_percu"] and isinstance(valeur, str):
                        if cle not in demandes[i] or not isinstance(demandes[i][cle], list):
                            demandes[i][cle] = []
                        demandes[i][cle].append(valeur)
                    else:
                        demandes[i][cle] = valeur

                demandes[i]["date_derniere_modification"] = datetime.datetime.now().isoformat()
                demande_trouvee_et_maj = True
                break
        return demande_trouvee_et_maj

    return read_modify_write_json(REMBOURSEMENTS_JSON_FILE, modification)


def ajouter_entree_historique_data(id_demande: str, nouvelle_entree: dict) -> bool:
    def modification(demandes: list) -> bool:
        demande_trouvee = False
        for i, demande in enumerate(demandes):
            if demande.get("id_demande") == id_demande:
                if "historique_statuts" not in demandes[i] or not isinstance(demandes[i]["historique_statuts"], list):
                    demandes[i]["historique_statuts"] = []
                demandes[i]["historique_statuts"].append(nouvelle_entree)
                demande_trouvee = True
                break
        return demande_trouvee

    return read_modify_write_json(REMBOURSEMENTS_JSON_FILE, modification)


def supprimer_demande_par_id_data(id_demande_a_supprimer: str) -> tuple[bool, str]:
    demande_a_supprimer_trouvee = [None]

    def modification(demandes: list) -> bool:
        original_len = len(demandes)
        demande_a_supprimer_trouvee[0] = next((d for d in demandes if d.get("id_demande") == id_demande_a_supprimer),
                                              None)

        if demande_a_supprimer_trouvee[0]:
            demandes[:] = [d for d in demandes if d.get("id_demande") != id_demande_a_supprimer]
            return len(demandes) < original_len
        return False

    succes = read_modify_write_json(REMBOURSEMENTS_JSON_FILE, modification)

    if not succes:
        return False, f"Demande ID {id_demande_a_supprimer} non trouvée."

    if demande_a_supprimer_trouvee[0]:
        ref_dossier = demande_a_supprimer_trouvee[0].get("reference_facture_dossier")
        if ref_dossier:
            chemin_dossier_demande = os.path.join(REMBOURSEMENT_FILES_DIR, ref_dossier)
            if os.path.exists(chemin_dossier_demande) and os.path.isdir(chemin_dossier_demande):
                try:
                    shutil.rmtree(chemin_dossier_demande)
                    print(f"Dossier {chemin_dossier_demande} supprimé avec succès.")
                except OSError as e:
                    print(f"Erreur lors de la suppression du dossier {chemin_dossier_demande}: {e}")
                    return True, f"Demande ID {id_demande_a_supprimer} supprimée du JSON, mais échec de la suppression du dossier {ref_dossier}."

    return True, f"Demande ID {id_demande_a_supprimer} supprimée avec succès."