# views/admin_user_management_view.py
import customtkinter as ctk
from tkinter import messagebox, simpledialog
from config.settings import ASSIGNABLE_ROLES
from .admin_config_view import AdminConfigView


class AdminUserManagementView(ctk.CTkToplevel):
    def __init__(self, master, auth_controller):
        super().__init__(master)
        self.auth_controller = auth_controller

        self.title("Gestion des Utilisateurs (Admin)")
        self.geometry("850x600")
        self.transient(master)
        self.grab_set()
        self.resizable(True, True)
        self.minsize(700, 400)

        main_frame = ctk.CTkFrame(self)
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        title_label = ctk.CTkLabel(main_frame, text="Gestion des Utilisateurs",
                                   font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(pady=(10, 15))

        action_bar_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        action_bar_frame.pack(fill="x", pady=(0, 10))

        btn_show_roles_info = ctk.CTkButton(action_bar_frame, text="Informations sur les Rôles",
                                            command=self._show_role_descriptions)
        btn_show_roles_info.pack(side="left", padx=5)

        btn_config_smtp = ctk.CTkButton(action_bar_frame, text="Configurer E-mail (SMTP)",
                                        command=self._open_smtp_config_dialog,
                                        fg_color="#334155", hover_color="#475569")
        btn_config_smtp.pack(side="left", padx=5)

        btn_create_user = ctk.CTkButton(action_bar_frame, text="Créer un Utilisateur",
                                        command=self._open_create_user_dialog)
        btn_create_user.pack(side="left", padx=5)

        self.scrollable_frame = ctk.CTkScrollableFrame(main_frame, label_text="Utilisateurs enregistrés (sauf 'admin')")
        self.scrollable_frame.pack(expand=True, fill="both", padx=5, pady=(0, 5))
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        self.populate_user_list()

        close_button = ctk.CTkButton(main_frame, text="Fermer", command=self.destroy, width=100)
        close_button.pack(pady=10)

    def _open_smtp_config_dialog(self):
        AdminConfigView(self, self.auth_controller)

    def populate_user_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        utilisateurs = self.auth_controller.get_all_users_for_management()

        if not utilisateurs:
            ctk.CTkLabel(self.scrollable_frame, text="Aucun autre utilisateur à gérer.").pack(pady=10)
            return

        for i, user_data in enumerate(utilisateurs):
            user_login = user_data.get("login")
            user_email = user_data.get("email")
            user_roles_list = user_data.get("roles", [])
            user_roles_str = ", ".join(user_roles_list) if user_roles_list else "Aucun rôle assigné"

            item_frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=3)
            item_frame.pack(fill="x", pady=(2, 2), padx=4)

            item_frame.columnconfigure(0, weight=2)
            item_frame.columnconfigure(1, weight=2)
            item_frame.columnconfigure(2, weight=0)
            item_frame.columnconfigure(3, weight=0)

            info_text = f"{user_login}"
            ctk.CTkLabel(item_frame, text=info_text, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0,
                                                                                                       padx=5, pady=3,
                                                                                                       sticky="w")

            email_text = f"Email: {user_email}"
            ctk.CTkLabel(item_frame, text=email_text, anchor="w", font=ctk.CTkFont(size=11)).grid(row=1, column=0,
                                                                                                  padx=5, pady=(0, 3),
                                                                                                  sticky="w")

            roles_text = f"Rôles: {user_roles_str}"
            ctk.CTkLabel(item_frame, text=roles_text, anchor="w", font=ctk.CTkFont(size=11), wraplength=250).grid(row=0,
                                                                                                                  rowspan=2,
                                                                                                                  column=1,
                                                                                                                  padx=5,
                                                                                                                  pady=3,
                                                                                                                  sticky="w")

            if user_login != "admin":
                modify_button = ctk.CTkButton(
                    item_frame,
                    text="Modifier",
                    width=70,
                    command=lambda u_login=user_login, u_email=user_email,
                                   u_roles=user_roles_list: self._open_modify_user_dialog(u_login, u_email, u_roles)
                )
                modify_button.grid(row=0, rowspan=2, column=2, padx=(10, 2), pady=5, sticky="e")

                delete_button = ctk.CTkButton(
                    item_frame,
                    text="Supprimer",
                    width=70,
                    fg_color="red",
                    hover_color="darkred",
                    command=lambda u=user_login: self._confirm_delete_user(u)
                )
                delete_button.grid(row=0, rowspan=2, column=3, padx=(2, 5), pady=5, sticky="e")

    def _confirm_delete_user(self, username_to_delete: str):
        if messagebox.askyesno("Confirmation de Suppression",
                               f"Êtes-vous sûr de vouloir supprimer l'utilisateur '{username_to_delete}' ?\n"
                               "Cette action est irréversible.",
                               icon=messagebox.WARNING, parent=self):

            succes, message = self.auth_controller.admin_delete_user(username_to_delete)
            if succes:
                messagebox.showinfo("Suppression Réussie", message, parent=self)
                self.populate_user_list()
            else:
                messagebox.showerror("Erreur de Suppression", message, parent=self)

    def _open_create_user_dialog(self):
        self._open_user_form_dialog(mode="create")

    def _open_modify_user_dialog(self, login: str, current_email: str, current_roles: list):
        self._open_user_form_dialog(mode="modify", login_original=login, email_actuel=current_email,
                                    roles_actuels=current_roles)

    def _open_user_form_dialog(self, mode: str, login_original: str = "", email_actuel: str = "",
                               roles_actuels: list | None = None):
        if roles_actuels is None: roles_actuels = []

        title = "Créer un Nouvel Utilisateur" if mode == "create" else f"Modifier Utilisateur: {login_original}"

        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("550x550")
        dialog.transient(self)
        dialog.grab_set()

        form_frame = ctk.CTkFrame(dialog)
        form_frame.pack(expand=True, fill="both", padx=20, pady=20)

        ctk.CTkLabel(form_frame, text="Login:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        login_entry = ctk.CTkEntry(form_frame, width=250)
        login_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        if mode == "modify":
            login_entry.insert(0, login_original)

        ctk.CTkLabel(form_frame, text="Email:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        email_entry = ctk.CTkEntry(form_frame, width=250)
        email_entry.insert(0, email_actuel if mode == "modify" else "")
        email_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(form_frame, text="Mot de passe:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        password_entry = ctk.CTkEntry(form_frame, width=250, show="*")
        password_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        if mode == "modify":
            password_entry.configure(placeholder_text="Laisser vide pour ne pas changer")

        ctk.CTkLabel(form_frame, text="Rôles:").grid(row=3, column=0, padx=5, pady=(10, 0), sticky="nw")

        roles_scroll_frame = ctk.CTkScrollableFrame(form_frame, height=150)
        roles_scroll_frame.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        role_vars = {}
        assignable_roles_list = self.auth_controller.get_assignable_roles()
        for role_name in assignable_roles_list:
            var = ctk.StringVar(value="on" if role_name in roles_actuels else "off")
            cb = ctk.CTkCheckBox(roles_scroll_frame, text=role_name, variable=var, onvalue="on", offvalue="off")
            cb.pack(anchor="w", padx=10, pady=2)
            role_vars[role_name] = var

        def _submit_user_form():
            login_val = login_entry.get().strip()
            email_val = email_entry.get().strip()
            password_val = password_entry.get().strip()
            selected_roles = [role for role, var in role_vars.items() if var.get() == "on"]

            if mode == "create":
                if not password_val:
                    messagebox.showerror("Erreur", "Le mot de passe est requis pour créer un utilisateur.",
                                         parent=dialog)
                    return
                succes, message = self.auth_controller.admin_create_user(login_val, email_val, password_val,
                                                                         selected_roles)
            else:
                succes, message = self.auth_controller.admin_update_user_details(login_original, login_val, email_val,
                                                                                 selected_roles,
                                                                                 password_val if password_val else None)

            if succes:
                messagebox.showinfo("Succès", message, parent=self)
                self.populate_user_list()
                dialog.destroy()
            else:
                messagebox.showerror("Erreur", message, parent=dialog)

        submit_button_text = "Créer Utilisateur" if mode == "create" else "Enregistrer Modifications"
        submit_button = ctk.CTkButton(form_frame, text=submit_button_text, command=_submit_user_form)
        submit_button.grid(row=4, column=0, columnspan=2, pady=20)

        dialog.after(100, lambda: login_entry.focus_set() if mode == "create" else email_entry.focus_set())

    def _show_role_descriptions(self):
        descriptions_data = self.auth_controller.get_role_descriptions_with_users()

        desc_window = ctk.CTkToplevel(self)
        desc_window.title("Description des Rôles et Utilisateurs Associés")
        desc_window.geometry("750x550")
        desc_window.transient(self)
        desc_window.grab_set()

        scroll_frame = ctk.CTkScrollableFrame(desc_window)
        scroll_frame.pack(expand=True, fill="both", padx=10, pady=10)

        for role, data in descriptions_data.items():
            desc = data.get("description", "Pas de description.")
            users_with_role = data.get("utilisateurs_actuels", [])

            ctk.CTkLabel(scroll_frame, text=f"{role.replace('_', ' ').title()}:",
                         font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 2))

            desc_textbox = ctk.CTkTextbox(scroll_frame, wrap="word", height=(desc.count('\n') + 2) * 18,
                                          activate_scrollbars=False, border_width=0,
                                          fg_color="transparent")
            desc_textbox.insert("1.0", desc)
            desc_textbox.configure(state="disabled")
            desc_textbox.pack(anchor="w", fill="x", padx=10, pady=(0, 5))

            if users_with_role:
                ctk.CTkLabel(scroll_frame, text="  Utilisateurs ayant ce rôle:",
                             font=ctk.CTkFont(size=11, slant="italic")).pack(anchor="w", padx=10)
                users_str = "\n".join([f"    - {user}" for user in users_with_role])
                ctk.CTkLabel(scroll_frame, text=users_str, justify="left", anchor="w", font=ctk.CTkFont(size=11)).pack(
                    anchor="w", padx=20, pady=(0, 10))
            else:
                ctk.CTkLabel(scroll_frame, text="  Aucun utilisateur n'a actuellement ce rôle.",
                             font=ctk.CTkFont(size=11, slant="italic")).pack(anchor="w", padx=10, pady=(0, 10))

            ctk.CTkFrame(scroll_frame, height=1, fg_color="gray50").pack(fill="x", pady=5)

        ctk.CTkButton(desc_window, text="Fermer", command=desc_window.destroy).pack(pady=10)