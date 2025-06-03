import os
import customtkinter as ctk
from tkinter import messagebox, simpledialog  #
import datetime  #
# Assurez-vous que toutes les constantes de statut nécessaires sont importées
from config.settings import (  #
    REMBOURSEMENTS_JSON_FILE, STATUT_CREEE,
    STATUT_REFUSEE_CONSTAT_TP, STATUT_ANNULEE,
    STATUT_PAIEMENT_EFFECTUE, STATUT_TROP_PERCU_CONSTATE,
    STATUT_VALIDEE, STATUT_REFUSEE_VALIDATION_CORRECTION_MLUPO
)
from models import user_model  #

POLLING_INTERVAL_MS = 10000  #

# Définition des couleurs (inchangées par rapport à la réponse précédente)
COULEUR_ACTIVE_POUR_UTILISATEUR = "#1E4D2B"  #
COULEUR_VERROUILLEE_PAR_AUTRE_ET_ACTIVE = "#504030"  #
COULEUR_VERROUILLEE_PAR_AUTRE_INFO = "orange"  #
COULEUR_VERROUILLEE_PAR_SOI = "green"  #
COULEUR_DEMANDE_TERMINEE = "#2E4374"  #
COULEUR_DEMANDE_ANNULEE = "#6A040F"  #
COULEUR_BORDURE_ACTIVE = "#38761D"  #
COULEUR_BORDURE_VERROUILLEE_AUTRE = "orange"  #
COULEUR_BORDURE_TERMINEE = "#4A55A2"  #
COULEUR_BORDURE_ANNULEE = "#9D0208"  #


class MainView(ctk.CTkFrame):
    def __init__(self, master, nom_utilisateur, on_logout_callback, remboursement_controller_factory):  #
        super().__init__(master, corner_radius=0, fg_color="transparent")  #
        self.master = master  #
        self.nom_utilisateur = nom_utilisateur  #
        self.on_logout = on_logout_callback  #
        self.remboursement_controller = remboursement_controller_factory(self.nom_utilisateur)  #

        self._last_known_remboursements_mtime = 0  #
        self._polling_job_id = None  #
        self.user_roles = []  #
        self._fetch_user_roles()  #

        self.pack(fill="both", expand=True)  #
        self.main_content_frame = ctk.CTkFrame(self, corner_radius=10)  #
        self.main_content_frame.pack(pady=20, padx=20, fill="both", expand=True)  #

        self.creer_widgets_barre_superieure_et_titre()  #
        self.creer_section_actions_et_rafraichissement()  #
        self._creer_barre_recherche()  #
        self.creer_conteneur_liste_demandes()  #
        self.creer_legende_couleurs()  #

        self.afficher_liste_demandes()  #
        self.start_polling()  #

    def _fetch_user_roles(self):  #
        user_info = user_model.obtenir_info_utilisateur(self.nom_utilisateur)  #
        if user_info:  #
            self.user_roles = user_info.get("roles", [])  #
        else:  #
            self.user_roles = []  #

    def est_admin(self) -> bool:  #
        return "admin" in self.user_roles  #

    def peut_creer_demande(self) -> bool:  #
        return "demandeur" in self.user_roles  #

    def est_comptable_tresorerie(self) -> bool:  #
        return "comptable_tresorerie" in self.user_roles  #

    def est_validateur_chef(self) -> bool:  #
        return "validateur_chef" in self.user_roles

    def creer_widgets_barre_superieure_et_titre(self):  #
        top_bar = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")  #
        top_bar.pack(fill="x", padx=10, pady=(10, 5), anchor="n")  #

        roles_str = f" (Rôles: {', '.join(self.user_roles)})" if self.user_roles else ""  #
        label_accueil = ctk.CTkLabel(top_bar,
                                     text=f"Utilisateur connecté : {self.nom_utilisateur}{roles_str}",  #
                                     font=ctk.CTkFont(size=12))  #
        label_accueil.pack(side="left", padx=5)  #

        bouton_deconnexion = ctk.CTkButton(top_bar, text="Déconnexion", command=self.on_logout, width=120)  #
        bouton_deconnexion.pack(side="right", padx=5)  #

        label_titre_principal = ctk.CTkLabel(self.main_content_frame, text="Tableau de Bord - Remboursements",
                                             font=ctk.CTkFont(size=24, weight="bold"))  #
        label_titre_principal.pack(pady=(10, 10), anchor="n")  #

    def creer_section_actions_et_rafraichissement(self):  #
        actions_bar_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")  #
        actions_bar_frame.pack(pady=(0, 5), padx=10, fill="x", anchor="n")  #

        if self.peut_creer_demande():  #
            bouton_nouvelle_demande = ctk.CTkButton(actions_bar_frame, text="Nouvelle Demande",
                                                    command=self._ouvrir_fenetre_creation_demande)  #
            bouton_nouvelle_demande.pack(side="left", pady=5, padx=(0, 10))  #

        bouton_rafraichir = ctk.CTkButton(actions_bar_frame, text="Rafraîchir Liste",
                                          command=self.afficher_liste_demandes, width=150)  #
        bouton_rafraichir.pack(side="left", pady=5, padx=10)  #

        if self.est_admin():  #
            pass  #

    def _creer_barre_recherche(self):  #
        search_bar_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")  #
        search_bar_frame.pack(fill="x", padx=10, pady=(5, 5))  #

        search_label = ctk.CTkLabel(search_bar_frame, text="Rechercher (Nom, Prénom, Réf.):",
                                    font=ctk.CTkFont(size=12))  #
        search_label.pack(side="left", padx=(0, 5))  #

        self.search_var = ctk.StringVar()  #
        self.search_var.trace_add("write", self._on_search_change)  #
        self.search_entry = ctk.CTkEntry(search_bar_frame, textvariable=self.search_var, width=300)  #
        self.search_entry.pack(side="left", padx=(0, 5), fill="x", expand=True)  #

        clear_button = ctk.CTkButton(search_bar_frame, text="X", width=30, command=self._clear_search)  #
        clear_button.pack(side="left", padx=(5, 0))  #

    def _clear_search(self, event=None):  #
        self.search_var.set("")  #

    def _on_search_change(self, *args):  #
        self.afficher_liste_demandes()  #

    def creer_conteneur_liste_demandes(self):  #
        self.scrollable_frame_demandes = ctk.CTkScrollableFrame(self.main_content_frame,
                                                                label_text="Liste des Demandes de Remboursement")  #
        self.scrollable_frame_demandes.pack(pady=(5, 5), padx=10, expand=True, fill="both")  #
        self.scrollable_frame_demandes.grid_columnconfigure(0, weight=1)  #

    def creer_legende_couleurs(self):  #
        legende_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")  #
        legende_frame.pack(fill="x", padx=10, pady=(5, 10), anchor="s")  #

        ctk.CTkLabel(legende_frame, text="Légende:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 10))  #

        legend_items = [  #
            ("Action Requise par Vous", COULEUR_ACTIVE_POUR_UTILISATEUR),  #
            ("Demande Terminée", COULEUR_DEMANDE_TERMINEE),  #
            ("Demande Annulée", COULEUR_DEMANDE_ANNULEE),  #
            ("Verrouillée (Autre)", COULEUR_VERROUILLEE_PAR_AUTRE_ET_ACTIVE)
        ]
        for texte, couleur_fond in legend_items:  #
            item_legende = ctk.CTkFrame(legende_frame, fg_color="transparent")  #
            item_legende.pack(side="left", padx=5)  #
            ctk.CTkFrame(item_legende, width=15, height=15, fg_color=couleur_fond, border_width=1).pack(side="left")  #
            ctk.CTkLabel(item_legende, text=texte, font=ctk.CTkFont(size=11)).pack(side="left", padx=3)  #

    def _check_for_data_updates(self):  #
        """Vérifie si le fichier JSON des remboursements a été modifié."""
        try:  #
            if os.path.exists(REMBOURSEMENTS_JSON_FILE):  #
                current_mtime = os.path.getmtime(REMBOURSEMENTS_JSON_FILE)  #
                if self._last_known_remboursements_mtime == 0:  #
                    self._last_known_remboursements_mtime = current_mtime  #
                elif current_mtime > self._last_known_remboursements_mtime:  #
                    print(
                        f"{datetime.datetime.now()}: Détection de modifications dans les données de remboursement, rafraîchissement...")  #
                    self._last_known_remboursements_mtime = current_mtime  #
                    self.afficher_liste_demandes()  #
            else:  #
                if self._last_known_remboursements_mtime != 0:  #
                    print(
                        f"{datetime.datetime.now()}: Fichier remboursements.json non trouvé, réinitialisation du suivi.")  #
                    self.afficher_liste_demandes()  #
                self._last_known_remboursements_mtime = 0  #
        except Exception as e:  #
            print(f"Erreur lors du polling des données: {e}")  #

        if self.winfo_exists():  #
            self._polling_job_id = self.after(POLLING_INTERVAL_MS, self._check_for_data_updates)  #

    def start_polling(self):  #
        if self._polling_job_id:  #
            self.after_cancel(self._polling_job_id)  #
        if os.path.exists(REMBOURSEMENTS_JSON_FILE):  #
            self._last_known_remboursements_mtime = os.path.getmtime(REMBOURSEMENTS_JSON_FILE)  #
        else:  #
            self._last_known_remboursements_mtime = 0  #

        self._check_for_data_updates()  #

    def stop_polling(self):  #
        if self._polling_job_id:  #
            self.after_cancel(self._polling_job_id)  #
            self._polling_job_id = None  #

    def _build_demande_item_widgets(self, parent_frame, demande_data):  #
        """Construit et retourne le frame d'un item de demande."""
        is_active_for_user = False  #
        current_status = demande_data.get("statut")  #
        cree_par_user = demande_data.get("cree_par")  #
        locked_by = demande_data.get("locked_by")  #

        item_bg_color = None  #
        border_color = "gray40"  #
        border_width = 1  #

        # Déterminer si la demande est active pour l'utilisateur actuel
        if self.est_comptable_tresorerie() and current_status == STATUT_CREEE:  #
            is_active_for_user = True  #
        elif (
                self.nom_utilisateur == cree_par_user or self.est_admin()) and current_status == STATUT_REFUSEE_CONSTAT_TP:  #
            is_active_for_user = True  #
        elif (self.est_validateur_chef() or self.est_admin()) and current_status == STATUT_TROP_PERCU_CONSTATE:
            is_active_for_user = True
        # Ajouter d'autres conditions pour les étapes futures (p.diop)

        # Priorité des couleurs de fond/bordure
        if current_status == STATUT_ANNULEE:  #
            item_bg_color = COULEUR_DEMANDE_ANNULEE  #
            border_color = COULEUR_BORDURE_ANNULEE  #
            border_width = 2  #
        elif current_status == STATUT_PAIEMENT_EFFECTUE:  #
            item_bg_color = COULEUR_DEMANDE_TERMINEE  #
            border_color = COULEUR_BORDURE_TERMINEE  #
            border_width = 2  #
        elif is_active_for_user:  #
            if locked_by and locked_by != self.nom_utilisateur:  #
                item_bg_color = COULEUR_VERROUILLEE_PAR_AUTRE_ET_ACTIVE  #
                border_color = COULEUR_BORDURE_VERROUILLEE_AUTRE  #
            else:  #
                item_bg_color = COULEUR_ACTIVE_POUR_UTILISATEUR  #
                border_color = COULEUR_BORDURE_ACTIVE  #
            border_width = 2  #

        item_frame = ctk.CTkFrame(parent_frame, border_width=border_width,
                                  corner_radius=5, fg_color=item_bg_color,
                                  border_color=border_color)  #

        item_frame.grid_columnconfigure(0, weight=2, minsize=280)  #
        item_frame.grid_columnconfigure(1, weight=3, minsize=300)  #
        item_frame.grid_columnconfigure(2, weight=0, minsize=140)  #

        basic_info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")  #
        basic_info_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=(5, 5))  #
        basic_info_frame.grid_columnconfigure(0, weight=0, minsize=100)  #
        basic_info_frame.grid_columnconfigure(1, weight=1)  #

        row_idx_info = 0  #
        common_pady_info = (1, 1)  #
        common_padx_info = (5, 2)  #
        label_font_info = ctk.CTkFont(weight="bold", size=12)  #
        value_font_info = ctk.CTkFont(size=12)  #

        labels_ref = {}  #

        def add_basic_info_row(label_text, value_text, key_name=None, text_color=None):  #
            nonlocal row_idx_info  #
            ctk.CTkLabel(basic_info_frame, text=label_text, font=label_font_info, anchor="w").grid(row=row_idx_info,
                                                                                                   column=0,
                                                                                                   sticky="nw",
                                                                                                   padx=common_padx_info,
                                                                                                   pady=common_pady_info)  #
            val_label = ctk.CTkLabel(basic_info_frame, text=value_text, font=value_font_info, anchor="w",
                                     justify="left", wraplength=0, text_color=text_color)  #
            val_label.grid(row=row_idx_info, column=1, sticky="ew", padx=common_padx_info, pady=common_pady_info)  #
            if key_name: labels_ref[key_name] = val_label  #
            row_idx_info += 1  #

        add_basic_info_row("Patient:", f"{demande_data.get('nom', 'N/A')} {demande_data.get('prenom', 'N/A')}")  #
        add_basic_info_row("Réf. Facture:", demande_data.get('reference_facture', 'N/A'))  #
        add_basic_info_row("Montant:", f"{demande_data.get('montant_demande', 0.0):.2f} €")  #

        date_creation_iso = demande_data.get('date_creation', '')  #
        date_creation_formatee = "N/A"  #
        if date_creation_iso:  #
            try:
                date_creation_obj = datetime.datetime.fromisoformat(
                    date_creation_iso); date_creation_formatee = date_creation_obj.strftime("%d/%m/%Y %H:%M")  #
            except ValueError:
                date_creation_formatee = "Date invalide"  #
        add_basic_info_row("Créée le:", date_creation_formatee)  #

        add_basic_info_row("Modifiée par:", demande_data.get('derniere_modification_par', 'N/A'),
                           key_name="modifie_par")  #
        add_basic_info_row("Statut Actuel:", demande_data.get('statut', 'Non défini'), key_name="statut")  #

        if locked_by:  #
            lock_text = f"{locked_by}" + (" (vous)" if locked_by == self.nom_utilisateur else "")  #
            add_basic_info_row("Verrouillée par:", lock_text, key_name="verrou_par",
                               text_color=COULEUR_VERROUILLEE_PAR_AUTRE_INFO if locked_by != self.nom_utilisateur else COULEUR_VERROUILLEE_PAR_SOI)  #

        historique_frame = ctk.CTkFrame(item_frame, fg_color="transparent")  #
        historique_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=(5, 5))  #

        ctk.CTkLabel(historique_frame, text="Historique/Commentaires:", font=label_font_info).pack(anchor="w",
                                                                                                   padx=common_padx_info,
                                                                                                   pady=(0, 2))  #

        hist_text_box = ctk.CTkTextbox(historique_frame, height=100, fg_color="gray20", border_width=1,
                                       activate_scrollbars=True)  #
        hist_text_box.pack(fill="both", expand=True, padx=common_padx_info, pady=(0, common_pady_info[1]))  #
        hist_text_box.configure(state="disabled")  #
        labels_ref["historique_box"] = hist_text_box  #

        historique = demande_data.get('historique_statuts', [])  #
        if historique:  #
            hist_text_box.configure(state="normal")  #
            hist_text_box.delete("1.0", "end")  #
            for entree_hist in reversed(historique):  #
                date_hist_iso = entree_hist.get('date', '')  #
                date_hist_formatee = "N/A"  #
                if date_hist_iso:  #
                    try:
                        date_hist_obj = datetime.datetime.fromisoformat(
                            date_hist_iso); date_hist_formatee = date_hist_obj.strftime("%d/%m/%Y %H:%M")  #
                    except ValueError:
                        date_hist_formatee = "Date invalide"  #
                par_hist = entree_hist.get('par', 'Système')  #
                statut_hist = entree_hist.get('statut', '')  #
                commentaire_hist = entree_hist.get('commentaire', '').strip()  #
                hist_text_box.insert("end", f"{date_hist_formatee} - {par_hist}:\n")  #
                current_demande_statut = demande_data.get('statut')  #
                if statut_hist and (
                        statut_hist != current_demande_statut or len(historique) == 1 or entree_hist == historique[
                    0]):  #
                    hist_text_box.insert("end", f"  Statut: {statut_hist}\n")  #
                if commentaire_hist: hist_text_box.insert("end", f"  Commentaire: {commentaire_hist}\n")  #
                hist_text_box.insert("end", "----\n")  #
            hist_text_box.configure(state="disabled")  #
        else:  #
            hist_text_box.configure(state="normal");
            hist_text_box.delete("1.0", "end");
            hist_text_box.insert("end", "Aucun historique.");
            hist_text_box.configure(state="disabled")  #

        action_buttons_frame = ctk.CTkFrame(item_frame, fg_color="transparent")  #
        action_buttons_frame.grid(row=0, column=2, sticky="ne", padx=(5, 10), pady=(5, 5))  #
        labels_ref["action_buttons_frame"] = action_buttons_frame  #

        for widget in action_buttons_frame.winfo_children(): widget.destroy()  #

        btn_width_action = 120  #
        btn_pady_action = (3, 3)  #

        path_facture = demande_data.get("chemin_abs_facture")  #
        path_rib = demande_data.get("chemin_abs_rib")  #
        facture_presente_et_valide = path_facture and os.path.exists(path_facture)  #
        rib_present_et_valide = path_rib and os.path.exists(path_rib)  #

        if facture_presente_et_valide:  #
            ctk.CTkButton(action_buttons_frame, text="Voir Facture", width=btn_width_action,
                          command=lambda p=path_facture: self._action_voir_pj(p)).pack(pady=btn_pady_action, padx=2,
                                                                                       fill="x")  #
            ctk.CTkButton(action_buttons_frame, text="DL Facture", width=btn_width_action,
                          command=lambda p=path_facture: self._action_telecharger_pj(p)).pack(pady=btn_pady_action,
                                                                                              padx=2, fill="x")  #
        else:
            ctk.CTkLabel(action_buttons_frame, text="Facture N/A", font=value_font_info, anchor="center",
                         height=50).pack(pady=btn_pady_action, padx=2, fill="x")  #

        # Afficher les captures de trop-perçu si elles existent
        chemins_trop_percu = demande_data.get("chemins_abs_trop_percu", [])
        if chemins_trop_percu:
            if facture_presente_et_valide:  # Ajouter un séparateur si la facture est là
                ctk.CTkFrame(action_buttons_frame, height=2, fg_color="gray50").pack(fill="x", pady=4, padx=15)
            ctk.CTkLabel(action_buttons_frame, text="Preuves TP:", font=label_font_info).pack(anchor="w", pady=(5, 0))
            for idx, p_tp in enumerate(chemins_trop_percu):
                if os.path.exists(p_tp):
                    ctk.CTkButton(action_buttons_frame, text=f"Voir Preuve TP {idx + 1}", width=btn_width_action,
                                  command=lambda p=p_tp: self._action_voir_pj(p)).pack(pady=btn_pady_action, padx=2,
                                                                                       fill="x")

        if rib_present_et_valide:  #
            if facture_presente_et_valide or chemins_trop_percu:  # Séparateur si qqc avant
                ctk.CTkFrame(action_buttons_frame, height=2, fg_color="gray50").pack(fill="x", pady=8, padx=15)  #
            ctk.CTkButton(action_buttons_frame, text="Voir RIB", width=btn_width_action,
                          command=lambda p=path_rib: self._action_voir_pj(p)).pack(pady=btn_pady_action, padx=2,
                                                                                   fill="x")  #
            ctk.CTkButton(action_buttons_frame, text="DL RIB", width=btn_width_action,
                          command=lambda p=path_rib: self._action_telecharger_pj(p)).pack(pady=btn_pady_action, padx=2,
                                                                                          fill="x")  #
        elif not (facture_presente_et_valide or chemins_trop_percu):  # Si ni facture ni preuve TP, afficher RIB N/A
            ctk.CTkLabel(action_buttons_frame, text="RIB N/A", font=value_font_info, anchor="center", height=50).pack(
                pady=btn_pady_action, padx=2, fill="x")  #

        id_demande = demande_data.get("id_demande");
        ref_dossier = demande_data.get("reference_facture_dossier");
        statut_actuel = demande_data.get("statut")  #
        is_locked_by_other = locked_by and locked_by != self.nom_utilisateur  #

        # Boutons de workflow
        action_effectuee_sur_cet_item = False  # Pour éviter multiples boutons d'action principaux pour un user

        if self.est_comptable_tresorerie() and statut_actuel == STATUT_CREEE:  #
            ctk.CTkButton(action_buttons_frame, text="Accepter (Constat TP)", width=btn_width_action, fg_color="green",
                          hover_color="darkgreen", state="disabled" if is_locked_by_other else "normal",
                          command=lambda d_id=id_demande, r_d=ref_dossier: self._action_mlupo_accepter(d_id, r_d)).pack(
                pady=(10, btn_pady_action[1]), padx=2, fill="x")  #
            ctk.CTkButton(action_buttons_frame, text="Refuser (Constat TP)", width=btn_width_action, fg_color="orange",
                          hover_color="darkorange", state="disabled" if is_locked_by_other else "normal",
                          command=lambda d_id=id_demande, r_d=ref_dossier: self._action_mlupo_refuser(d_id, r_d)).pack(
                pady=btn_pady_action, padx=2, fill="x")  #
            action_effectuee_sur_cet_item = True

        if (
                self.est_validateur_chef() or self.est_admin()) and statut_actuel == STATUT_TROP_PERCU_CONSTATE and not action_effectuee_sur_cet_item:
            ctk.CTkButton(action_buttons_frame, text="Valider Demande", width=btn_width_action,
                          fg_color="blue", hover_color="darkblue",
                          state="disabled" if is_locked_by_other else "normal",
                          command=lambda d_id=id_demande, r_d=ref_dossier: self._action_jdurousset_valider(d_id, r_d)
                          ).pack(pady=(10, btn_pady_action[1]), padx=2, fill="x")
            ctk.CTkButton(action_buttons_frame, text="Refuser Demande", width=btn_width_action,
                          fg_color="orange", hover_color="darkorange",
                          state="disabled" if is_locked_by_other else "normal",
                          command=lambda d_id=id_demande, r_d=ref_dossier: self._action_jdurousset_refuser(d_id, r_d)
                          ).pack(pady=btn_pady_action, padx=2, fill="x")
            action_effectuee_sur_cet_item = True

        if (self.nom_utilisateur == demande_data.get(
                "cree_par") or self.est_admin()) and statut_actuel == STATUT_REFUSEE_CONSTAT_TP and not action_effectuee_sur_cet_item:  #
            ctk.CTkButton(action_buttons_frame, text="Annuler Demande", width=btn_width_action, fg_color="#D32F2F",
                          hover_color="#B71C1C", state="disabled" if is_locked_by_other else "normal",
                          command=lambda d_id=id_demande, r_d=ref_dossier: self._action_pneri_annuler(d_id, r_d)).pack(
                pady=(10, btn_pady_action[1]), padx=2, fill="x")  #
            action_effectuee_sur_cet_item = True

        if self.est_admin():  #
            delete_btn_state = "disabled" if is_locked_by_other else "normal"  #
            ctk.CTkButton(action_buttons_frame, text="Supprimer (Admin)", width=btn_width_action, fg_color="red",
                          hover_color="darkred", state=delete_btn_state,
                          command=lambda demande_id=id_demande: self._action_supprimer_demande(demande_id)).pack(
                pady=(15, btn_pady_action[1]), padx=2, fill="x")  #

        return item_frame, labels_ref

    def afficher_liste_demandes(self, source_is_polling=False):  #
        self._fetch_user_roles()  #

        if hasattr(self, 'no_demandes_label_widget') and self.no_demandes_label_widget:  #
            self.no_demandes_label_widget.destroy()  #
            self.no_demandes_label_widget = None  #

        for widget in self.scrollable_frame_demandes.winfo_children():  #
            widget.destroy()  #

        toutes_les_demandes_data = self.remboursement_controller.get_toutes_les_demandes_formatees()  #
        terme_recherche = self.search_var.get().lower().strip() if hasattr(self, 'search_var') else ""  #
        demandes_a_afficher_data = []  #
        if not terme_recherche:  #
            demandes_a_afficher_data = toutes_les_demandes_data  #
        else:  #
            for d_data in toutes_les_demandes_data:  #
                if (terme_recherche in d_data.get('nom', '').lower() or  #
                        terme_recherche in d_data.get('prenom', '').lower() or  #
                        terme_recherche in d_data.get('reference_facture', '').lower()):  #
                    demandes_a_afficher_data.append(d_data)  #

        if not demandes_a_afficher_data:  #
            message_texte = "Aucune demande de remboursement à afficher."  #
            if terme_recherche:  #
                message_texte = f"Aucune demande ne correspond à '{terme_recherche}'."  #
            self.no_demandes_label_widget = ctk.CTkLabel(self.scrollable_frame_demandes,  #
                                                         text=message_texte,
                                                         font=ctk.CTkFont(size=14))  #
            self.no_demandes_label_widget.pack(pady=20, padx=20)  #
        else:  #
            for demande_data in demandes_a_afficher_data:  #
                item_frame, _ = self._build_demande_item_widgets(self.scrollable_frame_demandes, demande_data)  #
                item_frame.pack(fill="x", pady=4, padx=5)  #

    def _action_mlupo_accepter(self, id_demande: str, ref_dossier: str):  #
        if not self.remboursement_controller.tenter_verrouillage_demande(ref_dossier):  #
            locked_by = "un autre utilisateur"  #
            all_demandes = self.remboursement_controller.get_toutes_les_demandes_formatees()  #
            demande_info_live = next((d for d in all_demandes if d["id_demande"] == id_demande), None)  #
            if demande_info_live: locked_by = demande_info_live.get("locked_by", locked_by)  #
            messagebox.showwarning("Demande Verrouillée", f"Demande verrouillée par {locked_by}.", parent=self)  #
            return  #

        dialog = ctk.CTkToplevel(self)  #
        dialog.title(f"Accepter Constat TP - Demande {id_demande[:8]}")  #
        dialog.geometry("500x450")  #
        dialog.transient(self);
        dialog.grab_set()  #

        chemin_pj_var = ctk.StringVar(value="Aucune PJ sélectionnée (Obligatoire)")  #
        current_pj_path = None  #

        def _sel_pj():  #
            nonlocal current_pj_path  #
            path = self.remboursement_controller.selectionner_fichier_piece_jointe("Sélectionner Preuve Trop-Perçu")  #
            if path:  #
                chemin_pj_var.set(os.path.basename(path))  #
                current_pj_path = path  #

        ctk.CTkLabel(dialog, text="Preuve de Trop-Perçu (Image/PDF):").pack(pady=(10, 2))  #
        ctk.CTkButton(dialog, text="Choisir Fichier...", command=_sel_pj).pack(pady=(0, 5))  #
        ctk.CTkLabel(dialog, textvariable=chemin_pj_var).pack()  #

        ctk.CTkLabel(dialog, text="Commentaire (Obligatoire):").pack(pady=(10, 2))  #
        commentaire_box = ctk.CTkTextbox(dialog, height=100, width=450);
        commentaire_box.pack(pady=5, padx=10, fill="x", expand=True);
        commentaire_box.focus()  #

        def _submit():  #
            commentaire = commentaire_box.get("1.0", "end-1c").strip()  #
            if not current_pj_path:  #
                messagebox.showerror("Erreur", "La pièce jointe de preuve est obligatoire.", parent=dialog);
                return  #
            if not commentaire:  #
                messagebox.showerror("Erreur", "Le commentaire est obligatoire.", parent=dialog);
                return  #

            succes, msg = self.remboursement_controller.mlupo_accepter_constat(id_demande, ref_dossier, current_pj_path,
                                                                               commentaire)  #
            if succes:  #
                messagebox.showinfo("Succès", msg, parent=self)  #
                dialog.destroy()  #
                self.afficher_liste_demandes()  #
            else:  #
                messagebox.showerror("Erreur", msg, parent=dialog)  #

        def on_dialog_close():  #
            print(f"Fermeture Accepter TP pour {id_demande}, libération verrou.")  #
            self.remboursement_controller.liberer_verrou_demande(ref_dossier)  #
            dialog.destroy()  #

        dialog.protocol("WM_DELETE_WINDOW", on_dialog_close)  #
        ctk.CTkButton(dialog, text="Valider et Soumettre à J. Durousset", command=_submit).pack(pady=10)  #

    def _action_mlupo_refuser(self, id_demande: str, ref_dossier: str):  #
        if not self.remboursement_controller.tenter_verrouillage_demande(ref_dossier):  #
            locked_by = "un autre utilisateur"  #
            all_demandes = self.remboursement_controller.get_toutes_les_demandes_formatees()  #
            demande_info_live = next((d for d in all_demandes if d["id_demande"] == id_demande), None)  #
            if demande_info_live: locked_by = demande_info_live.get("locked_by", locked_by)  #
            messagebox.showwarning("Demande Verrouillée", f"Demande verrouillée par {locked_by}.", parent=self);
            return  #

        commentaire = simpledialog.askstring("Refus Constat Trop-Perçu",  #
                                             f"Motif du refus pour la demande {id_demande[:8]}:\n(Ce commentaire sera visible par P. Neri)",
                                             #
                                             parent=self)  #

        if commentaire is not None:  #
            if not commentaire.strip():  #
                messagebox.showerror("Erreur", "Le commentaire de refus est obligatoire.", parent=self)  #
                self.remboursement_controller.liberer_verrou_demande(ref_dossier)  #
                return  #

            succes, msg = self.remboursement_controller.mlupo_refuser_constat(id_demande, ref_dossier, commentaire)  #
            if succes:  #
                messagebox.showinfo("Refus Enregistré", msg, parent=self)  #
                self.afficher_liste_demandes()  #
            else:  #
                messagebox.showerror("Erreur", msg, parent=self)  #

        self.remboursement_controller.liberer_verrou_demande(ref_dossier)  #

    # --- Actions pour j.durousset / b.gonnet ---
    def _action_jdurousset_valider(self, id_demande: str, ref_dossier: str):
        if not self.remboursement_controller.tenter_verrouillage_demande(ref_dossier):
            # (Logique similaire à _action_mlupo_accepter pour message verrou)
            messagebox.showwarning("Demande Verrouillée", "Cette demande est verrouillée.", parent=self);
            return

        commentaire = simpledialog.askstring("Validation Demande",
                                             f"Commentaire pour la validation de la demande {id_demande[:8]} (Optionnel):",
                                             parent=self)

        # Si l'utilisateur clique sur "Annuler" dans la simpledialog, commentaire sera None
        # S'il clique sur OK sans rien écrire, commentaire sera une chaîne vide ""
        # On procède même si le commentaire est vide (optionnel)
        if commentaire is not None:
            succes, msg = self.remboursement_controller.jdurousset_valider_demande(id_demande, ref_dossier,
                                                                                   commentaire.strip() if commentaire else None)
            if succes:
                messagebox.showinfo("Validation Réussie", msg, parent=self)
                self.afficher_liste_demandes()
            else:
                messagebox.showerror("Erreur de Validation", msg, parent=self)

        self.remboursement_controller.liberer_verrou_demande(ref_dossier)

    def _action_jdurousset_refuser(self, id_demande: str, ref_dossier: str):
        if not self.remboursement_controller.tenter_verrouillage_demande(ref_dossier):
            messagebox.showwarning("Demande Verrouillée", "Cette demande est verrouillée.", parent=self);
            return

        commentaire = simpledialog.askstring("Refus Validation Demande",
                                             f"Motif du refus de validation pour la demande {id_demande[:8]}:\n(Ce commentaire sera visible par M. Lupo)",
                                             parent=self)
        if commentaire is not None:
            if not commentaire.strip():
                messagebox.showerror("Erreur", "Un commentaire est obligatoire pour refuser la validation.",
                                     parent=self)
                self.remboursement_controller.liberer_verrou_demande(ref_dossier)
                return

            succes, msg = self.remboursement_controller.jdurousset_refuser_demande(id_demande, ref_dossier, commentaire)
            if succes:
                messagebox.showinfo("Refus Enregistré", msg, parent=self)
                self.afficher_liste_demandes()
            else:
                messagebox.showerror("Erreur de Refus", msg, parent=self)

        self.remboursement_controller.liberer_verrou_demande(ref_dossier)

    def _action_pneri_annuler(self, id_demande: str, ref_dossier: str):  #
        if not self.remboursement_controller.tenter_verrouillage_demande(ref_dossier):  #
            locked_by = "un autre utilisateur"  #
            all_demandes = self.remboursement_controller.get_toutes_les_demandes_formatees()  #
            demande_info_live = next((d for d in all_demandes if d["id_demande"] == id_demande), None)  #
            if demande_info_live: locked_by = demande_info_live.get("locked_by", locked_by)  #
            messagebox.showwarning("Demande Verrouillée", f"Demande verrouillée par {locked_by}.", parent=self);
            return  #

        commentaire = simpledialog.askstring("Annulation de Demande",  #
                                             f"Commentaire d'annulation pour la demande {id_demande[:8]}: \n(Requis pour tracer l'annulation)",
                                             #
                                             parent=self)  #
        if commentaire is not None:  #
            if not commentaire.strip():  #
                messagebox.showerror("Erreur", "Le commentaire d'annulation est obligatoire.", parent=self)  #
                self.remboursement_controller.liberer_verrou_demande(ref_dossier)  #
                return  #

            succes, msg = self.remboursement_controller.pneri_annuler_demande(id_demande, ref_dossier, commentaire)  #
            if succes:  #
                messagebox.showinfo("Demande Annulée", msg, parent=self)  #
                self.afficher_liste_demandes()  #
            else:  #
                messagebox.showerror("Erreur", msg, parent=self)  #
        self.remboursement_controller.liberer_verrou_demande(ref_dossier)  #

    def _action_supprimer_demande(self, id_demande: str):  #
        if not id_demande:  #
            messagebox.showerror("Erreur", "ID de demande non valide pour la suppression.", parent=self)  #
            return  #

        demande_info = next((d for d in self.remboursement_controller.get_toutes_les_demandes_formatees() if
                             d.get("id_demande") == id_demande), None)  #
        if demande_info:  #
            locked_by = demande_info.get("locked_by")  #
            if locked_by and locked_by != self.nom_utilisateur:  #
                messagebox.showwarning("Suppression impossible", f"Cette demande est verrouillée par {locked_by}.",
                                       parent=self)  #
                return  #

        confirmation = messagebox.askyesno("Confirmation de suppression",  #
                                           f"Êtes-vous sûr de vouloir supprimer la demande ID: {id_demande}?\n"  #
                                           "Cette action est irréversible et supprimera aussi les fichiers associés.",
                                           #
                                           icon=messagebox.WARNING, parent=self)  #
        if confirmation:  #
            succes, message = self.remboursement_controller.supprimer_demande(id_demande)  #
            if succes:  #
                messagebox.showinfo("Suppression réussie", message, parent=self)  #
                self.afficher_liste_demandes()  #
            else:  #
                messagebox.showerror("Erreur de suppression", message, parent=self)  #

    def _action_voir_pj(self, chemin_pj):  #
        if not chemin_pj:  #
            messagebox.showwarning("Avertissement", "Aucun chemin de fichier spécifié pour la visualisation.",
                                   parent=self)  #
            return  #
        succes, message = self.remboursement_controller.ouvrir_piece_jointe_systeme(chemin_pj)  #
        if not succes:  #
            messagebox.showerror("Erreur d'ouverture", message, parent=self)  #

    def _action_telecharger_pj(self, chemin_pj):  #
        if not chemin_pj:  #
            messagebox.showwarning("Avertissement", "Aucun chemin de fichier source spécifié pour le téléchargement.",
                                   parent=self)  #
            return  #
        succes, message = self.remboursement_controller.telecharger_copie_piece_jointe(chemin_pj)  #
        if succes:  #
            messagebox.showinfo("Téléchargement", message, parent=self)  #
        elif "annulé" not in message.lower():  #
            messagebox.showerror("Erreur de téléchargement", message, parent=self)  #

    def _ouvrir_fenetre_creation_demande(self):  #
        dialog = ctk.CTkToplevel(self.master)  #
        dialog.title("Nouvelle Demande de Remboursement")  #
        dialog.geometry("650x650")  #
        dialog.transient(self.master)  #
        dialog.grab_set()  #

        form_frame = ctk.CTkFrame(dialog)  #
        form_frame.pack(expand=True, fill="both", padx=20, pady=20)  #

        current_row = 0  #
        labels_entries = {  #
            "Nom:": "nom",  #
            "Prénom:": "prenom",  #
            "Référence Facture:": "reference_facture",  #
            "Montant demandé (€):": "montant_demande_()"  #
        }
        self.entries_demande = {}  #

        for label_text, key_name in labels_entries.items():  #
            lbl = ctk.CTkLabel(form_frame, text=label_text)  #
            lbl.grid(row=current_row, column=0, padx=5, pady=8, sticky="w")  #
            entry = ctk.CTkEntry(form_frame, width=350)  #
            entry.grid(row=current_row, column=1, padx=5, pady=8, sticky="ew")  #
            self.entries_demande[key_name] = entry  #
            current_row += 1  #

        lbl_desc = ctk.CTkLabel(form_frame, text="Description/Raison:")  #
        lbl_desc.grid(row=current_row, column=0, padx=5, pady=(8, 0), sticky="nw")  #
        self.textbox_description = ctk.CTkTextbox(form_frame, width=350, height=100)  #
        self.textbox_description.grid(row=current_row, column=1, padx=5, pady=8, sticky="ew")  #
        current_row += 1  #

        form_frame.columnconfigure(1, weight=1)  #

        self.chemin_facture_var = ctk.StringVar(value="Aucun fichier sélectionné (Optionnel)")  #
        self.chemin_rib_var = ctk.StringVar(value="Aucun fichier sélectionné")  #
        self._entry_chemin_facture_complet = None  #
        self._entry_chemin_rib_complet = None  #

        def selectionner_facture():  #
            chemin = self.remboursement_controller.selectionner_fichier_piece_jointe(
                "Sélectionner la Facture PDF (Optionnel)")  #
            if chemin:  #
                self.chemin_facture_var.set(os.path.basename(chemin))  #
                self._entry_chemin_facture_complet = chemin  #
                if chemin.lower().endswith(".pdf"):  #
                    infos_extraites = self.remboursement_controller.extraire_info_facture_pdf(chemin)  #
                    if infos_extraites.get("nom"):  #
                        self.entries_demande["nom"].delete(0, "end")  #
                        self.entries_demande["nom"].insert(0, infos_extraites["nom"])  #
                    if infos_extraites.get("prenom"):  #
                        self.entries_demande["prenom"].delete(0, "end")  #
                        self.entries_demande["prenom"].insert(0, infos_extraites["prenom"])  #
                    if infos_extraites.get("reference"):  #
                        self.entries_demande["reference_facture"].delete(0, "end")  #
                        self.entries_demande["reference_facture"].insert(0, infos_extraites["reference"])  #
            else:  #
                self.chemin_facture_var.set("Aucun fichier sélectionné (Optionnel)")  #
                self._entry_chemin_facture_complet = None  #

        btn_facture = ctk.CTkButton(form_frame, text="Choisir Facture (Optionnel)", command=selectionner_facture)  #
        btn_facture.grid(row=current_row, column=0, padx=5, pady=10, sticky="w")  #
        lbl_facture_sel = ctk.CTkLabel(form_frame, textvariable=self.chemin_facture_var, wraplength=300)  #
        lbl_facture_sel.grid(row=current_row, column=1, padx=5, pady=10, sticky="ew")  #
        current_row += 1  #

        def selectionner_rib():  #
            chemin = self.remboursement_controller.selectionner_fichier_piece_jointe(
                "Sélectionner le RIB (Obligatoire)")  #
            if chemin:  #
                self.chemin_rib_var.set(os.path.basename(chemin))  #
                self._entry_chemin_rib_complet = chemin  #

        btn_rib = ctk.CTkButton(form_frame, text="Choisir RIB (Obligatoire)", command=selectionner_rib)  #
        btn_rib.grid(row=current_row, column=0, padx=5, pady=10, sticky="w")  #
        lbl_rib_sel = ctk.CTkLabel(form_frame, textvariable=self.chemin_rib_var, wraplength=300)  #
        lbl_rib_sel.grid(row=current_row, column=1, padx=5, pady=10, sticky="ew")  #
        current_row += 1  #

        def soumettre_demande():  #
            nom = self.entries_demande["nom"].get()  #
            prenom = self.entries_demande["prenom"].get()  #
            ref = self.entries_demande["reference_facture"].get()  #
            montant_str = self.entries_demande["montant_demande_()"].get()  #
            description = self.textbox_description.get("1.0", "end-1c").strip()  #

            facture_path = getattr(self, '_entry_chemin_facture_complet', None)  #
            rib_path = getattr(self, '_entry_chemin_rib_complet', None)  #

            succes, message = self.remboursement_controller.creer_demande_remboursement(
                nom, prenom, ref, montant_str, facture_path, rib_path, description  #
            )
            if succes:  #
                messagebox.showinfo("Succès", message, parent=dialog)  #
                dialog.destroy()  #
                self.afficher_liste_demandes()  #
            else:  #
                messagebox.showerror("Erreur", message, parent=dialog)  #

        btn_soumettre = ctk.CTkButton(form_frame, text="Enregistrer la Demande", command=soumettre_demande,
                                      height=35)  #
        btn_soumettre.grid(row=current_row, column=0, columnspan=2, pady=25, padx=5)  #

        dialog.after(100, lambda: self.entries_demande["nom"].focus_set())  #

    def __del__(self):  #
        self.stop_polling()  #