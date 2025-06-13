import os
import customtkinter as ctk
from .comment_dialog import CommentDialog


class ResoumissionConstatDialog(ctk.CTkToplevel):
    def __init__(self, master, remboursement_controller, id_demande, app_controller):
        super().__init__(master)
        self.master = master
        self.remboursement_controller = remboursement_controller
        self.id_demande = id_demande
        self.app_controller = app_controller

        self.title(f"Corriger Constat TP {id_demande[:8]}")
        self.geometry("550x450")
        self.transient(master)
        self.grab_set()
        self.minsize(500, 400)

        self.new_pj_path = None
        self.keep_pj_var = ctk.BooleanVar(value=False)

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        self._load_data_and_build_ui()

    def _load_data_and_build_ui(self):
        def task():
            return self.remboursement_controller.get_demande_by_id(self.id_demande)

        def on_complete(demande_data):
            if not demande_data:
                self.app_controller.show_toast("Impossible de charger les données de la demande.", "error")
                self.destroy()
                return
            self._build_ui(demande_data)

        self.app_controller.run_threaded_task(task, on_complete)

    def _build_ui(self, demande_data):
        # 1. Le conteneur des boutons est déclaré et packé en PREMIER, en bas.
        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.pack(side="bottom", pady=(10, 0), fill="x")

        # Un sous-conteneur pour centrer les boutons
        center_buttons_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        center_buttons_frame.pack()  # Se centre par défaut

        ctk.CTkButton(center_buttons_frame, text="Resoumettre le Constat",
                      command=self._submit_correction_constat).pack(side="left", padx=10)

        ctk.CTkButton(center_buttons_frame, text="Renvoyer au Demandeur",
                      command=self._reject_and_return_to_demandeur,
                      fg_color="#D35400", hover_color="#A84300").pack(side="left", padx=10)

        # 2. Le reste des widgets est maintenant packé en partant du haut.
        ctk.CTkLabel(self.main_frame, text="Veuillez fournir une nouvelle preuve et un commentaire.").pack(
            pady=(0, 15), side="top", padx=10)

        self.btn_sel_pj = ctk.CTkButton(self.main_frame, text="Choisir Nouvelle Preuve TP",
                                        command=self._sel_new_pj_tp)
        self.btn_sel_pj.pack(anchor="w", padx=20, pady=(5, 2), side="top")

        self.chemin_pj_var = ctk.StringVar(value="Aucun fichier sélectionné")
        self.lbl_pj_sel = ctk.CTkLabel(self.main_frame, textvariable=self.chemin_pj_var)
        self.original_text_color = self.lbl_pj_sel.cget("text_color")
        self.lbl_pj_sel.pack(anchor="w", padx=20, pady=(0, 5), side="top")

        pjs_existantes = demande_data.get("pieces_capture_trop_percu", [])
        self.cb_keep_pj = ctk.CTkCheckBox(self.main_frame, variable=self.keep_pj_var,
                                          command=self._toggle_pj_ui)
        if pjs_existantes:
            self.cb_keep_pj.configure(
                text=f"Conserver la preuve : {os.path.basename(pjs_existantes[-1])}")
        else:
            self.cb_keep_pj.configure(text="Pas de preuve précédente", state="disabled")
        self.cb_keep_pj.pack(anchor="w", padx=20, pady=(0, 10), side="top")

        ctk.CTkLabel(self.main_frame, text="Commentaire de correction (Obligatoire):").pack(pady=(15, 0), side="top",
                                                                                            padx=10)

        # 3. La zone de texte est la dernière à être packée par le haut et peut donc s'étendre librement.
        self.commentaire_box = ctk.CTkTextbox(self.main_frame)
        self.commentaire_box.pack(pady=(5, 10), padx=10, fill="both", expand=True, side="top")
        self.commentaire_box.focus()

    def _toggle_pj_ui(self):
        if self.keep_pj_var.get():
            self.btn_sel_pj.configure(state="disabled")
            self.lbl_pj_sel.configure(text_color="gray")
            self.new_pj_path = None
            self.chemin_pj_var.set("Ancienne preuve conservée")
        else:
            self.btn_sel_pj.configure(state="normal")
            self.lbl_pj_sel.configure(text_color=self.original_text_color)
            self.chemin_pj_var.set("Aucun fichier sélectionné")

    def _sel_new_pj_tp(self):
        path = self.remboursement_controller.selectionner_fichier_document_ou_image(
            "Nouvelle Preuve Trop-Perçu")
        if path:
            self.new_pj_path = path
            self.chemin_pj_var.set(os.path.basename(path))

    def _submit_correction_constat(self):
        commentaire = self.commentaire_box.get("1.0", "end-1c").strip()
        if not self.keep_pj_var.get() and not self.new_pj_path:
            self.app_controller.show_toast("Une nouvelle preuve est obligatoire si vous ne conservez pas l'ancienne.",
                                           "error")
            return
        if not commentaire:
            self.app_controller.show_toast("Un commentaire expliquant la correction est obligatoire.", "error")
            return

        def combined_task():
            action_success, action_message = self.remboursement_controller.mlupo_resoumettre_constat_corrige(
                self.id_demande, commentaire, self.new_pj_path
            )
            if not action_success:
                return {'status': 'error', 'message': action_message}

            refreshed_data = self.master._get_refreshed_and_sorted_data(force_reload=True)
            return {'status': 'success', 'data': refreshed_data, 'message': action_message}

        def on_complete(result):
            if result['status'] == 'error':
                self.app_controller.show_toast(result['message'], 'error')
            else:
                self.app_controller.show_toast(result['message'], 'success')
                self.master._render_demandes_list(result['data'])
            self.destroy()

        self.withdraw()
        self.app_controller.run_threaded_task(combined_task, on_complete)

    def _reject_and_return_to_demandeur(self):
        dialog = CommentDialog(self, title="Renvoyer au Demandeur",
                               prompt="Motif du renvoi à p.neri (obligatoire) :",
                               is_mandatory=True)
        commentaire = dialog.get_comment()

        if commentaire is None:
            return

        def combined_task():
            action_success, action_message = self.remboursement_controller.mlupo_refuser_correction(
                self.id_demande, commentaire
            )
            if not action_success:
                return {'status': 'error', 'message': action_message}

            refreshed_data = self.master._get_refreshed_and_sorted_data(force_reload=True)
            return {'status': 'success', 'data': refreshed_data, 'message': action_message}

        def on_complete(result):
            if result['status'] == 'error':
                self.app_controller.show_toast(result['message'], 'error')
            else:
                self.app_controller.show_toast(result['message'], 'success')
                self.master._render_demandes_list(result['data'])
            self.destroy()

        self.withdraw()
        self.app_controller.run_threaded_task(combined_task, on_complete)