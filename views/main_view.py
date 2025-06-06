# views/main_view.py
import os
import customtkinter as ctk
from tkinter import messagebox, simpledialog
import datetime
import traceback
from config.settings import (
    REMBOURSEMENTS_JSON_FILE, STATUT_CREEE,
    STATUT_REFUSEE_CONSTAT_TP, STATUT_ANNULEE,
    STATUT_PAIEMENT_EFFECTUE, STATUT_TROP_PERCU_CONSTATE,
    STATUT_VALIDEE, STATUT_REFUSEE_VALIDATION_CORRECTION_MLUPO
)
from models import user_model
from views.document_viewer import DocumentViewerWindow
from views.remboursement_item_view import RemboursementItemView
from views.document_history_viewer import DocumentHistoryViewer
from views.admin_user_management_view import AdminUserManagementView
from views.help_view import HelpView

POLLING_INTERVAL_MS = 5000

COULEUR_ACTIVE_POUR_UTILISATEUR = "#1E4D2B"
COULEUR_DEMANDE_TERMINEE = "#2E4374"
COULEUR_DEMANDE_ANNULEE = "#6A040F"
COULEUR_BORDURE_ACTIVE = "#38761D"
COULEUR_BORDURE_TERMINEE = "#4A55A2"
COULEUR_BORDURE_ANNULEE = "#9D0208"


class MainView(ctk.CTkFrame):
    def __init__(self, master, nom_utilisateur, on_logout_callback, remboursement_controller_factory,
                 auth_controller_instance):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.master = master
        self.nom_utilisateur = nom_utilisateur
        self.on_logout = on_logout_callback
        self.remboursement_controller = remboursement_controller_factory(self.nom_utilisateur)
        self.auth_controller = auth_controller_instance

        self.all_demandes_cache = []
        self._last_known_remboursements_mtime = 0
        self._polling_job_id = None
        self.user_roles = []
        self.no_demandes_label_widget = None

        try:
            self._fetch_user_roles()

            self.pack(fill="both", expand=True)
            self.main_content_frame = ctk.CTkFrame(self, corner_radius=10)
            self.main_content_frame.pack(pady=20, padx=20, fill="both", expand=True)

            self.creer_widgets_barre_superieure_et_titre()
            self.creer_section_actions_et_rafraichissement()
            self._creer_barre_recherche()
            self.creer_conteneur_liste_demandes()
            self.creer_legende_couleurs()

            self.afficher_liste_demandes(force_reload=True)
            self.start_polling()
        except Exception as e:
            print(f"ERREUR CRITIQUE DANS MainView.__init__: {e}")
            traceback.print_exc()
            ctk.CTkLabel(master if master else self,
                         text=f"Erreur critique à l'initialisation:\n{e}\nConsultez la console.", font=("Arial", 16),
                         text_color="red").pack(expand=True, padx=20, pady=20)

    def _fetch_user_roles(self):
        user_info = user_model.obtenir_info_utilisateur(self.nom_utilisateur)
        if user_info:
            self.user_roles = user_info.get("roles", [])
        else:
            self.user_roles = []

    def est_admin(self) -> bool:
        return "admin" in self.user_roles

    def peut_creer_demande(self) -> bool:
        return "demandeur" in self.user_roles

    def est_comptable_tresorerie(self) -> bool:
        return "comptable_tresorerie" in self.user_roles

    def est_validateur_chef(self) -> bool:
        return "validateur_chef" in self.user_roles

    def est_comptable_fournisseur(self) -> bool:
        return "comptable_fournisseur" in self.user_roles

    def creer_widgets_barre_superieure_et_titre(self):
        top_bar = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        top_bar.pack(fill="x", padx=10, pady=(10, 5), anchor="n")

        roles_str = f" (Rôles: {', '.join(self.user_roles)})" if self.user_roles else ""
        label_accueil = ctk.CTkLabel(top_bar,
                                     text=f"Utilisateur connecté : {self.nom_utilisateur}{roles_str}",
                                     font=ctk.CTkFont(size=12))
        label_accueil.pack(side="left", padx=5)

        bouton_aide = ctk.CTkButton(top_bar, text="Aide", command=self._ouvrir_fenetre_aide, width=70)
        bouton_aide.pack(side="right", padx=(0, 5))

        bouton_deconnexion = ctk.CTkButton(top_bar, text="Déconnexion", command=self.on_logout, width=120)
        bouton_deconnexion.pack(side="right", padx=5)

        label_titre_principal = ctk.CTkLabel(self.main_content_frame, text="Tableau de Bord - Remboursements",
                                             font=ctk.CTkFont(size=24, weight="bold"))
        label_titre_principal.pack(pady=(10, 10), anchor="n")

    def creer_section_actions_et_rafraichissement(self):
        actions_bar_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        actions_bar_frame.pack(pady=(0, 5), padx=10, fill="x", anchor="n")

        if self.peut_creer_demande():
            bouton_nouvelle_demande = ctk.CTkButton(actions_bar_frame, text="Nouvelle Demande",
                                                    command=self._ouvrir_fenetre_creation_demande)
            bouton_nouvelle_demande.pack(side="left", pady=5, padx=(0, 10))

        bouton_rafraichir = ctk.CTkButton(actions_bar_frame, text="Rafraîchir Liste",
                                          command=lambda: self.afficher_liste_demandes(force_reload=True), width=150)
        bouton_rafraichir.pack(side="left", pady=5, padx=10)

        if self.est_admin():
            btn_admin_users = ctk.CTkButton(actions_bar_frame, text="Gérer Utilisateurs",
                                            command=self._ouvrir_fenetre_gestion_utilisateurs,
                                            fg_color="#555555", hover_color="#444444")
            btn_admin_users.pack(side="left", pady=5, padx=10)

    def _ouvrir_fenetre_gestion_utilisateurs(self):
        if self.auth_controller:
            AdminUserManagementView(self, self.auth_controller)
        else:
            messagebox.showerror("Erreur", "Le contrôleur d'authentification n'est pas initialisé.", parent=self)

    def _ouvrir_fenetre_aide(self):
        HelpView(self, self.nom_utilisateur, self.user_roles)

    def _creer_barre_recherche(self):
        search_bar_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        search_bar_frame.pack(fill="x", padx=10, pady=(5, 5))

        search_label = ctk.CTkLabel(search_bar_frame, text="Rechercher (Nom, Prénom, Réf.):",
                                    font=ctk.CTkFont(size=12))
        search_label.pack(side="left", padx=(0, 5))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)
        self.search_entry = ctk.CTkEntry(search_bar_frame, textvariable=self.search_var, width=300)
        self.search_entry.pack(side="left", padx=(0, 5), fill="x", expand=True)

        clear_button = ctk.CTkButton(search_bar_frame, text="X", width=30, command=self._clear_search)
        clear_button.pack(side="left", padx=(5, 0))

    def _clear_search(self, event=None):
        self.search_var.set("")

    def _on_search_change(self, *args):
        self.afficher_liste_demandes(force_reload=False)

    def creer_conteneur_liste_demandes(self):
        self.scrollable_frame_demandes = ctk.CTkScrollableFrame(self.main_content_frame,
                                                                label_text="Liste des Demandes de Remboursement")
        self.scrollable_frame_demandes.pack(pady=(5, 5), padx=10, expand=True, fill="both")
        self.scrollable_frame_demandes.grid_columnconfigure(0, weight=1)

    def creer_legende_couleurs(self):
        legende_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        legende_frame.pack(fill="x", padx=10, pady=(5, 10), anchor="s")

        ctk.CTkLabel(legende_frame, text="Légende:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 10))

        legend_items = [
            ("Action Requise par Vous", COULEUR_ACTIVE_POUR_UTILISATEUR),
            ("Demande Terminée", COULEUR_DEMANDE_TERMINEE),
            ("Demande Annulée", COULEUR_DEMANDE_ANNULEE),
        ]
        for texte, couleur_fond in legend_items:
            item_legende = ctk.CTkFrame(legende_frame, fg_color="transparent")
            item_legende.pack(side="left", padx=5)
            ctk.CTkFrame(item_legende, width=15, height=15, fg_color=couleur_fond, border_width=1).pack(side="left")
            ctk.CTkLabel(item_legende, text=texte, font=ctk.CTkFont(size=11)).pack(side="left", padx=3)

    def _check_for_data_updates(self):
        try:
            current_mtime = 0
            if os.path.exists(REMBOURSEMENTS_JSON_FILE):
                current_mtime = os.path.getmtime(REMBOURSEMENTS_JSON_FILE)

            if current_mtime != self._last_known_remboursements_mtime:
                print(f"{datetime.datetime.now()}: Détection de modifications externes, rafraîchissement forcé...")
                self._last_known_remboursements_mtime = current_mtime
                self.afficher_liste_demandes(force_reload=True)
        except Exception as e:
            print(f"Erreur lors du polling des données: {e}")
        finally:
            if self.winfo_exists():
                self._polling_job_id = self.after(POLLING_INTERVAL_MS, self._check_for_data_updates)

    def start_polling(self):
        self.stop_polling()
        self._last_known_remboursements_mtime = 0  # Force check on first run
        self._check_for_data_updates()

    def stop_polling(self):
        if self._polling_job_id:
            self.after_cancel(self._polling_job_id)
            self._polling_job_id = None

    def afficher_liste_demandes(self, force_reload: bool = False):
        if force_reload:
            self._fetch_user_roles()
            self.all_demandes_cache = self.remboursement_controller.get_toutes_les_demandes_formatees()
            if os.path.exists(REMBOURSEMENTS_JSON_FILE):
                self._last_known_remboursements_mtime = os.path.getmtime(REMBOURSEMENTS_JSON_FILE)

        for widget in self.scrollable_frame_demandes.winfo_children():
            widget.destroy()

        terme_recherche = self.search_var.get().lower().strip() if hasattr(self, 'search_var') else ""
        demandes_a_afficher_data = []

        if not terme_recherche:
            demandes_a_afficher_data = self.all_demandes_cache
        else:
            for d_data in self.all_demandes_cache:
                if (terme_recherche in d_data.get('nom', '').lower() or
                        terme_recherche in d_data.get('prenom', '').lower() or
                        terme_recherche in d_data.get('reference_facture', '').lower()):
                    demandes_a_afficher_data.append(d_data)

        if self.no_demandes_label_widget:
            self.no_demandes_label_widget.destroy()
            self.no_demandes_label_widget = None

        if not demandes_a_afficher_data:
            message_texte = "Aucune demande de remboursement à afficher."
            if terme_recherche:
                message_texte = f"Aucune demande ne correspond à '{terme_recherche}'."
            self.no_demandes_label_widget = ctk.CTkLabel(self.scrollable_frame_demandes,
                                                         text=message_texte,
                                                         font=ctk.CTkFont(size=14))
            self.no_demandes_label_widget.pack(pady=20, padx=20)
        else:
            callbacks = {
                'voir_pj': self._action_voir_pj,
                'dl_pj': self._action_telecharger_pj,
                'mlupo_accepter': self._action_mlupo_accepter,
                'mlupo_refuser': self._action_mlupo_refuser,
                'jdurousset_valider': self._action_jdurousset_valider,
                'jdurousset_refuser': self._action_jdurousset_refuser,
                'pdiop_confirmer_paiement': self._action_pdiop_confirmer_paiement,
                'pneri_annuler': self._action_pneri_annuler,
                'pneri_resoumettre': self._action_pneri_resoumettre,
                'mlupo_resoumettre_constat': self._action_mlupo_resoumettre_constat,
                'supprimer_demande': self._action_supprimer_demande,
                'voir_historique_docs': self._action_voir_historique_docs
            }
            for demande_data in demandes_a_afficher_data:
                item_frame = RemboursementItemView(
                    master=self.scrollable_frame_demandes,
                    demande_data=demande_data,
                    current_user_name=self.nom_utilisateur,
                    user_roles=self.user_roles,
                    callbacks=callbacks
                )
                item_frame.pack(fill="x", pady=4, padx=5)

    def _action_voir_historique_docs(self, demande_data: dict):
        if not demande_data:
            messagebox.showwarning("Avertissement", "Données de la demande non disponibles pour voir l'historique.", parent=self)
            return

        callbacks_historique = {
            'voir_pj': self._action_voir_pj,
            'dl_pj': self._action_telecharger_pj
        }
        DocumentHistoryViewer(self, demande_data=demande_data, callbacks=callbacks_historique)

    def _action_mlupo_accepter(self, id_demande: str):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Accepter Constat TP - Demande {id_demande[:8]}")
        dialog.geometry("500x450")
        dialog.transient(self);
        dialog.grab_set()

        chemin_pj_var = ctk.StringVar(value="Aucune PJ sélectionnée (Obligatoire)")
        current_pj_path = None

        def _sel_pj():
            nonlocal current_pj_path
            path = self.remboursement_controller.selectionner_fichier_document_ou_image(
                "Sélectionner Preuve Trop-Perçu")
            if path:
                chemin_pj_var.set(os.path.basename(path))
                current_pj_path = path

        ctk.CTkLabel(dialog, text="Preuve de Trop-Perçu (Image/PDF/Doc...):").pack(pady=(10, 2))
        ctk.CTkButton(dialog, text="Choisir Fichier...", command=_sel_pj).pack(pady=(0, 5))
        ctk.CTkLabel(dialog, textvariable=chemin_pj_var).pack()

        ctk.CTkLabel(dialog, text="Commentaire (Obligatoire):").pack(pady=(10, 2))
        commentaire_box = ctk.CTkTextbox(dialog, height=100, width=450);
        commentaire_box.pack(pady=5, padx=10, fill="x", expand=True);
        commentaire_box.focus()

        def _submit():
            commentaire = commentaire_box.get("1.0", "end-1c").strip()
            if not current_pj_path:
                messagebox.showerror("Erreur", "La pièce jointe de preuve est obligatoire.", parent=dialog);
                return
            if not commentaire:
                messagebox.showerror("Erreur", "Le commentaire est obligatoire.", parent=dialog);
                return

            succes, msg = self.remboursement_controller.mlupo_accepter_constat(id_demande, current_pj_path,
                                                                               commentaire)
            if succes:
                messagebox.showinfo("Succès", msg, parent=self)
                dialog.destroy()
                self.afficher_liste_demandes(force_reload=True)
            else:
                messagebox.showerror("Erreur", msg, parent=dialog)

        ctk.CTkButton(dialog, text="Valider et Soumettre à J. Durousset", command=_submit).pack(pady=10)

    def _action_mlupo_refuser(self, id_demande: str):
        commentaire = simpledialog.askstring("Refus Constat Trop-Perçu",
                                             f"Motif du refus pour la demande {id_demande[:8]}:\n(Ce commentaire sera visible par P. Neri)",
                                             parent=self)

        if commentaire is not None:
            if not commentaire.strip():
                messagebox.showerror("Erreur", "Le commentaire de refus est obligatoire.", parent=self)
                return

            succes, msg = self.remboursement_controller.mlupo_refuser_constat(id_demande, commentaire)
            if succes:
                messagebox.showinfo("Refus Enregistré", msg, parent=self)
                self.afficher_liste_demandes(force_reload=True)
            else:
                messagebox.showerror("Erreur", msg, parent=self)

    def _action_jdurousset_valider(self, id_demande: str):
        commentaire = simpledialog.askstring("Validation Demande",
                                             f"Commentaire pour la validation de la demande {id_demande[:8]} (Optionnel):",
                                             parent=self)

        if commentaire is not None:
            succes, msg = self.remboursement_controller.jdurousset_valider_demande(id_demande,
                                                                                   commentaire.strip() if commentaire else None)
            if succes:
                messagebox.showinfo("Validation Réussie", msg, parent=self)
                self.afficher_liste_demandes(force_reload=True)
            else:
                messagebox.showerror("Erreur de Validation", msg, parent=self)

    def _action_jdurousset_refuser(self, id_demande: str):
        commentaire = simpledialog.askstring("Refus Validation Demande",
                                             f"Motif du refus de validation pour la demande {id_demande[:8]}:\n(Ce commentaire sera visible par M. Lupo)",
                                             parent=self)
        if commentaire is not None:
            if not commentaire.strip():
                messagebox.showerror("Erreur", "Un commentaire est obligatoire pour refuser la validation.",
                                     parent=self)
                return

            succes, msg = self.remboursement_controller.jdurousset_refuser_demande(id_demande, commentaire)
            if succes:
                messagebox.showinfo("Refus Enregistré", msg, parent=self)
                self.afficher_liste_demandes(force_reload=True)
            else:
                messagebox.showerror("Erreur de Refus", msg, parent=self)

    def _action_pdiop_confirmer_paiement(self, id_demande: str):
        commentaire = simpledialog.askstring("Confirmation Paiement",
                                             f"Commentaire pour la confirmation du paiement de la demande {id_demande[:8]} (Optionnel):",
                                             parent=self)

        if commentaire is not None:
            succes, msg = self.remboursement_controller.pdiop_confirmer_paiement_effectue(id_demande,
                                                                                          commentaire.strip() if commentaire else None)
            if succes:
                messagebox.showinfo("Paiement Confirmé", msg, parent=self)
                self.afficher_liste_demandes(force_reload=True)
            else:
                messagebox.showerror("Erreur", msg, parent=self)

    def _action_pneri_annuler(self, id_demande: str):
        commentaire = simpledialog.askstring("Annulation de Demande",
                                             f"Commentaire d'annulation pour la demande {id_demande[:8]}: \n(Requis pour tracer l'annulation)",
                                             parent=self)
        if commentaire is not None:
            if not commentaire.strip():
                messagebox.showerror("Erreur", "Le commentaire d'annulation est obligatoire.", parent=self)
                return

            succes, msg = self.remboursement_controller.pneri_annuler_demande(id_demande, commentaire)
            if succes:
                messagebox.showinfo("Demande Annulée", msg, parent=self)
                self.afficher_liste_demandes(force_reload=True)
            else:
                messagebox.showerror("Erreur", msg, parent=self)

    def _action_pneri_resoumettre(self, id_demande: str):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Corriger et Resoumettre Demande {id_demande[:8]}")
        dialog.geometry("600x500")
        dialog.transient(self);
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Veuillez fournir les documents mis à jour et un commentaire.").pack(pady=10)

        chemin_facture_var = ctk.StringVar(value="Nouvelle Facture: Non sélectionnée (Optionnel)")
        new_facture_path = None

        def _sel_new_facture():
            nonlocal new_facture_path
            path = self.remboursement_controller.selectionner_fichier_document_ou_image(
                "Nouvelle Facture (Optionnel)")
            if path:
                chemin_facture_var.set(os.path.basename(path)); new_facture_path = path
            else:
                chemin_facture_var.set("Nouvelle Facture: Non sélectionnée (Optionnel)"); new_facture_path = None

        ctk.CTkButton(dialog, text="Choisir Nouvelle Facture", command=_sel_new_facture).pack(pady=5)
        ctk.CTkLabel(dialog, textvariable=chemin_facture_var).pack()

        chemin_rib_var = ctk.StringVar(value="Nouveau RIB: Non sélectionné (Obligatoire)")
        new_rib_path = None

        def _sel_new_rib():
            nonlocal new_rib_path
            path = self.remboursement_controller.selectionner_fichier_document_ou_image("Nouveau RIB (Obligatoire)")
            if path:
                chemin_rib_var.set(os.path.basename(path)); new_rib_path = path
            else:
                chemin_rib_var.set("Nouveau RIB: Non sélectionné (Obligatoire)"); new_rib_path = None

        ctk.CTkButton(dialog, text="Choisir Nouveau RIB", command=_sel_new_rib).pack(pady=5)
        ctk.CTkLabel(dialog, textvariable=chemin_rib_var).pack()

        ctk.CTkLabel(dialog, text="Commentaire de correction (Obligatoire):").pack(pady=(10, 0))
        commentaire_box = ctk.CTkTextbox(dialog, height=80, width=450);
        commentaire_box.pack(pady=5, padx=10, fill="x", expand=True);
        commentaire_box.focus()

        def _submit_correction():
            commentaire = commentaire_box.get("1.0", "end-1c").strip()
            if not new_rib_path:
                messagebox.showerror("Erreur", "Un nouveau RIB (ou l'ancien re-sélectionné) est obligatoire.",
                                     parent=dialog);
                return
            if not commentaire:
                messagebox.showerror("Erreur", "Un commentaire expliquant la correction est obligatoire.",
                                     parent=dialog);
                return

            succes, msg = self.remboursement_controller.pneri_resoumettre_demande_corrigee(
                id_demande, commentaire, new_facture_path, new_rib_path
            )
            if succes:
                messagebox.showinfo("Succès", msg, parent=self)
                dialog.destroy()
                self.afficher_liste_demandes(force_reload=True)
            else:
                messagebox.showerror("Erreur", msg, parent=dialog)

        ctk.CTkButton(dialog, text="Resoumettre la Demande", command=_submit_correction).pack(pady=20)

    def _action_mlupo_resoumettre_constat(self, id_demande: str):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Corriger Constat TP - Demande {id_demande[:8]}")
        dialog.geometry("500x450")
        dialog.transient(self);
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Veuillez fournir une nouvelle preuve et un commentaire.").pack(pady=10)

        chemin_pj_var = ctk.StringVar(value="Nouvelle Preuve TP: Non sélectionnée (Obligatoire)")
        new_pj_path = None

        def _sel_new_pj_tp():
            nonlocal new_pj_path
            path = self.remboursement_controller.selectionner_fichier_document_ou_image(
                "Nouvelle Preuve Trop-Perçu (Obligatoire)")
            if path:
                chemin_pj_var.set(os.path.basename(path)); new_pj_path = path
            else:
                chemin_pj_var.set("Nouvelle Preuve TP: Non sélectionnée (Obligatoire)"); new_pj_path = None

        ctk.CTkButton(dialog, text="Choisir Nouvelle Preuve TP", command=_sel_new_pj_tp).pack(pady=5)
        ctk.CTkLabel(dialog, textvariable=chemin_pj_var).pack()

        ctk.CTkLabel(dialog, text="Commentaire de correction (Obligatoire):").pack(pady=(10, 0))
        commentaire_box = ctk.CTkTextbox(dialog, height=80, width=450);
        commentaire_box.pack(pady=5, padx=10, fill="x", expand=True);
        commentaire_box.focus()

        def _submit_correction_constat():
            commentaire = commentaire_box.get("1.0", "end-1c").strip()
            if not new_pj_path:
                messagebox.showerror("Erreur", "Une nouvelle pièce jointe de preuve est obligatoire.", parent=dialog);
                return
            if not commentaire:
                messagebox.showerror("Erreur", "Un commentaire expliquant la correction est obligatoire.",
                                     parent=dialog);
                return

            succes, msg = self.remboursement_controller.mlupo_resoumettre_constat_corrige(
                id_demande, commentaire, new_pj_path
            )
            if succes:
                messagebox.showinfo("Succès", msg, parent=self)
                dialog.destroy()
                self.afficher_liste_demandes(force_reload=True)
            else:
                messagebox.showerror("Erreur", msg, parent=dialog)

        ctk.CTkButton(dialog, text="Resoumettre le Constat", command=_submit_correction_constat).pack(pady=20)

    def _action_supprimer_demande(self, id_demande: str):
        if not id_demande:
            messagebox.showerror("Erreur", "ID de demande non valide pour la suppression.", parent=self)
            return

        confirmation = messagebox.askyesno("Confirmation de suppression",
                                           f"Êtes-vous sûr de vouloir supprimer la demande ID: {id_demande}?\n"
                                           "Cette action est irréversible et supprimera aussi les fichiers associés.",
                                           icon=messagebox.WARNING, parent=self)
        if confirmation:
            succes, message = self.remboursement_controller.supprimer_demande(id_demande)
            if succes:
                messagebox.showinfo("Suppression réussie", message, parent=self)
                self.afficher_liste_demandes(force_reload=True)
            else:
                messagebox.showerror("Erreur de suppression", message, parent=self)

    def _action_voir_pj(self, chemin_pj):
        if not chemin_pj:
            messagebox.showwarning("Avertissement", "Aucun chemin de fichier spécifié pour la visualisation.",
                                   parent=self)
            return
        if not os.path.exists(chemin_pj):
            messagebox.showerror("Erreur", f"Fichier non trouvé : {chemin_pj}", parent=self)
            return

        titre_fenetre = f"Aperçu - {os.path.basename(chemin_pj)}"
        DocumentViewerWindow(self, chemin_pj, titre_fenetre)

    def _action_telecharger_pj(self, chemin_pj):
        if not chemin_pj:
            messagebox.showwarning("Avertissement", "Aucun chemin de fichier source spécifié pour le téléchargement.",
                                   parent=self)
            return
        succes, message = self.remboursement_controller.telecharger_copie_piece_jointe(chemin_pj)
        if succes:
            messagebox.showinfo("Téléchargement", message, parent=self)
        elif "annulé" not in message.lower():
            messagebox.showerror("Erreur de téléchargement", message, parent=self)

    def _ouvrir_fenetre_creation_demande(self):
        dialog = ctk.CTkToplevel(self.master)
        dialog.title("Nouvelle Demande de Remboursement")
        dialog.geometry("650x650")
        dialog.transient(self.master)
        dialog.grab_set()

        form_frame = ctk.CTkFrame(dialog)
        form_frame.pack(expand=True, fill="both", padx=20, pady=20)

        current_row = 0
        labels_entries = {
            "Nom:": "nom",
            "Prénom:": "prenom",
            "Référence Facture:": "reference_facture",
            "Montant demandé (€):": "montant_demande_()"
        }
        self.entries_demande = {}

        for label_text, key_name in labels_entries.items():
            lbl = ctk.CTkLabel(form_frame, text=label_text)
            lbl.grid(row=current_row, column=0, padx=5, pady=8, sticky="w")
            entry = ctk.CTkEntry(form_frame, width=350)
            entry.grid(row=current_row, column=1, padx=5, pady=8, sticky="ew")
            self.entries_demande[key_name] = entry
            current_row += 1

        lbl_desc = ctk.CTkLabel(form_frame, text="Description/Raison:")
        lbl_desc.grid(row=current_row, column=0, padx=5, pady=(8, 0), sticky="nw")
        self.textbox_description = ctk.CTkTextbox(form_frame, width=350, height=100)
        self.textbox_description.grid(row=current_row, column=1, padx=5, pady=8, sticky="ew")
        current_row += 1

        form_frame.columnconfigure(1, weight=1)

        self.chemin_facture_var = ctk.StringVar(value="Aucun fichier sélectionné (Optionnel)")
        self.chemin_rib_var = ctk.StringVar(value="Aucun fichier sélectionné")
        self._entry_chemin_facture_complet = None
        self._entry_chemin_rib_complet = None

        def selectionner_facture():
            chemin = self.remboursement_controller.selectionner_fichier_document_ou_image(
                "Sélectionner la Facture (Optionnel)")
            if chemin:
                self.chemin_facture_var.set(os.path.basename(chemin))
                self._entry_chemin_facture_complet = chemin
                if chemin.lower().endswith(".pdf"):
                    infos_extraites = self.remboursement_controller.extraire_info_facture_pdf(chemin)
                    if infos_extraites.get("nom"):
                        self.entries_demande["nom"].delete(0, "end")
                        self.entries_demande["nom"].insert(0, infos_extraites["nom"])
                    if infos_extraites.get("prenom"):
                        self.entries_demande["prenom"].delete(0, "end")
                        self.entries_demande["prenom"].insert(0, infos_extraites["prenom"])
                    if infos_extraites.get("reference"):
                        self.entries_demande["reference_facture"].delete(0, "end")
                        self.entries_demande["reference_facture"].insert(0, infos_extraites["reference"])
            else:
                self.chemin_facture_var.set("Aucun fichier sélectionné (Optionnel)")
                self._entry_chemin_facture_complet = None

        btn_facture = ctk.CTkButton(form_frame, text="Choisir Facture (Optionnel)", command=selectionner_facture)
        btn_facture.grid(row=current_row, column=0, padx=5, pady=10, sticky="w")
        lbl_facture_sel = ctk.CTkLabel(form_frame, textvariable=self.chemin_facture_var, wraplength=300)
        lbl_facture_sel.grid(row=current_row, column=1, padx=5, pady=10, sticky="ew")
        current_row += 1

        def selectionner_rib():
            chemin = self.remboursement_controller.selectionner_fichier_document_ou_image(
                "Sélectionner le RIB (Obligatoire)")
            if chemin:
                self.chemin_rib_var.set(os.path.basename(chemin))
                self._entry_chemin_rib_complet = chemin

        btn_rib = ctk.CTkButton(form_frame, text="Choisir RIB (Obligatoire)", command=selectionner_rib)
        btn_rib.grid(row=current_row, column=0, padx=5, pady=10, sticky="w")
        lbl_rib_sel = ctk.CTkLabel(form_frame, textvariable=self.chemin_rib_var, wraplength=300)
        lbl_rib_sel.grid(row=current_row, column=1, padx=5, pady=10, sticky="ew")
        current_row += 1

        def soumettre_demande():
            nom = self.entries_demande["nom"].get()
            prenom = self.entries_demande["prenom"].get()
            ref = self.entries_demande["reference_facture"].get()
            montant_str = self.entries_demande["montant_demande_()"].get()
            description = self.textbox_description.get("1.0", "end-1c").strip()

            facture_path = getattr(self, '_entry_chemin_facture_complet', None)
            rib_path = getattr(self, '_entry_chemin_rib_complet', None)

            succes, message = self.remboursement_controller.creer_demande_remboursement(
                nom, prenom, ref, montant_str, facture_path, rib_path, description
            )
            if succes:
                messagebox.showinfo("Succès", message, parent=dialog)
                dialog.destroy()
                self.afficher_liste_demandes(force_reload=True)
            else:
                messagebox.showerror("Erreur", message, parent=dialog)

        btn_soumettre = ctk.CTkButton(form_frame, text="Enregistrer la Demande", command=soumettre_demande,
                                      height=35)
        btn_soumettre.grid(row=current_row, column=0, columnspan=2, pady=25, padx=5)

        dialog.after(100, lambda: self.entries_demande["nom"].focus_set())

    def __del__(self):
        self.stop_polling()