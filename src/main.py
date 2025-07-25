import flet as ft
from database import init_db, get_all_entries, insert_entry, delete_entry, get_entry_by_code, insert_out, get_all_outs, set_config, get_config, get_entry_by_type, get_price_unique, set_price
from helpers.helpers import getDatacell, getDataColumns
from components.Container import Container
from components.Button import Button
from components.TextField import TextField
from components.Alert import Alert
from components.AppBar import AppBar
from datetime import datetime
import json
import pandas as pd
import os


def main(page: ft.Page):
    init_db()
    

    # GLOBALS VARS
    current_tab = 0
    bisnness_name = "Estacionamiento Debora Hernández"
    fee = 0
    data_table = []
    entrys = get_all_entries() 
    outs = []
    total = 0
    nBoxes = 19
    nBoxesAirBnb = 2
    config = None
    datacells = getDatacell(entrys)
    columns = getDataColumns(["FOLIO", "CÓDIGO", "FECHA", "HORA", "TIPO DE ENTRADA"])
    printer = None


    ############################################################################################################

    # PAGE PROPIERTIES
    page.title = "Control " + bisnness_name
    page.theme_mode = ft.ThemeMode.DARK

    ############################################################################################################
    
    # FUCTIONS

    def get_plain_data():
        registros = get_all_outs()
        return [
            [r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]]
            for r in registros
        ]

    def download_report_csv(e):

        plain_data = get_plain_data()
        columns = ["ID", "Código", "Hora de entrada", "Fecha de entrada", "Hora de salida", "Fecha de salida", "Tipo de entrada", "Precio", "Total"]
        df = pd.DataFrame(plain_data, columns=columns)

        try:
            
            df.to_csv(path_or_buf=f'reporte.csv', index=False)
            snack_bar = ft.SnackBar(ft.Text(f"Reporte guardado en {os.getcwd()}"))
            page.open(snack_bar)
        except Exception as ex:
            snack_bar = ft.SnackBar(ft.Text("Error al guardar el reporte: " + str(ex)))
            page.open(snack_bar)
        page.update()

    def show_page(index, callback=None):
    # Oculta todas
        for i, p in enumerate([page_0, page_1, page_2]):
            p.visible = (i == index)
            
        # Ejecuta la lógica especial para esa página (si se pasa)
        if callback:
            callback()

        page.update()

    def save_config(e):
        nonlocal config, printer
        config = {
                "valor": usb_selector.value,
            }
        printer = usb_selector.value
        set_config("impresora", json.dumps(config)) 
        show_page(0)
        page.open(ft.SnackBar(ft.Text("Configuración guardada")))

    def colorBoxs():
        nonlocal nBoxes
        e = get_entry_by_type("Boleto normal")
        n = len(e) if e else 0
        diff = nBoxes - n
        boxs.value = str(diff)
        if diff <= 1:
            containerBoxs.gradient = ft.LinearGradient(begin=ft.alignment.top_left, end=ft.alignment.bottom_right, colors=["#FF0000", "#FF0000"])
        elif 1 < diff < 5:
            containerBoxs.gradient = ft.LinearGradient(begin=ft.alignment.top_left, end=ft.alignment.bottom_right, colors=["#FFA500", "#FFA500"])
        else:
            containerBoxs.gradient = ft.LinearGradient(begin=ft.alignment.top_left, end=ft.alignment.bottom_right, colors=["#014601", "#2F922F"])
        page.update()
    def colorBoxsAirBnb():
        nonlocal  nBoxesAirBnb
        e = get_entry_by_type("Boleto AirBnb")
        n = len(e) if e else 0
        diff = nBoxesAirBnb - n
        boxsText_airbnb.value = str(diff)
        page.update()
    def getBD():
        nonlocal entrys
        entrys = get_all_entries()
        datacells = getDatacell(entrys)
        registers_database.rows.clear()
        registers_database.rows = datacells
        read_qr.value = ""
        read_qr.focus()
        page.update()

    def createOut(code, price=0, total=0):
        out_date = datetime.now().strftime("%Y-%m-%d")
        out_time = datetime.now().strftime("%H:%M:%S")
        insert_out(code[1], code[2], code[3], out_time, out_date, code[6], price, total)
        outs = get_all_outs()
        delete_entry(code[1])
        getBD()
        colorBoxs() 
        colorBoxsAirBnb()
        message("Boleto de salida generado con éxito")
        page.update()

    def message(text=None):
        snack_bar = ft.SnackBar(ft.Text("Código no encontrado" if text is None else text, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), bgcolor=ft.Colors.RED_400, duration=ft.Duration(seconds=3))
        read_qr.value = ""
        page.open(snack_bar)
        read_qr.focus()
        page.update()

    def get_usb_printers():
            try:
                import win32print
                return [printer[2] for printer in win32print.EnumPrinters(2)]
            except:
                return []
            
    def load_config():
        try:
            config_json = get_config("impresora")
            if config_json:
                config = json.loads(config_json)
                usb_selector.value = config.get("valor", None)
        except Exception as e:
            snack_bar = ft.SnackBar(ft.Text(f"Error al cargar la configuración: {e}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), bgcolor=ft.Colors.RED_400, duration=ft.Duration(seconds=3))
            page.open(snack_bar)
            page.update()

    def load_prices():
        try:
            nombre, precio = get_price_unique()
            name_fee.value = nombre
            price_fee.value = str(precio)
            page.update()
        except Exception as e:
            snack_bar = ft.SnackBar(ft.Text(f"Error al cargar la tarifa: {e}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), bgcolor=ft.Colors.RED_400, duration=ft.Duration(seconds=3))
            page.open(snack_bar)

    
    ############################################################################################################

    # ONCHANGES & ONSUBMITS

    def addAirBnb(plate=""):
        if not time_picker.value or not date_picker.value:
            message("Debes seleccionar fecha y hora de salida")
            return

        entry = {
            "codigo": plate,
            "hora_entrada": datetime.now().strftime("%H:%M:%S"),
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "hora_salida": time_picker.value.strftime("%H:%M:%S"),
            "fecha_salida": date_picker.value.strftime("%Y-%m-%d"),
            "precio": 0,
            "status": "Entrada"
        }

        insert_entry(entry["codigo"], entry["hora_entrada"], entry["fecha"],
                    entry["hora_salida"], entry["fecha_salida"],
                    "Boleto AirBnb", entry["precio"], "Boleto AirBnb")

        alert.open = False
        colorBoxsAirBnb()
        getBD()



    def airBnbOut(code):
        try:
            entry_date = datetime.strptime(code[5], "%Y-%m-%d").date()
        except Exception:
            message("Fecha de salida inválida en el boleto")
            return

        today = datetime.now().date()
        if today >= entry_date:
            createOut(code)
        else:
            message("El boleto no puede salir hoy")


    def onSubmitReadQr(e):
        entry = {
            #codigo, hora_entrada, precio, status
            "codigo": str(datetime.now().strftime("%Y%m%d%H%M%S")),
            "hora_entrada": datetime.now().strftime("%H:%M:%S"),
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "hora_salida": None,
            "fecha_salida": None,
            "precio": 0,
            "status": "Entrada"
        }
        if e.control.value == "AutoNuevo":
            insert_entry(entry["codigo"], entry["hora_entrada"], entry["fecha"], entry["hora_salida"], entry["fecha_salida"], "Boleto normal", entry["precio"], "Boleto normal")
            getBD()
            colorBoxs()
        elif e.control.value == "AirBnb":
            alert.open = True
            page.update()
        else:
            code = get_entry_by_code(e.control.value)
            if code is None:
                message()
            else:
                createOut(code) if code[6] == "Boleto normal" else airBnbOut(code)

    
            

    def onChangePage(e):
        nonlocal current_tab
        current_tab = e

        match current_tab:
            case 0:
                show_page(0)
            case 1:
                show_page(1, callback=load_config)
            case 2:
                show_page(2, callback=load_prices) 

    ############################################################################################################

    # ONCLICKS
    def delete_registers(e):
        alert_delete_registers.open = True

    def closeAlertRegisters(e):
        alert_delete_registers.open = False

    def close_alert(e):
        alert.open = False
        page.update()

    def handle_change_date(e):
        rangeDate.visible = False
        textDate.text = f'Fecha de salida: {str(date_picker.value)[:10]}'
        textDate.visible = True
        page.update()
    
    def handle_change_time(e):
        rangeTime.visible = False
        textTime.text = f'Hora de salida: {time_picker.value}'
        textTime.visible = True
        page.update()

    def handle_accept_airbnb(e):
        addAirBnb(plate=plate.value)
        colorBoxsAirBnb()
        alert.open = False
        page.update()

    def save_fee(e):
        nonlocal fee
        set_price(name_fee.value, price_fee.value)
        fee = float(price_fee.value)
        show_page(0)
        page.open(ft.SnackBar(ft.Text("Configuración guardada")))
        page.update()

    ############################################################################################################


 
    # PAGES
    plate = TextField(label="Placa").build()
    time_picker = ft.TimePicker(
        confirm_text="Confirmar",
        cancel_text="Cancelar",
        error_invalid_text="Tempo fuera de rango",
        help_text="Elige tu zona horaria",
        on_change=handle_change_time,
    )
    date_picker = ft.DatePicker(
        confirm_text="Confirmar",
        cancel_text="Cancelar",
        error_invalid_text="Fecha fuera de rango",
        help_text="Elige tu zona horaria",
        on_change=handle_change_date,
        
    )
    textDate = ft.TextButton(visible=False, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)), on_click=lambda _: page.open(date_picker))
    textTime = ft.TextButton(visible=False, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)), on_click=lambda _: page.open(time_picker))
    rangeTime = Button(text="TIEMPO", on_click=lambda _: page.open(time_picker), icon=ft.Icons.TIMER, bgcolor=ft.Colors.BLACK54).build()
    rangeDate = Button(text="FECHA", on_click=lambda _: page.open(date_picker), icon=ft.Icons.DATE_RANGE, bgcolor=ft.Colors.BLACK54).build()
    contentAlert = ft.Column(
        [
            plate,
            textTime,
            rangeTime,
            rangeDate,
            textDate,
        ], expand=True
    )
    read_qr = TextField(label="Leer QR", keyboard_type=ft.KeyboardType.NUMBER, onSubmit=onSubmitReadQr).build()
    download_report = Button(text="DESCARGAR REPORTE", on_click=download_report_csv).build()
    delete_registers_button = Button(text="BORRAR REGISTROS", bgcolor=ft.Colors.RED_400, icon=ft.Icons.DELETE).build()
    alert_delete_registers = Alert(content=ft.Text("Seguro que desea borrar los registros?"), action="Borrar", onAdd=delete_registers, onCancel=closeAlertRegisters).build()
    alert_delete_registers.open = False
    boxs = ft.Text("19", size=74, text_align=ft.TextAlign.CENTER, expand=True)
    boxsText_airbnb = ft.Text("2", size=74, text_align=ft.TextAlign.CENTER, expand=True)
    content_data = ft.Column(
        [
            ft.Row(
                [
                    read_qr
                ], height=50
            ),
            download_report,
            delete_registers_button,
            alert_delete_registers
        ], alignment=ft.MainAxisAlignment.START
    )
    last_entry = ft.Column(
        [
            ft.Text("CAJONES DISPONIBLES", size=26, weight=ft.FontWeight.BOLD),
            ft.Row([
                boxs
            ], expand=True, alignment=ft.MainAxisAlignment.CENTER
            )
        ]
    )
    boxs_airbnb = ft.Column(
        [
            ft.Text("CAJONES DISPONIBLES AIRBNB", size=16, weight=ft.FontWeight.BOLD),
            ft.Row([
                boxsText_airbnb
            ], expand=True, alignment=ft.MainAxisAlignment.CENTER
            )
        ]
    )
    containerBoxs = Container(business_name=bisnness_name, content=last_entry).build()
    containerBoxs_airbnb = Container(business_name=bisnness_name, content=boxs_airbnb).build()

    registers_database = ft.DataTable(
    columns= columns,
    rows=datacells,
    expand=True,
    )

    page_0 = ft.Row(
        [
            ft.Column(
                [
                    Container(height=200, business_name=bisnness_name, content=content_data).build(),
                    containerBoxs,
                    containerBoxs_airbnb
                    
                ], width=350
            ),
            ft.Column(
                [
                     Container(business_name=bisnness_name, content=ft.Row(
                         [
                            registers_database
                         ], expand=True
                     )).build(),
                ], expand=True
            ),

        ], expand=True
    )

    ###########################################################################################################
    # page 1

    usb_selector = ft.Dropdown(
        label="Impresoras USB",
        options=[ft.dropdown.Option(p) for p in get_usb_printers()],
        width=300, border_color=ft.Colors.WHITE,
    )

    config_container = Container(
        business_name=bisnness_name,
        content=ft.Column(
            [
                ft.Text("CONFIGURACIÓN DE IMPRESORA", size=26, weight=ft.FontWeight.BOLD),
                usb_selector,
                ft.Row(
                    [
                        Button(text="GUARDAR", on_click=save_config, icon=ft.Icons.SAVE, width=300).build(),
                    ], expand=True, alignment=ft.MainAxisAlignment.CENTER
                ),
            ],
            spacing=20, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        height=400,
    ).build()

    page_1 = ft.Row(
        [
            ft.Column(
                [config_container],
                expand=True,
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        ],
        expand=True
    )

    page_1.visible = False

    ###########################################################################################################
    # page 2
    name_fee = TextField(label="Nombre de la tarifa", width=300).build()
    price_fee = TextField(label="Precio por hora", keyboard_type=ft.KeyboardType.NUMBER, width=300).build()


    fee_container = Container(
        business_name=bisnness_name,
        content=ft.Column(
            [
                ft.Text("CONFIGURACIÓN DE TARIFA", size=26, weight=ft.FontWeight.BOLD),
                ft.Column(
                    [
                        name_fee,
                        price_fee,
                    ]
                ),
                ft.Row(
                    [
                        Button(text="GUARDAR",  icon=ft.Icons.SAVE, width=300, on_click=save_fee).build(),
                    ], expand=True, alignment=ft.MainAxisAlignment.CENTER
                ),
            ],
            spacing=20, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        height=400,
    ).build()
    page_2 = ft.Row(
        [
            ft.Column(
                [
                    fee_container
                ], expand=True,
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        ],
        expand=True
    )

    page_2.visible = False


     ############################################################################################################
    # ALERTS
    alert = Alert(content=contentAlert, action="Aceptar", onCancel=close_alert, title="Boleto AirBnb", height=200, width=500, onAdd=handle_accept_airbnb).build()
    alert.open = False
    
    ############################################################################################################

    ############################################################################################################
    
    
    page.appbar = AppBar(bisnness_name=bisnness_name, onChange=onChangePage).build()
    colorBoxs()
    colorBoxsAirBnb()
    page.add(
        ft.SafeArea(
            ft.Column(
                [
                    page_0,
                    page_1,
                    page_2,
                    alert
                ], expand=True
            ), expand=True
        )
    )
    read_qr.focus()
ft.app(main)
