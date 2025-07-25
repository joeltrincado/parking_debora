import flet as ft

class Alert():
    def __init__(self, content, onAdd = None, onCancel = None, height = None, width = None, title = None, action = None, *args, **kwargs):
        self.content = content
        self.onAdd = onAdd
        self.onCancel = onCancel
        self.action = action
        self.height = height
        self.width = width
        self.title = title
    def build(self):
        return ft.AlertDialog(
            content=ft.Container(content=self.content, height=self.height if self.height is not None else None, width=self.width if self.width is not None else None),
            title=ft.Text(self.title if self.title is not None else "Alerta"),
            actions=[
                ft.TextButton("Agregar" if self.action is None else self.action, on_click=self.onAdd),
                ft.TextButton("Cancelar" , on_click=self.onCancel),
            ],
            shape=ft.RoundedRectangleBorder(radius=10),
            )