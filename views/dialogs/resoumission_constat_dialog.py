# views/dialogs/resoumission_constat_dialog.py
import os
import customtkinter as ctk
from tkinter import messagebox

class ResoumissionConstatDialog(ctk.CTkToplevel):
    def __init__(self, master, remboursement_controller, id_demande):
        super().__init__(master)
        self.master = master
        self.remboursement_controller = remboursement_controller
        self.id_demande = id_demande

        demande_data = self.remboursement_controller.get_demande_by_id(id_demande)
        if not demande_data:
            messagebox.showerror("Erreur", "Impossible de charger les données de la demande.", parent=master)
            self.after(1, self.destroy)
            return

        self.title(f"Corriger Constat TP {id_demande[:8]}")
        self.geometry("500x450")
        self.transient(master)
        self.grab_set()

        self.new_pj_path = None
        self.keep_pj_var = ctk.BooleanVar(value=False)

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=20, pady=10)

        ctk.CTkLabel(main_frame, text="Veuillez fournir une nouvelle preuve et un commentaire.").pack(pady=(0, 15))

        self.btn_sel_pj = ctk.CTkButton(main_frame, text="Choisir Nouvelle Preuve TP", command=self._sel_new_pj_tp)
        self.chemin_pj_var = ctk.StringVar(value="Aucun fichier sélectionné")
        self.lbl_pj_sel = ctk.CTkLabel(main_frame, textvariable=self.chemin_pj_var)
        self.original_text_color = self.lbl_pj_sel.cget("text_color")

        self.btn_sel_pj.pack(anchor="w", padx=20, pady=(5, 2))
        self.lbl_pj_sel.pack(anchor="w", padx=20, pady=(0, 5))

        pjs_existantes = demande_data.get("pieces_capture_trop_percu", [])
        self.cb_keep_pj = ctk.CTkCheckBox(main_frame, variable=self.keep_pj_var, command=self._toggle_pj_ui)
        if pjs_existantes:
            self.cb_keep_pj.configure(text=f"Conserver la preuve : {os.path.basename(pjs_existantes[-1])}")
        else:
            self.cb_keep_pj.configure(text="Pas de preuve précédente", state="disabled")
        self.cb_keep_pj.pack(anchor="w", padx=20, pady=(0, 10))

        ctk.CTkLabel(main_frame, text="Commentaire de correction (Obligatoire):").pack(pady=(15, 0))
        self.commentaire_box = ctk.CTkTextbox(main_frame, height=80)
        self.commentaire_box.pack(pady=5, padx=20, fill="x", expand=True)
        self.commentaire_box.focus()

        ctk.CTkButton(self, text="Resoumettre le Constat", command=self._submit_correction_constat).pack(pady=20)

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
        path = self.remboursement_controller.selectionner_fichier_document_ou_image("Nouvelle Preuve Trop-Perçu")
        if path:
            self.new_pj_path = path
            self.chemin_pj_var.set(os.path.basename(path))

    def _submit_correction_constat(self):
        commentaire = self.commentaire_box.get("1.0", "end-1c").strip()
        if not self.keep_pj_var.get() and not self.new_pj_path:
            messagebox.showerror("Erreur", "Une nouvelle preuve est obligatoire si vous ne conservez pas l'ancienne.", parent=self)
            return
        if not commentaire:
            messagebox.showerror("Erreur", "Un commentaire expliquant la correction est obligatoire.", parent=self)
            return

        succes, msg = self.remboursement_controller.mlupo_resoumettre_constat_corrige(
            self.id_demande, commentaire, self.new_pj_path
        )
        if succes:
            messagebox.showinfo("Succès", msg, parent=self.master)
            self.master.afficher_liste_demandes(force_reload=True)
            self.destroy()
        else:
            messagebox.showerror("Erreur", msg, parent=self)