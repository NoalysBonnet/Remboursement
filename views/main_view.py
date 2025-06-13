import os
import customtkinter as ctk
from tkinter import messagebox, simpledialog
import datetime
from PIL import Image, ImageDraw, ImageFont

from config.settings import (
    REMBOURSEMENTS_JSON_DIR, STATUT_CREEE,
    STATUT_REFUSEE_CONSTAT_TP, STATUT_ANNULEE,
    STATUT_PAIEMENT_EFFECTUE, STATUT_TROP_PERCU_CONSTATE,
    STATUT_VALIDEE, STATUT_REFUSEE_VALIDATION_CORRECTION_MLUPO,
    PROFILE_PICTURES_DIR
)
from models import user_model
from utils import archive_utils
from views.document_viewer import DocumentViewerWindow
from views.remboursement_item_view import RemboursementItemView
from views.document_history_viewer import DocumentHistoryViewer
from views.admin_user_management_view import AdminUserManagementView
from views.help_view import HelpView
from views.profile_view import ProfileView
from utils.image_utils import create_circular_image
from views.dialogs.comment_dialog import CommentDialog

POLLING_INTERVAL_MS = 5000
COULEUR_ACTIVE_POUR_UTILISATEUR = "#1E4D2B"
COULEUR_DEMANDE_TERMINEE = "#2E4374"
COULEUR_DEMANDE_ANNULEE = "#6A040F"


class MainView(ctk.CTkFrame):
    def __init__(self, master, nom_utilisateur, app_controller, remboursement_controller_factory):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.pack(fill="both", expand=True)

        self.master = master
        self.nom_utilisateur = nom_utilisateur
        self.app_controller = app_controller
        self.auth_controller = app_controller.auth_controller
        self.remboursement_controller = remboursement_controller_factory(self.nom_utilisateur)

        self.pfp_size = 80
        self._polling_job_id = None
        self._last_known_remboursements_mtime = 0
        self.all_demandes_cache = []
        self._is_refreshing = False

        self._fetch_user_data()
        self.initial_theme = self.user_data.get("theme_color", "blue")

        self.current_sort = "Date de création (récent)"
        self.current_filter = self.user_data.get("default_filter", "Toutes les demandes")
        self.include_archives = ctk.BooleanVar(value=False)
        self.search_var = ctk.StringVar()

        self.callbacks = {
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
            'voir_historique_docs': self._action_voir_historique_docs,
            'admin_manual_archive': self._action_admin_manual_archive
        }

        self._creer_widgets()
        self.afficher_liste_demandes(force_reload=True)
        self.start_polling()

    def _fetch_user_data(self):
        self.user_data = user_model.obtenir_info_utilisateur(self.nom_utilisateur)
        self.user_roles = self.user_data.get("roles", []) if self.user_data else []

    def _creer_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        self.user_info_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        self.user_info_frame.pack(side="left", padx=5, pady=2)

        self.pfp_label = ctk.CTkLabel(self.user_info_frame, text="", width=self.pfp_size, height=self.pfp_size)
        self.pfp_label.pack(side="left")
        self.user_name_label = ctk.CTkLabel(self.user_info_frame, text="", font=ctk.CTkFont(size=18, weight="bold"))
        self.user_name_label.pack(side="left", padx=15)
        self._update_user_display()

        right_buttons_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        right_buttons_frame.pack(side="right")
        ctk.CTkButton(right_buttons_frame, text="Mon Profil", command=self._open_profile_view, width=100,
                      fg_color="gray").pack(side="left", padx=5)
        ctk.CTkButton(right_buttons_frame, text="Aide", command=self._open_help_view, width=70).pack(side="left",
                                                                                                     padx=5)
        ctk.CTkButton(right_buttons_frame, text="Déconnexion", command=self.app_controller.on_logout,
                      width=120).pack(
            side="left", padx=(5, 0))

        main_content_frame = ctk.CTkFrame(self)
        main_content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        main_content_frame.grid_columnconfigure(0, weight=1)
        main_content_frame.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(main_content_frame, text="Tableau de Bord - Remboursements",
                     font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, pady=(10, 10), sticky="n")

        actions_bar_frame = ctk.CTkFrame(main_content_frame, fg_color="transparent")
        actions_bar_frame.grid(row=1, column=0, pady=(0, 5), padx=10, sticky="ew")

        if self.peut_creer_demande():
            ctk.CTkButton(actions_bar_frame, text="Nouvelle Demande",
                          command=self._ouvrir_fenetre_creation_demande).pack(side="left", pady=5, padx=(0, 10))

        self.bouton_rafraichir = ctk.CTkButton(actions_bar_frame, text="Rafraîchir (F5)",
                                               command=lambda: self.afficher_liste_demandes(force_reload=True),
                                               width=120)
        self.bouton_rafraichir.pack(side="left", pady=5, padx=10)
        self.notification_badge = ctk.CTkLabel(self.bouton_rafraichir, text="", fg_color="red", corner_radius=8,
                                               width=18, height=18, font=("Arial", 11, "bold"))
        self.winfo_toplevel().bind("<F5>", lambda event: self.afficher_liste_demandes(force_reload=True))

        if self.est_admin():
            ctk.CTkButton(actions_bar_frame, text="Gérer Utilisateurs",
                          command=self._open_admin_user_management_view,
                          fg_color="#555555", hover_color="#444444").pack(side="left", pady=5, padx=10)
            ctk.CTkButton(actions_bar_frame, text="Purger les Archives", command=self._action_admin_purge_archives,
                          fg_color="#9D0208", hover_color="#6A040F").pack(side="left", pady=5, padx=10)

        options_frame = ctk.CTkFrame(actions_bar_frame, fg_color="transparent")
        options_frame.pack(side="right", pady=5)
        ctk.CTkLabel(options_frame, text="Trier par:").pack(side="left", padx=(10, 5))
        sort_options = ["Date de création (récent)", "Date de création (ancien)", "Montant (décroissant)",
                        "Montant (croissant)", "Nom du patient (A-Z)"]
        self.sort_menu = ctk.CTkOptionMenu(options_frame, values=sort_options, command=self._set_sort, width=180)
        self.sort_menu.set(self.current_sort)
        self.sort_menu.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(options_frame, text="Filtrer par:").pack(side="left", padx=(10, 5))
        filter_options = ["Toutes les demandes", "En attente de mon action", "En cours", "Terminées et annulées"]
        self.filter_menu = ctk.CTkOptionMenu(options_frame, values=filter_options, command=self._set_filter,
                                             width=180)
        self.filter_menu.set(self.current_filter)
        self.filter_menu.pack(side="left")

        search_frame_parent = ctk.CTkFrame(main_content_frame, fg_color="transparent")
        search_frame_parent.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        ctk.CTkLabel(search_frame_parent, text="Rechercher (Nom, Prénom, Réf.):",
                     font=ctk.CTkFont(size=12)).pack(
            side="left", padx=(0, 5))
        self.search_entry = ctk.CTkEntry(search_frame_parent, textvariable=self.search_var, width=300)
        self.search_entry.pack(side="left", padx=(0, 5), fill="x", expand=True)
        self.search_var.trace_add("write", lambda name, index, mode: self.afficher_liste_demandes())
        ctk.CTkButton(search_frame_parent, text="X", width=30, command=self._clear_search).pack(side="left",
                                                                                                padx=(5, 0))
        ctk.CTkCheckBox(search_frame_parent, text="Inclure les archives", variable=self.include_archives,
                        command=self._on_archive_toggle).pack(side="left", padx=20)

        self.scrollable_frame_demandes = ctk.CTkScrollableFrame(main_content_frame,
                                                                label_text="Liste des Demandes de Remboursement")
        self.scrollable_frame_demandes.grid(row=3, column=0, pady=(5, 5), padx=10, sticky="nsew")
        self.scrollable_frame_demandes.grid_columnconfigure(0, weight=1)

        legende_frame = ctk.CTkFrame(main_content_frame, fg_color="transparent")
        legende_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=(5, 10))
        ctk.CTkLabel(legende_frame, text="Légende:", font=ctk.CTkFont(weight="bold")).pack(side="left",
                                                                                           padx=(0, 10))
        legend_items = [("Action Requise", COULEUR_ACTIVE_POUR_UTILISATEUR),
                        ("Terminée", COULEUR_DEMANDE_TERMINEE),
                        ("Annulée", COULEUR_DEMANDE_ANNULEE)]
        for texte, couleur in legend_items:
            item = ctk.CTkFrame(legende_frame, fg_color="transparent")
            item.pack(side="left", padx=5)
            ctk.CTkFrame(item, width=15, height=15, fg_color=couleur, border_width=1).pack(side="left")
            ctk.CTkLabel(item, text=texte, font=ctk.CTkFont(size=11)).pack(side="left", padx=3)

    def _update_user_display(self):
        def task():
            self._fetch_user_data()
            pfp_path = self.user_data.get("profile_picture_path")
            pfp_image = None
            if pfp_path and os.path.exists(os.path.join(PROFILE_PICTURES_DIR, pfp_path)):
                pfp_image = create_circular_image(os.path.join(PROFILE_PICTURES_DIR, pfp_path), self.pfp_size)
            return pfp_image

        def on_complete(pfp_image):
            if not pfp_image:
                placeholder = Image.new('RGBA', (self.pfp_size, self.pfp_size), (80, 80, 80, 255))
                draw = ImageDraw.Draw(placeholder)
                try:
                    font = ImageFont.truetype("arial", 45)
                except IOError:
                    font = ImageFont.load_default()
                draw.text((self.pfp_size / 2, self.pfp_size / 2), self.nom_utilisateur[0].upper(), font=font,
                          anchor="mm")
                pfp_image = ctk.CTkImage(light_image=placeholder, dark_image=placeholder,
                                         size=(self.pfp_size, self.pfp_size))
            self.pfp_label.configure(image=pfp_image)
            self.pfp_label.image = pfp_image
            roles_str = f" (Rôles: {', '.join(self.user_roles)})" if self.user_roles else ""
            self.user_name_label.configure(text=f"{self.nom_utilisateur}{roles_str}")

        self.app_controller.run_threaded_task(task, on_complete)

    def _get_refreshed_and_sorted_data(self, force_reload):
        if force_reload:
            self.all_demandes_cache = self.remboursement_controller.get_toutes_les_demandes_formatees(
                self.include_archives.get())
            if os.path.exists(REMBOURSEMENTS_JSON_DIR):
                self._last_known_remboursements_mtime = os.path.getmtime(REMBOURSEMENTS_JSON_DIR)

        search_term = self.search_var.get().lower().strip()
        if search_term:
            demandes_filtrees = [d for d in self.all_demandes_cache if
                                 search_term in d.get('nom', '').lower() or search_term in d.get('prenom',
                                                                                                 '').lower() or search_term in str(
                                     d.get('reference_facture', '')).lower()]
        else:
            demandes_filtrees = self.all_demandes_cache

        if self.current_filter == "En attente de mon action":
            demandes_filtrees = [d for d in demandes_filtrees if self._is_active_for_user(d)]
        elif self.current_filter == "En cours":
            demandes_filtrees = [d for d in demandes_filtrees if
                                 d.get('statut') not in [STATUT_PAIEMENT_EFFECTUE, STATUT_ANNULEE]]
        elif self.current_filter == "Terminées et annulées":
            demandes_filtrees = [d for d in demandes_filtrees if
                                 d.get('statut') in [STATUT_PAIEMENT_EFFECTUE, STATUT_ANNULEE]]

        reverse_sort = self.current_sort in ["Date de création (récent)", "Montant (décroissant)"]

        def get_sort_key(demande):
            sort_field_map = {"Date de création (récent)": "date_creation",
                              "Date de création (ancien)": "date_creation",
                              "Montant (décroissant)": "montant_demande",
                              "Montant (croissant)": "montant_demande", "Nom du patient (A-Z)": "nom"}
            sort_field = sort_field_map.get(self.current_sort, "date_creation")
            value = demande.get(sort_field)
            if isinstance(value, str) and "date" in sort_field:
                try:
                    return datetime.datetime.fromisoformat(value)
                except ValueError:
                    return datetime.datetime.min
            return value if value is not None else (datetime.datetime.min if "date" in sort_field else "")

        return sorted(demandes_filtrees, key=get_sort_key, reverse=reverse_sort)

    def _render_demandes_list(self, demandes_a_afficher):
        for widget in self.scrollable_frame_demandes.winfo_children():
            widget.destroy()

        if not demandes_a_afficher:
            ctk.CTkLabel(self.scrollable_frame_demandes, text="Aucune demande à afficher.",
                         font=ctk.CTkFont(size=14, slant="italic")).pack(pady=20)
        else:
            for demande_data in demandes_a_afficher:
                item_frame = RemboursementItemView(master=self.scrollable_frame_demandes,
                                                   demande_data=demande_data,
                                                   current_user_name=self.nom_utilisateur,
                                                   user_roles=self.user_roles,
                                                   callbacks=self.callbacks)
                item_frame.pack(pady=5, padx=5, fill="x", expand=True)
        self._update_notification_badge()

    def afficher_liste_demandes(self, force_reload=False):
        if self._is_refreshing:
            return
        self._is_refreshing = True

        def task():
            return self._get_refreshed_and_sorted_data(force_reload)

        def on_complete(data):
            self._render_demandes_list(data)
            self._is_refreshing = False

        self.app_controller.run_threaded_task(task, on_complete)

    def _update_notification_badge(self):
        count = sum(1 for d in self.all_demandes_cache if self._is_active_for_user(d))
        if count > 0:
            self.notification_badge.configure(text=str(count))
            self.notification_badge.place(in_=self.bouton_rafraichir, relx=1.0, rely=0.0, anchor="ne")
        else:
            self.notification_badge.place_forget()

    def _is_active_for_user(self, demande):
        current_status = demande.get("statut")
        cree_par_user = demande.get("cree_par")
        if self.est_comptable_tresorerie() and current_status == STATUT_CREEE: return True
        if (
                self.nom_utilisateur == cree_par_user or self.est_admin()) and current_status == STATUT_REFUSEE_CONSTAT_TP: return True
        if (
                self.est_validateur_chef() or self.est_admin()) and current_status == STATUT_TROP_PERCU_CONSTATE: return True
        if (
                self.est_comptable_tresorerie() or self.est_admin()) and current_status == STATUT_REFUSEE_VALIDATION_CORRECTION_MLUPO: return True
        if (self.est_comptable_fournisseur() or self.est_admin()) and current_status == STATUT_VALIDEE: return True
        return False

    def est_admin(self):
        return "admin" in self.user_roles

    def peut_creer_demande(self):
        return "demandeur" in self.user_roles

    def est_comptable_tresorerie(self):
        return "comptable_tresorerie" in self.user_roles

    def est_validateur_chef(self):
        return "validateur_chef" in self.user_roles

    def est_comptable_fournisseur(self):
        return "comptable_fournisseur" in self.user_roles

    def _set_sort(self, sort_choice):
        self.current_sort = sort_choice
        self.afficher_liste_demandes()

    def _set_filter(self, filter_choice):
        self.current_filter = filter_choice
        self.afficher_liste_demandes()

    def _clear_search(self):
        self.search_var.set("")

    def _on_archive_toggle(self):
        self.afficher_liste_demandes(force_reload=True)

    def _open_help_view(self):
        HelpView(self, self.nom_utilisateur, self.user_roles)

    def _open_admin_user_management_view(self):
        AdminUserManagementView(self, self.auth_controller, self.app_controller)

    def stop_polling(self):
        if self._polling_job_id: self.after_cancel(self._polling_job_id)
        self._polling_job_id = None

    def start_polling(self):
        self.stop_polling()
        self._last_known_remboursements_mtime = 0
        self._check_for_data_updates()

    def _check_for_data_updates(self):
        try:
            current_mtime = os.path.getmtime(
                REMBOURSEMENTS_JSON_DIR) if os.path.exists(REMBOURSEMENTS_JSON_DIR) else 0
            if current_mtime != self._last_known_remboursements_mtime:
                self.afficher_liste_demandes(force_reload=True)
        except Exception as e:
            print(f"Erreur lors du polling : {e}")
        finally:
            if self.winfo_exists(): self._polling_job_id = self.after(POLLING_INTERVAL_MS,
                                                                      self._check_for_data_updates)

    def _open_profile_view(self):
        def task():
            return user_model.obtenir_info_utilisateur(self.nom_utilisateur)

        def on_complete(user_data):
            if user_data:
                self.user_data = user_data
                ProfileView(self, self.auth_controller, self.app_controller, user_data,
                            on_save_callback=self._on_profile_saved)

        self.app_controller.run_threaded_task(task, on_complete)

    def _on_profile_saved(self):
        self._update_user_display()
        self.current_filter = self.user_data.get("default_filter", "Toutes les demandes")
        self.filter_menu.set(self.current_filter)
        self.afficher_liste_demandes(force_reload=False)
        new_theme = self.user_data.get("theme_color", "blue")
        if new_theme != self.initial_theme: self.app_controller.request_restart(
            "Le changement de thème nécessite un redémarrage.")

    def _ouvrir_fenetre_creation_demande(self):
        from views.dialogs.creation_demande_dialog import CreationDemandeDialog
        CreationDemandeDialog(self, self.remboursement_controller, self.app_controller)

    def _action_voir_pj(self, demande_id, rel_path):
        def task():
            return self.remboursement_controller.get_viewable_attachment_path(demande_id, rel_path)

        def on_complete(result):
            chemin_pj, temp_dir = result
            if chemin_pj and os.path.exists(chemin_pj):
                DocumentViewerWindow(self, chemin_pj, f"Aperçu - {os.path.basename(rel_path)}",
                                     temp_dir_to_clean=temp_dir)
            else:
                self.app_controller.show_toast(f"Fichier non trouvé : {rel_path}", "error")
                if temp_dir: archive_utils.cleanup_temp_dir(temp_dir)

        self.app_controller.run_threaded_task(task, on_complete)

    def _action_telecharger_pj(self, demande_id, rel_path):
        def task():
            return self.remboursement_controller.get_viewable_attachment_path(demande_id, rel_path)

        def on_complete(result):
            chemin_pj, temp_dir = result
            if not chemin_pj:
                self.app_controller.show_toast(f"Fichier non trouvé ou impossible à extraire : {rel_path}", "error")
                return

            succes, message = self.remboursement_controller.telecharger_copie_piece_jointe(chemin_pj, temp_dir)
            if succes:
                self.app_controller.show_toast(message, 'success')
            elif "annulé" not in message.lower():
                self.app_controller.show_toast(message, 'error')

        self.app_controller.run_threaded_task(task, on_complete)

    def _perform_workflow_action(self, action_task_function):
        if self._is_refreshing:
            return
        self._is_refreshing = True

        def combined_task():
            action_success, action_message = action_task_function()
            if not action_success:
                return {'status': 'error', 'message': action_message}

            refreshed_data = self._get_refreshed_and_sorted_data(force_reload=True)
            return {'status': 'success', 'data': refreshed_data, 'message': action_message}

        def on_complete(result):
            if result['status'] == 'error':
                self.app_controller.show_toast(result['message'], 'error')
            else:
                self.app_controller.show_toast(result['message'], 'success')
                self._render_demandes_list(result['data'])
            self._is_refreshing = False

        self.app_controller.run_threaded_task(combined_task, on_complete)

    def _action_mlupo_accepter(self, id_demande):
        from views.dialogs.acceptation_constat_dialog import AcceptationConstatDialog
        AcceptationConstatDialog(self, self.remboursement_controller, id_demande, self.app_controller)

    def _action_mlupo_refuser(self, id_demande):
        dialog = CommentDialog(self, title="Refus du Constat", prompt="Veuillez indiquer le motif du refus :",
                               is_mandatory=True)
        commentaire = dialog.get_comment()
        if commentaire is not None:
            self._perform_workflow_action(
                lambda: self.remboursement_controller.mlupo_refuser_constat(id_demande, commentaire))

    def _action_jdurousset_valider(self, id_demande):
        dialog = CommentDialog(self, title="Validation de la Demande", prompt="Voulez-vous ajouter un commentaire ?",
                               is_mandatory=False)
        commentaire = dialog.get_comment()
        if commentaire is not None:
            self._perform_workflow_action(
                lambda: self.remboursement_controller.jdurousset_valider_demande(id_demande, commentaire))

    def _action_jdurousset_refuser(self, id_demande):
        dialog = CommentDialog(self, title="Refus de la Demande", prompt="Veuillez indiquer le motif du refus :",
                               is_mandatory=True)
        commentaire = dialog.get_comment()
        if commentaire is not None:
            self._perform_workflow_action(
                lambda: self.remboursement_controller.jdurousset_refuser_demande(id_demande, commentaire))

    def _action_pdiop_confirmer_paiement(self, id_demande):
        dialog = CommentDialog(self, title="Confirmation du Paiement", prompt="Voulez-vous ajouter un commentaire ?",
                               is_mandatory=False)
        commentaire = dialog.get_comment()
        if commentaire is not None:
            self._perform_workflow_action(
                lambda: self.remboursement_controller.pdiop_confirmer_paiement_effectue(id_demande, commentaire))

    def _action_pneri_annuler(self, id_demande):
        dialog = CommentDialog(self, title="Annulation de la Demande",
                               prompt="Veuillez indiquer la raison de l'annulation :", is_mandatory=True)
        commentaire = dialog.get_comment()
        if commentaire is not None:
            self._perform_workflow_action(
                lambda: self.remboursement_controller.pneri_annuler_demande(id_demande, commentaire))

    def _action_pneri_resoumettre(self, id_demande):
        from views.dialogs.resoumission_demande_dialog import ResoumissionDemandeDialog
        ResoumissionDemandeDialog(self, self.remboursement_controller, id_demande, self.app_controller)

    def _action_mlupo_resoumettre_constat(self, id_demande):
        from views.dialogs.resoumission_constat_dialog import ResoumissionConstatDialog
        ResoumissionConstatDialog(self, self.remboursement_controller, id_demande, self.app_controller)

    def _action_supprimer_demande(self, id_demande):
        if messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer la demande {id_demande}?",
                               icon='warning', parent=self):
            self._perform_workflow_action(lambda: self.remboursement_controller.supprimer_demande(id_demande))

    def _action_admin_purge_archives(self):
        age_str = simpledialog.askstring("Purger les Archives",
                                         "Entrez l'âge minimum (en années) des archives à supprimer.", parent=self)
        if age_str:
            try:
                age_en_annees = int(age_str)
                if messagebox.askyesno("Confirmation Purge",
                                       f"Êtes-vous sûr de vouloir purger les archives de plus de {age_en_annees} an(s) ?\nCette action est IRRÉVERSIBLE.",
                                       icon='warning', parent=self):
                    if self._is_refreshing: return
                    self._is_refreshing = True

                    def combined_task():
                        nb_suppr, erreurs = self.remboursement_controller.admin_purge_archives(age_en_annees)
                        msg = f"{nb_suppr} demande(s) ont été purgées."
                        if erreurs: msg += f"\nErreurs : {', '.join(erreurs)}"

                        data = self._get_refreshed_and_sorted_data(force_reload=True)
                        return {'message': msg, 'data': data}

                    def on_complete(result):
                        self.app_controller.show_toast(result['message'], 'info')
                        self._render_demandes_list(result['data'])
                        self._is_refreshing = False

                    self.app_controller.run_threaded_task(combined_task, on_complete)
            except ValueError:
                self.app_controller.show_toast("Veuillez entrer un nombre valide.", "error")

    def _action_voir_historique_docs(self, demande_data):
        DocumentHistoryViewer(self, demande_data=demande_data, callbacks=self.callbacks)

    def _action_admin_manual_archive(self, id_demande: str):
        if messagebox.askyesno("Archivage Manuel",
                               f"Êtes-vous sûr de vouloir archiver manuellement la demande {id_demande} ?",
                               parent=self):
            self._perform_workflow_action(lambda: self.remboursement_controller.admin_manual_archive(id_demande))

    def __del__(self):
        self.stop_polling()