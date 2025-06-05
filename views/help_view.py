# views/help_view.py
import customtkinter as ctk
from config.settings import ROLES_UTILISATEURS, ASSIGNABLE_ROLES
from models import user_model  # Pour récupérer les utilisateurs par rôle

# Récupérer les couleurs définies dans MainView ou settings.py si elles y sont
# Pour cet exemple, je vais les redéfinir ici pour la démo de la légende.
# Idéalement, elles seraient importées d'un endroit commun.
COULEUR_ACTIVE_POUR_UTILISATEUR = "#1E4D2B"
COULEUR_DEMANDE_TERMINEE = "#2E4374"
COULEUR_DEMANDE_ANNULEE = "#6A040F"


class HelpView(ctk.CTkToplevel):
    def __init__(self, master, current_user_name: str, user_roles: list):
        super().__init__(master)
        self.current_user_name = current_user_name
        self.user_roles = user_roles

        self.title("Aide - Gestion des Remboursements")
        self.geometry("750x650")  # Taille ajustable
        self.transient(master)
        self.grab_set()
        self.resizable(True, True)
        self.minsize(500, 400)

        # Frame principal scrollable
        scrollable_frame = ctk.CTkScrollableFrame(self)
        scrollable_frame.pack(expand=True, fill="both", padx=15, pady=15)

        # --- Section Introduction ---
        intro_label = ctk.CTkLabel(scrollable_frame,
                                   text="Bienvenue dans l'Application de Gestion des Remboursements !",
                                   font=ctk.CTkFont(size=18, weight="bold"))
        intro_label.pack(pady=(0, 10), anchor="w")

        intro_text = (
            "Cette application vous permet de suivre et de gérer le processus de remboursement des trop-perçus "
            "clients. Chaque utilisateur a des actions spécifiques en fonction de son rôle.")
        ctk.CTkLabel(scrollable_frame, text=intro_text, wraplength=680, justify="left").pack(anchor="w", pady=(0, 15))

        # --- Section Légende des Couleurs ---
        self._creer_legende(scrollable_frame)

        # --- Section Aide par Rôle ---
        ctk.CTkLabel(scrollable_frame, text="Fonctionnalités selon votre/vos rôle(s) :",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5), anchor="w")

        displayed_roles_help = set()

        for role in self.user_roles:
            if role in ROLES_UTILISATEURS and role not in displayed_roles_help:
                role_data = ROLES_UTILISATEURS[role]
                ctk.CTkLabel(scrollable_frame, text=f"En tant que {role.replace('_', ' ').title()} :",
                             font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 2), anchor="w")

                # Utiliser un Textbox pour un meilleur formatage des descriptions multilignes
                desc_box = ctk.CTkTextbox(scrollable_frame, wrap="word", activate_scrollbars=False, border_width=0,
                                          fg_color="transparent")
                desc_box.insert("1.0", role_data.get("description", "Aucune description disponible."))

                # Ajuster la hauteur du Textbox en fonction du contenu
                desc_box.configure(state="disabled")  # Pour le rendre non-éditable et calculer la hauteur
                # Le calcul de la hauteur est complexe ; pour l'instant, on donne une hauteur fixe ou on se base sur le nombre de lignes.
                # Ou on laisse le scrollable frame principal gérer si le texte est très long.
                num_lines = role_data.get("description", "").count('\n') + 5  # Estimation grossière
                desc_box.configure(height=num_lines * 18)  # Ajuster le multiplicateur au besoin
                desc_box.pack(fill="x", padx=(10, 0), pady=(0, 10), anchor="w")
                displayed_roles_help.add(role)

        if "admin" not in self.user_roles and not displayed_roles_help:  # Si aucun rôle spécifique n'a d'aide
            ctk.CTkLabel(scrollable_frame,
                         text="Aucune fonctionnalité spécifique à votre rôle principal n'est détaillée ici, "
                              "vous avez probablement un accès général ou de visualisation.",
                         wraplength=680, justify="left").pack(anchor="w", pady=(0, 15))

        # --- Section Spécifique Admin ---
        if "admin" in self.user_roles:
            ctk.CTkLabel(scrollable_frame, text="Consignes Spéciales pour l'Administrateur :",
                         font=ctk.CTkFont(size=16, weight="bold", underline=True)).pack(pady=(20, 5), anchor="w")

            admin_intro = ("En tant qu'administrateur, vous disposez de droits étendus sur l'application. "
                           "Ces droits vous permettent de superviser et de corriger le flux de travail, "
                           "mais impliquent également de grandes responsabilités. Veuillez utiliser ces fonctionnalités avec prudence.")
            ctk.CTkLabel(scrollable_frame, text=admin_intro, wraplength=680, justify="left").pack(anchor="w",
                                                                                                  pady=(0, 10))

            admin_warnings = [
                ("Suppression de demandes :",
                 "Cette action est IRRÉVERSIBLE. Elle supprime définitivement la demande et tous les fichiers associés (factures, RIBs, preuves). Assurez-vous qu'une demande doit réellement être supprimée."),
                ("Gestion des utilisateurs :",
                 "La modification ou suppression d'un utilisateur peut impacter sa capacité à se connecter ou la traçabilité de ses actions passées (par exemple, si son login est modifié)."),
                ("Rôle 'admin' :",
                 "Il est crucial de ne pas supprimer le compte 'admin' principal ou de ne pas lui retirer son rôle 'admin', car cela pourrait bloquer l'accès aux fonctions d'administration.")
            ]
            for warning_title, warning_text in admin_warnings:
                ctk.CTkLabel(scrollable_frame, text=warning_title, font=ctk.CTkFont(size=13, weight="bold")).pack(
                    anchor="w", pady=(5, 0), padx=5)
                ctk.CTkLabel(scrollable_frame, text=warning_text, wraplength=670, justify="left").pack(anchor="w",
                                                                                                       padx=15,
                                                                                                       pady=(0, 5))

            admin_capabilities_title = ROLES_UTILISATEURS.get("admin", {}).get("description",
                                                                               "Droits étendus sur toutes les fonctionnalités.")
            ctk.CTkLabel(scrollable_frame, text="\nFonctionnalités Administrateur :",
                         font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 2))

            admin_desc_box = ctk.CTkTextbox(scrollable_frame, wrap="word", activate_scrollbars=False, border_width=0,
                                            fg_color="transparent")
            admin_desc_box.insert("1.0", admin_capabilities_title)
            num_lines_admin = admin_capabilities_title.count('\n') + 5
            admin_desc_box.configure(height=num_lines_admin * 18, state="disabled")
            admin_desc_box.pack(fill="x", padx=(10, 0), pady=(0, 10), anchor="w")

        close_button = ctk.CTkButton(self, text="Fermer", command=self.destroy, width=100)
        close_button.pack(pady=10, side="bottom")

    def _creer_legende(self, parent_frame):
        legende_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        legende_frame.pack(fill="x", pady=(10, 15), anchor="w")

        ctk.CTkLabel(legende_frame, text="Légende des couleurs des demandes :", font=ctk.CTkFont(weight="bold")).pack(
            side="left", padx=(0, 10))

        legend_items = [
            ("Action Requise par Vous", COULEUR_ACTIVE_POUR_UTILISATEUR),
            ("Demande Terminée", COULEUR_DEMANDE_TERMINEE),
            ("Demande Annulée", COULEUR_DEMANDE_ANNULEE),
        ]
        for texte, couleur_fond in legend_items:
            item_legende = ctk.CTkFrame(legende_frame, fg_color="transparent")
            item_legende.pack(side="left", padx=5)
            ctk.CTkFrame(item_legende, width=15, height=15, fg_color=couleur_fond, border_width=1).pack(side="left")
            ctk.CTkLabel(item_legende, text=texte, font=ctk.CTkFont(size=11)).pack(side="left", padx=3)