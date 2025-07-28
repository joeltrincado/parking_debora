import flet as ft

class AppBar():
    def __init__(self, business_name=None, items = None, onChange = None, filters = None, *args, **kwargs):
        self.business_name = business_name
        self.items = items
        self.onChange = onChange
        self.filters = filters

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
        leading=ft.Icon(ft.Icons.CAR_RENTAL),
        leading_width=40,
        title=ft.Text("Control " + self.business_name if self.business_name is not None else "Control", size=20, weight=ft.FontWeight.BOLD),
        center_title=False,
        toolbar_height=60,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        actions=[
            ft.Row([self.filters ], expand=True, alignment=ft.MainAxisAlignment.END),
            ft.PopupMenuButton(
                icon=ft.Icons.MENU,
                items=i
            ),
        ],
    )