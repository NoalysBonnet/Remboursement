import os
import customtkinter as ctk
from tkinter import messagebox
import datetime  #


class MainView(ctk.CTkFrame):
    def __init__(self, master, nom_utilisateur, on_logout_callback, remboursement_controller_factory):  #
        super().__init__(master, corner_radius=0, fg_color="transparent")  #
        self.master = master  #
        self.nom_utilisateur = nom_utilisateur  #
        self.on_logout = on_logout_callback  #
        self.remboursement_controller = remboursement_controller_factory(self.nom_utilisateur)  #

        self.pack(fill="both", expand=True)  #
        self.main_content_frame = ctk.CTkFrame(self, corner_radius=10)  #
        self.main_content_frame.pack(pady=20, padx=20, fill="both", expand=True)  #

        self.creer_widgets_barre_superieure_et_titre()  #
        self.creer_section_actions()  #
        self._creer_barre_recherche()  # Nouvelle méthode pour la barre de recherche
        self.creer_conteneur_liste_demandes()  #

        self.afficher_liste_demandes()  #

    def creer_widgets_barre_superieure_et_titre(self):  #
        top_bar = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")  #
        top_bar.pack(fill="x", padx=10, pady=(10, 5), anchor="n")  #

        label_accueil = ctk.CTkLabel(top_bar,
                                     text=f"Utilisateur connecté : {self.nom_utilisateur}",
                                     font=ctk.CTkFont(size=12))  #
        label_accueil.pack(side="left", padx=5)  #

        bouton_deconnexion = ctk.CTkButton(top_bar, text="Déconnexion", command=self.on_logout, width=120)  #
        bouton_deconnexion.pack(side="right", padx=5)  #

        label_titre_principal = ctk.CTkLabel(self.main_content_frame, text="Tableau de Bord - Remboursements",
                                             font=ctk.CTkFont(size=24, weight="bold"))  #
        label_titre_principal.pack(pady=(10, 10), anchor="n")  # pady réduit #

    def creer_section_actions(self):  #
        # Ce frame peut être packé avant ou après la barre de recherche selon la préférence
        # Pour l'instant, je le laisse ici, il apparaîtra sous le titre et au-dessus de la recherche.
        # Si "Nouvelle Demande" doit être toujours visible en haut, son positionnement est bon.
        self.actions_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")  #
        self.actions_frame.pack(pady=(0, 5), padx=10, fill="x", anchor="n")  #

        if self.nom_utilisateur == "p.neri":  #
            bouton_nouvelle_demande = ctk.CTkButton(self.actions_frame, text="Nouvelle Demande de Remboursement",
                                                    command=self._ouvrir_fenetre_creation_demande)  #
            bouton_nouvelle_demande.pack(pady=5, padx=10, anchor="w")  #

    def _creer_barre_recherche(self):
        search_bar_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        search_bar_frame.pack(fill="x", padx=10, pady=(5, 5))

        search_label = ctk.CTkLabel(search_bar_frame, text="Rechercher (Nom, Prénom, Réf.):", font=ctk.CTkFont(size=12))
        search_label.pack(side="left", padx=(5, 5))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)
        self.search_entry = ctk.CTkEntry(search_bar_frame, textvariable=self.search_var, width=300)
        self.search_entry.pack(side="left", padx=(0, 5), fill="x", expand=True)

        # Optionnel: un bouton pour effacer la recherche
        # clear_button = ctk.CTkButton(search_bar_frame, text="X", width=30, command=self._clear_search)
        # clear_button.pack(side="left", padx=(5,0))

    def _clear_search(self, event=None):
        self.search_var.set("")

    def _on_search_change(self, *args):
        # Un petit délai pourrait être ajouté ici si la liste est très grande pour éviter trop de rafraîchissements
        # self.after_cancel(self._search_job_id) # si on utilise after
        # self._search_job_id = self.after(300, self.afficher_liste_demandes) # 300ms delay
        self.afficher_liste_demandes()

    def creer_conteneur_liste_demandes(self):  #
        self.scrollable_frame_demandes = ctk.CTkScrollableFrame(self.main_content_frame,
                                                                label_text="Liste des Demandes de Remboursement")  #
        self.scrollable_frame_demandes.pack(pady=(5, 10), padx=10, expand=True, fill="both")  #
        self.scrollable_frame_demandes.grid_columnconfigure(0, weight=1)  #

    def afficher_liste_demandes(self):  #
        for widget in self.scrollable_frame_demandes.winfo_children():  #
            widget.destroy()  #

        toutes_les_demandes = self.remboursement_controller.get_toutes_les_demandes_formatees()  #
        demandes_a_afficher = []

        terme_recherche = ""
        if hasattr(self, 'search_var'):  # S'assurer que search_var est initialisé
            terme_recherche = self.search_var.get().lower().strip()

        if not terme_recherche:
            demandes_a_afficher = toutes_les_demandes
        else:
            for demande_data in toutes_les_demandes:
                nom_match = terme_recherche in demande_data.get('nom', '').lower()
                prenom_match = terme_recherche in demande_data.get('prenom', '').lower()
                ref_match = terme_recherche in demande_data.get('reference_facture', '').lower()

                if nom_match or prenom_match or ref_match:
                    demandes_a_afficher.append(demande_data)

        if not demandes_a_afficher:  #
            message_texte = "Aucune demande de remboursement à afficher pour le moment."
            if terme_recherche:
                message_texte = f"Aucune demande ne correspond à votre recherche ('{terme_recherche}')."

            no_demandes_label = ctk.CTkLabel(self.scrollable_frame_demandes,
                                             text=message_texte,
                                             font=ctk.CTkFont(size=14))  #
            no_demandes_label.pack(pady=20, padx=20)  #
            return  #

        for i, demande_data in enumerate(demandes_a_afficher):  # # Utiliser la liste filtrée
            item_frame = ctk.CTkFrame(self.scrollable_frame_demandes, border_width=1, corner_radius=5)  #
            item_frame.pack(fill="x", pady=4, padx=5)  #

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

            def add_basic_info_row(label_text, value_text):  #
                nonlocal row_idx_info  #
                ctk.CTkLabel(basic_info_frame, text=label_text, font=label_font_info, anchor="w").grid(row=row_idx_info,
                                                                                                       column=0,
                                                                                                       sticky="nw",
                                                                                                       padx=common_padx_info,
                                                                                                       pady=common_pady_info)  #
                val_label = ctk.CTkLabel(basic_info_frame, text=value_text, font=value_font_info, anchor="w",
                                         justify="left", wraplength=0)  #
                val_label.grid(row=row_idx_info, column=1, sticky="ew", padx=common_padx_info, pady=common_pady_info)  #
                row_idx_info += 1  #

            add_basic_info_row("Patient:", f"{demande_data.get('nom', 'N/A')} {demande_data.get('prenom', 'N/A')}")  #
            add_basic_info_row("Réf. Facture:", demande_data.get('reference_facture', 'N/A'))  #
            add_basic_info_row("Montant:", f"{demande_data.get('montant_demande', 0.0):.2f} €")  #

            date_creation_iso = demande_data.get('date_creation', '')  #
            date_creation_formatee = "N/A"  #
            if date_creation_iso:  #
                try:  #
                    date_creation_obj = datetime.datetime.fromisoformat(date_creation_iso)  #
                    date_creation_formatee = date_creation_obj.strftime("%d/%m/%Y %H:%M")  #
                except ValueError:  #
                    date_creation_formatee = "Date invalide"  #
            add_basic_info_row("Créée le:", date_creation_formatee)  #

            add_basic_info_row("Modifiée par:", demande_data.get('derniere_modification_par', 'N/A'))  #
            add_basic_info_row("Statut:", demande_data.get('statut', 'Non défini'))  #

            description_frame = ctk.CTkFrame(item_frame, fg_color="transparent")  #
            description_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=(5, 5))  #
            description_frame.grid_columnconfigure(0, weight=1)  #
            description_frame.grid_rowconfigure(1, weight=1)  #

            ctk.CTkLabel(description_frame, text="Description:", font=label_font_info, anchor="w").grid(row=0, column=0,
                                                                                                        sticky="nw",
                                                                                                        padx=common_padx_info,
                                                                                                        pady=common_pady_info)  #
            desc_text = demande_data.get('description', 'N/A')  #
            desc_label = ctk.CTkLabel(description_frame, text=desc_text, font=value_font_info, anchor="nw",
                                      justify="left", wraplength=300)  #
            desc_label.grid(row=1, column=0, sticky="nsew", padx=common_padx_info, pady=(0, common_pady_info[1]))  #

            action_buttons_frame = ctk.CTkFrame(item_frame, fg_color="transparent")  #
            action_buttons_frame.grid(row=0, column=2, sticky="ne", padx=(5, 10), pady=(5, 5))  #

            btn_width_action = 120  #
            btn_pady_action = (3, 3)  #

            path_facture = demande_data.get("chemin_abs_facture")  #
            if path_facture and os.path.exists(path_facture):  #
                btn_voir_facture = ctk.CTkButton(action_buttons_frame, text="Voir Facture", width=btn_width_action,
                                                 command=lambda p=path_facture: self._action_voir_pj(p))  #
                btn_voir_facture.pack(pady=btn_pady_action, padx=2, fill="x")  #
                btn_dl_facture = ctk.CTkButton(action_buttons_frame, text="DL Facture", width=btn_width_action,
                                               command=lambda p=path_facture: self._action_telecharger_pj(p))  #
                btn_dl_facture.pack(pady=btn_pady_action, padx=2, fill="x")  #
            else:  #
                ctk.CTkLabel(action_buttons_frame, text="Facture N/A", font=value_font_info, anchor="center",
                             height=50).pack(pady=btn_pady_action, padx=2, fill="x")  #

            if path_facture and os.path.exists(path_facture) and demande_data.get("chemin_abs_rib") and os.path.exists(
                    demande_data.get("chemin_abs_rib")):  #
                sep = ctk.CTkFrame(action_buttons_frame, height=2, fg_color="gray50")  #
                sep.pack(fill="x", pady=8, padx=15)  #

            path_rib = demande_data.get("chemin_abs_rib")  #
            if path_rib and os.path.exists(path_rib):  #
                btn_voir_rib = ctk.CTkButton(action_buttons_frame, text="Voir RIB", width=btn_width_action,
                                             command=lambda p=path_rib: self._action_voir_pj(p))  #
                btn_voir_rib.pack(pady=btn_pady_action, padx=2, fill="x")  #
                btn_dl_rib = ctk.CTkButton(action_buttons_frame, text="DL RIB", width=btn_width_action,
                                           command=lambda p=path_rib: self._action_telecharger_pj(p))  #
                btn_dl_rib.pack(pady=btn_pady_action, padx=2, fill="x")  #
            else:  #
                ctk.CTkLabel(action_buttons_frame, text="RIB N/A", font=value_font_info, anchor="center",
                             height=50).pack(pady=btn_pady_action, padx=2, fill="x")  #

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
            chemin = self.remboursement_controller.selectionner_fichier_pdf(
                "Sélectionner la Facture PDF (Optionnel)")  #
            if chemin:  #
                self.chemin_facture_var.set(os.path.basename(chemin))  #
                self._entry_chemin_facture_complet = chemin  #
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

        btn_facture = ctk.CTkButton(form_frame, text="Choisir Facture (PDF, Optionnel)",
                                    command=selectionner_facture)  #
        btn_facture.grid(row=current_row, column=0, padx=5, pady=10, sticky="w")  #
        lbl_facture_sel = ctk.CTkLabel(form_frame, textvariable=self.chemin_facture_var, wraplength=300)  #
        lbl_facture_sel.grid(row=current_row, column=1, padx=5, pady=10, sticky="ew")  #
        current_row += 1  #

        def selectionner_rib():  #
            chemin = self.remboursement_controller.selectionner_fichier_pdf("Sélectionner le RIB PDF (Obligatoire)")  #
            if chemin:  #
                self.chemin_rib_var.set(os.path.basename(chemin))  #
                self._entry_chemin_rib_complet = chemin  #

        btn_rib = ctk.CTkButton(form_frame, text="Choisir RIB (PDF, Obligatoire)", command=selectionner_rib)  #
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