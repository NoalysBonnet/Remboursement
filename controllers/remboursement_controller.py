from models import remboursement_model
from utils import pdf_utils, archive_utils
from tkinter import filedialog
import os
import sys
import shutil
import datetime

from config.settings import (
    STATUT_CREEE, STATUT_TROP_PERCU_CONSTATE,
    STATUT_REFUSEE_CONSTAT_TP, STATUT_ANNULEE,
    STATUT_VALIDEE, STATUT_REFUSEE_VALIDATION_CORRECTION_MLUPO,
    STATUT_PAIEMENT_EFFECTUE
)


class RemboursementController:
    def __init__(self, utilisateur_actuel: str):
        self.utilisateur_actuel = utilisateur_actuel

    def archive_old_requests(self):
        """Lance la tâche système d'archivage des anciennes demandes."""
        count = remboursement_model.archiver_les_vieilles_demandes()
        if count > 0:
            print(f"{count} demande(s) ont été archivée(s).")

    def extraire_info_facture_pdf(self, chemin_pdf: str) -> dict:
        if not chemin_pdf or not os.path.exists(chemin_pdf):
            return {"nom": "", "prenom": "", "reference": ""}
        return pdf_utils.extraire_infos_facture(chemin_pdf)

    def _valider_donnees_demande(self, nom: str, prenom: str, reference_facture: str, montant_demande_str: str,
                                 description: str, chemin_facture_source: str | None, chemin_rib_source: str
                                 ) -> tuple[bool, str, float | None]:
        """Effectue la validation synchrone des données du formulaire."""
        if not all([nom, prenom, reference_facture, montant_demande_str, description]):
            return False, "Tous les champs de texte sont obligatoires.", None
        if not chemin_rib_source:
            return False, "La sélection du fichier RIB est obligatoire.", None

        try:
            montant_demande = float(montant_demande_str.replace(",", "."))
            if montant_demande <= 0:
                return False, "Le montant demandé doit être un nombre positif.", None
        except ValueError:
            return False, "Le montant demandé doit être un nombre valide.", None

        if chemin_facture_source and not os.path.exists(chemin_facture_source):
            return False, f"Fichier facture non trouvé : {chemin_facture_source}", None
        if not os.path.exists(chemin_rib_source):
            return False, f"Fichier RIB non trouvé : {chemin_rib_source}", None

        return True, "", montant_demande

    def creer_demande_remboursement(
            self, nom: str, prenom: str, reference_facture: str, montant_demande: float,
            description: str, chemin_facture_source: str | None, chemin_rib_source: str
    ) -> tuple[bool, str]:
        """Crée la demande après validation (partie asynchrone)."""
        nouvelle_demande = remboursement_model.creer_nouvelle_demande(
            nom, prenom, reference_facture, montant_demande,
            chemin_facture_source, chemin_rib_source, self.utilisateur_actuel, description
        )
        if nouvelle_demande:
            return True, f"Demande pour {prenom.title()} {nom.upper()} créée."
        else:
            return False, "Erreur lors de la création de la demande."

    def get_demande_by_id(self, demande_id: str) -> dict | None:
        return remboursement_model.obtenir_demande_par_id(demande_id)

    def get_toutes_les_demandes_formatees(self, include_archives: bool = False) -> list[dict]:
        return remboursement_model.obtenir_toutes_les_demandes(include_archives)

    def selectionner_fichier_document_ou_image(self, titre_dialogue="Sélectionner un fichier"):
        filetypes = (("Tous les fichiers", "*.*"), ("Documents PDF", "*.pdf"), ("Images", "*.png *.jpg *.jpeg"))
        return filedialog.askopenfilename(title=titre_dialogue, filetypes=filetypes)

    def supprimer_demande(self, id_demande: str) -> tuple[bool, str]:
        return remboursement_model.supprimer_demande_par_id(id_demande)

    def admin_purge_archives(self, age_en_annees: int) -> tuple[int, list[str]]:
        return remboursement_model.admin_supprimer_archives_anciennes(age_en_annees)

    def admin_manual_archive(self, demande_id: str) -> tuple[bool, str]:
        return remboursement_model.archiver_demande_par_id(demande_id)

    def get_viewable_attachment_path(self, demande_id: str, rel_path: str) -> tuple[str | None, str | None]:
        demande_data = self.get_demande_by_id(demande_id)
        if not demande_data: return None, None
        is_archived = demande_data.get('is_archived', False)
        if not is_archived:
            return remboursement_model.get_chemin_absolu_piece_jointe(rel_path, is_archived=False), None
        else:
            ref_dossier = demande_data.get("reference_facture_dossier")
            if not ref_dossier: return None, None
            zip_archive_path = remboursement_model.get_chemin_absolu_pj_archive_zip(ref_dossier)
            file_inside_zip = os.path.basename(rel_path)
            return archive_utils.extract_file_to_temp(zip_archive_path, file_inside_zip)

    def telecharger_copie_piece_jointe(self, chemin_absolu_pj_source: str, temp_dir_to_clean: str | None) -> tuple[
        bool, str]:
        if not chemin_absolu_pj_source or not os.path.exists(chemin_absolu_pj_source):
            if temp_dir_to_clean: archive_utils.cleanup_temp_dir(temp_dir_to_clean)
            return False, "Fichier source non trouvé ou chemin invalide."

        nom_fichier_original = os.path.basename(chemin_absolu_pj_source)
        ext = nom_fichier_original.rsplit('.', 1)[1] if '.' in nom_fichier_original else ""
        filetypes = ((f"Fichier .{ext.upper()}", f"*.{ext.lower()}"), ("Tous les fichiers", "*.*"))

        chemin_destination = filedialog.asksaveasfilename(
            defaultextension=f".{ext}", initialfile=nom_fichier_original,
            title="Enregistrer la pièce jointe sous...", filetypes=filetypes
        )
        if not chemin_destination:
            if temp_dir_to_clean: archive_utils.cleanup_temp_dir(temp_dir_to_clean)
            return False, "Téléchargement annulé par l'utilisateur."
        try:
            shutil.copy2(chemin_absolu_pj_source, chemin_destination)
            return True, f"Fichier enregistré avec succès."
        except Exception as e:
            return False, f"Erreur lors de l'enregistrement du fichier : {e}"
        finally:
            if temp_dir_to_clean: archive_utils.cleanup_temp_dir(temp_dir_to_clean)

    def mlupo_accepter_constat(self, id_demande: str, chemin_pj_trop_percu_source: str, commentaire: str) -> tuple[
        bool, str]:
        succes_pj, msg_pj, _ = remboursement_model.ajouter_piece_jointe_trop_percu(
            id_demande, chemin_pj_trop_percu_source, self.utilisateur_actuel
        )
        if not succes_pj:
            return False, f"Erreur lors de l'ajout de la pièce jointe : {msg_pj}"

        succes_statut, msg_statut = remboursement_model.accepter_constat_trop_percu(
            id_demande, commentaire, self.utilisateur_actuel
        )

        return (succes_statut, msg_statut)

    def mlupo_refuser_constat(self, id_demande: str, commentaire: str) -> tuple[bool, str]:
        return remboursement_model.refuser_constat_trop_percu(id_demande, commentaire, self.utilisateur_actuel)

    def pneri_annuler_demande(self, id_demande: str, commentaire: str) -> tuple[bool, str]:
        return remboursement_model.annuler_demande(id_demande, commentaire, self.utilisateur_actuel)

    def jdurousset_valider_demande(self, id_demande: str, commentaire: str | None) -> tuple[bool, str]:
        return remboursement_model.valider_demande_par_validateur(id_demande, commentaire, self.utilisateur_actuel)

    def jdurousset_refuser_demande(self, id_demande: str, commentaire: str) -> tuple[bool, str]:
        return remboursement_model.refuser_demande_par_validateur(id_demande, commentaire, self.utilisateur_actuel)

    def pdiop_confirmer_paiement_effectue(self, id_demande: str, commentaire: str | None) -> tuple[bool, str]:
        return remboursement_model.confirmer_paiement_effectue(id_demande, self.utilisateur_actuel, commentaire)

    def pneri_resoumettre_demande_corrigee(self, id_demande: str, commentaire: str, nouveau_chemin_facture: str | None,
                                           nouveau_chemin_rib: str | None) -> tuple[bool, str]:
        return remboursement_model.pneri_resoumettre_demande_corrigee(id_demande, commentaire, nouveau_chemin_facture,
                                                                      nouveau_chemin_rib, self.utilisateur_actuel)

    def mlupo_resoumettre_constat_corrige(self, id_demande: str, commentaire: str,
                                          nouveau_chemin_pj_trop_percu: str | None) -> tuple[bool, str]:
        return remboursement_model.mlupo_resoumettre_constat_corrige(id_demande, commentaire,
                                                                     nouveau_chemin_pj_trop_percu,
                                                                     self.utilisateur_actuel)

    def mlupo_refuser_correction(self, id_demande: str, commentaire: str) -> tuple[bool, str]:
        return remboursement_model.mlupo_refuser_correction(id_demande, commentaire, self.utilisateur_actuel)