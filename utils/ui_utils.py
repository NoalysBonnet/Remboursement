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
    Représente un seul widget de notification. Il est géré par le ToastManager.
    """
    _styles = {
        'success': {'fg_color': '#2E8B57', 'text_color': 'white', 'duration': 2500},
        'info': {'fg_color': '#1E90FF', 'text_color': 'white', 'duration': 2500},
        'warning': {'fg_color': '#FFC107', 'text_color': 'black', 'duration': 4000},
        'error': {'fg_color': '#B71C1C', 'text_color': 'white', 'duration': 3500}
    }

    def __init__(self, parent, message, m_type, on_destroy_callback):
        super().__init__(parent, corner_radius=6)
        self.on_destroy_callback = on_destroy_callback

        style = self._styles.get(m_type, self._styles['info'])

        self.configure(fg_color=style['fg_color'])
        label = ctk.CTkLabel(self, text=message, font=ctk.CTkFont(size=14),
                             text_color=style['text_color'], wraplength=350)
        label.pack(padx=15, pady=10)

        duration = style.get('duration', 3000)
        self.after(duration, self._start_destroy)

    def _start_destroy(self):
        self.on_destroy_callback(self)
        self.destroy()


class ToastManager:
    """
    Gère la création, l'empilement et la destruction des notifications toast.
    """

    def __init__(self, parent):
        self.parent = parent
        self.active_toasts = []
        self.padding_x = 0.02  # Utiliser une fraction pour relx
        self.padding_y = 10    # Garder les pixels pour l'espacement vertical

    def show_toast(self, message, m_type='success'):
        toast = ToastNotification(self.parent, message, m_type, on_destroy_callback=self._remove_toast)
        toast.lift()
        self.active_toasts.append(toast)
        self._reposition_toasts()

    def _remove_toast(self, toast_instance):
        if toast_instance in self.active_toasts:
            self.active_toasts.remove(toast_instance)
        self._reposition_toasts()

    def _reposition_toasts(self):
        self.parent.update_idletasks()
        parent_height = self.parent.winfo_height()

        if parent_height < 100:
            self.parent.after(100, self._reposition_toasts)
            return

        rel_x_pos = 1.0 - self.padding_x
        y_for_bottom_edge = parent_height - self.padding_y

        for toast in reversed(self.active_toasts):
            toast.update_idletasks()
            toast_height = toast.winfo_reqheight()

            # Convertir la position y absolue en relative
            rel_y_pos = y_for_bottom_edge / parent_height

            toast.place(relx=rel_x_pos, rely=rel_y_pos, anchor='se')
            toast.lift()

            # Mettre à jour la position y pour la prochaine notification (au-dessus)
            y_for_bottom_edge -= (toast_height + self.padding_y)