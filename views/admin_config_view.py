# views/admin_config_view.py
import customtkinter as ctk
from tkinter import messagebox


class AdminConfigView(ctk.CTkToplevel):
    def __init__(self, master, auth_controller):
        super().__init__(master)
        self.transient(master)
        self.grab_set()
        self.title("Configuration des E-mails (SMTP)")
        self.geometry("550x450")

        self.auth_controller = auth_controller
        self.config_data = self.auth_controller.get_smtp_config()

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        self.entries = {}
        fields = {
            "server": "Serveur SMTP:",
            "port": "Port:",
            "email_sender": "E-mail de l'expéditeur:",
            "password": "Mot de passe d'application:",
            "use_tls": "Utiliser TLS (True/False):",
            "use_ssl": "Utiliser SSL (True/False):"
        }

        for i, (key, label) in enumerate(fields.items()):
            ctk.CTkLabel(self.main_frame, text=label).grid(row=i, column=0, padx=10, pady=8, sticky="w")
            entry = ctk.CTkEntry(self.main_frame, width=250)
            if key == "password":
                entry.configure(show="*")
            entry.insert(0, self.config_data.get(key, ""))
            entry.grid(row=i, column=1, padx=10, pady=8, sticky="ew")
            self.entries[key] = entry

        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)

        ctk.CTkButton(button_frame, text="Tester la Connexion", command=self._test_connection).pack(side="left",
                                                                                                    padx=10)
        ctk.CTkButton(button_frame, text="Enregistrer", command=self._save_config).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Annuler", command=self.destroy, fg_color="gray").pack(side="left", padx=10)

    def _get_current_values(self):
        """Récupère les valeurs actuelles des champs d'entrée."""
        return {key: entry.get() for key, entry in self.entries.items()}

    def _test_connection(self):
        current_config = self._get_current_values()
        # Convertir port en int et booléens pour le test
        try:
            current_config['port'] = int(current_config.get('port', 587))
            current_config['use_tls'] = current_config.get('use_tls', 'true').lower() in ('true', '1', 't')
            current_config['use_ssl'] = current_config.get('use_ssl', 'false').lower() in ('true', '1', 't')
        except ValueError:
            messagebox.showerror("Erreur", "Le port doit être un nombre.", parent=self)
            return

        is_ok, message = self.auth_controller.test_smtp_connection(current_config)
        if is_ok:
            messagebox.showinfo("Succès", "La connexion au serveur SMTP a réussi !", parent=self)
        else:
            messagebox.showerror("Échec de la Connexion",
                                 f"Impossible de se connecter au serveur SMTP.\n\nErreur : {message}", parent=self)

    def _save_config(self):
        new_config_data = self._get_current_values()
        success, message = self.auth_controller.save_smtp_config(new_config_data)
        if success:
            messagebox.showinfo("Succès",
                                "Configuration enregistrée.\nL'application doit être redémarrée pour appliquer les changements.",
                                parent=self)
            self.destroy()
        else:
            messagebox.showerror("Erreur", f"Impossible d'enregistrer la configuration : {message}", parent=self)