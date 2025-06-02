# C:\Users\maxen\PycharmProjects\PythonProject\views\main_view.py
import customtkinter as ctk


class MainView(ctk.CTkFrame):
    def __init__(self, master, nom_utilisateur, on_logout_callback):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.master = master
        self.nom_utilisateur = nom_utilisateur
        self.on_logout = on_logout_callback  # Callback vers AppController pour la déconnexion
        self.pack(fill="both", expand=True)
        self.creer_widgets_principaux()

    def creer_widgets_principaux(self):
        # Frame principal interne pour un meilleur padding et organisation
        main_content_frame = ctk.CTkFrame(self, corner_radius=10)
        main_content_frame.pack(pady=20, padx=20, fill="both", expand=True)

        top_bar = ctk.CTkFrame(main_content_frame, fg_color="transparent")
        top_bar.pack(fill="x", padx=10, pady=(10, 5))

        label_accueil = ctk.CTkLabel(top_bar,
                                     text=f"Utilisateur connecté : {self.nom_utilisateur}",
                                     font=ctk.CTkFont(size=12))
        label_accueil.pack(side="left", padx=5)

        bouton_deconnexion = ctk.CTkButton(top_bar, text="Déconnexion", command=self.on_logout, width=120)
        bouton_deconnexion.pack(side="right", padx=5)

        # Titre principal de l'interface
        label_titre_principal = ctk.CTkLabel(main_content_frame, text="Tableau de Bord - Remboursements",
                                             font=ctk.CTkFont(size=24, weight="bold"))
        label_titre_principal.pack(pady=(10, 20))

        # Espace pour le contenu futur
        contenu_frame = ctk.CTkFrame(main_content_frame, fg_color="transparent")
        contenu_frame.pack(pady=10, padx=10, expand=True, fill="both")

        label_todo = ctk.CTkLabel(contenu_frame,
                                  text="La liste des clients, le formulaire d'ajout/modification de demande,\n"
                                       "et les autres fonctionnalités de gestion seront implémentées ici.",
                                  font=ctk.CTkFont(size=14),
                                  justify="left")
        label_todo.pack(pady=20, padx=20, anchor="nw")