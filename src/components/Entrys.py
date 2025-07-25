import flet as ft

class Entrys():
    def __init__(self, entrys=None):
        self.entrys = entrys
        self.rows = []

    def generate_rows(self):
        rows = []
        for items in self.entrys:
            rows.append( ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(items[0]))),  # id
                ft.DataCell(ft.Text(items[1])),       # date
                ft.DataCell(ft.Text(items[2])),       # status
            ])
            )
        return rows


    def build(self):
        self.rows = self.generate_rows()
        return ft.DataTable(columns=[
            ft.DataColumn(label=ft.Text("ID")),
            ft.DataColumn(label=ft.Text("HORA DE ENTRADA")),
            ft.DataColumn(label=ft.Text("ESTADO")),
        ], rows=self.rows, expand=True)