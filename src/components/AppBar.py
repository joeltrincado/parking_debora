import flet as ft

class AppBar():
    def __init__(self, bisnness_name=None, items = None, onChange = None, *args, **kwargs):
        self.bisnness_name = bisnness_name
        self.items = items
        self.onChange = onChange

    def build(self):
        i = []
        if self.items is not None:
            for item in self.items:
                i.append(
                    ft.PopupMenuItem(
                        text=item["text"],
                        # on_click=item["on_click"]
                    )
                )
        else:
            i = [
                    ft.PopupMenuItem(text="Entradas", on_click=lambda e: self.onChange(0)),
                    ft.PopupMenuItem(text="Impresora", on_click=lambda e: self.onChange(1)),
                    ft.PopupMenuItem(text="Tarifa", on_click=lambda e: self.onChange(2)),
                    # ft.PopupMenuItem(text="Ayuda", on_click=lambda e: self.onChange(3)),
                ]
            
        return ft.AppBar(
        leading=ft.Icon(ft.Icons.ACCESS_TIME),
        leading_width=40,
        title=ft.Text("Control " + self.bisnness_name if self.bisnness_name is not None else "Control", size=20, weight=ft.FontWeight.BOLD),
        center_title=False,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        actions=[
            ft.PopupMenuButton(
                icon=ft.Icons.MENU,
                items=i
            ),
        ],
    )