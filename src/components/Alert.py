import flet as ft

class Alert():
    def __init__(self, content, onAdd = None, onCancel = None, height = None, width = None, title = None, action = None, cancel = None, *args, **kwargs):
        self.content = content
        self.onAdd = onAdd
        self.onCancel = onCancel
        self.action = action
        self.height = height
        self.width = width
        self.title = title
        self.cancel = cancel
    def build(self):
        return ft.AlertDialog(
    content=ft.Container(
        content=ft.Column(
            controls=[self.content],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        ),
        height=self.height,
        width=self.width,
    ),
    title=ft.Text(self.title if self.title else "Alerta"),
    actions=[
        *( [ft.TextButton("Agregar" if self.action is None else self.action, on_click=self.onAdd)] if self.onAdd else [] ),
        ft.TextButton("Cancelar" if self.cancel is None else self.cancel , on_click=self.onCancel),
    ],
    shape=ft.RoundedRectangleBorder(radius=10),
)

