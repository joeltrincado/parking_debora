import flet as ft

class Button():
    def __init__(self, text = None,icon = None, label = None, on_click = None, width = None, bgcolor = None, color = None, icon_color = None, *args, **kwargs):
        self.label = label
        self.on_click = on_click
        self.text = text
        self.icon = icon
        self.width = width
        self.bgcolor = bgcolor
        self.color = color
        self.icon_color = icon_color

    def build (self):
        return ft.Row(
            [
                ft.FilledButton(
            text=self.text if self.text.upper() is not None else "DESCARGAR",
            icon=self.icon if self.icon is not None else ft.Icons.DOWNLOAD,
            on_click=self.on_click if self.on_click is not None else None,
            expand=True if self.width is None else False,
            icon_color=self.icon_color if self.icon_color is not None else ft.Colors.WHITE,
            bgcolor=self.bgcolor if self.bgcolor is not None else ft.Colors.BLUE_400,
            height=50,
            color=self.color if self.color is not None else ft.Colors.WHITE,
            width=self.width if self.width is not None else None,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=5)
            ),
        )
            ], height=50
        )