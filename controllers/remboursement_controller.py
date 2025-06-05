from models import remboursement_model
from utils import pdf_utils
from tkinter import filedialog
import os
import sys
import subprocess
import shutil
from config.settings import STATUT_CREEE, STATUT_TROP_PERCU_CONSTATE, STATUT_REFUSEE_CONSTAT_TP, STATUT_ANNULEE, \
    STATUT_VALIDEE, STATUT_REFUSEE_VALIDATION_CORRECTION_MLUPO, STATUT_PAIEMENT_EFFECTUE


class RemboursementController:
    def __init__(self, utilisateur_actuel: str):
        self.utilisateur_actuel = utilisateur_actuel

    def extraire_info_facture_pdf(self, chemin_pdf: str) -> dict:
        if not chemin_pdf or not os.path.exists(chemin_pdf):
            return {"nom": "", "prenom": "", "reference": ""}
        return pdf_utils.extraire_infos_facture(chemin_pdf)

    def creer_demande_remboursement(
            self,
            nom: str,
            prenom: str,
            reference_facture: str,
            montant_demande_str: str,
            chemin_facture_source: str | None,
            chemin_rib_source: str,
            description: str
    ) -> tuple[bool, str]:
        if not nom:
            return False, "Le champ 'Nom' est obligatoire."
        if not prenom:
            return False, "Le champ 'Prénom' est obligatoire."
        if not reference_facture:
            return False, "Le champ 'Référence Facture' est obligatoire."
        if not montant_demande_str:
            return False, "Le champ 'Montant demandé' est obligatoire."
        if not description:
            return False, "Le champ 'Description/Raison de la demande' est obligatoire."
        if not chemin_rib_source:
            return False, "La sélection du fichier RIB est obligatoire."

        try:
            montant_demande = float(montant_demande_str)
            if montant_demande <= 0:
                return False, "Le montant demandé doit être un nombre positif."
        except ValueError:
            return False, "Le montant demandé doit être un nombre valide."

        if chemin_facture_source and not os.path.exists(chemin_facture_source):
            return False, f"Fichier facture non trouvé : {chemin_facture_source}"

        if not os.path.exists(chemin_rib_source):
            return False, f"Fichier RIB non trouvé : {chemin_rib_source}"

        nouvelle_demande = remboursement_model.creer_nouvelle_demande(
            nom=nom,
            prenom=prenom,
            reference_facture=reference_facture,
            montant_demande=montant_demande,
            chemin_facture_source=chemin_facture_source,
            chemin_rib_source=chemin_rib_source,
            utilisateur_createur=self.utilisateur_actuel,
            description=description
        )

        if nouvelle_demande:
            return True, f"Demande {nouvelle_demande['id_demande']} créée avec succès."
        else:
            return False, "Erreur lors de la création de la demande dans le modèle."

    def selectionner_fichier_document_ou_image(self, titre_dialogue="Sélectionner un fichier") -> str | None:
        filetypes = (
            ("Tous les fichiers supportés", "*.pdf *.png *.jpg *.jpeg *.gif *.bmp *.docx *.odt *.txt"),
            ("Documents PDF", "*.pdf"),
            ("Images", "*.png *.jpg *.jpeg *.gif *.bmp"),
            ("Documents Word", "*.docx"),
            ("Documents OpenOffice Text", "*.odt"),
            ("Fichiers Texte", "*.txt"),
            ("Tous les fichiers", "*.*")
        )
        chemin_fichier = filedialog.askopenfilename(
            title=titre_dialogue,
            filetypes=filetypes
        )
        return chemin_fichier if chemin_fichier else None

    def get_toutes_les_demandes_formatees(self) -> list[dict]:
        demandes = remboursement_model.obtenir_toutes_les_demandes()
        demandes_formatees = []
        for demande_data in demandes:
            # Gestion pour 'chemins_factures_stockees' (qui est une liste)
            abs_factures = []
            chemins_factures_rel = demande_data.get("chemins_factures_stockees", [])
            if isinstance(chemins_factures_rel, list):
                for rel_path in chemins_factures_rel:
                    abs_path = remboursement_model.get_chemin_absolu_piece_jointe(rel_path)
                    if abs_path: abs_factures.append(abs_path)
            elif isinstance(chemins_factures_rel, str):  # Rétrocompatibilité si c'était une chaîne
                abs_path = remboursement_model.get_chemin_absolu_piece_jointe(chemins_factures_rel)
                if abs_path: abs_factures.append(abs_path)
            demande_data["chemins_abs_factures_stockees"] = abs_factures

            # Gestion pour 'chemins_rib_stockes' (qui est une liste)
            abs_ribs = []
            chemins_rib_rel = demande_data.get("chemins_rib_stockes", [])
            if isinstance(chemins_rib_rel, list):
                for rel_path in chemins_rib_rel:
                    abs_path = remboursement_model.get_chemin_absolu_piece_jointe(rel_path)
                    if abs_path: abs_ribs.append(abs_path)
            elif isinstance(chemins_rib_rel, str):  # Rétrocompatibilité
                abs_path = remboursement_model.get_chemin_absolu_piece_jointe(chemins_rib_rel)
                if abs_path: abs_ribs.append(abs_path)
            demande_data["chemins_abs_rib_stockes"] = abs_ribs

            demande_data["chemins_abs_trop_percu"] = []
            if demande_data.get("pieces_capture_trop_percu"):
                for rel_path in demande_data["pieces_capture_trop_percu"]:
                    abs_path = remboursement_model.get_chemin_absolu_piece_jointe(rel_path)
                    if abs_path:
                        demande_data["chemins_abs_trop_percu"].append(abs_path)

            demandes_formatees.append(demande_data)
        return sorted(demandes_formatees, key=lambda d: d.get("date_creation", ""), reverse=True)

    def telecharger_copie_piece_jointe(self, chemin_absolu_pj_source: str) -> tuple[bool, str]:
        if not chemin_absolu_pj_source or not os.path.exists(chemin_absolu_pj_source):
            return False, "Fichier source non trouvé ou chemin invalide."

        nom_fichier_original = os.path.basename(chemin_absolu_pj_source)
        filetypes_save = (("Tous les fichiers", "*.*"),)
        if '.' in nom_fichier_original:
            ext = nom_fichier_original.rsplit('.', 1)[1]
            filetypes_save = ((f"Fichier .{ext.upper()}", f"*.{ext.lower()}"), ("Tous les fichiers", "*.*"))

        chemin_destination = filedialog.asksaveasfilename(
            defaultextension=os.path.splitext(nom_fichier_original)[1],
            initialfile=nom_fichier_original,
            title="Enregistrer la pièce jointe sous...",
            filetypes=filetypes_save
        )
        if not chemin_destination:
            return False, "Téléchargement annulé par l'utilisateur."

        try:
            shutil.copy2(chemin_absolu_pj_source, chemin_destination)
            return True, f"Fichier enregistré avec succès sous {chemin_destination}"
        except Exception as e:
            return False, f"Erreur lors de l'enregistrement du fichier : {e}"

    def supprimer_demande(self, id_demande: str) -> tuple[bool, str]:
        return remboursement_model.supprimer_demande_par_id(id_demande)

    def mlupo_accepter_constat(
            self,
            id_demande: str,
            chemin_pj_trop_percu_source: str,
            commentaire: str
    ) -> tuple[bool, str]:
        if not chemin_pj_trop_percu_source or not os.path.exists(chemin_pj_trop_percu_source):
            return False, f"Fichier de preuve de trop-perçu obligatoire et non trouvé : {chemin_pj_trop_percu_source}"
        if not commentaire.strip():
            return False, "Un commentaire est obligatoire pour cette action."

        # 1. Ajouter d'abord la PJ
        succes_pj, msg_pj, _ = remboursement_model.ajouter_piece_jointe_trop_percu(
            id_demande, chemin_pj_trop_percu_source, self.utilisateur_actuel
        )
        if not succes_pj:
            return False, f"Erreur lors de l'ajout de la PJ : {msg_pj}"

        # 2. Puis mettre à jour le statut et le commentaire
        succes_statut, msg_statut = remboursement_model.accepter_constat_trop_percu(
            id_demande, commentaire, self.utilisateur_actuel
        )

        if succes_statut:
            return True, msg_statut
        else:
            # Si le statut n'a pas pu être mis à jour, il faudrait idéalement une transaction ou une annulation de l'ajout de PJ.
            # Pour l'instant, on retourne l'erreur de statut.
            return False, f"PJ ajoutée, mais erreur de mise à jour du statut : {msg_statut}"

    def mlupo_refuser_constat(self, id_demande: str, commentaire: str) -> tuple[bool, str]:
        if not commentaire.strip():
            return False, "Un commentaire est obligatoire pour justifier le refus."
        return remboursement_model.refuser_constat_trop_percu(
            id_demande, commentaire, self.utilisateur_actuel
        )

    def pneri_annuler_demande(self, id_demande: str, commentaire: str) -> tuple[bool, str]:
        if not commentaire.strip():
            return False, "Un commentaire est requis pour l'annulation."
        return remboursement_model.annuler_demande(
            id_demande, commentaire, self.utilisateur_actuel
        )

    def jdurousset_valider_demande(self, id_demande: str, commentaire: str | None) -> tuple[bool, str]:
        return remboursement_model.valider_demande_par_validateur(
            id_demande, commentaire, self.utilisateur_actuel
        )

    def jdurousset_refuser_demande(self, id_demande: str, commentaire: str) -> tuple[bool, str]:
        if not commentaire.strip():
            return False, "Un commentaire est obligatoire pour justifier le refus."
        return remboursement_model.refuser_demande_par_validateur(
            id_demande, commentaire, self.utilisateur_actuel
        )

    def pdiop_confirmer_paiement_effectue(self, id_demande: str, commentaire: str | None) -> tuple[bool, str]:
        return remboursement_model.confirmer_paiement_effectue(
            id_demande, self.utilisateur_actuel, commentaire
        )

    def pneri_resoumettre_demande_corrigee(self, id_demande: str, commentaire: str,
                                           nouveau_chemin_facture: str | None,
                                           nouveau_chemin_rib: str) -> tuple[bool, str]:
        if not nouveau_chemin_rib or not os.path.exists(nouveau_chemin_rib):
            return False, "Un nouveau RIB valide est obligatoire pour la resoumission."
        if nouveau_chemin_facture and not os.path.exists(nouveau_chemin_facture):
            return False, f"Nouveau fichier facture non trouvé: {nouveau_chemin_facture}"
        if not commentaire.strip():
            return False, "Un commentaire expliquant la correction est obligatoire."

        return remboursement_model.pneri_resoumettre_demande_corrigee(
            id_demande, commentaire,
            nouveau_chemin_facture, nouveau_chemin_rib,
            self.utilisateur_actuel
        )

    def mlupo_resoumettre_constat_corrige(self, id_demande: str, commentaire: str,
                                          nouveau_chemin_pj_trop_percu: str) -> tuple[bool, str]:
        if not nouveau_chemin_pj_trop_percu or not os.path.exists(nouveau_chemin_pj_trop_percu):
            return False, "Une nouvelle preuve de trop-perçu valide est obligatoire."
        if not commentaire.strip():
            return False, "Un commentaire expliquant la correction est obligatoire."

        return remboursement_model.mlupo_resoumettre_constat_corrige(
            id_demande, commentaire,
            nouveau_chemin_pj_trop_percu,
            self.utilisateur_actuel
        )