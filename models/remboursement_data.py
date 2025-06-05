import json
import os
import datetime
import uuid
import shutil
import re
import tempfile
from config.settings import REMBOURSEMENT_BASE_DIR, REMBOURSEMENTS_JSON_FILE


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


def _sauvegarder_fichier_json_atomic(chemin_fichier: str, donnees: list | dict):  # Accepte list ou dict
    dir_name = os.path.dirname(chemin_fichier)
    if not os.path.exists(dir_name):
        try:
            os.makedirs(dir_name)
        except OSError as e:
            print(f"Erreur critique lors de la création du dossier pour la sauvegarde atomique '{dir_name}': {e}")
            raise

    temp_file_path = ""
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False,
                                         dir=dir_name,
                                         prefix=os.path.basename(chemin_fichier).replace('.json', '') + '~',
                                         suffix='.json.tmp') as tf:
            json.dump(donnees, tf, indent=4, ensure_ascii=False)
            temp_file_path = tf.name

        os.replace(temp_file_path, chemin_fichier)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde atomique de {chemin_fichier}: {e}")
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                pass
        raise


def charger_toutes_les_demandes_data() -> list:
    if os.path.exists(REMBOURSEMENTS_JSON_FILE):
        try:
            with open(REMBOURSEMENTS_JSON_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
        except Exception as e:
            print(f"Erreur inattendue lors du chargement de {REMBOURSEMENTS_JSON_FILE}: {e}")
            return []
    return []


def sauvegarder_toutes_les_demandes_data(remboursements: list):
    try:
        _sauvegarder_fichier_json_atomic(REMBOURSEMENTS_JSON_FILE, remboursements)
    except Exception as e:
        print(
            f"Erreur inattendue lors de la sauvegarde (via _sauvegarder_fichier_json_atomic) de {REMBOURSEMENTS_JSON_FILE}: {e}")


def creer_demande_data(nouvelle_demande_dict: dict) -> dict | None:
    demandes = charger_toutes_les_demandes_data()
    demandes.append(nouvelle_demande_dict)
    sauvegarder_toutes_les_demandes_data(demandes)

    ref_dossier = nouvelle_demande_dict.get("reference_facture_dossier")
    id_unique_demande = nouvelle_demande_dict.get("id_demande")
    if ref_dossier and id_unique_demande:
        dossier_demande_specifique = os.path.join(REMBOURSEMENT_BASE_DIR, ref_dossier)
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
    demandes = charger_toutes_les_demandes_data()
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

    if demande_trouvee_et_maj:
        sauvegarder_toutes_les_demandes_data(demandes)
        return True
    return False


def ajouter_entree_historique_data(id_demande: str, nouvelle_entree: dict) -> bool:
    demandes = charger_toutes_les_demandes_data()
    demande_trouvee = False
    for i, demande in enumerate(demandes):
        if demande.get("id_demande") == id_demande:
            if "historique_statuts" not in demandes[i]:
                demandes[i]["historique_statuts"] = []
            demandes[i]["historique_statuts"].append(nouvelle_entree)
            demande_trouvee = True
            break
    if demande_trouvee:
        sauvegarder_toutes_les_demandes_data(demandes)
        return True
    return False


def supprimer_demande_par_id_data(id_demande_a_supprimer: str) -> tuple[bool, str]:
    demandes = charger_toutes_les_demandes_data()
    demande_a_supprimer_trouvee = None
    nouvelle_liste_demandes = [d for d in demandes if d.get("id_demande") != id_demande_a_supprimer]

    if len(nouvelle_liste_demandes) == len(demandes):
        return False, f"Demande ID {id_demande_a_supprimer} non trouvée."

    demande_a_supprimer_trouvee = next((d for d in demandes if d.get("id_demande") == id_demande_a_supprimer), None)
    sauvegarder_toutes_les_demandes_data(nouvelle_liste_demandes)

    if demande_a_supprimer_trouvee:
        ref_dossier = demande_a_supprimer_trouvee.get("reference_facture_dossier")
        if ref_dossier:
            chemin_dossier_demande = os.path.join(REMBOURSEMENT_BASE_DIR, ref_dossier)
            if os.path.exists(chemin_dossier_demande) and os.path.isdir(chemin_dossier_demande):
                try:
                    shutil.rmtree(chemin_dossier_demande)
                    print(f"Dossier {chemin_dossier_demande} supprimé avec succès.")
                except OSError as e:
                    print(f"Erreur lors de la suppression du dossier {chemin_dossier_demande}: {e}")
                    return True, f"Demande ID {id_demande_a_supprimer} supprimée du JSON, mais échec de la suppression du dossier {ref_dossier}."

    return True, f"Demande ID {id_demande_a_supprimer} supprimée avec succès."