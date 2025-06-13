import os
import customtkinter as ctk
from tkinter import messagebox


class CreationDemandeDialog(ctk.CTkToplevel):
    def __init__(self, master, remboursement_controller, app_controller):
        super().__init__(master)
        self.master = master
        self.remboursement_controller = remboursement_controller
        self.app_controller = app_controller

        self.title("Nouvelle Demande de Remboursement")
        self.geometry("650x650")
        self.transient(master)
        self.grab_set()

        self._entry_chemin_facture_complet = None
        self._entry_chemin_rib_complet = None
        self.entries_demande = {}

        self._build_ui()
        self.after(100, lambda: self.entries_demande["nom"].focus_set())

    def _build_ui(self):
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(expand=True, fill="both", padx=20, pady=20)
        form_frame.columnconfigure(1, weight=1)

        current_row = 0
        labels_entries = {
            "Nom:": "nom", "Prénom:": "prenom", "Référence Facture:": "reference_facture",
            "Montant demandé (€):": "montant_demande"
        }

        for label_text, key_name in labels_entries.items():
            ctk.CTkLabel(form_frame, text=label_text).grid(row=current_row, column=0, padx=5, pady=8, sticky="w")
            entry = ctk.CTkEntry(form_frame, width=350)
            entry.grid(row=current_row, column=1, padx=5, pady=8, sticky="ew")
            self.entries_demande[key_name] = entry
            current_row += 1

        ctk.CTkLabel(form_frame, text="Description/Raison:").grid(row=current_row, column=0, padx=5,
                                                                  pady=(8, 0),
                                                                  sticky="nw")
        self.textbox_description = ctk.CTkTextbox(form_frame, width=350, height=100)
        self.textbox_description.grid(row=current_row, column=1, padx=5, pady=8, sticky="ew")
        current_row += 1

        self.chemin_facture_var = ctk.StringVar(value="Aucun fichier sélectionné (Optionnel)")
        self.chemin_rib_var = ctk.StringVar(value="Aucun fichier sélectionné (Obligatoire)")

        btn_facture = ctk.CTkButton(form_frame, text="Choisir Facture", command=self._selectionner_facture)
        btn_facture.grid(row=current_row, column=0, padx=5, pady=10, sticky="w")
        ctk.CTkLabel(form_frame, textvariable=self.chemin_facture_var, wraplength=300).grid(row=current_row,
                                                                                            column=1,
                                                                                            padx=5, pady=10,
                                                                                            sticky="ew")
        current_row += 1

        btn_rib = ctk.CTkButton(form_frame, text="Choisir RIB", command=self._selectionner_rib)
        btn_rib.grid(row=current_row, column=0, padx=5, pady=10, sticky="w")
        ctk.CTkLabel(form_frame, textvariable=self.chemin_rib_var, wraplength=300).grid(row=current_row, column=1,
                                                                                        padx=5, pady=10,
                                                                                        sticky="ew")
        current_row += 1

        btn_soumettre = ctk.CTkButton(form_frame, text="Enregistrer la Demande",
                                      command=self._soumettre_demande,
                                      height=35)
        btn_soumettre.grid(row=current_row, column=0, columnspan=2, pady=25, padx=5)

    def _selectionner_facture(self):
        chemin = self.remboursement_controller.selectionner_fichier_document_ou_image(
            "Sélectionner la Facture")
        if not chemin:
            self.chemin_facture_var.set("Aucun fichier sélectionné (Optionnel)")
            self._entry_chemin_facture_complet = None
            return

        self.chemin_facture_var.set(os.path.basename(chemin))
        self._entry_chemin_facture_complet = chemin
        if chemin.lower().endswith(".pdf"):
            def task():
                return self.remboursement_controller.extraire_info_facture_pdf(chemin)

            def on_complete(infos):
                if infos.get("nom"):
                    self.entries_demande["nom"].delete(0, "end")
                    self.entries_demande["nom"].insert(0, infos.get("nom"))

                if infos.get("prenom"):
                    self.entries_demande["prenom"].delete(0, "end")
                    self.entries_demande["prenom"].insert(0, infos.get("prenom"))

                if infos.get("reference"):
                    self.entries_demande["reference_facture"].delete(0, "end")
                    self.entries_demande["reference_facture"].insert(0, infos.get("reference"))

            self.app_controller.run_threaded_task(task, on_complete)

    def _selectionner_rib(self):
        chemin = self.remboursement_controller.selectionner_fichier_document_ou_image("Sélectionner le RIB")
        if chemin:
            self.chemin_rib_var.set(os.path.basename(chemin))
            self._entry_chemin_rib_complet = chemin

    def _soumettre_demande(self):
        form_data = {
            "nom": self.entries_demande["nom"].get(),
            "prenom": self.entries_demande["prenom"].get(),
            "reference_facture": self.entries_demande["reference_facture"].get(),
            "montant_demande_str": self.entries_demande["montant_demande"].get(),
            "description": self.textbox_description.get("1.0", "end-1c").strip(),
            "chemin_facture_source": self._entry_chemin_facture_complet,
            "chemin_rib_source": self._entry_chemin_rib_complet
        }

        def task():
            return self.remboursement_controller.creer_demande_remboursement(**form_data)

        def on_complete(result):
            succes, message = result
            if succes:
                messagebox.showinfo("Succès", message, parent=self.master)
                self.master.afficher_liste_demandes(force_reload=True)
            else:
                messagebox.showerror("Erreur", message, parent=self.master)
            self.destroy()

        self.withdraw()
        self.app_controller.run_threaded_task(task, on_complete)