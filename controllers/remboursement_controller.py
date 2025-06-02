from models import remboursement_model  #
from utils import pdf_utils  #
from tkinter import filedialog  #
import os
import sys  #
import subprocess  #
import shutil  #


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
            chemin_facture_source: str | None,  # Facture optionnelle
            chemin_rib_source: str,
            description: str  # Nouveau champ
    ) -> tuple[bool, str]:  #
        """
        Valide les données et crée une nouvelle demande de remboursement.
        Retourne (succès, message_ou_id_demande).
        """  #
        # Champs obligatoires
        if not nom:  #
            return False, "Le champ 'Nom' est obligatoire."  #
        if not prenom:  #
            return False, "Le champ 'Prénom' est obligatoire."  #
        if not reference_facture:  #
            return False, "Le champ 'Référence Facture' est obligatoire."  #
        if not montant_demande_str:  #
            return False, "Le champ 'Montant demandé' est obligatoire."  #
        if not description:
            return False, "Le champ 'Description/Raison de la demande' est obligatoire."
        if not chemin_rib_source:  #
            return False, "La sélection du fichier RIB est obligatoire."  #

        try:  #
            montant_demande = float(montant_demande_str)  #
            if montant_demande <= 0:  #
                return False, "Le montant demandé doit être un nombre positif."  #
        except ValueError:  #
            return False, "Le montant demandé doit être un nombre valide."  #

        # Vérification de l'existence des fichiers si les chemins sont fournis
        if chemin_facture_source and not os.path.exists(chemin_facture_source):  #
            return False, f"Fichier facture non trouvé : {chemin_facture_source}"  #

        if not os.path.exists(chemin_rib_source):  # # chemin_rib_source est vérifié non-vide plus haut
            return False, f"Fichier RIB non trouvé : {chemin_rib_source}"  #

        nouvelle_demande = remboursement_model.creer_nouvelle_demande(
            nom=nom,  #
            prenom=prenom,  #
            reference_facture=reference_facture,  #
            montant_demande=montant_demande,  #
            chemin_facture_source=chemin_facture_source,  #
            chemin_rib_source=chemin_rib_source,  #
            utilisateur_createur=self.utilisateur_actuel,  #
            description=description  # Nouveau champ
        )

        if nouvelle_demande:  #
            return True, f"Demande {nouvelle_demande['id_demande']} créée avec succès."  #
        else:  #
            return False, "Erreur lors de la création de la demande dans le modèle."  #

    def selectionner_fichier_pdf(self, titre_dialogue="Sélectionner un fichier PDF") -> str | None:  #
        """Ouvre une boîte de dialogue pour sélectionner un fichier PDF."""
        chemin_fichier = filedialog.askopenfilename(
            title=titre_dialogue,  #
            filetypes=(("Fichiers PDF", "*.pdf"), ("Tous les fichiers", "*.*"))  #
        )
        return chemin_fichier if chemin_fichier else None  #

    def get_toutes_les_demandes_formatees(self) -> list[dict]:  #
        """Récupère toutes les demandes et prépare les chemins des PJ pour la vue."""
        demandes = remboursement_model.obtenir_toutes_les_demandes()  #
        demandes_formatees = []  #
        for demande_data in demandes:  #
            demande_data["chemin_abs_facture"] = remboursement_model.get_chemin_absolu_piece_jointe(
                demande_data.get("chemin_facture_stockee"))  #
            demande_data["chemin_abs_rib"] = remboursement_model.get_chemin_absolu_piece_jointe(
                demande_data.get("chemin_rib_stocke"))  #
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
            filetypes=(("Fichiers PDF", "*.pdf"), ("Tous les fichiers", "*.*"))  #
        )
        if not chemin_destination:  #
            return False, "Téléchargement annulé par l'utilisateur."  #

        try:  #
            shutil.copy2(chemin_absolu_pj_source, chemin_destination)  #
            return True, f"Fichier enregistré avec succès sous {chemin_destination}"  #
        except Exception as e:  #
            return False, f"Erreur lors de l'enregistrement du fichier : {e}"  #