import customtkinter as ctk
import tkinter


class LoadingCursor:
    """
    Un gestionnaire de contexte (context manager) pour afficher un curseur d'attente
    pendant les opérations potentiellement longues.
    """

    def __init__(self, widget):
        self.widget = widget
        self.toplevel = self.widget.winfo_toplevel()

    def __enter__(self):
        self.toplevel.configure(cursor="watch")
        self.toplevel.update_idletasks()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.toplevel.configure(cursor="")


class LoadingOverlay(ctk.CTkFrame):
    """
    Une surcouche qui s'affiche par-dessus une fenêtre pour indiquer un chargement,
    empêchant l'interaction de l'utilisateur et le 'freeze' de l'application.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.configure(fg_color=("gray20", "gray20"))
        self.progress_bar = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress_bar.place(relx=0.5, rely=0.5, anchor="center")
        self.label = ctk.CTkLabel(self, text="Chargement en cours...", font=ctk.CTkFont(size=16))
        self.label.place(relx=0.5, rely=0.5, y=-40, anchor="center")

    def show(self):
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()
        self.progress_bar.start()

    def hide(self):
        self.progress_bar.stop()
        self.place_forget()


class ToastNotification(ctk.CTkFrame):
    """
    Un widget de notification "toast" qui s'affiche et disparaît automatiquement.
    """

    def __init__(self, parent):
        super().__init__(parent, corner_radius=6)
        self._hide_job = None
        self._styles = {
            'success': {'fg_color': '#2E8B57', 'text_color': 'white'},
            'info': {'fg_color': '#1E90FF', 'text_color': 'white'}
        }
        self._label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=14))
        self._label.pack(padx=15, pady=10)

    def show(self, message, m_type='success', duration=2500):
        if self._hide_job:
            self.after_cancel(self._hide_job)

        style = self._styles.get(m_type, self._styles['info'])
        self.configure(fg_color=style['fg_color'])
        self._label.configure(text=message, text_color=style['text_color'])

        self.lift()
        self.place(relx=0.02, rely=0.98, anchor='sw')

        self._hide_job = self.after(duration, self._hide)

    def _hide(self):
        self.place_forget()
        self._hide_job = None