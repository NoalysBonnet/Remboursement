import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont
import os

from views.profile_view import ProfileView
from views.admin_user_management_view import AdminUserManagementView
from views.help_view import HelpView
from utils.image_utils import create_circular_image
from config.settings import PROFILE_PICTURES_DIR


def creer_barre_superieure(main_view: ctk.CTkFrame):
    top_bar = ctk.CTkFrame(main_view.main_content_frame, fg_color="transparent")
    top_bar.pack(fill="x", padx=10, pady=(10, 5), anchor="n")

    main_view.user_info_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
    main_view.user_info_frame.pack(side="left", padx=5, pady=2)

    main_view.pfp_label = ctk.CTkLabel(main_view.user_info_frame, text="", width=main_view.pfp_size,
                                       height=main_view.pfp_size)
    main_view.pfp_label.pack(side="left")

    main_view.user_name_label = ctk.CTkLabel(main_view.user_info_frame, text="", font=ctk.CTkFont(size=18, weight="bold"))
    main_view.user_name_label.pack(side="left", padx=15)

    update_user_display(main_view)

    right_buttons_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
    right_buttons_frame.pack(side="right")

    bouton_profil = ctk.CTkButton(right_buttons_frame, text="Mon Profil", command=main_view._open_profile_view,
                                  width=100, fg_color="gray")
    bouton_profil.pack(side="left", padx=5)

    bouton_aide = ctk.CTkButton(right_buttons_frame, text="Aide", command=lambda: open_help_view(main_view), width=70)
    bouton_aide.pack(side="left", padx=5)

    bouton_deconnexion = ctk.CTkButton(right_buttons_frame, text="Déconnexion",
                                       command=main_view.app_controller.on_logout, width=120)
    bouton_deconnexion.pack(side="left", padx=(5, 0))

    label_titre_principal = ctk.CTkLabel(main_view.main_content_frame, text="Tableau de Bord - Remboursements",
                                         font=ctk.CTkFont(size=24, weight="bold"))
    label_titre_principal.pack(pady=(10, 10), anchor="n")


def update_user_display(main_view: ctk.CTkFrame):
    pfp_path = main_view.user_data.get("profile_picture_path")
    pfp_image = None
    if pfp_path:
        full_pfp_path = os.path.join(PROFILE_PICTURES_DIR, pfp_path)
        if os.path.exists(full_pfp_path):
            pfp_image = create_circular_image(full_pfp_path, main_view.pfp_size)

    if not pfp_image:
        placeholder = Image.new('RGBA', (main_view.pfp_size, main_view.pfp_size), (80, 80, 80, 255))
        draw = ImageDraw.Draw(placeholder)
        try:
            font = ImageFont.truetype("arial", 45)
        except IOError:
            font = ImageFont.load_default()
        draw.text((main_view.pfp_size / 2, main_view.pfp_size / 2), main_view.nom_utilisateur[0].upper(), font=font,
                  anchor="mm")
        pfp_image = ctk.CTkImage(light_image=placeholder, dark_image=placeholder,
                                 size=(main_view.pfp_size, main_view.pfp_size))

    main_view.pfp_label.configure(image=pfp_image)
    main_view.pfp_label.image = pfp_image

    roles_str = f" (Rôles: {', '.join(main_view.user_roles)})" if main_view.user_roles else ""
    main_view.user_name_label.configure(text=f"{main_view.nom_utilisateur}{roles_str}")


def creer_section_actions_et_options(main_view: ctk.CTkFrame):
    from views.dialogs.creation_demande_dialog import CreationDemandeDialog

    actions_bar_frame = ctk.CTkFrame(main_view.main_content_frame, fg_color="transparent")
    actions_bar_frame.pack(pady=(0, 5), padx=10, fill="x", anchor="n")

    if main_view.peut_creer_demande():
        bouton_nouvelle_demande = ctk.CTkButton(actions_bar_frame, text="Nouvelle Demande",
                                                command=lambda: CreationDemandeDialog(main_view,
                                                                                      main_view.remboursement_controller))
        bouton_nouvelle_demande.pack(side="left", pady=5, padx=(0, 10))

    main_view.bouton_rafraichir = ctk.CTkButton(actions_bar_frame, text="Rafraîchir (F5)",
                                           command=lambda: main_view.afficher_liste_demandes(force_reload=True),
                                           width=120)
    main_view.bouton_rafraichir.pack(side="left", pady=5, padx=10)

    main_view.notification_badge = ctk.CTkLabel(main_view.bouton_rafraichir, text="", fg_color="red", corner_radius=8,
                                           width=18, height=18, font=("Arial", 11, "bold"))

    if main_view.est_admin():
        btn_admin_users = ctk.CTkButton(actions_bar_frame, text="Gérer Utilisateurs",
                                        command=lambda: open_admin_user_management_view(main_view),
                                        fg_color="#555555", hover_color="#444444")
        btn_admin_users.pack(side="left", pady=5, padx=10)

        btn_purge_archives = ctk.CTkButton(actions_bar_frame, text="Purger les Archives",
                                           command=main_view._action_admin_purge_archives,
                                           fg_color="#9D0208", hover_color="#6A040F")
        btn_purge_archives.pack(side="left", pady=5, padx=10)

    options_frame = ctk.CTkFrame(actions_bar_frame, fg_color="transparent")
    options_frame.pack(side="right", pady=5)

    ctk.CTkLabel(options_frame, text="Trier par:").pack(side="left", padx=(10, 5))
    sort_options = ["Date de création (récent)", "Date de création (ancien)", "Montant (décroissant)",
                    "Montant (croissant)", "Nom du patient (A-Z)"]
    main_view.sort_menu = ctk.CTkOptionMenu(options_frame, values=sort_options, command=main_view._set_sort, width=180)
    main_view.sort_menu.set(main_view.current_sort)
    main_view.sort_menu.pack(side="left", padx=(0, 10))

    ctk.CTkLabel(options_frame, text="Filtrer par:").pack(side="left", padx=(10, 5))
    filter_options = ["Toutes les demandes", "En attente de mon action", "En cours", "Terminées et annulées"]
    main_view.filter_menu = ctk.CTkOptionMenu(options_frame, values=filter_options, command=main_view._set_filter, width=180)
    main_view.filter_menu.set(main_view.current_filter)
    main_view.filter_menu.pack(side="left")


def creer_barre_recherche(main_view: ctk.CTkFrame):
    search_frame_parent = ctk.CTkFrame(main_view.main_content_frame, fg_color="transparent")
    search_frame_parent.pack(fill="x", padx=10, pady=(5, 5))

    search_label = ctk.CTkLabel(search_frame_parent, text="Rechercher (Nom, Prénom, Réf.):",
                                font=ctk.CTkFont(size=12))
    search_label.pack(side="left", padx=(0, 5))

    main_view.search_var = ctk.StringVar()
    main_view.search_var.trace_add("write", lambda name, index, mode: main_view.afficher_liste_demandes())
    main_view.search_entry = ctk.CTkEntry(search_frame_parent, textvariable=main_view.search_var, width=300)
    main_view.search_entry.pack(side="left", padx=(0, 5), fill="x", expand=True)

    clear_button = ctk.CTkButton(search_frame_parent, text="X", width=30, command=main_view._clear_search)
    clear_button.pack(side="left", padx=(5, 0))

    archive_checkbox = ctk.CTkCheckBox(search_frame_parent, text="Inclure les archives",
                                       variable=main_view.include_archives, command=main_view._on_archive_toggle)
    archive_checkbox.pack(side="left", padx=20)


def creer_conteneur_liste_demandes(main_view: ctk.CTkFrame):
    main_view.scrollable_frame_demandes = ctk.CTkScrollableFrame(main_view.main_content_frame,
                                                            label_text="Liste des Demandes de Remboursement")
    main_view.scrollable_frame_demandes.pack(pady=(5, 5), padx=10, expand=True, fill="both")
    main_view.scrollable_frame_demandes.grid_columnconfigure(0, weight=1)


def creer_legende_couleurs(main_view: ctk.CTkFrame):
    from views.main_view import COULEUR_ACTIVE_POUR_UTILISATEUR, COULEUR_DEMANDE_TERMINEE, COULEUR_DEMANDE_ANNULEE

    legende_frame = ctk.CTkFrame(main_view.main_content_frame, fg_color="transparent")
    legende_frame.pack(fill="x", padx=10, pady=(5, 10), anchor="s")

    ctk.CTkLabel(legende_frame, text="Légende:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 10))

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


def open_admin_user_management_view(main_view: ctk.CTkFrame):
    if main_view.auth_controller:
        AdminUserManagementView(main_view, main_view.auth_controller)
    else:
        from tkinter import messagebox
        messagebox.showerror("Erreur", "Le contrôleur d'authentification n'est pas initialisé.", parent=main_view)


def open_help_view(main_view: ctk.CTkFrame):
    HelpView(main_view, main_view.nom_utilisateur, main_view.user_roles)