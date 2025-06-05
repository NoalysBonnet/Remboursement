import customtkinter as ctk
from tkinter import messagebox, simpledialog
import logging
from utils.email_utils import envoyer_email_reinitialisation  # C'est cet import qui cause problème
from config.settings import SMTP_CONFIG


class LoginView(ctk.CTkFrame):
    def __init__(self, master_frame, auth_controller, on_login_success_callback, true_root_window):
        super().__init__(master_frame, corner_radius=0, fg_color="transparent")
        self.master_frame = master_frame
        self.true_root_window = true_root_window
        self.auth_controller = auth_controller
        self.on_login_success = on_login_success_callback
        self.pack(expand=True, fill="both")
        self._creer_widgets()

    def _creer_widgets(self):
        main_frame = ctk.CTkFrame(self, corner_radius=15)
        main_frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(main_frame, text="Connexion", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(20, 15))

        ctk.CTkLabel(main_frame, text="Nom d'utilisateur:").pack(padx=20, pady=(10, 2), anchor="w")
        self.entry_nom_utilisateur = ctk.CTkEntry(main_frame, width=250)
        self.entry_nom_utilisateur.pack(padx=20, pady=(0, 10), fill="x")

        ctk.CTkLabel(main_frame, text="Mot de passe:").pack(padx=20, pady=(5, 2), anchor="w")
        self.entry_mot_de_passe = ctk.CTkEntry(main_frame, show="*", width=250)
        self.entry_mot_de_passe.pack(padx=20, pady=(0, 10), fill="x")
        self.entry_mot_de_passe.bind("<Return>", self._action_connexion)

        self.bouton_connexion = ctk.CTkButton(main_frame, text="Se Connecter", command=self._action_connexion,
                                              height=35)
        self.bouton_connexion.pack(padx=20, pady=15, fill="x")

        options_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        options_frame.pack(padx=20, pady=(0, 20), fill="x")

        bouton_mdp_oublie = ctk.CTkButton(options_frame, text="Mot de passe oublié ?",
                                          command=self._ouvrir_fenetre_mdp_oublie_etape1, fg_color="transparent",
                                          text_color=("gray10", "gray90"), hover=False,
                                          font=ctk.CTkFont(size=12, underline=True))
        bouton_mdp_oublie.pack(side="left")

        self.entry_nom_utilisateur.after(100, lambda: self.entry_nom_utilisateur.focus_set())

    def _action_connexion(self, event=None):
        nom_utilisateur = self.entry_nom_utilisateur.get()
        mot_de_passe = self.entry_mot_de_passe.get()

        if not nom_utilisateur or not mot_de_passe:
            messagebox.showerror("Erreur de saisie", "Veuillez entrer un nom d'utilisateur et un mot de passe.",
                                 parent=self.true_root_window)
            return

        utilisateur_connecte, message_erreur = self.auth_controller.connecter_utilisateur(nom_utilisateur, mot_de_passe)

        if utilisateur_connecte:
            self.on_login_success(nom_utilisateur)
        else:
            messagebox.showerror("Échec de la connexion",
                                 message_erreur or "Nom d'utilisateur ou mot de passe incorrect.",
                                 parent=self.true_root_window)
            self.entry_mot_de_passe.delete(0, "end")

    def _ouvrir_fenetre_modifier_mdp(self):
        dialog = ctk.CTkToplevel(self.true_root_window)
        dialog.title("Modifier le mot de passe")
        dialog.geometry("400x350")
        dialog.transient(self.true_root_window)
        dialog.grab_set()
        dialog.attributes("-topmost", True)

        ctk.CTkLabel(dialog, text="Nom d'utilisateur actuel:").pack(pady=5, padx=20, anchor="w")
        entry_user = ctk.CTkEntry(dialog, width=300)
        entry_user.pack(pady=(0, 10), padx=20, fill="x")

        ctk.CTkLabel(dialog, text="Ancien mot de passe:").pack(pady=5, padx=20, anchor="w")
        entry_old_pass = ctk.CTkEntry(dialog, show="*", width=300)
        entry_old_pass.pack(pady=(0, 10), padx=20, fill="x")

        ctk.CTkLabel(dialog, text="Nouveau mot de passe:").pack(pady=5, padx=20, anchor="w")
        entry_new_pass = ctk.CTkEntry(dialog, show="*", width=300)
        entry_new_pass.pack(pady=(0, 10), padx=20, fill="x")

        ctk.CTkLabel(dialog, text="Confirmer nouveau mot de passe:").pack(pady=5, padx=20, anchor="w")
        entry_confirm_pass = ctk.CTkEntry(dialog, show="*", width=300)
        entry_confirm_pass.pack(pady=(0, 10), padx=20, fill="x")

        def _valider_modification():
            user = entry_user.get()
            old_pass = entry_old_pass.get()
            new_pass = entry_new_pass.get()
            confirm_pass = entry_confirm_pass.get()

            if not all([user, old_pass, new_pass, confirm_pass]):
                messagebox.showerror("Erreur", "Tous les champs sont requis.", parent=dialog)
                return
            if new_pass != confirm_pass:
                messagebox.showerror("Erreur", "Les nouveaux mots de passe ne correspondent pas.", parent=dialog)
                return

            is_strong, message_strength = self.auth_controller.valider_force_mot_de_passe(new_pass)
            if not is_strong:
                messagebox.showerror("Mot de passe faible", message_strength, parent=dialog)
                return

            success, msg = self.auth_controller.modifier_mot_de_passe_utilisateur(user, old_pass, new_pass)
            if success:
                messagebox.showinfo("Succès", msg, parent=dialog)
                dialog.destroy()
            else:
                messagebox.showerror("Erreur", msg, parent=dialog)

        ctk.CTkButton(dialog, text="Valider", command=_valider_modification).pack(pady=20)
        dialog.after(100, entry_user.focus_set)

    def _ouvrir_fenetre_mdp_oublie_etape1(self):
        if not SMTP_CONFIG:  # Vérifier si la configuration SMTP est chargée
            messagebox.showerror("Fonctionnalité non disponible",
                                 "La configuration pour l'envoi d'e-mails est manquante ou invalide.\n"
                                 "Veuillez contacter l'administrateur.",
                                 parent=self.true_root_window)
            return

        nom_utilisateur_pour_reset = simpledialog.askstring(
            "Mot de passe oublié - Étape 1",
            "Veuillez entrer votre nom d'utilisateur:",
            parent=self.true_root_window
        )
        if nom_utilisateur_pour_reset:
            user_info = self.auth_controller.obtenir_info_utilisateur(nom_utilisateur_pour_reset)
            if not user_info or not user_info.get("email"):
                messagebox.showerror("Erreur", "Nom d'utilisateur inconnu ou email non configuré pour ce compte.",
                                     parent=self.true_root_window)
                return

            code_reset = self.auth_controller.generer_et_stocker_code_reset(nom_utilisateur_pour_reset)
            if code_reset:
                email_destinataire = user_info["email"]
                sujet = "Réinitialisation de votre mot de passe - Gestion Remboursements"
                corps = (f"Bonjour {nom_utilisateur_pour_reset},\n\n"
                         f"Vous avez demandé une réinitialisation de mot de passe pour l'application Gestion Remboursements.\n"
                         f"Votre code de réinitialisation est : {code_reset}\n\n"
                         f"Ce code est valable pendant 5 minutes.\n"
                         f"Si vous n'avez pas demandé cette réinitialisation, veuillez ignorer cet e-mail.")

                try:
                    envoye, message_envoi = envoyer_email_reinitialisation(SMTP_CONFIG, email_destinataire, sujet,
                                                                           corps)
                    if envoye:
                        messagebox.showinfo("Email envoyé",
                                            f"Un code de réinitialisation a été envoyé à {email_destinataire}.",
                                            parent=self.true_root_window)
                        self._ouvrir_fenetre_mdp_oublie_etape2(nom_utilisateur_pour_reset)
                    else:
                        messagebox.showerror("Erreur d'envoi",
                                             f"Impossible d'envoyer l'email de réinitialisation.\nErreur: {message_envoi}",
                                             parent=self.true_root_window)
                except Exception as e:
                    logging.error(f"Erreur lors de l'envoi de l'email de réinitialisation: {e}", exc_info=True)
                    messagebox.showerror("Erreur Critique",
                                         "Une erreur critique est survenue lors de l'envoi de l'email.",
                                         parent=self.true_root_window)
            else:
                messagebox.showerror("Erreur", "Impossible de générer un code de réinitialisation.",
                                     parent=self.true_root_window)

    def _ouvrir_fenetre_mdp_oublie_etape2(self, nom_utilisateur_pour_reset):
        dialog = ctk.CTkToplevel(self.true_root_window)
        dialog.title("Mot de passe oublié - Étape 2")
        dialog.geometry("450x380")
        dialog.transient(self.true_root_window)
        dialog.grab_set()
        dialog.attributes("-topmost", True)

        ctk.CTkLabel(dialog, text=f"Un code a été envoyé à l'adresse email associée à '{nom_utilisateur_pour_reset}'.",
                     wraplength=400).pack(pady=10, padx=20)

        ctk.CTkLabel(dialog, text="Code de réinitialisation:").pack(pady=(10, 2), padx=20, anchor="w")
        entry_code = ctk.CTkEntry(dialog, width=300)
        entry_code.pack(pady=(0, 10), padx=20, fill="x")

        ctk.CTkLabel(dialog, text="Nouveau mot de passe:").pack(pady=(5, 2), padx=20, anchor="w")
        entry_nouveau_mdp = ctk.CTkEntry(dialog, show="*", width=300)
        entry_nouveau_mdp.pack(pady=(0, 10), padx=20, fill="x")

        ctk.CTkLabel(dialog, text="Confirmer nouveau mot de passe:").pack(pady=(5, 2), padx=20, anchor="w")
        entry_confirmer_mdp = ctk.CTkEntry(dialog, show="*", width=300)
        entry_confirmer_mdp.pack(pady=(0, 10), padx=20, fill="x")

        def _valider_reinitialisation():
            code = entry_code.get()
            nouveau_mdp = entry_nouveau_mdp.get()
            confirmer_mdp = entry_confirmer_mdp.get()

            if not all([code, nouveau_mdp, confirmer_mdp]):
                messagebox.showerror("Erreur", "Tous les champs sont requis.", parent=dialog)
                return

            if nouveau_mdp != confirmer_mdp:
                messagebox.showerror("Erreur", "Les nouveaux mots de passe ne correspondent pas.", parent=dialog)
                return

            is_strong, message_strength = self.auth_controller.valider_force_mot_de_passe(nouveau_mdp)
            if not is_strong:
                messagebox.showerror("Mot de passe faible", message_strength, parent=dialog)
                return

            code_valide = self.auth_controller.verifier_et_supprimer_code_reset(nom_utilisateur_pour_reset, code)
            if not code_valide:
                messagebox.showerror("Erreur", "Code de réinitialisation invalide ou expiré.", parent=dialog)
                return

            reinitialisation_ok, msg_reinit = self.auth_controller.reinitialiser_mot_de_passe_utilisateur(
                nom_utilisateur_pour_reset, nouveau_mdp)
            if reinitialisation_ok:
                messagebox.showinfo("Succès", "Votre mot de passe a été réinitialisé avec succès.", parent=dialog)
                dialog.destroy()
            else:
                messagebox.showerror("Erreur", msg_reinit or "Impossible de réinitialiser le mot de passe.",
                                     parent=dialog)

        ctk.CTkButton(dialog, text="Réinitialiser le mot de passe", command=_valider_reinitialisation).pack(pady=20)
        dialog.after(100, entry_code.focus_set)