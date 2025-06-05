import os
import customtkinter as ctk
from tkinter import messagebox, simpledialog
import datetime
import traceback
import logging
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
from utils.dnd_utils import clean_dropped_filepaths

# Définition des constantes de couleur au niveau du module, AVANT leur utilisation
POLLING_INTERVAL_MS = 10000

COULEUR_ACTIVE_POUR_UTILISATEUR = "#1E4D2B"
COULEUR_DEMANDE_TERMINEE = "#2E4374"
COULEUR_DEMANDE_ANNULEE = "#6A040F"  # S'assurer que cette ligne est présente et correcte
COULEUR_BORDURE_ACTIVE = "#38761D"
COULEUR_BORDURE_TERMINEE = "#4A55A2"
COULEUR_BORDURE_ANNULEE = "#9D0208"  # S'assurer que cette ligne est présente et correcte

tkinter_dnd_available_for_view = False
DND_FILES = None

try:
    from tkinterdnd2 import DND_FILES as DND_FILES_lib

    DND_FILES = DND_FILES_lib
    tkinter_dnd_available_for_view = True
    logging.info("tkinterdnd2 (DND_FILES) importé avec succès pour MainView.")
except ImportError:
    logging.warning(
        "tkinterdnd2 non trouvé dans MainView lors de l'import de DND_FILES. Le glisser-déposer sera désactivé.")
except Exception as e:
    logging.error(f"Erreur inattendue lors de l'import de DND_FILES depuis tkinterdnd2: {e}", exc_info=True)


class MainView(ctk.CTkFrame):
    def __init__(self, master_frame, nom_utilisateur, on_logout_callback,
                 remboursement_controller_factory, auth_controller_instance,
                 true_root_window):  # true_root_window ajouté
        super().__init__(master_frame, corner_radius=0, fg_color="transparent")
        self.master_frame = master_frame
        self.true_root_window = true_root_window  # Stocker la vraie fenêtre racine
        self.nom_utilisateur = nom_utilisateur
        self.on_logout = on_logout_callback
        self.remboursement_controller = remboursement_controller_factory(self.nom_utilisateur)
        self.auth_controller = auth_controller_instance
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
            self.afficher_liste_demandes()
            self.start_polling()
        except Exception as e:
            logging.error(f"ERREUR CRITIQUE DANS MainView.__init__: {e}", exc_info=True)
            ctk.CTkLabel(self.master_frame,
                         text=f"Erreur critique à l'initialisation:\n{e}\nConsultez les logs.", font=("Arial", 16),
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
        ctk.CTkLabel(top_bar, text=f"Utilisateur : {self.nom_utilisateur}{roles_str}", font=ctk.CTkFont(size=12)).pack(
            side="left", padx=5)
        ctk.CTkButton(top_bar, text="Aide", command=self._ouvrir_fenetre_aide, width=70).pack(side="right", padx=(0, 5))
        ctk.CTkButton(top_bar, text="Déconnexion", command=self.on_logout, width=120).pack(side="right", padx=5)
        ctk.CTkLabel(self.main_content_frame, text="Tableau de Bord - Remboursements",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 10), anchor="n")

    def creer_section_actions_et_rafraichissement(self):
        actions_bar_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        actions_bar_frame.pack(pady=(0, 5), padx=10, fill="x", anchor="n")
        if self.peut_creer_demande():
            ctk.CTkButton(actions_bar_frame, text="Nouvelle Demande",
                          command=self._ouvrir_fenetre_creation_demande).pack(side="left", pady=5, padx=(0, 10))
        ctk.CTkButton(actions_bar_frame, text="Rafraîchir Liste", command=self.afficher_liste_demandes, width=150).pack(
            side="left", pady=5, padx=10)
        if self.est_admin():
            ctk.CTkButton(actions_bar_frame, text="Gérer Utilisateurs",
                          command=self._ouvrir_fenetre_gestion_utilisateurs, fg_color="#555555",
                          hover_color="#444444").pack(side="left", pady=5, padx=10)

    def _ouvrir_fenetre_gestion_utilisateurs(self):
        if self.auth_controller:
            AdminUserManagementView(self.true_root_window, self.auth_controller)
        else:
            messagebox.showerror("Erreur", "Contrôleur d'auth non initialisé.", parent=self.true_root_window)

    def _ouvrir_fenetre_aide(self):
        HelpView(self.true_root_window, self.nom_utilisateur, self.user_roles)

    def _creer_barre_recherche(self):
        search_bar_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        search_bar_frame.pack(fill="x", padx=10, pady=(5, 5))
        ctk.CTkLabel(search_bar_frame, text="Rechercher (Nom, Prénom, Réf.):", font=ctk.CTkFont(size=12)).pack(
            side="left", padx=(0, 5))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)
        self.search_entry = ctk.CTkEntry(search_bar_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", padx=(0, 5), fill="x", expand=True)
        ctk.CTkButton(search_bar_frame, text="X", width=30, command=self._clear_search).pack(side="left", padx=(5, 0))

    def _clear_search(self, event=None):
        self.search_var.set("")

    def _on_search_change(self, *args):
        self.afficher_liste_demandes()

    def creer_conteneur_liste_demandes(self):
        self.scrollable_frame_demandes = ctk.CTkScrollableFrame(self.main_content_frame,
                                                                label_text="Liste des Demandes de Remboursement")
        self.scrollable_frame_demandes.pack(pady=(5, 5), padx=10, expand=True, fill="both")
        self.scrollable_frame_demandes.grid_columnconfigure(0, weight=1)

    def creer_legende_couleurs(self):
        legende_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        legende_frame.pack(fill="x", padx=10, pady=(5, 10), anchor="s")
        ctk.CTkLabel(legende_frame, text="Légende:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 10))
        legend_items = [("Action Requise", COULEUR_ACTIVE_POUR_UTILISATEUR), ("Terminée", COULEUR_DEMANDE_TERMINEE),
                        ("Annulée", COULEUR_DEMANDE_ANNULEE)]
        for texte, couleur_fond in legend_items:
            item = ctk.CTkFrame(legende_frame, fg_color="transparent");
            item.pack(side="left", padx=5)
            ctk.CTkFrame(item, width=15, height=15, fg_color=couleur_fond, border_width=1).pack(side="left")
            ctk.CTkLabel(item, text=texte, font=ctk.CTkFont(size=11)).pack(side="left", padx=3)

    def _check_for_data_updates(self):
        try:
            if os.path.exists(REMBOURSEMENTS_JSON_FILE):
                current_mtime = os.path.getmtime(REMBOURSEMENTS_JSON_FILE)
                if self._last_known_remboursements_mtime == 0 or current_mtime > self._last_known_remboursements_mtime:
                    logging.info("Mise à jour des données détectée, rafraîchissement.")
                    self._last_known_remboursements_mtime = current_mtime
                    self.afficher_liste_demandes()
            elif self._last_known_remboursements_mtime != 0:
                logging.warning("Fichier remboursements.json non trouvé.")
                self._last_known_remboursements_mtime = 0
                self.afficher_liste_demandes()
        except Exception as e:
            logging.error(f"Erreur polling: {e}", exc_info=True)
        if self.winfo_exists(): self._polling_job_id = self.after(POLLING_INTERVAL_MS, self._check_for_data_updates)

    def start_polling(self):
        if self._polling_job_id: self.after_cancel(self._polling_job_id)
        self._last_known_remboursements_mtime = os.path.getmtime(REMBOURSEMENTS_JSON_FILE) if os.path.exists(
            REMBOURSEMENTS_JSON_FILE) else 0
        logging.info("Polling démarré.");
        self._check_for_data_updates()

    def stop_polling(self):
        if self._polling_job_id: logging.info("Polling arrêté."); self.after_cancel(
            self._polling_job_id); self._polling_job_id = None

    def afficher_liste_demandes(self, source_is_polling=False):
        self._fetch_user_roles()
        if hasattr(self,
                   'no_demandes_label_widget') and self.no_demandes_label_widget and self.no_demandes_label_widget.winfo_exists():
            self.no_demandes_label_widget.destroy();
            self.no_demandes_label_widget = None
        for widget in self.scrollable_frame_demandes.winfo_children(): widget.destroy()
        all_demandes = self.remboursement_controller.get_toutes_les_demandes_formatees()
        term = self.search_var.get().lower().strip() if hasattr(self, 'search_var') else ""
        to_display = [d for d in all_demandes if not term or (
                    term in d.get('nom', '').lower() or term in d.get('prenom', '').lower() or term in d.get(
                'reference_facture', '').lower())]
        if not to_display:
            msg = "Aucune demande à afficher." + (f" pour '{term}'." if term else "")
            self.no_demandes_label_widget = ctk.CTkLabel(self.scrollable_frame_demandes, text=msg,
                                                         font=ctk.CTkFont(size=14))
            self.no_demandes_label_widget.pack(pady=20, padx=20)
        else:
            callbacks = {k: getattr(self, f'_action_{k}') for k in
                         ['voir_pj', 'dl_pj', 'mlupo_accepter', 'mlupo_refuser', 'jdurousset_valider',
                          'jdurousset_refuser', 'pdiop_confirmer_paiement', 'pneri_annuler', 'pneri_resoumettre',
                          'mlupo_resoumettre_constat', 'supprimer_demande', 'voir_historique_docs']}
            for data in to_display:
                RemboursementItemView(self.scrollable_frame_demandes, data, self.nom_utilisateur, self.user_roles,
                                      callbacks).pack(fill="x", pady=4, padx=5)

    def _action_voir_historique_docs(self, demande_data: dict):
        DocumentHistoryViewer(self.true_root_window, demande_data,
                              {'voir_pj': self._action_voir_pj, 'dl_pj': self._action_telecharger_pj})

    def _setup_dnd_target(self, parent_dialog_pour_msgbox, target_widget_dnd_frame, file_variable_label_var,
                          callback_on_drop_valid_file):
        if not tkinter_dnd_available_for_view or DND_FILES is None:
            logging.warning(
                f"DND non disponible (lib: {tkinter_dnd_available_for_view}, DND_FILES: {DND_FILES}), pour {target_widget_dnd_frame.winfo_class()}.")
            if hasattr(target_widget_dnd_frame, "dnd_text_label_widget"):
                target_widget_dnd_frame.dnd_text_label_widget.configure(
                    text=target_widget_dnd_frame.dnd_text_label_widget.cget(
                        "text") + "\n(Glisser-déposer indisponible)")
            return
        try:
            original_border_color = target_widget_dnd_frame.cget("border_color")
        except:
            original_border_color = "gray50"
        hover_border_color = "green"
        logging.debug(f"Setup DND pour {target_widget_dnd_frame.winfo_class()}")

        def drop_enter(e):
            logging.debug(f"DND Enter: {e.data}"); target_widget_dnd_frame.configure(
                border_color=hover_border_color); return e.action

        def drop_leave(e):
            logging.debug("DND Leave"); target_widget_dnd_frame.configure(
                border_color=original_border_color); return e.action

        def drop(e):
            logging.debug(f"DND Drop: {e.data}")
            target_widget_dnd_frame.configure(border_color=original_border_color)
            paths = clean_dropped_filepaths(e.data)
            if paths and os.path.isfile(paths[0]):
                file_variable_label_var.set(os.path.basename(paths[0]));
                callback_on_drop_valid_file(paths[0])
            else:
                messagebox.showwarning("Drop", "Fichier non valide ou aucun fichier déposé.",
                                       parent=parent_dialog_pour_msgbox)
            return e.action

        try:
            target_widget_dnd_frame.drop_target_register(DND_FILES)
            target_widget_dnd_frame.dnd_bind('<<DropEnter>>', drop_enter)
            target_widget_dnd_frame.dnd_bind('<<DropLeave>>', drop_leave)
            target_widget_dnd_frame.dnd_bind('<<Drop>>', drop)
            logging.info(f"DND target registered for {target_widget_dnd_frame.winfo_class()}")
        except Exception as e_dnd:
            logging.error(f"Erreur DND register pour {target_widget_dnd_frame.winfo_class()}: {e_dnd}", exc_info=True)

    def _creer_zone_selection_fichier_avec_dnd(self, parent_pour_elements_layout, parent_dialog_pour_msgbox,
                                               label_texte_bouton: str,
                                               variable_chemin_affiche: ctk.StringVar,
                                               callback_selection_manuelle,
                                               callback_assignation_chemin_complet,
                                               aide_texte_optionnel: str = ""):
        container = ctk.CTkFrame(parent_pour_elements_layout, fg_color="transparent")
        dnd_target = ctk.CTkFrame(container, height=80, border_width=2, border_color="gray50")
        dnd_target.pack(fill="x", expand=True, pady=(0, 3))
        dnd_target.pack_propagate(False)
        dnd_target.dnd_text_label_widget = ctk.CTkLabel(dnd_target, text=f"Glissez-déposez {aide_texte_optionnel} ici",
                                                        font=ctk.CTkFont(size=11), text_color="gray60")
        dnd_target.dnd_text_label_widget.place(relx=0.5, rely=0.3, anchor="center")
        ctk.CTkButton(dnd_target, text=label_texte_bouton, command=callback_selection_manuelle, width=150).place(
            relx=0.5, rely=0.7, anchor="center")
        label_width = 300
        if hasattr(parent_pour_elements_layout,
                   'winfo_exists') and parent_pour_elements_layout.winfo_exists() and parent_pour_elements_layout.winfo_width() > 0:
            label_width = parent_pour_elements_layout.winfo_width() - 40
            if label_width < 100: label_width = 300
        ctk.CTkLabel(container, textvariable=variable_chemin_affiche, wraplength=label_width, anchor="w",
                     justify="left").pack(fill="x", expand=True, pady=(2, 0))
        self._setup_dnd_target(parent_dialog_pour_msgbox, dnd_target, variable_chemin_affiche,
                               callback_assignation_chemin_complet)
        return container

    def _action_mlupo_accepter(self, id_demande: str):
        dialog = ctk.CTkToplevel(self.true_root_window)
        dialog.title(f"Accepter Constat TP - Demande {id_demande[:8]}")
        dialog.geometry("550x480")
        dialog.transient(self.true_root_window);
        dialog.grab_set();
        dialog.attributes("-topmost", True)
        content_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        content_frame.pack(expand=True, fill="both", padx=20, pady=15)
        self._current_pj_path_mlupo_accept = None
        chemin_pj_var_mlupo_accept = ctk.StringVar(value="Aucune PJ sélectionnée (Obligatoire)")

        def assign_pj_path(path):
            self._current_pj_path_mlupo_accept = path

        def select_pj_manuelle():
            path = self.remboursement_controller.selectionner_fichier_document_ou_image(
                "Sélectionner Preuve Trop-Perçu")
            if path: chemin_pj_var_mlupo_accept.set(os.path.basename(path)); assign_pj_path(path)

        ctk.CTkLabel(content_frame, text="Preuve de Trop-Perçu (Image/PDF/Doc...):").pack(pady=(0, 2), anchor="w")
        zone_pj = self._creer_zone_selection_fichier_avec_dnd(
            parent_pour_elements_layout=content_frame, parent_dialog_pour_msgbox=dialog,
            label_texte_bouton="Choisir Fichier...", variable_chemin_affiche=chemin_pj_var_mlupo_accept,
            callback_selection_manuelle=select_pj_manuelle, callback_assignation_chemin_complet=assign_pj_path,
            aide_texte_optionnel="la preuve de trop-perçu")
        zone_pj.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(content_frame, text="Commentaire (Obligatoire):").pack(pady=(5, 2), anchor="w")
        commentaire_box = ctk.CTkTextbox(content_frame, height=100)
        commentaire_box.pack(pady=(0, 10), fill="x", expand=True)
        dialog.after(150, commentaire_box.focus)
        btn_submit = ctk.CTkButton(content_frame, text="Valider et Soumettre", command=lambda: _submit_action())
        btn_submit.pack(pady=10)

        def _submit_action():
            commentaire = commentaire_box.get("1.0", "end-1c").strip()
            if not self._current_pj_path_mlupo_accept: messagebox.showerror("Erreur",
                                                                            "La PJ de preuve est obligatoire.",
                                                                            parent=dialog); return
            if not commentaire: messagebox.showerror("Erreur", "Le commentaire est obligatoire.", parent=dialog); return
            succes, msg = self.remboursement_controller.mlupo_accepter_constat(id_demande,
                                                                               self._current_pj_path_mlupo_accept,
                                                                               commentaire)
            if succes:
                messagebox.showinfo("Succès", msg,
                                    parent=self.true_root_window); dialog.destroy(); self.afficher_liste_demandes()
            else:
                messagebox.showerror("Erreur", msg, parent=dialog)

    def _action_pneri_resoumettre(self, id_demande: str):
        dialog = ctk.CTkToplevel(self.true_root_window)
        dialog.title(f"Corriger et Resoumettre Demande {id_demande[:8]}")
        dialog.geometry("650x630")
        dialog.transient(self.true_root_window);
        dialog.grab_set();
        dialog.attributes("-topmost", True)
        main_dialog_content_frame = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        main_dialog_content_frame.pack(expand=True, fill="both", padx=10, pady=10)
        ctk.CTkLabel(main_dialog_content_frame,
                     text="Veuillez fournir les documents mis à jour et un commentaire.").pack(pady=(0, 10), padx=10,
                                                                                               anchor="w")
        self._new_facture_path_pneri = None;
        self._new_rib_path_pneri = None
        chemin_facture_var_pneri = ctk.StringVar(value="Nouvelle Facture: Non sélectionnée (Optionnel)")
        chemin_rib_var_pneri = ctk.StringVar(value="Nouveau RIB: Non sélectionné (Obligatoire)")

        def assign_new_facture_path(path):
            self._new_facture_path_pneri = path

        def assign_new_rib_path(path):
            self._new_rib_path_pneri = path

        def select_new_facture_manuelle():
            path = self.remboursement_controller.selectionner_fichier_document_ou_image("Nouvelle Facture (Optionnel)")
            if path:
                chemin_facture_var_pneri.set(os.path.basename(path)); assign_new_facture_path(path)
            else:
                chemin_facture_var_pneri.set("Nouvelle Facture: Non sélectionnée (Optionnel)"); assign_new_facture_path(
                    None)

        def select_new_rib_manuelle():
            path = self.remboursement_controller.selectionner_fichier_document_ou_image("Nouveau RIB (Obligatoire)")
            if path: chemin_rib_var_pneri.set(os.path.basename(path)); assign_new_rib_path(path)

        ctk.CTkLabel(main_dialog_content_frame, text="Nouvelle Facture (Optionnel):").pack(anchor="w", padx=10,
                                                                                           pady=(5, 0))
        zone_facture = self._creer_zone_selection_fichier_avec_dnd(
            parent_pour_elements_layout=main_dialog_content_frame, parent_dialog_pour_msgbox=dialog,
            label_texte_bouton="Choisir Nouvelle Facture", variable_chemin_affiche=chemin_facture_var_pneri,
            callback_selection_manuelle=select_new_facture_manuelle,
            callback_assignation_chemin_complet=assign_new_facture_path,
            aide_texte_optionnel="la nouvelle facture")
        zone_facture.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(main_dialog_content_frame, text="Nouveau RIB (Obligatoire):").pack(anchor="w", padx=10,
                                                                                        pady=(5, 0))
        zone_rib = self._creer_zone_selection_fichier_avec_dnd(
            parent_pour_elements_layout=main_dialog_content_frame, parent_dialog_pour_msgbox=dialog,
            label_texte_bouton="Choisir Nouveau RIB", variable_chemin_affiche=chemin_rib_var_pneri,
            callback_selection_manuelle=select_new_rib_manuelle,
            callback_assignation_chemin_complet=assign_new_rib_path,
            aide_texte_optionnel="le nouveau RIB")
        zone_rib.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(main_dialog_content_frame, text="Commentaire de correction (Obligatoire):").pack(anchor="w",
                                                                                                      padx=10,
                                                                                                      pady=(10, 0))
        commentaire_box = ctk.CTkTextbox(main_dialog_content_frame, height=80);
        commentaire_box.pack(pady=5, padx=10, fill="x", expand=True);
        dialog.after(150, commentaire_box.focus)
        btn_submit = ctk.CTkButton(main_dialog_content_frame, text="Resoumettre la Demande",
                                   command=lambda: _submit_correction_action())
        btn_submit.pack(pady=20)

        def _submit_correction_action():
            commentaire = commentaire_box.get("1.0", "end-1c").strip()
            if not self._new_rib_path_pneri: messagebox.showerror("Erreur", "Un nouveau RIB est obligatoire.",
                                                                  parent=dialog); return
            if not commentaire: messagebox.showerror("Erreur", "Un commentaire est obligatoire.", parent=dialog); return
            succes, msg = self.remboursement_controller.pneri_resoumettre_demande_corrigee(id_demande, commentaire,
                                                                                           self._new_facture_path_pneri,
                                                                                           self._new_rib_path_pneri)
            if succes:
                messagebox.showinfo("Succès", msg,
                                    parent=self.true_root_window); dialog.destroy(); self.afficher_liste_demandes()
            else:
                messagebox.showerror("Erreur", msg, parent=dialog)

    def _action_mlupo_resoumettre_constat(self, id_demande: str):
        dialog = ctk.CTkToplevel(self.true_root_window)
        dialog.title(f"Corriger Constat TP - Demande {id_demande[:8]}")
        dialog.geometry("550x480")
        dialog.transient(self.true_root_window);
        dialog.grab_set();
        dialog.attributes("-topmost", True)
        content_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        content_frame.pack(expand=True, fill="both", padx=20, pady=15)
        ctk.CTkLabel(content_frame, text="Veuillez fournir une nouvelle preuve et un commentaire.").pack(pady=(0, 10),
                                                                                                         anchor="w")
        self._new_pj_path_mlupo_resubmit = None
        chemin_pj_var_mlupo_resubmit = ctk.StringVar(value="Nouvelle Preuve TP: Non sélectionnée (Obligatoire)")

        def assign_new_pj_tp_path(path):
            self._new_pj_path_mlupo_resubmit = path

        def select_new_pj_tp_manuelle():
            path = self.remboursement_controller.selectionner_fichier_document_ou_image(
                "Nouvelle Preuve Trop-Perçu (Obligatoire)")
            if path: chemin_pj_var_mlupo_resubmit.set(os.path.basename(path)); assign_new_pj_tp_path(path)

        ctk.CTkLabel(content_frame, text="Nouvelle Preuve de Trop-Perçu:").pack(anchor="w", pady=(5, 0))
        zone_pj_tp = self._creer_zone_selection_fichier_avec_dnd(
            parent_pour_elements_layout=content_frame, parent_dialog_pour_msgbox=dialog,
            label_texte_bouton="Choisir Nouvelle Preuve TP", variable_chemin_affiche=chemin_pj_var_mlupo_resubmit,
            callback_selection_manuelle=select_new_pj_tp_manuelle,
            callback_assignation_chemin_complet=assign_new_pj_tp_path,
            aide_texte_optionnel="la nouvelle preuve TP")
        zone_pj_tp.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(content_frame, text="Commentaire de correction (Obligatoire):").pack(anchor="w", pady=(10, 0))
        commentaire_box = ctk.CTkTextbox(content_frame, height=80);
        commentaire_box.pack(pady=5, fill="x", expand=True);
        dialog.after(150, commentaire_box.focus)
        btn_submit = ctk.CTkButton(content_frame, text="Resoumettre le Constat",
                                   command=lambda: _submit_correction_constat_action())
        btn_submit.pack(pady=20)

        def _submit_correction_constat_action():
            commentaire = commentaire_box.get("1.0", "end-1c").strip()
            if not self._new_pj_path_mlupo_resubmit: messagebox.showerror("Erreur",
                                                                          "Une nouvelle preuve TP est obligatoire.",
                                                                          parent=dialog); return
            if not commentaire: messagebox.showerror("Erreur", "Un commentaire est obligatoire.", parent=dialog); return
            succes, msg = self.remboursement_controller.mlupo_resoumettre_constat_corrige(id_demande, commentaire,
                                                                                          self._new_pj_path_mlupo_resubmit)
            if succes:
                messagebox.showinfo("Succès", msg,
                                    parent=self.true_root_window); dialog.destroy(); self.afficher_liste_demandes()
            else:
                messagebox.showerror("Erreur", msg, parent=dialog)

    def _ouvrir_fenetre_creation_demande(self):
        dialog = ctk.CTkToplevel(self.true_root_window)
        dialog.title("Nouvelle Demande de Remboursement")
        dialog.geometry("700x780")
        dialog.transient(self.true_root_window);
        dialog.grab_set();
        dialog.attributes("-topmost", True)

        form_container = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        form_container.pack(expand=True, fill="both", padx=10, pady=10)

        form_container.columnconfigure(0, weight=0, minsize=160)
        form_container.columnconfigure(1, weight=1)

        current_row = 0
        labels_entries = {
            "Nom du patient:": "nom", "Prénom du patient:": "prenom",
            "Référence Facture:": "reference_facture",
            "Montant demandé (€):": "montant_demande_()"
        }
        self.entries_demande = {}

        for label_text, key_name in labels_entries.items():
            ctk.CTkLabel(form_container, text=label_text, anchor="w").grid(row=current_row, column=0, padx=(0, 10),
                                                                           pady=8, sticky="w")
            entry = ctk.CTkEntry(form_container)
            entry.grid(row=current_row, column=1, padx=5, pady=8, sticky="ew")
            self.entries_demande[key_name] = entry
            current_row += 1

        ctk.CTkLabel(form_container, text="Description/Raison:", anchor="nw").grid(row=current_row, column=0,
                                                                                   padx=(0, 10), pady=(8, 0),
                                                                                   sticky="nw")
        self.textbox_description = ctk.CTkTextbox(form_container, height=100)
        self.textbox_description.grid(row=current_row, column=1, padx=5, pady=8, sticky="ew")
        current_row += 1

        ctk.CTkLabel(form_container, text="Facture Client (Opt.):", anchor="nw").grid(row=current_row, column=0,
                                                                                      padx=(0, 10), pady=(10, 0),
                                                                                      sticky="nw")
        self.chemin_facture_var_creation = ctk.StringVar(value="Facture: Non sélectionnée")
        self._entry_chemin_facture_complet_creation = None

        def assign_facture_path(path):
            self._entry_chemin_facture_complet_creation = path
            if path and path.lower().endswith(".pdf"): self.after(50, lambda p=path: _process_pdf(p))

        def _process_pdf(pdf_path):
            infos = self.remboursement_controller.extraire_info_facture_pdf(pdf_path)
            if infos.get("nom"): self.entries_demande["nom"].delete(0, "end"); self.entries_demande["nom"].insert(0,
                                                                                                                  infos[
                                                                                                                      "nom"])
            if infos.get("prenom"): self.entries_demande["prenom"].delete(0, "end"); self.entries_demande[
                "prenom"].insert(0, infos["prenom"])
            if infos.get("reference"): self.entries_demande["reference_facture"].delete(0, "end"); self.entries_demande[
                "reference_facture"].insert(0, infos["reference"])

        def select_facture_manual():
            p = self.remboursement_controller.selectionner_fichier_document_ou_image("Sélectionner Facture (Optionnel)")
            if p:
                self.chemin_facture_var_creation.set(f"{os.path.basename(p)}"); assign_facture_path(p)
            else:
                self.chemin_facture_var_creation.set("Facture: Non sélectionnée"); assign_facture_path(None)

        zone_facture = self._creer_zone_selection_fichier_avec_dnd(
            parent_pour_elements_layout=form_container, parent_dialog_pour_msgbox=dialog,
            label_texte_bouton="Choisir Facture", variable_chemin_affiche=self.chemin_facture_var_creation,
            callback_selection_manuelle=select_facture_manual, callback_assignation_chemin_complet=assign_facture_path,
            aide_texte_optionnel="la facture")
        zone_facture.grid(row=current_row, column=1, padx=5, pady=(5, 0), sticky="ew")
        current_row += 1

        ctk.CTkLabel(form_container, text="RIB Client (Oblig.):", anchor="nw").grid(row=current_row, column=0,
                                                                                    padx=(0, 10), pady=(10, 0),
                                                                                    sticky="nw")
        self.chemin_rib_var_creation = ctk.StringVar(value="RIB: Non sélectionné")
        self._entry_chemin_rib_complet_creation = None

        def assign_rib_path(path):
            self._entry_chemin_rib_complet_creation = path

        def select_rib_manual():
            p = self.remboursement_controller.selectionner_fichier_document_ou_image("Sélectionner RIB (Obligatoire)")
            if p: self.chemin_rib_var_creation.set(f"{os.path.basename(p)}"); assign_rib_path(p)

        zone_rib = self._creer_zone_selection_fichier_avec_dnd(
            parent_pour_elements_layout=form_container, parent_dialog_pour_msgbox=dialog,
            label_texte_bouton="Choisir RIB", variable_chemin_affiche=self.chemin_rib_var_creation,
            callback_selection_manuelle=select_rib_manual, callback_assignation_chemin_complet=assign_rib_path,
            aide_texte_optionnel="le RIB")
        zone_rib.grid(row=current_row, column=1, padx=5, pady=(5, 0), sticky="ew")
        current_row += 1

        submit_button = ctk.CTkButton(form_container, text="Enregistrer la Demande", command=lambda: _submit_action(),
                                      height=35)
        submit_button.grid(row=current_row, column=0, columnspan=2, pady=25, padx=5)

        dialog.after(150, lambda: self.entries_demande["nom"].focus_set())

        def _submit_action():
            nom = self.entries_demande["nom"].get();
            prenom = self.entries_demande["prenom"].get()
            ref = self.entries_demande["reference_facture"].get();
            montant_str = self.entries_demande["montant_demande_()"].get()
            desc = self.textbox_description.get("1.0", "end-1c").strip()
            fact_path = self._entry_chemin_facture_complet_creation;
            rib_path = self._entry_chemin_rib_complet_creation
            ok, msg = self.remboursement_controller.creer_demande_remboursement(nom, prenom, ref, montant_str,
                                                                                fact_path, rib_path, desc)
            if ok:
                messagebox.showinfo("Succès", msg,
                                    parent=self.true_root_window);dialog.destroy();self.afficher_liste_demandes()
            else:
                messagebox.showerror("Erreur", msg, parent=dialog)

    def _action_mlupo_refuser(self, id_demande: str):
        commentaire = simpledialog.askstring("Refus Constat Trop-Perçu",
                                             f"Motif du refus pour la demande {id_demande[:8]}:\n(Ce commentaire sera visible par P. Neri)",
                                             parent=self.true_root_window)
        if commentaire is not None:
            if not commentaire.strip(): messagebox.showerror("Erreur", "Le commentaire de refus est obligatoire.",
                                                             parent=self.true_root_window); return
            succes, msg = self.remboursement_controller.mlupo_refuser_constat(id_demande, commentaire)
            if succes:
                messagebox.showinfo("Refus Enregistré", msg,
                                    parent=self.true_root_window); self.afficher_liste_demandes()
            else:
                messagebox.showerror("Erreur", msg, parent=self.true_root_window)

    def _action_jdurousset_valider(self, id_demande: str):
        commentaire = simpledialog.askstring("Validation Demande",
                                             f"Commentaire pour la validation de la demande {id_demande[:8]} (Optionnel):",
                                             parent=self.true_root_window)
        if commentaire is not None:
            succes, msg = self.remboursement_controller.jdurousset_valider_demande(id_demande,
                                                                                   commentaire.strip() if commentaire else None)
            if succes:
                messagebox.showinfo("Validation Réussie", msg,
                                    parent=self.true_root_window); self.afficher_liste_demandes()
            else:
                messagebox.showerror("Erreur de Validation", msg, parent=self.true_root_window)

    def _action_jdurousset_refuser(self, id_demande: str):
        commentaire = simpledialog.askstring("Refus Validation Demande",
                                             f"Motif du refus de validation pour la demande {id_demande[:8]}:\n(Ce commentaire sera visible par M. Lupo)",
                                             parent=self.true_root_window)
        if commentaire is not None:
            if not commentaire.strip(): messagebox.showerror("Erreur",
                                                             "Un commentaire est obligatoire pour refuser la validation.",
                                                             parent=self.true_root_window); return
            succes, msg = self.remboursement_controller.jdurousset_refuser_demande(id_demande, commentaire)
            if succes:
                messagebox.showinfo("Refus Enregistré", msg,
                                    parent=self.true_root_window); self.afficher_liste_demandes()
            else:
                messagebox.showerror("Erreur de Refus", msg, parent=self.true_root_window)

    def _action_pdiop_confirmer_paiement(self, id_demande: str):
        commentaire = simpledialog.askstring("Confirmation Paiement",
                                             f"Commentaire pour la confirmation du paiement de la demande {id_demande[:8]} (Optionnel):",
                                             parent=self.true_root_window)
        if commentaire is not None:
            succes, msg = self.remboursement_controller.pdiop_confirmer_paiement_effectue(id_demande,
                                                                                          commentaire.strip() if commentaire else None)
            if succes:
                messagebox.showinfo("Paiement Confirmé", msg,
                                    parent=self.true_root_window); self.afficher_liste_demandes()
            else:
                messagebox.showerror("Erreur", msg, parent=self.true_root_window)

    def _action_pneri_annuler(self, id_demande: str):
        commentaire = simpledialog.askstring("Annulation de Demande",
                                             f"Commentaire d'annulation pour la demande {id_demande[:8]}: \n(Requis pour tracer l'annulation)",
                                             parent=self.true_root_window)
        if commentaire is not None:
            if not commentaire.strip(): messagebox.showerror("Erreur", "Le commentaire d'annulation est obligatoire.",
                                                             parent=self.true_root_window); return
            succes, msg = self.remboursement_controller.pneri_annuler_demande(id_demande, commentaire)
            if succes:
                messagebox.showinfo("Demande Annulée", msg,
                                    parent=self.true_root_window); self.afficher_liste_demandes()
            else:
                messagebox.showerror("Erreur", msg, parent=self.true_root_window)

    def _action_supprimer_demande(self, id_demande: str):
        if not id_demande: messagebox.showerror("Erreur", "ID de demande non valide pour la suppression.",
                                                parent=self.true_root_window); return
        confirmation = messagebox.askyesno("Confirmation de suppression",
                                           f"Êtes-vous sûr de vouloir supprimer la demande ID: {id_demande}?\nCette action est irréversible.",
                                           icon=messagebox.WARNING, parent=self.true_root_window)
        if confirmation:
            succes, message = self.remboursement_controller.supprimer_demande(id_demande)
            if succes:
                messagebox.showinfo("Suppression réussie", message,
                                    parent=self.true_root_window); self.afficher_liste_demandes()
            else:
                messagebox.showerror("Erreur de suppression", message, parent=self.true_root_window)

    def _action_voir_pj(self, chemin_pj):
        if not chemin_pj: messagebox.showwarning("Avertissement", "Aucun chemin de fichier spécifié.",
                                                 parent=self.true_root_window); return
        if not os.path.exists(chemin_pj): messagebox.showerror("Erreur", f"Fichier non trouvé : {chemin_pj}",
                                                               parent=self.true_root_window); return
        DocumentViewerWindow(self.true_root_window, chemin_pj, f"Aperçu - {os.path.basename(chemin_pj)}")

    def _action_telecharger_pj(self, chemin_pj):
        if not chemin_pj: messagebox.showwarning("Avertissement", "Aucun chemin de fichier source spécifié.",
                                                 parent=self.true_root_window); return
        succes, message = self.remboursement_controller.telecharger_copie_piece_jointe(chemin_pj)
        if succes:
            messagebox.showinfo("Téléchargement", message, parent=self.true_root_window)
        elif "annulé" not in message.lower():
            messagebox.showerror("Erreur de téléchargement", message, parent=self.true_root_window)

    def __del__(self):
        self.stop_polling()