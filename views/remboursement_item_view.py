# views/remboursement_item_view.py
import os
import customtkinter as ctk
import datetime
from config.settings import (
    STATUT_CREEE, STATUT_REFUSEE_CONSTAT_TP, STATUT_TROP_PERCU_CONSTATE,
    STATUT_VALIDEE, STATUT_REFUSEE_VALIDATION_CORRECTION_MLUPO,
    STATUT_ANNULEE, STATUT_PAIEMENT_EFFECTUE
)

# Couleurs (peuvent être importées de settings ou définies ici si spécifiques à l'item)
COULEUR_ACTIVE_POUR_UTILISATEUR = "#1E4D2B"
COULEUR_DEMANDE_TERMINEE = "#2E4374"
COULEUR_DEMANDE_ANNULEE = "#6A040F"
COULEUR_BORDURE_ACTIVE = "#38761D"
COULEUR_BORDURE_TERMINEE = "#4A55A2"
COULEUR_BORDURE_ANNULEE = "#9D0208"


class RemboursementItemView(ctk.CTkFrame):
    def __init__(self, master, demande_data: dict, current_user_name: str, user_roles: list, callbacks: dict):
        super().__init__(master, border_width=1, corner_radius=5)

        self.demande_data = demande_data
        self.current_user_name = current_user_name
        self.user_roles = user_roles
        self.callbacks = callbacks  # {'voir_pj': func, 'dl_pj': func, 'mlupo_accepter': func, ...}

        self._setup_item_colors()
        self._build_ui()

    def _est_admin(self) -> bool:
        return "admin" in self.user_roles

    def _est_comptable_tresorerie(self) -> bool:
        return "comptable_tresorerie" in self.user_roles

    def _est_validateur_chef(self) -> bool:
        return "validateur_chef" in self.user_roles

    def _setup_item_colors(self):
        is_active_for_user = False
        current_status = self.demande_data.get("statut")
        cree_par_user = self.demande_data.get("cree_par")

        # Logique de mise en évidence
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
        # Ajouter d'autres conditions pour les futures étapes

        item_bg_color = None
        border_color = "gray40"
        border_width = 1

        if current_status == STATUT_ANNULEE:
            item_bg_color = COULEUR_DEMANDE_ANNULEE
            border_color = COULEUR_BORDURE_ANNULEE
            border_width = 2
        elif current_status == STATUT_PAIEMENT_EFFECTUE:
            item_bg_color = COULEUR_DEMANDE_TERMINEE
            border_color = COULEUR_BORDURE_TERMINEE
            border_width = 2
        elif is_active_for_user:
            item_bg_color = COULEUR_ACTIVE_POUR_UTILISATEUR
            border_color = COULEUR_BORDURE_ACTIVE
            border_width = 2

        self.configure(border_width=border_width, fg_color=item_bg_color, border_color=border_color)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=2, minsize=280)
        self.grid_columnconfigure(1, weight=3, minsize=300)
        self.grid_columnconfigure(2, weight=0, minsize=140)

        # --- Cadre des infos de base ---
        basic_info_frame = ctk.CTkFrame(self, fg_color="transparent")
        basic_info_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=(5, 5))
        basic_info_frame.grid_columnconfigure(0, weight=0, minsize=100)
        basic_info_frame.grid_columnconfigure(1, weight=1)

        row_idx_info = 0
        common_pady_info = (1, 1)
        common_padx_info = (5, 2)
        label_font_info = ctk.CTkFont(weight="bold", size=12)
        value_font_info = ctk.CTkFont(size=12)

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

        date_creation_iso = self.demande_data.get('date_creation', '')
        date_creation_formatee = "N/A"
        if date_creation_iso:
            try:
                date_creation_obj = datetime.datetime.fromisoformat(
                    date_creation_iso); date_creation_formatee = date_creation_obj.strftime("%d/%m/%Y %H:%M")
            except ValueError:
                date_creation_formatee = "Date invalide"
        add_basic_info_row("Créée le:", date_creation_formatee)

        add_basic_info_row("Modifiée par:", self.demande_data.get('derniere_modification_par', 'N/A'))
        add_basic_info_row("Statut Actuel:", self.demande_data.get('statut', 'Non défini'))

        # --- Cadre de l'historique ---
        historique_frame = ctk.CTkFrame(self, fg_color="transparent")
        historique_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=(5, 5))
        ctk.CTkLabel(historique_frame, text="Historique/Commentaires:", font=label_font_info).pack(anchor="w",
                                                                                                   padx=common_padx_info,
                                                                                                   pady=(0, 2))
        hist_text_box = ctk.CTkTextbox(historique_frame, height=100, fg_color="gray20", border_width=1,
                                       activate_scrollbars=True)
        hist_text_box.pack(fill="both", expand=True, padx=common_padx_info, pady=(0, common_pady_info[1]))
        hist_text_box.configure(state="disabled")

        historique = self.demande_data.get('historique_statuts', [])
        if historique:
            hist_text_box.configure(state="normal")
            hist_text_box.delete("1.0", "end")
            for entree_hist in reversed(historique):
                date_hist_iso = entree_hist.get('date', '')
                date_hist_formatee = "N/A"
                if date_hist_iso:
                    try:
                        date_hist_obj = datetime.datetime.fromisoformat(
                            date_hist_iso); date_hist_formatee = date_hist_obj.strftime("%d/%m/%Y %H:%M")
                    except ValueError:
                        date_hist_formatee = "Date invalide"
                par_hist = entree_hist.get('par', 'Système')
                statut_hist = entree_hist.get('statut', '')
                commentaire_hist = entree_hist.get('commentaire', '').strip()
                hist_text_box.insert("end", f"{date_hist_formatee} - {par_hist}:\n")
                current_demande_statut = self.demande_data.get('statut')
                if statut_hist and (
                        statut_hist != current_demande_statut or len(historique) == 1 or entree_hist == historique[0]):
                    hist_text_box.insert("end", f"  Statut: {statut_hist}\n")
                if commentaire_hist: hist_text_box.insert("end", f"  Commentaire: {commentaire_hist}\n")
                hist_text_box.insert("end", "----\n")
            hist_text_box.configure(state="disabled")
        else:
            hist_text_box.configure(state="normal");
            hist_text_box.delete("1.0", "end");
            hist_text_box.insert("end", "Aucun historique.");
            hist_text_box.configure(state="disabled")

        # --- Cadre des boutons d'action ---
        action_buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_buttons_frame.grid(row=0, column=2, sticky="ne", padx=(5, 10), pady=(5, 5))

        btn_width_action = 120
        btn_pady_action = (3, 3)

        path_facture = self.demande_data.get("chemin_abs_facture")
        path_rib = self.demande_data.get("chemin_abs_rib")
        facture_presente_et_valide = path_facture and os.path.exists(path_facture)
        rib_present_et_valide = path_rib and os.path.exists(path_rib)
        chemins_trop_percu = self.demande_data.get("chemins_abs_trop_percu", [])

        if facture_presente_et_valide:
            ctk.CTkButton(action_buttons_frame, text="Voir Facture", width=btn_width_action,
                          command=lambda p=path_facture: self.callbacks['voir_pj'](p)).pack(pady=btn_pady_action,
                                                                                            padx=2, fill="x")
            ctk.CTkButton(action_buttons_frame, text="DL Facture", width=btn_width_action,
                          command=lambda p=path_facture: self.callbacks['dl_pj'](p)).pack(pady=btn_pady_action, padx=2,
                                                                                          fill="x")
        else:
            ctk.CTkLabel(action_buttons_frame, text="Facture N/A", font=value_font_info, anchor="center",
                         height=50).pack(pady=btn_pady_action, padx=2, fill="x")

        if chemins_trop_percu:
            if facture_presente_et_valide:
                ctk.CTkFrame(action_buttons_frame, height=2, fg_color="gray50").pack(fill="x", pady=4, padx=15)
            ctk.CTkLabel(action_buttons_frame, text="Preuves TP:", font=label_font_info).pack(anchor="w", pady=(5, 0))
            for idx, p_tp in enumerate(chemins_trop_percu):
                if os.path.exists(p_tp):
                    ctk.CTkButton(action_buttons_frame, text=f"Voir Preuve TP {idx + 1}", width=btn_width_action,
                                  command=lambda p=p_tp: self.callbacks['voir_pj'](p)).pack(pady=btn_pady_action,
                                                                                            padx=2, fill="x")
                    ctk.CTkButton(action_buttons_frame, text=f"DL Preuve TP {idx + 1}", width=btn_width_action,
                                  command=lambda p=p_tp: self.callbacks['dl_pj'](p)).pack(pady=btn_pady_action, padx=2,
                                                                                          fill="x")

        if rib_present_et_valide:
            if facture_presente_et_valide or chemins_trop_percu:
                ctk.CTkFrame(action_buttons_frame, height=2, fg_color="gray50").pack(fill="x", pady=8, padx=15)
            ctk.CTkButton(action_buttons_frame, text="Voir RIB", width=btn_width_action,
                          command=lambda p=path_rib: self.callbacks['voir_pj'](p)).pack(pady=btn_pady_action, padx=2,
                                                                                        fill="x")
            ctk.CTkButton(action_buttons_frame, text="DL RIB", width=btn_width_action,
                          command=lambda p=path_rib: self.callbacks['dl_pj'](p)).pack(pady=btn_pady_action, padx=2,
                                                                                      fill="x")
        elif not (facture_presente_et_valide or chemins_trop_percu):
            ctk.CTkLabel(action_buttons_frame, text="RIB N/A", font=value_font_info, anchor="center", height=50).pack(
                pady=btn_pady_action, padx=2, fill="x")

        id_demande = self.demande_data.get("id_demande");
        statut_actuel = self.demande_data.get("statut")

        action_effectuee_sur_cet_item = False

        if self._est_comptable_tresorerie() and statut_actuel == STATUT_CREEE:
            ctk.CTkButton(action_buttons_frame, text="Accepter (Constat TP)", width=btn_width_action, fg_color="green",
                          hover_color="darkgreen",
                          command=lambda d_id=id_demande: self.callbacks['mlupo_accepter'](d_id)).pack(
                pady=(10, btn_pady_action[1]), padx=2, fill="x")
            ctk.CTkButton(action_buttons_frame, text="Refuser (Constat TP)", width=btn_width_action, fg_color="orange",
                          hover_color="darkorange",
                          command=lambda d_id=id_demande: self.callbacks['mlupo_refuser'](d_id)).pack(
                pady=btn_pady_action, padx=2, fill="x")
            action_effectuee_sur_cet_item = True

        if (
                self._est_validateur_chef() or self._est_admin()) and statut_actuel == STATUT_TROP_PERCU_CONSTATE and not action_effectuee_sur_cet_item:
            ctk.CTkButton(action_buttons_frame, text="Valider Demande", width=btn_width_action, fg_color="blue",
                          hover_color="darkblue",
                          command=lambda d_id=id_demande: self.callbacks['jdurousset_valider'](d_id)).pack(
                pady=(10, btn_pady_action[1]), padx=2, fill="x")
            ctk.CTkButton(action_buttons_frame, text="Refuser Demande", width=btn_width_action, fg_color="orange",
                          hover_color="darkorange",
                          command=lambda d_id=id_demande: self.callbacks['jdurousset_refuser'](d_id)).pack(
                pady=btn_pady_action, padx=2, fill="x")
            action_effectuee_sur_cet_item = True

        if (self.current_user_name == self.demande_data.get(
                "cree_par") or self._est_admin()) and statut_actuel == STATUT_REFUSEE_CONSTAT_TP and not action_effectuee_sur_cet_item:
            ctk.CTkButton(action_buttons_frame, text="Annuler Demande", width=btn_width_action, fg_color="#D32F2F",
                          hover_color="#B71C1C",
                          command=lambda d_id=id_demande: self.callbacks['pneri_annuler'](d_id)).pack(
                pady=(10, btn_pady_action[1]), padx=2, fill="x")
            action_effectuee_sur_cet_item = True

        if self._est_admin():
            ctk.CTkButton(action_buttons_frame, text="Supprimer (Admin)", width=btn_width_action, fg_color="red",
                          hover_color="darkred",
                          command=lambda demande_id=id_demande: self.callbacks['supprimer_demande'](demande_id)).pack(
                pady=(15, btn_pady_action[1]), padx=2, fill="x")