import flet as ft

class TextField():
    def __init__(self,label = None, onChange = None, onSubmit = None, value = None, width = None, keyboard_type = None, *args, **kwargs):
        self.label = label
        self.onChange = onChange
        self.onSubmit = onSubmit
        self.value = value
        self.width = width
        self.keyboard_type = keyboard_type

    def focus(self):
        self.build().focus()

    def build(self):
        return ft.TextField(
            label=self.label if self.label is not None else None,
            keyboard_type=self.keyboard_type if self.keyboard_type is not None else None,
            width=self.width if self.width is not None else None,
            value=self.value if self.value is not None else None,
            on_change=self.onChange if self.onChange is not None else None,
            on_submit=self.onSubmit if self.onSubmit is not None else None,
            expand=True,
            border_radius=10,
            color=ft.Colors.WHITE,
            border_color=ft.Colors.WHITE,

        )