import flet as ft

class Container():
    def __init__(self, business_name, height=None, content=None, expand=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bisnness_name = business_name
        self.height = height
        self.content = content
        self.expand = expand

    def build(self):
        return ft.Container(
            content=ft.Text(value="Contenedor " + self.bisnness_name, size=30, weight=ft.FontWeight.BOLD) if self.content is None else self.content,
            alignment=ft.alignment.top_center,
            gradient=ft.LinearGradient(colors=[ft.Colors.GREY_900, ft.Colors.BLACK54]),
            expand=self.expand,
            height=self.height,
            border_radius=10,
            padding=10,
        )
