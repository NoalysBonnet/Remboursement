import os
import customtkinter as ctk
from tkinter import messagebox


class AcceptationConstatDialog(ctk.CTkToplevel):
    def __init__(self, master, remboursement_controller, id_demande):
        super().__init__(master)
        self.master = master
        self.remboursement_controller = remboursement_controller
        self.id_demande = id_demande
        self.current_pj_path = None

        self.title(f"Accepter Constat TP - Demande {id_demande[:8]}")
        self.geometry("500x450")
        self.transient(master)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        self.chemin_pj_var = ctk.StringVar(value="Aucune PJ sélectionnée (Obligatoire)")

        ctk.CTkLabel(self, text="Preuve de Trop-Perçu (Image/PDF/Doc...):").pack(pady=(10, 2))
        ctk.CTkButton(self, text="Choisir Fichier...", command=self._select_pj).pack(pady=(0, 5))
        ctk.CTkLabel(self, textvariable=self.chemin_pj_var).pack()

        ctk.CTkLabel(self, text="Commentaire (Obligatoire):").pack(pady=(10, 2))
        self.commentaire_box = ctk.CTkTextbox(self, height=100, width=450)
        self.commentaire_box.pack(pady=5, padx=10, fill="x", expand=True)
        self.commentaire_box.focus()

        ctk.CTkButton(self, text="Valider et Soumettre à J. Durousset", command=self._submit).pack(pady=10)

    def _select_pj(self):
        path = self.remboursement_controller.selectionner_fichier_document_ou_image("Sélectionner Preuve Trop-Perçu")
        if path:
            self.chemin_pj_var.set(os.path.basename(path))
            self.current_pj_path = path

    def _submit(self):
        commentaire = self.commentaire_box.get("1.0", "end-1c").strip()
        succes, msg = self.remboursement_controller.mlupo_accepter_constat(
            self.id_demande, self.current_pj_path, commentaire
        )
        if succes:
            messagebox.showinfo("Succès", msg, parent=self.master)
            self.master.afficher_liste_demandes(force_reload=True)
            self.destroy()
        else:
            messagebox.showerror("Erreur", msg, parent=self)