import os
import customtkinter as ctk
from tkinter import messagebox


class ResoumissionDemandeDialog(ctk.CTkToplevel):
    def __init__(self, master, remboursement_controller, id_demande, app_controller):
        super().__init__(master)
        self.master = master
        self.remboursement_controller = remboursement_controller
        self.id_demande = id_demande
        self.app_controller = app_controller

        self.title(f"Corriger Demande {id_demande[:8]}")
        self.geometry("600x550")
        self.transient(master)
        self.grab_set()

        self.new_facture_path = None
        self.new_rib_path = None
        self.keep_facture_var = ctk.BooleanVar(value=False)
        self.keep_rib_var = ctk.BooleanVar(value=False)

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=10)

        self._load_data_and_build_ui()

    def _load_data_and_build_ui(self):
        def task():
            return self.remboursement_controller.get_demande_by_id(self.id_demande)

        def on_complete(demande_data):
            if not demande_data:
                messagebox.showerror("Erreur", "Impossible de charger les données de la demande.", parent=self.master)
                self.destroy()
                return
            self._build_ui(demande_data)

        self.app_controller.run_threaded_task(task, on_complete)

    def _build_ui(self, demande_data):
        ctk.CTkLabel(self.main_frame, text="Veuillez fournir les documents mis à jour et un commentaire.").pack(
            pady=(0, 15))

        self.btn_sel_facture = ctk.CTkButton(self.main_frame, text="Choisir Nouvelle Facture (Optionnel)",
                                             command=self._sel_new_facture)
        self.chemin_facture_var = ctk.StringVar(value="Aucun fichier sélectionné")
        self.lbl_facture_sel = ctk.CTkLabel(self.main_frame, textvariable=self.chemin_facture_var)
        self.original_text_color = self.lbl_facture_sel.cget("text_color")

        self.btn_sel_facture.pack(anchor="w", padx=20, pady=(5, 2))
        self.lbl_facture_sel.pack(anchor="w", padx=20, pady=(0, 5))

        factures_existantes = demande_data.get("chemins_factures_stockees", [])
        self.cb_keep_facture = ctk.CTkCheckBox(self.main_frame, variable=self.keep_facture_var,
                                               command=self._toggle_facture_ui)
        if factures_existantes:
            self.cb_keep_facture.configure(
                text=f"Conserver la facture : {os.path.basename(factures_existantes[-1])}")
        else:
            self.cb_keep_facture.configure(text="Pas de facture précédente", state="disabled")
        self.cb_keep_facture.pack(anchor="w", padx=20, pady=(0, 10))

        self.btn_sel_rib = ctk.CTkButton(self.main_frame, text="Choisir Nouveau RIB", command=self._sel_new_rib)
        self.chemin_rib_var = ctk.StringVar(value="Aucun fichier sélectionné")
        self.lbl_rib_sel = ctk.CTkLabel(self.main_frame, textvariable=self.chemin_rib_var)

        self.btn_sel_rib.pack(anchor="w", padx=20, pady=(5, 2))
        self.lbl_rib_sel.pack(anchor="w", padx=20, pady=(0, 5))

        ribs_existants = demande_data.get("chemins_rib_stockes", [])
        self.cb_keep_rib = ctk.CTkCheckBox(self.main_frame, variable=self.keep_rib_var,
                                           command=self._toggle_rib_ui)
        if ribs_existants:
            self.cb_keep_rib.configure(text=f"Conserver le RIB : {os.path.basename(ribs_existants[-1])}")
        else:
            self.cb_keep_rib.configure(text="Pas de RIB précédent", state="disabled")
        self.cb_keep_rib.pack(anchor="w", padx=20, pady=(0, 10))

        ctk.CTkLabel(self.main_frame, text="Commentaire de correction (Obligatoire):").pack(pady=(15, 0))
        self.commentaire_box = ctk.CTkTextbox(self.main_frame, height=80)
        self.commentaire_box.pack(pady=5, padx=20, fill="x", expand=True)
        self.commentaire_box.focus()

        ctk.CTkButton(self, text="Resoumettre la Demande", command=self._submit_correction).pack(pady=20)

    def _toggle_facture_ui(self):
        if self.keep_facture_var.get():
            self.btn_sel_facture.configure(state="disabled")
            self.lbl_facture_sel.configure(text_color="gray")
            self.new_facture_path = None
            self.chemin_facture_var.set("Ancienne facture conservée")
        else:
            self.btn_sel_facture.configure(state="normal")
            self.lbl_facture_sel.configure(text_color=self.original_text_color)
            self.chemin_facture_var.set("Aucun fichier sélectionné")

    def _toggle_rib_ui(self):
        if self.keep_rib_var.get():
            self.btn_sel_rib.configure(state="disabled")
            self.lbl_rib_sel.configure(text_color="gray")
            self.new_rib_path = None
            self.chemin_rib_var.set("Ancien RIB conservé")
        else:
            self.btn_sel_rib.configure(state="normal")
            self.lbl_rib_sel.configure(text_color=self.original_text_color)
            self.chemin_rib_var.set("Aucun fichier sélectionné")

    def _sel_new_facture(self):
        path = self.remboursement_controller.selectionner_fichier_document_ou_image("Nouvelle Facture")
        if path:
            self.new_facture_path = path
            self.chemin_facture_var.set(os.path.basename(path))

    def _sel_new_rib(self):
        path = self.remboursement_controller.selectionner_fichier_document_ou_image("Nouveau RIB")
        if path:
            self.new_rib_path = path
            self.chemin_rib_var.set(os.path.basename(path))

    def _submit_correction(self):
        commentaire = self.commentaire_box.get("1.0", "end-1c").strip()
        if not self.keep_rib_var.get() and not self.new_rib_path:
            messagebox.showerror("Erreur",
                                 "Un nouveau RIB est obligatoire si vous ne conservez pas l'ancien.",
                                 parent=self)
            return
        if not commentaire:
            messagebox.showerror("Erreur",
                                 "Un commentaire expliquant la correction est obligatoire.", parent=self)
            return

        def combined_task():
            action_success, action_message = self.remboursement_controller.pneri_resoumettre_demande_corrigee(
                self.id_demande, commentaire, self.new_facture_path, self.new_rib_path
            )
            if not action_success:
                return {'status': 'error', 'message': action_message}

            refreshed_data = self.master._get_refreshed_and_sorted_data(force_reload=True)
            return {'status': 'success', 'data': refreshed_data, 'message': action_message}

        def on_complete(result):
            if result['status'] == 'error':
                messagebox.showerror("Erreur", result['message'], parent=self.master)
            else:
                self.app_controller.show_toast(result['message'])
                self.master._render_demandes_list(result['data'])
            self.destroy()

        self.withdraw()
        self.app_controller.run_threaded_task(combined_task, on_complete)