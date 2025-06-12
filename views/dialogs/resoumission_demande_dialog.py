# views/dialogs/resoumission_demande_dialog.py
import os
import customtkinter as ctk
from tkinter import messagebox

class ResoumissionDemandeDialog(ctk.CTkToplevel):
    def __init__(self, master, remboursement_controller, id_demande):
        super().__init__(master)
        self.master = master
        self.remboursement_controller = remboursement_controller
        self.id_demande = id_demande

        demande_data = self.remboursement_controller.get_demande_by_id(self.id_demande)
        if not demande_data:
            messagebox.showerror("Erreur", "Impossible de charger les données de la demande.", parent=master)
            self.after(1, self.destroy)
            return

        self.title(f"Corriger Demande {id_demande[:8]}")
        self.geometry("600x550")
        self.transient(master)
        self.grab_set()

        self.new_facture_path = None
        self.new_rib_path = None
        self.keep_facture_var = ctk.BooleanVar(value=False)
        self.keep_rib_var = ctk.BooleanVar(value=False)

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=20, pady=10)

        ctk.CTkLabel(main_frame, text="Veuillez fournir les documents mis à jour et un commentaire.").pack(pady=(0, 15))

        # --- Section Facture ---
        self.btn_sel_facture = ctk.CTkButton(main_frame, text="Choisir Nouvelle Facture (Optionnel)", command=self._sel_new_facture)
        self.chemin_facture_var = ctk.StringVar(value="Aucun fichier sélectionné")
        self.lbl_facture_sel = ctk.CTkLabel(main_frame, textvariable=self.chemin_facture_var)
        self.original_text_color = self.lbl_facture_sel.cget("text_color")

        self.btn_sel_facture.pack(anchor="w", padx=20, pady=(5, 2))
        self.lbl_facture_sel.pack(anchor="w", padx=20, pady=(0, 5))

        factures_existantes = demande_data.get("chemins_factures_stockees", [])
        self.cb_keep_facture = ctk.CTkCheckBox(main_frame, variable=self.keep_facture_var, command=self._toggle_facture_ui)
        if factures_existantes:
            self.cb_keep_facture.configure(text=f"Conserver la facture : {os.path.basename(factures_existantes[-1])}")
        else:
            self.cb_keep_facture.configure(text="Pas de facture précédente", state="disabled")
        self.cb_keep_facture.pack(anchor="w", padx=20, pady=(0, 10))

        # --- Section RIB ---
        self.btn_sel_rib = ctk.CTkButton(main_frame, text="Choisir Nouveau RIB", command=self._sel_new_rib)
        self.chemin_rib_var = ctk.StringVar(value="Aucun fichier sélectionné")
        self.lbl_rib_sel = ctk.CTkLabel(main_frame, textvariable=self.chemin_rib_var)

        self.btn_sel_rib.pack(anchor="w", padx=20, pady=(5, 2))
        self.lbl_rib_sel.pack(anchor="w", padx=20, pady=(0, 5))

        ribs_existants = demande_data.get("chemins_rib_stockes", [])
        self.cb_keep_rib = ctk.CTkCheckBox(main_frame, variable=self.keep_rib_var, command=self._toggle_rib_ui)
        if ribs_existants:
            self.cb_keep_rib.configure(text=f"Conserver le RIB : {os.path.basename(ribs_existants[-1])}")
        else:
            self.cb_keep_rib.configure(text="Pas de RIB précédent", state="disabled")
        self.cb_keep_rib.pack(anchor="w", padx=20, pady=(0, 10))

        # --- Commentaire et Soumission ---
        ctk.CTkLabel(main_frame, text="Commentaire de correction (Obligatoire):").pack(pady=(15, 0))
        self.commentaire_box = ctk.CTkTextbox(main_frame, height=80)
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
            messagebox.showerror("Erreur", "Un nouveau RIB est obligatoire si vous ne conservez pas l'ancien.", parent=self)
            return
        if not commentaire:
            messagebox.showerror("Erreur", "Un commentaire expliquant la correction est obligatoire.", parent=self)
            return

        succes, msg = self.remboursement_controller.pneri_resoumettre_demande_corrigee(
            self.id_demande, commentaire, self.new_facture_path, self.new_rib_path
        )
        if succes:
            messagebox.showinfo("Succès", msg, parent=self.master)
            self.master.afficher_liste_demandes(force_reload=True)
            self.destroy()
        else:
            messagebox.showerror("Erreur", msg, parent=self)