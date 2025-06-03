# views/document_viewer.py
import os
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import fitz  # PyMuPDF


class DocumentViewerWindow(ctk.CTkToplevel):
    def __init__(self, master, file_path: str, title: str):
        super().__init__(master)
        self.title(title)
        self.geometry("850x700")
        self.transient(master)
        self.grab_set()
        self.resizable(True, True)
        self.minsize(400, 300)

        self.file_path = file_path
        self.document_type = None

        self.pdf_doc = None
        self.pdf_current_page_num = 0
        self.pdf_page_count = 0
        self.pdf_current_matrix_scale = 1.3
        self.pdf_100_percent_render_scale = 2.0

        self.pil_original_image = None
        self.image_current_display_scale = 1.0

        self._drag_start_x = 0
        self._drag_start_y = 0
        self._is_dragging = False

        controls_frame = ctk.CTkFrame(self, height=40)
        controls_frame.pack(fill="x", pady=(5, 0), padx=5)

        ctk.CTkButton(controls_frame, text="Zoom +", width=80, command=self.zoom_in).pack(side="left", padx=3, pady=5)
        ctk.CTkButton(controls_frame, text="Zoom -", width=80, command=self.zoom_out).pack(side="left", padx=3, pady=5)
        ctk.CTkButton(controls_frame, text="Ajuster/130%", width=100, command=self.action_ajuster_contenu).pack(
            side="left", padx=3, pady=5)  # Renommé
        ctk.CTkButton(controls_frame, text="Qualité (100%)", width=110, command=self.zoom_reset_qualite).pack(
            side="left", padx=3, pady=5)  # Nouveau bouton pour le 100% qualité PDF

        self.page_info_label = ctk.CTkLabel(controls_frame, text="", width=120)
        self.page_info_label.pack(side="right", padx=10, pady=5)
        self.next_page_button = ctk.CTkButton(controls_frame, text="Suiv. >", width=80, command=self.next_page,
                                              state="disabled")
        self.next_page_button.pack(side="right", padx=3, pady=5)
        self.prev_page_button = ctk.CTkButton(controls_frame, text="< Préc.", width=80, command=self.prev_page,
                                              state="disabled")
        self.prev_page_button.pack(side="right", padx=3, pady=5)

        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.pack(expand=True, fill="both", padx=5, pady=5)

        self.image_label = ctk.CTkLabel(self.scrollable_frame, text="")
        self.image_label.pack(padx=0, pady=0)

        self.load_document_and_display()

        self.scrollable_frame.bind("<MouseWheel>", self._on_mouse_wheel_zoom)
        self.scrollable_frame.bind("<Button-4>", self._on_mouse_wheel_zoom)
        self.scrollable_frame.bind("<Button-5>", self._on_mouse_wheel_zoom)

        self.image_label.bind("<ButtonPress-1>", self._on_drag_start)
        self.image_label.bind("<B1-Motion>", self._on_drag_motion)
        self.image_label.bind("<ButtonRelease-1>", self._on_drag_stop)
        self.image_label.configure(cursor="fleur")

    def load_document_and_display(self):
        try:
            ext = self.file_path.lower().split('.')[-1]
            if ext in ("png", "jpg", "jpeg", "gif", "bmp"):
                self.document_type = 'image'
                self.pil_original_image = Image.open(self.file_path)
                self.pdf_doc = None
                self.pdf_page_count = 1
                self.image_current_display_scale = 1.0
                self.prev_page_button.configure(state="disabled")
                self.next_page_button.configure(state="disabled")
            elif ext == "pdf":
                self.document_type = 'pdf'
                self.pdf_doc = fitz.open(self.file_path)
                self.pdf_page_count = self.pdf_doc.page_count
                self.pil_original_image = None
                self.pdf_current_matrix_scale = self.pdf_initial_zoom_scale
                self.prev_page_button.configure(state="disabled" if self.pdf_page_count <= 1 else "normal")
                self.next_page_button.configure(state="disabled" if self.pdf_page_count <= 1 else "normal")
            else:
                self.document_type = 'unsupported'
                self.image_label.configure(text=f"Type de fichier non supporté : {os.path.basename(self.file_path)}")
                return

            self._render_current_view()
        except Exception as e:
            self.image_label.configure(text=f"Erreur au chargement du document:\n{e}")
            print(f"Erreur détaillée DocumentViewer (load_document_and_display): {e}")

    def _render_current_view(self):
        pil_img_to_render = None
        try:
            if self.document_type == 'image' and self.pil_original_image:
                original_width, original_height = self.pil_original_image.size
                render_width = int(original_width * self.image_current_display_scale)
                render_height = int(original_height * self.image_current_display_scale)
                render_width = max(1, render_width)
                render_height = max(1, render_height)
                pil_img_to_render = self.pil_original_image.resize((render_width, render_height),
                                                                   Image.Resampling.LANCZOS)
                self.page_info_label.configure(text=f"Zoom: {self.image_current_display_scale * 100:.0f}%")

            elif self.document_type == 'pdf' and self.pdf_doc and self.pdf_page_count > 0:
                page = self.pdf_doc.load_page(self.pdf_current_page_num)
                mat = fitz.Matrix(self.pdf_current_matrix_scale, self.pdf_current_matrix_scale)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                pil_img_to_render = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                self.page_info_label.configure(
                    text=f"Page {self.pdf_current_page_num + 1} / {self.pdf_page_count} (Zoom: {self.pdf_current_matrix_scale * 72:.0f} DPI)")  # DPI approx
                self.prev_page_button.configure(state="normal" if self.pdf_current_page_num > 0 else "disabled")
                self.next_page_button.configure(
                    state="normal" if self.pdf_current_page_num < self.pdf_page_count - 1 else "disabled")

            if pil_img_to_render and pil_img_to_render.width > 0 and pil_img_to_render.height > 0:
                ctk_img = ctk.CTkImage(light_image=pil_img_to_render, dark_image=pil_img_to_render,
                                       size=pil_img_to_render.size)
                self.image_label.configure(image=ctk_img, text="")
            elif self.document_type == 'unsupported':
                self.image_label.configure(image=None,
                                           text=f"Type de fichier non supporté : {os.path.basename(self.file_path)}")
            else:
                self.image_label.configure(image=None, text="Document vide ou erreur de rendu.")

        except Exception as e:
            self.image_label.configure(image=None, text=f"Erreur d'affichage du document:\n{e}")
            print(f"Erreur détaillée _render_current_view: {e}")

    def _on_mouse_wheel_zoom(self, event):  #
        if event.state & 0x0004:  # Ctrl key
            if event.delta > 0 or event.num == 4:  #
                self.zoom_in()  #
            elif event.delta < 0 or event.num == 5:  #
                self.zoom_out()  #

    def _on_drag_start(self, event):  #
        self.scrollable_frame._parent_canvas.scan_mark(event.x, event.y)  #
        self.image_label.configure(cursor="hand2")  #

    def _on_drag_motion(self, event):  #
        self.scrollable_frame._parent_canvas.scan_dragto(event.x, event.y, gain=1)  #

    def _on_drag_stop(self, event):  #
        self.image_label.configure(cursor="fleur")  #

    def zoom_in(self):  #
        if self.document_type == 'pdf':  #
            self.pdf_current_matrix_scale *= 1.25  #
        elif self.document_type == 'image':  #
            self.image_current_display_scale *= 1.25  #
        self._render_current_view()  #

    def zoom_out(self):  #
        if self.document_type == 'pdf':  #
            self.pdf_current_matrix_scale = max(0.1, self.pdf_current_matrix_scale / 1.25)  #
        elif self.document_type == 'image':  #
            self.image_current_display_scale = max(0.05, self.image_current_display_scale / 1.25)  #
        self._render_current_view()  #

    def action_ajuster_contenu(self):  # Anciennement zoom_reset, maintenant "Ajuster" ou "Zoom initial"
        if self.document_type == 'pdf':
            self.pdf_current_matrix_scale = self.pdf_initial_zoom_scale
        elif self.document_type == 'image' and self.pil_original_image:
            original_width, original_height = self.pil_original_image.size
            # Donner une taille au scrollable_frame s'il n'en a pas encore (cas initial)
            frame_w = max(1, self.scrollable_frame.winfo_width() if self.scrollable_frame.winfo_width() > 1 else 750)
            frame_h = max(1, self.scrollable_frame.winfo_height() if self.scrollable_frame.winfo_height() > 1 else 550)

            if original_width > 0 and original_height > 0:
                ratio = min(frame_w / original_width, frame_h / original_height)
                # Si l'image est plus petite que la fenêtre, on peut la laisser à 100% ou l'ajuster.
                # Pour "Ajuster", on la fait toujours tenir.
                self.image_current_display_scale = ratio
            else:
                self.image_current_display_scale = 1.0
        self._render_current_view()

    def zoom_reset_qualite(self):  # Action du bouton "100% Qualité" (anciennement "100%")
        if self.document_type == 'pdf':
            self.pdf_current_matrix_scale = self.pdf_100_percent_render_scale
        elif self.document_type == 'image':
            self.image_current_display_scale = 1.0
        self._render_current_view()

    def next_page(self):  #
        if self.pdf_doc and self.pdf_current_page_num < self.pdf_page_count - 1:  #
            self.pdf_current_page_num += 1  #
            self._render_current_view()  # Afficher la nouvelle page avec le zoom actuel

    def prev_page(self):  #
        if self.pdf_doc and self.pdf_current_page_num > 0:  #
            self.pdf_current_page_num -= 1  #
            self._render_current_view()  # Afficher la nouvelle page avec le zoom actuel

    def destroy(self):  #
        if self.pdf_doc:  #
            try:  #
                self.pdf_doc.close()  #
            except Exception as e:  #
                print(f"Erreur lors de la fermeture du document PDF: {e}")  #
            self.pdf_doc = None  #
        super().destroy()  #