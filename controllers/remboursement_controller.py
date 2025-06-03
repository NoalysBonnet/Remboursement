from models import remboursement_model  #
from utils import pdf_utils  #
from tkinter import filedialog  #
import os
import sys  #
import subprocess  #
import shutil  #
from config.settings import STATUT_CREEE, STATUT_TROP_PERCU_CONSTATE, STATUT_REFUSEE_CONSTAT_TP, STATUT_ANNULEE, \
    STATUT_VALIDEE, STATUT_REFUSEE_VALIDATION_CORRECTION_MLUPO  #


class RemboursementController:
    def __init__(self, utilisateur_actuel: str):  #
        self.utilisateur_actuel = utilisateur_actuel  #

    def extraire_info_facture_pdf(self, chemin_pdf: str) -> dict:  #
        """Appelle l'utilitaire d'extraction PDF."""
        if not chemin_pdf or not os.path.exists(chemin_pdf):  #
            return {"nom": "", "prenom": "", "reference": ""}  #
        return pdf_utils.extraire_infos_facture(chemin_pdf)  #

    def creer_demande_remboursement(
            self,
            nom: str,
            prenom: str,
            reference_facture: str,
            montant_demande_str: str,
            chemin_facture_source: str | None,  #
            chemin_rib_source: str,
            description: str  #
    ) -> tuple[bool, str]:  #
        if not nom:  #
            return False, "Le champ 'Nom' est obligatoire."  #
        if not prenom:  #
            return False, "Le champ 'Prénom' est obligatoire."  #
        if not reference_facture:  #
            return False, "Le champ 'Référence Facture' est obligatoire."  #
        if not montant_demande_str:  #
            return False, "Le champ 'Montant demandé' est obligatoire."  #
        if not description:  #
            return False, "Le champ 'Description/Raison de la demande' est obligatoire."  #
        if not chemin_rib_source:  #
            return False, "La sélection du fichier RIB est obligatoire."  #

        try:  #
            montant_demande = float(montant_demande_str)  #
            if montant_demande <= 0:  #
                return False, "Le montant demandé doit être un nombre positif."  #
        except ValueError:  #
            return False, "Le montant demandé doit être un nombre valide."  #

        if chemin_facture_source and not os.path.exists(chemin_facture_source):  #
            return False, f"Fichier facture non trouvé : {chemin_facture_source}"  #

        if not os.path.exists(chemin_rib_source):  #
            return False, f"Fichier RIB non trouvé : {chemin_rib_source}"  #

        nouvelle_demande = remboursement_model.creer_nouvelle_demande(
            nom=nom,  #
            prenom=prenom,  #
            reference_facture=reference_facture,  #
            montant_demande=montant_demande,  #
            chemin_facture_source=chemin_facture_source,  #
            chemin_rib_source=chemin_rib_source,  #
            utilisateur_createur=self.utilisateur_actuel,  #
            description=description  #
        )

        if nouvelle_demande:  #
            return True, f"Demande {nouvelle_demande['id_demande']} créée avec succès."  #
        else:  #
            return False, "Erreur lors de la création de la demande dans le modèle."  #

    def selectionner_fichier_piece_jointe(self, titre_dialogue="Sélectionner un fichier") -> str | None:  #
        """Ouvre une boîte de dialogue pour sélectionner un fichier (PDF ou Image)."""
        chemin_fichier = filedialog.askopenfilename(
            title=titre_dialogue,  #
            filetypes=(("Tous les fichiers pris en charge", "*.pdf *.png *.jpg *.jpeg *.gif"),  #
                       ("Fichiers PDF", "*.pdf"),
                       ("Images PNG", "*.png"),
                       ("Images JPEG", "*.jpg *.jpeg"),
                       ("Images GIF", "*.gif"),
                       ("Tous les fichiers", "*.*"))
        )
        return chemin_fichier if chemin_fichier else None  #

    def get_toutes_les_demandes_formatees(self) -> list[dict]:  #
        """Récupère toutes les demandes et prépare les chemins des PJ."""  # Suppression de "vérifie les verrous"
        demandes = remboursement_model.obtenir_toutes_les_demandes()  #
        demandes_formatees = []  #
        for demande_data in demandes:  #
            demande_data["chemin_abs_facture"] = remboursement_model.get_chemin_absolu_piece_jointe(
                demande_data.get("chemin_facture_stockee"))  #
            demande_data["chemin_abs_rib"] = remboursement_model.get_chemin_absolu_piece_jointe(
                demande_data.get("chemin_rib_stocke"))  #

            demande_data["chemins_abs_trop_percu"] = []  #
            if demande_data.get("pieces_capture_trop_percu"):  #
                for rel_path in demande_data["pieces_capture_trop_percu"]:  #
                    abs_path = remboursement_model.get_chemin_absolu_piece_jointe(rel_path)  #
                    if abs_path:  #
                        demande_data["chemins_abs_trop_percu"].append(abs_path)  #

            # Plus de champ locked_by à ajouter ici
            # ref_dossier = demande_data.get("reference_facture_dossier")
            # if ref_dossier:
            #     demande_data["locked_by"] = remboursement_model.is_demande_locked(ref_dossier)
            # else:
            #     demande_data["locked_by"] = None

            demandes_formatees.append(demande_data)  #
        return sorted(demandes_formatees, key=lambda d: d.get("date_creation", ""), reverse=True)  #

    def ouvrir_piece_jointe_systeme(self, chemin_absolu_pj: str) -> tuple[bool, str]:  #
        """Tente d'ouvrir la pièce jointe avec l'application par défaut du système."""
        if not chemin_absolu_pj or not os.path.exists(chemin_absolu_pj):  #
            return False, "Fichier non trouvé ou chemin invalide."  #
        try:  #
            if os.name == 'nt':  #
                os.startfile(chemin_absolu_pj)  #
            elif sys.platform == 'darwin':  #
                subprocess.run(['open', chemin_absolu_pj], check=True)  #
            else:  #
                subprocess.run(['xdg-open', chemin_absolu_pj], check=True)  #
            return True, "Ouverture du fichier demandée."  #
        except FileNotFoundError:  #
            return False, "Fichier non trouvé. Vérifiez le chemin."  #
        except subprocess.CalledProcessError as e:  #
            return False, f"Erreur lors de l'ouverture du fichier (commande externe) : {e}"  #
        except Exception as e:  #
            return False, f"Impossible d'ouvrir le fichier : {e}"  #

    def telecharger_copie_piece_jointe(self, chemin_absolu_pj_source: str) -> tuple[bool, str]:  #
        """Demande à l'utilisateur où enregistrer une copie de la PJ."""
        if not chemin_absolu_pj_source or not os.path.exists(chemin_absolu_pj_source):  #
            return False, "Fichier source non trouvé ou chemin invalide."  #

        nom_fichier_original = os.path.basename(chemin_absolu_pj_source)  #
        chemin_destination = filedialog.asksaveasfilename(
            defaultextension=os.path.splitext(nom_fichier_original)[1],  #
            initialfile=nom_fichier_original,  #
            title="Enregistrer la pièce jointe sous...",  #
            filetypes=(("Tous les fichiers pris en charge", "*.pdf *.png *.jpg *.jpeg"), ("Fichiers PDF", "*.pdf"),
                       ("Images", "*.png *.jpg *.jpeg"), ("Tous les fichiers", "*.*"))  #
        )
        if not chemin_destination:  #
            return False, "Téléchargement annulé par l'utilisateur."  #

        try:  #
            shutil.copy2(chemin_absolu_pj_source, chemin_destination)  #
            return True, f"Fichier enregistré avec succès sous {chemin_destination}"  #
        except Exception as e:  #
            return False, f"Erreur lors de l'enregistrement du fichier : {e}"  #

    # Les méthodes tenter_verrouillage_demande et liberer_verrou_demande sont supprimées
    # car le système de verrouillage par fichier .lock est retiré.

    def supprimer_demande(self, id_demande: str) -> tuple[bool, str]:  #
        """Gère la suppression d'une demande de remboursement."""
        return remboursement_model.supprimer_demande_par_id(id_demande)  #

    def mlupo_accepter_constat(  #
            self,
            id_demande: str,
            # ref_dossier: str, # Plus besoin de ref_dossier pour le verrouillage ici
            chemin_pj_trop_percu_source: str,
            commentaire: str
    ) -> tuple[bool, str]:
        if not chemin_pj_trop_percu_source or not os.path.exists(chemin_pj_trop_percu_source):  #
            return False, f"Fichier de preuve de trop-perçu obligatoire et non trouvé : {chemin_pj_trop_percu_source}"  #
        if not commentaire.strip():  #
            return False, "Un commentaire est obligatoire pour cette action."  #

        succes_pj, msg_pj, _ = remboursement_model.ajouter_piece_jointe_trop_percu(
            id_demande, chemin_pj_trop_percu_source, self.utilisateur_actuel
        )  #
        if not succes_pj:  #
            return False, f"Erreur PJ: {msg_pj}"  #

        succes_statut, msg_statut = remboursement_model.accepter_constat_trop_percu(
            id_demande, commentaire, self.utilisateur_actuel
        )  #

        return succes_statut, msg_statut  #

    def mlupo_refuser_constat(self, id_demande: str, commentaire: str) -> tuple[bool, str]:  # ref_dossier supprimé
        """m.lupo refuse le constat, ajoute commentaire, demande retourne à p.neri."""
        if not commentaire.strip():  #
            return False, "Un commentaire est obligatoire pour justifier le refus."  #

        succes, message = remboursement_model.refuser_constat_trop_percu(
            id_demande, commentaire, self.utilisateur_actuel
        )  #
        return succes, message  #

    def pneri_annuler_demande(self, id_demande: str, commentaire: str) -> tuple[bool, str]:  # ref_dossier supprimé
        """p.neri annule une demande (typiquement après un refus de m.lupo)."""
        if not commentaire.strip():  #
            return False, "Un commentaire est requis pour l'annulation."  #

        succes, message = remboursement_model.annuler_demande(
            id_demande, commentaire, self.utilisateur_actuel
        )  #
        return succes, message  #

    def jdurousset_valider_demande(self, id_demande: str, commentaire: str | None) -> tuple[
        bool, str]:  # ref_dossier supprimé
        """j.durousset valide la demande."""
        succes, message = remboursement_model.valider_demande_par_validateur(
            id_demande, commentaire, self.utilisateur_actuel
        )  #
        return succes, message  #

    def jdurousset_refuser_demande(self, id_demande: str, commentaire: str) -> tuple[bool, str]:  # ref_dossier supprimé
        """j.durousset refuse la demande, la renvoyant à m.lupo."""
        if not commentaire.strip():  #
            return False, "Un commentaire est obligatoire pour justifier le refus."  #

        succes, message = remboursement_model.refuser_demande_par_validateur(
            id_demande, commentaire, self.utilisateur_actuel
        )  #
        return succes, message  #