# views/document_history_viewer.py
import os
import customtkinter as ctk


class DocumentHistoryViewer(ctk.CTkToplevel):
    def __init__(self, master, demande_data: dict, callbacks: dict):
        super().__init__(master)

        self.demande_data = demande_data
        self.callbacks = callbacks  # {'voir_pj': func, 'dl_pj': func}

        self.title(f"Historique des Documents - Demande {demande_data.get('id_demande', '')[:8]}")
        self.geometry("700x500")
        self.transient(master)
        self.grab_set()
        self.resizable(True, True)

        main_frame = ctk.CTkScrollableFrame(self)
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        label_font = ctk.CTkFont(weight="bold")

        # Section Factures
        chemins_factures = self.demande_data.get("chemins_abs_factures_stockees", [])
        if chemins_factures:
            ctk.CTkLabel(main_frame, text="Historique des Factures:", font=label_font).pack(anchor="w", pady=(10, 5))
            for idx, path in enumerate(chemins_factures):
                if path and os.path.exists(path):
                    item_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
                    item_frame.pack(fill="x", pady=2)
                    ctk.CTkLabel(item_frame, text=f"Version {idx + 1}: {os.path.basename(path)}").pack(side="left",
                                                                                                       padx=5)
                    ctk.CTkButton(item_frame, text="DL", width=60,
                                  command=lambda p=path: self.callbacks['dl_pj'](p)).pack(side="right", padx=2)
                    ctk.CTkButton(item_frame, text="Voir", width=60,
                                  command=lambda p=path: self.callbacks['voir_pj'](p)).pack(side="right", padx=2)

        # Section RIBs
        chemins_ribs = self.demande_data.get("chemins_abs_rib_stockes", [])
        if chemins_ribs:
            ctk.CTkLabel(main_frame, text="Historique des RIBs:", font=label_font).pack(anchor="w", pady=(15, 5))
            for idx, path in enumerate(chemins_ribs):
                if path and os.path.exists(path):
                    item_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
                    item_frame.pack(fill="x", pady=2)
                    ctk.CTkLabel(item_frame, text=f"Version {idx + 1}: {os.path.basename(path)}").pack(side="left",
                                                                                                       padx=5)
                    ctk.CTkButton(item_frame, text="DL", width=60,
                                  command=lambda p=path: self.callbacks['dl_pj'](p)).pack(side="right", padx=2)
                    ctk.CTkButton(item_frame, text="Voir", width=60,
                                  command=lambda p=path: self.callbacks['voir_pj'](p)).pack(side="right", padx=2)

        # Section Preuves de Trop-Perçu
        chemins_trop_percu = self.demande_data.get("chemins_abs_trop_percu", [])
        if chemins_trop_percu:
            ctk.CTkLabel(main_frame, text="Historique des Preuves de Trop-Perçu:", font=label_font).pack(anchor="w",
                                                                                                         pady=(15, 5))
            for idx, path in enumerate(chemins_trop_percu):
                if path and os.path.exists(path):
                    item_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
                    item_frame.pack(fill="x", pady=2)
                    ctk.CTkLabel(item_frame, text=f"Version {idx + 1}: {os.path.basename(path)}").pack(side="left",
                                                                                                       padx=5)
                    ctk.CTkButton(item_frame, text="DL", width=60,
                                  command=lambda p=path: self.callbacks['dl_pj'](p)).pack(side="right", padx=2)
                    ctk.CTkButton(item_frame, text="Voir", width=60,
                                  command=lambda p=path: self.callbacks['voir_pj'](p)).pack(side="right", padx=2)

        if not chemins_factures and not chemins_ribs and not chemins_trop_percu:
            ctk.CTkLabel(main_frame, text="Aucun document historisé pour cette demande.").pack(pady=20)

        close_button = ctk.CTkButton(self, text="Fermer", command=self.destroy)
        close_button.pack(pady=10)