# views/remboursement_item_view.py
import os
import customtkinter as ctk
import datetime
from config.settings import (
    STATUT_CREEE, STATUT_REFUSEE_CONSTAT_TP, STATUT_TROP_PERCU_CONSTATE,
    STATUT_VALIDEE, STATUT_REFUSEE_VALIDATION_CORRECTION_MLUPO,
    STATUT_ANNULEE, STATUT_PAIEMENT_EFFECTUE
)

COULEUR_ACTIVE_POUR_UTILISATEUR = "#1E4D2B"
COULEUR_DEMANDE_TERMINEE = "#2E4374"
COULEUR_DEMANDE_ANNULEE = "#6A040F"
COULEUR_BORDURE_ACTIVE = "#38761D"
COULEUR_BORDURE_TERMINEE = "#4A55A2"
COULEUR_BORDURE_ANNULEE = "#9D0208"
COULEUR_BORDURE_DEFAUT = "gray40"


class RemboursementItemView(ctk.CTkFrame):
    def __init__(self, master, demande_data: dict, current_user_name: str, user_roles: list, callbacks: dict):
        super().__init__(master, border_width=1, corner_radius=5)

        self.demande_data = demande_data
        self.current_user_name = current_user_name
        self.user_roles = user_roles
        self.callbacks = callbacks

        self._setup_item_colors_and_ui()

    def _est_admin(self) -> bool:
        return "admin" in self.user_roles

    def _est_comptable_tresorerie(self) -> bool:
        return "comptable_tresorerie" in self.user_roles

    def _est_validateur_chef(self) -> bool:
        return "validateur_chef" in self.user_roles

    def _est_comptable_fournisseur(self) -> bool:
        return "comptable_fournisseur" in self.user_roles

    def _setup_item_colors_and_ui(self):
        is_active_for_user = False
        current_status = self.demande_data.get("statut")
        cree_par_user = self.demande_data.get("cree_par")

        if self._est_comptable_tresorerie() and current_status == STATUT_CREEE:
            is_active_for_user = True
        elif (
                self.current_user_name == cree_par_user or self._est_admin()) and current_status == STATUT_REFUSEE_CONSTAT_TP:
            is_active_for_user = True
        elif (self._est_validateur_chef() or self._est_admin()) and current_status == STATUT_TROP_PERCU_CONSTATE:
            is_active_for_user = True
        elif (
                self._est_comptable_tresorerie() or self._est_admin()) and current_status == STATUT_REFUSEE_VALIDATION_CORRECTION_MLUPO:
            is_active_for_user = True
        elif (self._est_comptable_fournisseur() or self._est_admin()) and current_status == STATUT_VALIDEE:
            is_active_for_user = True

        item_fg_color_to_set = "transparent"
        border_color_to_set = COULEUR_BORDURE_DEFAUT
        border_width_to_set = 1

        if current_status == STATUT_ANNULEE:
            item_fg_color_to_set = COULEUR_DEMANDE_ANNULEE
            border_color_to_set = COULEUR_BORDURE_ANNULEE
            border_width_to_set = 2
        elif current_status == STATUT_PAIEMENT_EFFECTUE:
            item_fg_color_to_set = COULEUR_DEMANDE_TERMINEE
            border_color_to_set = COULEUR_BORDURE_TERMINEE
            border_width_to_set = 2
        elif is_active_for_user:
            item_fg_color_to_set = COULEUR_ACTIVE_POUR_UTILISATEUR
            border_color_to_set = COULEUR_BORDURE_ACTIVE
            border_width_to_set = 2

        self.configure(border_width=border_width_to_set, fg_color=item_fg_color_to_set,
                       border_color=border_color_to_set)
        self._build_ui_content()

    def _build_ui_content(self):
        content_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        content_frame.pack(fill="both", expand=True, padx=1, pady=1)

        content_frame.grid_columnconfigure(0, weight=2, minsize=280)
        content_frame.grid_columnconfigure(1, weight=3, minsize=300)
        content_frame.grid_columnconfigure(2, weight=0, minsize=140)

        basic_info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        basic_info_frame.grid(row=0, column=0, sticky="nsew", padx=(8, 5), pady=5)
        basic_info_frame.grid_columnconfigure(1, weight=1)

        row_idx_info = 0
        common_pady_info = (2, 2)
        common_padx_info = (5, 2)
        label_font_info = ctk.CTkFont(weight="bold", size=12)
        value_font_info = ctk.CTkFont(size=13)

        def add_basic_info_row(label_text, value_text, text_color=None):
            nonlocal row_idx_info
            ctk.CTkLabel(basic_info_frame, text=label_text, font=label_font_info, anchor="w").grid(row=row_idx_info,
                                                                                                   column=0,
                                                                                                   sticky="nw",
                                                                                                   padx=common_padx_info,
                                                                                                   pady=common_pady_info)
            val_label = ctk.CTkLabel(basic_info_frame, text=value_text, font=value_font_info, anchor="w",
                                     justify="left", wraplength=0, text_color=text_color)
            val_label.grid(row=row_idx_info, column=1, sticky="ew", padx=common_padx_info, pady=common_pady_info)
            row_idx_info += 1

        add_basic_info_row("Patient:",
                           f"{self.demande_data.get('nom', 'N/A')} {self.demande_data.get('prenom', 'N/A')}")
        add_basic_info_row("Réf. Facture:", self.demande_data.get('reference_facture', 'N/A'))
        add_basic_info_row("Montant:", f"{self.demande_data.get('montant_demande', 0.0):.2f} €")

        # --- Logique de date corrigée pour 'date_creation' ---
        date_creation_val = self.demande_data.get('date_creation')
        date_creation_formatee = "N/A"
        if isinstance(date_creation_val, datetime.datetime):
            date_creation_formatee = date_creation_val.strftime("%d/%m/%Y %H:%M")
        elif isinstance(date_creation_val, str) and date_creation_val:
            try:
                date_creation_obj = datetime.datetime.fromisoformat(date_creation_val)
                date_creation_formatee = date_creation_obj.strftime("%d/%m/%Y %H:%M")
            except ValueError:
                date_creation_formatee = "Date invalide"
        add_basic_info_row("Créée le:", date_creation_formatee)

        add_basic_info_row("Modifiée par:", self.demande_data.get('derniere_modification_par', 'N/A'))
        add_basic_info_row("Statut Actuel:", self.demande_data.get('statut', 'Non défini'))

        # --- Logique de date corrigée pour 'date_paiement_effectue' ---
        date_paiement_val = self.demande_data.get('date_paiement_effectue')
        if date_paiement_val:
            date_paiement_formatee = "N/A"
            if isinstance(date_paiement_val, datetime.datetime):
                date_paiement_formatee = date_paiement_val.strftime("%d/%m/%Y %H:%M")
            elif isinstance(date_paiement_val, str):
                try:
                    date_paiement_obj = datetime.datetime.fromisoformat(date_paiement_val)
                    date_paiement_formatee = date_paiement_obj.strftime("%d/%m/%Y %H:%M")
                except ValueError:
                    date_paiement_formatee = "Date invalide"
            add_basic_info_row("Paiement Effectué le:", date_paiement_formatee, text_color="lightgreen")

        historique_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        historique_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 5), pady=5)

        ctk.CTkLabel(historique_frame, text="Historique/Commentaires:", font=label_font_info).pack(anchor="w",
                                                                                                   padx=common_padx_info,
                                                                                                   pady=(0, 2))

        hist_text_box = ctk.CTkTextbox(historique_frame, height=110, fg_color="gray20", border_width=1,
                                       activate_scrollbars=True)
        hist_text_box.pack(fill="both", expand=True, padx=common_padx_info, pady=(0, common_pady_info[1]))
        hist_text_box.configure(state="disabled")

        historique = self.demande_data.get('historique_statuts', [])
        if historique:
            hist_text_box.configure(state="normal")
            hist_text_box.delete("1.0", "end")
            for entree_hist in reversed(historique):
                # --- Logique de date corrigée pour les dates de l'historique ---
                date_hist_val = entree_hist.get('date')
                date_hist_formatee = "N/A"
                if isinstance(date_hist_val, datetime.datetime):
                    date_hist_formatee = date_hist_val.strftime("%d/%m/%Y %H:%M")
                elif isinstance(date_hist_val, str) and date_hist_val:
                    try:
                        date_hist_obj = datetime.datetime.fromisoformat(date_hist_val)
                        date_hist_formatee = date_hist_obj.strftime("%d/%m/%Y %H:%M")
                    except ValueError:
                        date_hist_formatee = "Date invalide"

                par_hist = entree_hist.get('par', 'Système')
                statut_hist = entree_hist.get('statut', '')
                commentaire_hist = entree_hist.get('commentaire', '').strip()
                hist_text_box.insert("end", f"{date_hist_formatee} - {par_hist}:\n")
                current_demande_statut = self.demande_data.get('statut')
                if statut_hist and (
                        statut_hist != current_demande_statut or len(historique) == 1 or entree_hist == historique[
                    0]):
                    hist_text_box.insert("end", f"  Statut: {statut_hist}\n")
                if commentaire_hist: hist_text_box.insert("end", f"  Commentaire: {commentaire_hist}\n")
                hist_text_box.insert("end", "----\n")
            hist_text_box.configure(state="disabled")
        else:
            hist_text_box.configure(state="normal");
            hist_text_box.delete("1.0", "end");
            hist_text_box.insert("end", "Aucun historique.");
            hist_text_box.configure(state="disabled")

        action_buttons_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        action_buttons_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 8), pady=5)

        btn_width_action = 120
        btn_pady_action = (3, 3)
        value_font_info = ctk.CTkFont(size=12)
        label_font_info = ctk.CTkFont(weight="bold", size=12)

        chemins_factures_list = self.demande_data.get("chemins_abs_factures_stockees", [])
        if not isinstance(chemins_factures_list, list): chemins_factures_list = [
            chemins_factures_list] if chemins_factures_list else []

        chemins_rib_list = self.demande_data.get("chemins_abs_rib_stockes", [])
        if not isinstance(chemins_rib_list, list): chemins_rib_list = [chemins_rib_list] if chemins_rib_list else []

        chemins_tp_list = self.demande_data.get("chemins_abs_trop_percu", [])

        if any(len(lst) > 1 for lst in [chemins_factures_list, chemins_rib_list, chemins_tp_list]):
            btn_hist_docs = ctk.CTkButton(action_buttons_frame, text="Historique Docs",
                                          width=btn_width_action, fg_color="gray50",
                                          command=lambda d=self.demande_data: self.callbacks['voir_historique_docs'](d))
            btn_hist_docs.pack(pady=(5, btn_pady_action[1]), padx=2, fill="x")
            ctk.CTkFrame(action_buttons_frame, height=2, fg_color="gray50").pack(fill="x", pady=4, padx=15)

        path_facture = chemins_factures_list[-1] if chemins_factures_list and chemins_factures_list[
            -1] and os.path.exists(chemins_factures_list[-1]) else None
        path_rib = chemins_rib_list[-1] if chemins_rib_list and chemins_rib_list[-1] and os.path.exists(
            chemins_rib_list[-1]) else None
        path_trop_percu = chemins_tp_list[-1] if chemins_tp_list and chemins_tp_list[-1] and os.path.exists(
            chemins_tp_list[-1]) else None

        if path_facture:
            ctk.CTkButton(action_buttons_frame, text="Voir Facture", width=btn_width_action,
                          command=lambda p=path_facture: self.callbacks['voir_pj'](p)).pack(pady=btn_pady_action,
                                                                                            padx=2, fill="x")
            ctk.CTkButton(action_buttons_frame, text="DL Facture", width=btn_width_action,
                          command=lambda p=path_facture: self.callbacks['dl_pj'](p)).pack(pady=btn_pady_action, padx=2,
                                                                                          fill="x")
        else:
            ctk.CTkLabel(action_buttons_frame, text="Facture N/A", font=value_font_info, anchor="center",
                         height=30).pack(pady=btn_pady_action, padx=2, fill="x")

        if path_trop_percu:
            if path_facture:
                ctk.CTkFrame(action_buttons_frame, height=2, fg_color="gray50").pack(fill="x", pady=4, padx=15)
            ctk.CTkLabel(action_buttons_frame, text="Dernière Preuve TP:", font=label_font_info).pack(anchor="w",
                                                                                                      pady=(5, 0))
            ctk.CTkButton(action_buttons_frame, text="Voir Preuve TP", width=btn_width_action,
                          command=lambda p=path_trop_percu: self.callbacks['voir_pj'](p)).pack(pady=btn_pady_action,
                                                                                               padx=2, fill="x")
            ctk.CTkButton(action_buttons_frame, text="DL Preuve TP", width=btn_width_action,
                          command=lambda p=path_trop_percu: self.callbacks['dl_pj'](p)).pack(pady=btn_pady_action,
                                                                                             padx=2, fill="x")

        if path_rib:
            if path_facture or path_trop_percu:
                ctk.CTkFrame(action_buttons_frame, height=2, fg_color="gray50").pack(fill="x", pady=8, padx=15)
            ctk.CTkButton(action_buttons_frame, text="Voir RIB", width=btn_width_action,
                          command=lambda p=path_rib: self.callbacks['voir_pj'](p)).pack(pady=btn_pady_action, padx=2,
                                                                                        fill="x")
            ctk.CTkButton(action_buttons_frame, text="DL RIB", width=btn_width_action,
                          command=lambda p=path_rib: self.callbacks['dl_pj'](p)).pack(pady=btn_pady_action, padx=2,
                                                                                      fill="x")
        elif not (path_facture or path_trop_percu):
            ctk.CTkLabel(action_buttons_frame, text="RIB N/A", font=value_font_info, anchor="center", height=30).pack(
                pady=btn_pady_action, padx=2, fill="x")

        id_demande = self.demande_data.get("id_demande")
        statut_actuel = self.demande_data.get("statut")
        has_workflow_buttons = False

        buttons_to_add = []
        if self._est_comptable_tresorerie() and statut_actuel == STATUT_CREEE:
            buttons_to_add.append(
                ("Accepter (Constat TP)", lambda: self.callbacks['mlupo_accepter'](id_demande), "green", "darkgreen"))
            buttons_to_add.append(
                ("Refuser (Constat TP)", lambda: self.callbacks['mlupo_refuser'](id_demande), "orange", "darkorange"))
            has_workflow_buttons = True

        if (self._est_validateur_chef() or self._est_admin()) and statut_actuel == STATUT_TROP_PERCU_CONSTATE:
            buttons_to_add.append(
                ("Valider Demande", lambda: self.callbacks['jdurousset_valider'](id_demande), "blue", "darkblue"))
            buttons_to_add.append(
                ("Refuser Demande", lambda: self.callbacks['jdurousset_refuser'](id_demande), "orange", "darkorange"))
            has_workflow_buttons = True

        if (self._est_comptable_fournisseur() or self._est_admin()) and statut_actuel == STATUT_VALIDEE:
            buttons_to_add.append(
                ("Confirmer Paiement", lambda: self.callbacks['pdiop_confirmer_paiement'](id_demande), "#006400",
                 "#004d00"))
            has_workflow_buttons = True

        if (self.current_user_name == self.demande_data.get(
                "cree_par") or self._est_admin()) and statut_actuel == STATUT_REFUSEE_CONSTAT_TP:
            buttons_to_add.append(
                ("Corriger Demande", lambda: self.callbacks['pneri_resoumettre'](id_demande), "teal", None))
            buttons_to_add.append(
                ("Annuler Demande", lambda: self.callbacks['pneri_annuler'](id_demande), "#D32F2F", "#B71C1C"))
            has_workflow_buttons = True

        if (
                self._est_comptable_tresorerie() or self._est_admin()) and statut_actuel == STATUT_REFUSEE_VALIDATION_CORRECTION_MLUPO:
            buttons_to_add.append(
                ("Corriger Constat TP", lambda: self.callbacks['mlupo_resoumettre_constat'](id_demande), "teal", None))
            has_workflow_buttons = True

        if has_workflow_buttons:
            action_buttons_workflow_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            action_buttons_workflow_frame.grid(row=1, column=0, columnspan=3, pady=(8, 4), sticky="ew")
            action_buttons_workflow_frame.grid_columnconfigure(0, weight=1)

            inner_buttons_frame = ctk.CTkFrame(action_buttons_workflow_frame, fg_color="transparent")
            inner_buttons_frame.grid(row=0, column=0)

            for text, command, fg_color, hover_color in buttons_to_add:
                ctk.CTkButton(inner_buttons_frame, text=text, width=btn_width_action, fg_color=fg_color,
                              hover_color=hover_color, command=command).pack(side="left", padx=5)

        if self._est_admin():
            admin_actions_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            admin_actions_frame.grid(row=2, column=0, columnspan=3, pady=(4, 8), sticky="e")
            ctk.CTkButton(admin_actions_frame, text="Supprimer (Admin)", width=btn_width_action, fg_color="red",
                          hover_color="darkred",
                          command=lambda demande_id=id_demande: self.callbacks['supprimer_demande'](demande_id)).pack(
                side="right", padx=(0, 5))