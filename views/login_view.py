# views/login_view.py
import customtkinter as ctk
from tkinter import messagebox, simpledialog

from utils.password_utils import check_password_strength


class LoginView(ctk.CTkFrame):
    def __init__(self, master, auth_controller, on_login_success_callback):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.master = master
        self.auth_controller = auth_controller
        self.on_login_success = on_login_success_callback
        self.pack(fill="both", expand=True)
        self.creer_widgets_connexion()

    def creer_widgets_connexion(self):
        main_frame = ctk.CTkFrame(self, width=380, height=420,
                                  corner_radius=10)
        main_frame.place(relx=0.5, rely=0.5, anchor="center")

        label_titre = ctk.CTkLabel(main_frame, text="Connexion Utilisateur", font=ctk.CTkFont(size=20, weight="bold"))
        label_titre.pack(pady=(30, 15))

        self.entry_utilisateur = ctk.CTkEntry(main_frame, placeholder_text="Nom d'utilisateur",
                                              width=250)
        self.entry_utilisateur.pack(pady=10, padx=20)
        self.entry_utilisateur.bind("<Return>", lambda event: self._action_connexion())

        self.entry_mdp = ctk.CTkEntry(main_frame, placeholder_text="Mot de passe", show="*",
                                      width=250)
        self.entry_mdp.pack(pady=5, padx=20)
        self.entry_mdp.bind("<Return>", lambda event: self._action_connexion())

        self.show_password_var_login = ctk.BooleanVar()
        ctk.CTkCheckBox(main_frame, text="Afficher le mot de passe", variable=self.show_password_var_login,
                        command=self._toggle_login_password_visibility).pack(padx=20, pady=(0, 10), anchor="w")

        bouton_connexion = ctk.CTkButton(main_frame, text="Se connecter", command=self._action_connexion,
                                         width=200)
        bouton_connexion.pack(pady=10, padx=20)

        bouton_modifier_mdp = ctk.CTkButton(main_frame, text="Modifier mon mot de passe",
                                            command=self._ouvrir_fenetre_modifier_mdp, width=220,
                                            fg_color="gray")
        bouton_modifier_mdp.pack(pady=6, padx=20)

        bouton_mdp_oublie = ctk.CTkButton(main_frame, text="Mot de passe oublié ?",
                                          command=self._ouvrir_fenetre_mdp_oublie_etape1, width=220,
                                          fg_color="gray")
        bouton_mdp_oublie.pack(pady=(6, 30), padx=20)

        self.after(100, self.entry_utilisateur.focus_set)

    def _toggle_login_password_visibility(self):
        show_char = "" if self.show_password_var_login.get() else "*"
        self.entry_mdp.configure(show=show_char)

    def _action_connexion(self):
        nom_utilisateur = self.entry_utilisateur.get()
        mot_de_passe = self.entry_mdp.get()

        if not nom_utilisateur or not mot_de_passe:
            messagebox.showerror("Erreur de saisie", "Veuillez entrer un nom d'utilisateur et un mot de passe.",
                                 parent=self.master)
            return

        utilisateur_connecte = self.auth_controller.tenter_connexion(nom_utilisateur, mot_de_passe)
        if utilisateur_connecte:
            self.focus_set()
            self.after(10, lambda: self.on_login_success(utilisateur_connecte))
        else:
            messagebox.showerror("Échec de la connexion", "Nom d'utilisateur ou mot de passe incorrect.",
                                 parent=self.master)
            self.entry_mdp.delete(0, 'end')

    def _ouvrir_fenetre_modifier_mdp(self):
        dialog = ctk.CTkToplevel(self.master)
        dialog.title("Modifier le mot de passe")
        dialog.geometry("480x520")
        dialog.transient(self.master)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Nom d'utilisateur:", font=ctk.CTkFont(size=14)).pack(pady=(20, 0))
        entry_user = ctk.CTkEntry(dialog, width=300, height=30)
        entry_user.pack(pady=5)

        ctk.CTkLabel(dialog, text="Ancien mot de passe:", font=ctk.CTkFont(size=14)).pack(pady=(10, 0))
        entry_ancien_mdp = ctk.CTkEntry(dialog, show="*", width=300, height=30)
        entry_ancien_mdp.pack(pady=5)

        ctk.CTkLabel(dialog, text="Nouveau mot de passe:", font=ctk.CTkFont(size=14)).pack(pady=(10, 0))
        entry_nouveau_mdp = ctk.CTkEntry(dialog, show="*", width=300, height=30)
        entry_nouveau_mdp.pack(pady=5)

        strength_progress = ctk.CTkProgressBar(dialog, progress_color="grey")
        strength_progress.set(0)
        strength_progress.pack(fill="x", padx=90, pady=(5, 2))
        strength_label = ctk.CTkLabel(dialog, text="", font=ctk.CTkFont(size=12))
        strength_label.pack(fill="x", padx=90)

        ctk.CTkLabel(dialog, text="Confirmer nouveau mot de passe:", font=ctk.CTkFont(size=14)).pack(pady=(10, 0))
        entry_confirm_mdp = ctk.CTkEntry(dialog, show="*", width=300, height=30)
        entry_confirm_mdp.pack(pady=5)

        def _update_strength(event=None):
            password = entry_nouveau_mdp.get()
            if not password:
                strength_label.configure(text="")
                strength_progress.set(0)
                return
            score, feedback = check_password_strength(password)
            progress = score / 5.0
            colors = {"Très faible": "#D32F2F", "Faible": "#F44336", "Moyen": "#FFC107", "Fort": "#4CAF50",
                      "Très fort": "#4CAF50"}
            color = colors.get(feedback, "grey")
            strength_progress.set(progress)
            strength_progress.configure(progress_color=color)
            strength_label.configure(text=feedback, text_color=color)

        entry_nouveau_mdp.bind("<KeyRelease>", _update_strength)

        show_password_var = ctk.BooleanVar()

        def _toggle_visibility():
            show_char = "" if show_password_var.get() else "*"
            entry_ancien_mdp.configure(show=show_char)
            entry_nouveau_mdp.configure(show=show_char)
            entry_confirm_mdp.configure(show=show_char)

        ctk.CTkCheckBox(dialog, text="Afficher les mots de passe", variable=show_password_var,
                        command=_toggle_visibility).pack(pady=10)

        def valider_modification():
            user = entry_user.get()
            ancien = entry_ancien_mdp.get()
            nouveau = entry_nouveau_mdp.get()
            confirm = entry_confirm_mdp.get()

            if not all([user, ancien, nouveau, confirm]):
                messagebox.showerror("Erreur", "Tous les champs sont requis.", parent=dialog)
                return
            if nouveau != confirm:
                messagebox.showerror("Erreur", "Le nouveau mot de passe et sa confirmation ne correspondent pas.",
                                     parent=dialog)
                return
            if len(nouveau) < 6:
                messagebox.showerror("Erreur", "Le nouveau mot de passe doit comporter au moins 6 caractères.",
                                     parent=dialog)
                return

            success, message = self.auth_controller.modifier_mot_de_passe(user, ancien, nouveau)
            if success:
                messagebox.showinfo("Succès", message, parent=dialog)
                dialog.destroy()
            else:
                messagebox.showerror("Erreur", message, parent=dialog)

        bouton_valider_modif = ctk.CTkButton(dialog, text="Valider la Modification", command=valider_modification,
                                             height=35)
        bouton_valider_modif.pack(pady=20)
        dialog.after(100, lambda: entry_user.focus_set())

    def _ouvrir_fenetre_mdp_oublie_etape1(self):
        nom_utilisateur = simpledialog.askstring("Mot de passe oublié - Étape 1",
                                                 "Veuillez entrer votre nom d'utilisateur:",
                                                 parent=self.master)
        if not nom_utilisateur:
            return

        succes_envoi, email_dest, message = self.auth_controller.demarrer_procedure_reset_mdp(nom_utilisateur)

        if succes_envoi:
            messagebox.showinfo("Code envoyé",
                                f"Un email avec un code de réinitialisation a été envoyé à {email_dest}.\n"
                                f"Veuillez vérifier votre boîte de réception (et vos spams).",
                                parent=self.master)
            self._ouvrir_fenetre_mdp_oublie_etape2(nom_utilisateur)
        else:
            if message and "Code pour test:" in message:
                messagebox.showwarning("Échec envoi email (Mode Test)",
                                       f"L'envoi de l'email à {email_dest} a échoué.\n"
                                       f"{message}",
                                       parent=self.master)
                self._ouvrir_fenetre_mdp_oublie_etape2(nom_utilisateur)
            else:
                messagebox.showerror("Erreur", message or "Impossible de démarrer la procédure de réinitialisation.",
                                     parent=self.master)

    def _ouvrir_fenetre_mdp_oublie_etape2(self, nom_utilisateur_pour_reset):
        dialog = ctk.CTkToplevel(self.master)
        dialog.title("Mot de passe oublié - Étape 2")
        dialog.geometry("480x480")
        dialog.transient(self.master)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=f"Réinitialisation pour : {nom_utilisateur_pour_reset}",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 5))
        ctk.CTkLabel(dialog, text="Veuillez entrer le code reçu par email et votre nouveau mot de passe.",
                     font=ctk.CTkFont(size=12)).pack(pady=5, padx=10)

        ctk.CTkLabel(dialog, text="Code de réinitialisation (5 chiffres):", font=ctk.CTkFont(size=14)).pack(
            pady=(10, 0))
        entry_code = ctk.CTkEntry(dialog, width=120, height=30, justify="center", font=ctk.CTkFont(size=14))
        entry_code.pack(pady=5)

        ctk.CTkLabel(dialog, text="Nouveau mot de passe:", font=ctk.CTkFont(size=14)).pack(pady=(10, 0))
        entry_nouveau_mdp = ctk.CTkEntry(dialog, show="*", width=250, height=30)
        entry_nouveau_mdp.pack(pady=5)

        strength_progress = ctk.CTkProgressBar(dialog, progress_color="grey")
        strength_progress.set(0)
        strength_progress.pack(fill="x", padx=115, pady=(5, 2))
        strength_label = ctk.CTkLabel(dialog, text="", font=ctk.CTkFont(size=12))
        strength_label.pack(fill="x", padx=115)

        ctk.CTkLabel(dialog, text="Confirmer nouveau mot de passe:", font=ctk.CTkFont(size=14)).pack(pady=(10, 0))
        entry_confirm_mdp = ctk.CTkEntry(dialog, show="*", width=250, height=30)
        entry_confirm_mdp.pack(pady=5)

        def _update_strength(event=None):
            password = entry_nouveau_mdp.get()
            if not password:
                strength_label.configure(text="")
                strength_progress.set(0)
                return
            score, feedback = check_password_strength(password)
            progress = score / 5.0
            colors = {"Très faible": "#D32F2F", "Faible": "#F44336", "Moyen": "#FFC107", "Fort": "#4CAF50",
                      "Très fort": "#4CAF50"}
            color = colors.get(feedback, "grey")
            strength_progress.set(progress)
            strength_progress.configure(progress_color=color)
            strength_label.configure(text=feedback, text_color=color)

        entry_nouveau_mdp.bind("<KeyRelease>", _update_strength)

        show_password_var = ctk.BooleanVar()

        def _toggle_visibility():
            show_char = "" if show_password_var.get() else "*"
            entry_nouveau_mdp.configure(show=show_char)
            entry_confirm_mdp.configure(show=show_char)

        ctk.CTkCheckBox(dialog, text="Afficher les mots de passe", variable=show_password_var,
                        command=_toggle_visibility).pack(pady=10)

        def valider_reset():
            code_saisi = entry_code.get()
            nouveau = entry_nouveau_mdp.get()
            confirm = entry_confirm_mdp.get()

            if not all([code_saisi, nouveau, confirm]):
                messagebox.showerror("Erreur", "Tous les champs sont requis.", parent=dialog)
                return
            if nouveau != confirm:
                messagebox.showerror("Erreur", "Le nouveau mot de passe et sa confirmation ne correspondent pas.",
                                     parent=dialog)
                return
            if len(nouveau) < 6:
                messagebox.showerror("Erreur", "Le nouveau mot de passe doit comporter au moins 6 caractères.",
                                     parent=dialog)
                return

            succes, msg_validation = self.auth_controller.verifier_code_et_reinitialiser_mdp(nom_utilisateur_pour_reset,
                                                                                             code_saisi, nouveau)
            if succes:
                messagebox.showinfo("Succès", msg_validation, parent=dialog)
                dialog.destroy()
            else:
                messagebox.showerror("Erreur", msg_validation, parent=dialog)

        bouton_valider_reset = ctk.CTkButton(dialog, text="Réinitialiser le mot de passe", command=valider_reset,
                                             height=35)
        bouton_valider_reset.pack(pady=20)

        dialog.after(100, lambda: entry_code.focus_set())