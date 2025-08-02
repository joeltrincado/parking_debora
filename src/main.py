# Importación prioritaria y esencial
import flet as ft
from datetime import datetime
import json
import os
import re
# Variables globales para verificar si se seleccionó fecha y hora
hora_seleccionada = False
fecha_seleccionada = False

# Módulos internos ligeros (funciones no costosas)
from database import (
    init_db, get_all_entries, insert_entry, delete_entry,
    get_entry_by_code, get_price_by_day, get_price_by_type,
    insert_out, set_all_prices, get_all_outs, set_config,
    delete_all_outs, get_config, get_entry_by_type,
)

from helpers.helpers import (
    getDatacell, getDataColumns,  # rápidos
    print_ticket_usb  # pesado si importa win32print => modularizado abajo
)



def main(page: ft.Page):
    from components.Container import Container
    from components.Button import Button
    from components.TextField import TextField
    from components.Alert import Alert
    from components.AppBar import AppBar
    init_db()
    

    # GLOBALS VARS
    # Variables para saber si el usuario realmente seleccionó una fecha/hora

    state = {
        "current_tab": 0,
        "business_name": "Estacionamiento CECI",
        "fee": 0,
        "entries": [],
        "outs": [],
        "total": 0,
        "nBoxes": 19,
        "nBoxesAirBnb": 2,
        "config": None,
        "printer": None,
    }
    datacells = getDatacell(state["entries"])
    columns = getDataColumns(["FOLIO", "CÓDIGO", "FECHA", "HORA", "TIPO DE ENTRADA"])
    PASSWORD = "1234"  # Puedes cambiarla o hacerla configurable
    
    impresora_config = get_config("impresora")
    if impresora_config:
        try:
            config = json.loads(impresora_config)
            state["config"] = config
            state["printer"] = config.get("valor", None)
        except:
            message("Error al cargar la configuración de la impresora")




    ############################################################################################################

    # PAGE PROPIERTIES
    page.title = "Control " + state["business_name"]
    page.theme_mode = ft.ThemeMode.DARK

    ############################################################################################################
    
    # FUCTIONS

    def update_boxes_view():
        total_normales = state["nBoxes"]
        total_airbnb = state["nBoxesAirBnb"]

        actuales_normales = len([e for e in state["entries"] if e[6] == "Boleto normal" or e[6] == "Boleto Pensión" or e[6] == "Boleto Extraviado"])
        actuales_airbnb = len([e for e in state["entries"] if e[6] == "Boleto AirBnb"])

        disponibles_normales = max(total_normales - actuales_normales, 0)
        disponibles_airbnb = max(total_airbnb - actuales_airbnb, 0)

        boxs.value = str(disponibles_normales)
        boxsText_airbnb.value = str(disponibles_airbnb)
        page.update()


    def handle_menu_protected(target_index):
        def go():
            show_page(target_index, callback=load_config if target_index == 1 else load_prices if target_index == 2 else None)

        show_password_alert("Acceso restringido", go)


    def show_password_alert(title, on_success):

        def validate_password(e):
            if password_field.value == PASSWORD:
                password_field.value = ""
                alert_password.open = False
                on_success()
            else:
                password_field.error_text = "Contraseña incorrecta"
            page.update()

        password_field = ft.TextField(label="Contraseña", password=True, width=300, on_submit=validate_password)
        alert_password.title = ft.Text(title)  # <- CORRECTO
        alert_password.content = password_field
        alert_password.actions = [
            ft.TextButton("Cancelar", on_click=lambda e: close_password_alert()),
            ft.TextButton("Aceptar", on_click=validate_password)
        ]
        alert_password.open = True
        page.update()


    def close_password_alert():
        alert_password.open = False
        page.update()


    def guardar_cajones(e):
        try:
            state["nBoxes"] = int(input_normal_boxes.value)
            state["nBoxesAirBnb"] = int(input_airbnb_boxes.value)
            set_config("cajones_normales", str(state["nBoxes"]))
            set_config("cajones_airbnb", str(state["nBoxesAirBnb"]))
            update_boxes_view()
            alert_config_cajones.open = False
            page.open(ft.SnackBar(ft.Text("Configuración actualizada")))
        except ValueError:
            page.open(ft.SnackBar(ft.Text("Valores inválidos")))
        page.update()



    def load_boxes_config():
        try:
            cajones = get_config("cajones_normales")
            airbnb = get_config("cajones_airbnb")
            state["nBoxes"] = int(cajones) if cajones else 19
            state["nBoxesAirBnb"] = int(airbnb) if airbnb else 2
        except:
            state["nBoxes"] = 19
            state["nBoxesAirBnb"] = 2


    def close_alert_outs(e):
        alert_clean_outs.open = False
        page.update()

    def get_plain_data():
        registros = get_all_outs()
        return [
            [r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]]
            for r in registros
        ]

    def download_report_csv(e):
        import pandas as pd
        import os
        plain_data = get_plain_data()
        registros = []

        for r in plain_data:
            entrada = datetime.strptime(f"{r[3]} {r[2]}", "%Y-%m-%d %H:%M:%S")
            salida = datetime.strptime(f"{r[5]} {r[4]}", "%Y-%m-%d %H:%M:%S")
            duracion = salida - entrada
            duracion_min = int(duracion.total_seconds() // 60)
            duracion_hrs = round(duracion_min / 60, 2)
            dia_semana = salida.strftime('%A')

            if r[6] == "Boleto normal":
                cobro = f"Normal ({duracion_min} min)"
                if duracion_min > 60:
                    cobro += " + adicional"
            elif r[6] == "Boleto Pensión":
                cobro = "Pensión diaria"
            elif r[6] == "Boleto Extraviado":
                cobro = "Tarifa fija por extravío"
            else:
                cobro = "AirBnb"

            registros.append([
                r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8],
                duracion_min, duracion_hrs, dia_semana, cobro
            ])

        columnas = [
            "ID", "Código", "Hora entrada", "Fecha entrada", "Hora salida", "Fecha salida",
            "Tipo", "Precio unitario", "Total", "Duración (min)", "Duración (horas)",
            "Día de la semana", "Cobro aplicado"
        ]

        df = pd.DataFrame(registros, columns=columnas)

        try:
            df.to_csv(path_or_buf='reporte.csv', index=False)
            page.open(ft.SnackBar(ft.Text(f"Reporte guardado en {os.getcwd()}")))
            alert_clean_outs.open = True
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text("Error al guardar el reporte: " + str(ex))))
        
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
        selected_printer = usb_selector.value
        available_printers = get_usb_printers()

        if not available_printers:
            page.open(ft.SnackBar(ft.Text("No hay impresoras disponibles", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), bgcolor=ft.Colors.RED_400))
            return

        if selected_printer not in available_printers:
            page.open(ft.SnackBar(ft.Text("Selecciona una impresora válida", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), bgcolor=ft.Colors.RED_400))
            return

        if not is_printer_connected(selected_printer):
            page.open(ft.SnackBar(ft.Text("La impresora seleccionada no está conectada", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), bgcolor=ft.Colors.RED_400))
            return

        state["config"] = {"valor": selected_printer}
        state["printer"] = selected_printer
        set_config("impresora", json.dumps(state["config"]))
        show_page(0)
        page.open(ft.SnackBar(ft.Text("Impresora configurada correctamente")))

    def getBD(filtro="Todos"):
        entradas = get_all_entries()
        if filtro != "Todos":
            entradas = [e for e in entradas if e[6] == filtro]

        state["entries"] = entradas
        datacells = getDatacell(state["entries"])
        registers_database.rows.clear()
        registers_database.rows = datacells

        update_boxes_view()  # <- AGREGAR ESTO
        page.update()



    def close_alert_airbnb_pending(e):
        alert_airbnb_pending.open = False
        page.update()

    def createOut(code, price=0, total=0):
        out_date = datetime.now().strftime("%Y-%m-%d")
        fecha_salida_formato = formatear_fecha(datetime.now().strftime("%Y-%m-%d"))
        out_time = datetime.now().strftime("%H:%M:%S")
 
        tiempo_texto = ""
        if code[6] == "Boleto normal":
            entrada = datetime.strptime(f"{code[3]} {code[2]}", "%Y-%m-%d %H:%M:%S")
            salida = datetime.now()
            duracion = salida - entrada
            tiempo_total_segundos = duracion.total_seconds()
            horas = int(tiempo_total_segundos // 3600)
            minutos = int((tiempo_total_segundos % 3600) // 60)

            tiempo_texto = f" | Tiempo: {horas}h {minutos}min"

            # Si estuvo más de 10h, tarifa de pensión
            if tiempo_total_segundos >= 36000:
                _, precio_unitario = get_price_by_type("pension")
                total = precio_unitario
                price = precio_unitario
                tiempo_texto += " | Tarifa tipo pensión aplicada"
            else:
                es_jueves = datetime.now().weekday() == 3
                _, precio_unitario = get_price_by_day(es_jueves)
                try:
                    precio_unitario = float(precio_unitario)
                except:
                    precio_unitario = 0.0

                # Se cobra la primera hora completa
                total = precio_unitario

                # Si pasó más de una hora, se calcula el resto por fracciones de 30 min
                if horas >= 1:
                    horas_restantes = horas - 1
                    total += horas_restantes * precio_unitario

                    if minutos > 0:
                        if minutos <= 30:
                            total += precio_unitario / 2
                        else:
                            total += precio_unitario

                price = precio_unitario

        elif code[6] == "Boleto Pensión":
            entrada = datetime.strptime(f"{code[3]} {code[2]}", "%Y-%m-%d %H:%M:%S")
            salida = datetime.now()
            duracion = salida - entrada
            dias = duracion.days + 1 if duracion.seconds > 0 else duracion.days
            _, precio_unitario = get_price_by_type("pension")
            total = precio_unitario * dias
            price = precio_unitario
            tiempo_texto = f" | Tarifa Pensión aplicada ({dias} días)"

        elif code[6] == "Boleto Extraviado":
            _, precio_unitario = get_price_by_type("extraviado")
            total = precio_unitario
            price = precio_unitario
            tiempo_texto = " | Tarifa Extraviado aplicada"

        else:  # Boleto AirBnb
            price = 0.0
            total = 0.0
            tiempo_texto = " | Entrada tipo AirBnb"

        # Insertar en tabla de salidas
        insert_out(code[1], code[2], code[3], out_time, out_date, code[6], price, total)
        delete_entry(code[1])

        # 🖨️ Imprimir ticket de salida
        if state["printer"]:
            salida_data = {
                "placa": code[1],
                "hora_entrada": code[2],
                "fecha_entrada": code[3],
                "hora_salida": out_time,
                "fecha_salida": fecha_salida_formato,
                "total": f"{total:.2f}",
                "tipo": code[6]
            }
            print_ticket_usb(printer_name=state["printer"], data=salida_data, entrada=False)

        # Refrescar pantalla
        getBD()
        message(f"Boleto de salida generado. Total: ${total:.2f}{tiempo_texto}")
        page.update()



    def delete_all(e):
        delete_all_outs()
        alert_delete_registers.open = False
        snack_bar = ft.SnackBar(ft.Text("Se han borrado los registros de salidas."))
        page.open(snack_bar)

    def check_airbnb_pending():
        boletos = get_entry_by_type("Boleto AirBnb")
        hoy = datetime.now().date()
        pendientes = []

        for b in boletos:
            try:
                fecha_salida = datetime.strptime(b[5], "%Y-%m-%d").date()
                if fecha_salida <= hoy:
                    pendientes.append(b)
            except:
                continue

        if pendientes:
            show_pending_airbnb_alert(pendientes)

    def show_pending_airbnb_alert(pendientes):
        botones = []

        for boleto in pendientes:
            texto = f"{boleto[1]} - Sale {boleto[5]}"
            boton = ft.ElevatedButton(
                text=texto,
                on_click=lambda e, b=boleto: handle_airbnb_exit_from_alert(b), height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5))
            )
            botones.append(boton)

        alert_airbnb_pending.content = ft.Column([
            ft.Text("Boletos tipo AirBnb pendientes de salida:", height=50),
            *botones
        ], height=200, scroll=True)
        alert_airbnb_pending.open = True
        page.update()

    def handle_airbnb_exit_from_alert(boleto):
        createOut(boleto)
        alert_airbnb_pending.open = False
        page.update()
        


    def message(text=None):
        snack_bar = ft.SnackBar(ft.Text("Código no encontrado" if text is None else text, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), bgcolor=ft.Colors.RED_400, duration=ft.Duration(seconds=3))
        read_qr.value = ""
        page.open(snack_bar)
        read_qr.focus()
        page.update()

    def is_printer_connected(printer_name):
        try:
            import win32print
            hprinter = win32print.OpenPrinter(printer_name)
            win32print.ClosePrinter(hprinter)
            return True
        except:
            return False


    def get_usb_printers():
        try:
            import win32print
            return [printer[2] for printer in win32print.EnumPrinters(2)]
        except:
            return []

    def load_config():
        usb_selector.options = [ft.dropdown.Option(p) for p in get_usb_printers()]
        try:
            config_json = get_config("impresora")
            if config_json:
                config = json.loads(config_json)
                usb_selector.value = config.get("valor", None)
                state["config"] = config
                state["printer"] = config.get("valor", None)
        except Exception as e:
            snack_bar = ft.SnackBar(ft.Text(f"Error al cargar la configuración: {e}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), bgcolor=ft.Colors.RED_400, duration=ft.Duration(seconds=3))
            page.open(snack_bar)
        page.update()


    def load_prices():
        try:
            nombre_n, precio_n = get_price_by_type("normal")
            nombre_j, precio_j = get_price_by_type("jueves")
            nombre_p, precio_p = get_price_by_type("pension")
            nombre_e, precio_e = get_price_by_type("extraviado")

            name_fee_normal.value = nombre_n
            price_fee_normal.value = str(precio_n)
            name_fee_jueves.value = nombre_j
            price_fee_jueves.value = str(precio_j)
            name_fee_pension.value = nombre_p
            price_fee_pension.value = str(precio_p)
            name_fee_extraviado.value = nombre_e
            price_fee_extraviado.value = str(precio_e)
            page.update()
        except Exception as e:
            page.open(ft.SnackBar(ft.Text(f"Error al cargar tarifas: {e}")))



    def limpiar_salidas():
        delete_all_outs()
        alert_clean_outs.open = False
        page.open(ft.SnackBar(ft.Text("Se han borrado los registros de salidas.")))
        page.update()

    def close_alert_cajones(e):
        alert_config_cajones.open = False
        page.update()


    
    ############################################################################################################

    # ONCHANGES & ONSUBMITS

    def addAirBnb(plate=""):
        global hora_seleccionada, fecha_seleccionada 

        import re
        if not re.match(r"^[A-Z0-9]{5,8}$", plate):
            message("Placa inválida")
            return
        if  hora_seleccionada == False  or  fecha_seleccionada == False:
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
        
        ticket_data = {
            "placa": entry["codigo"],
            "hora_entrada": entry["hora_entrada"],
            "fecha_entrada": formatear_fecha(datetime.now().strftime("%Y-%m-%d")),
            "tipo": "Boleto AirBnb",
            "precio": "Precio Especial",
            "titulo": "Boleto AirBnb"
        }





        insert_entry(entry["codigo"], entry["hora_entrada"], entry["fecha"],
                    entry["hora_salida"], entry["fecha_salida"],
                    "Boleto AirBnb", entry["precio"], "Boleto AirBnb")
        print_ticket_usb(printer_name=state["printer"], data=ticket_data)


        alert.open = False
        plateField.value = ""
        date_picker.value = datetime.now().date()
        time_picker.value = datetime.now().time().replace(second=0, microsecond=0)
        textTime.visible = False
        textDate.visible = False
        rangeTime.visible = True
        rangeDate.visible = True
        hora_seleccionada = False
        fecha_seleccionada = False
        page.update()
        getBD()
        update_boxes_view()



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

    def formatear_fecha(fecha_iso):
        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        fecha = datetime.strptime(fecha_iso, "%Y-%m-%d")
        dia = fecha.day
        mes = meses[fecha.month - 1]
        año = fecha.year
        return f"{dia} de {mes} del {año}"
    def onSubmitReadQr(e):
        valor = e.control.value.strip().lower()
        now = datetime.now()
        codigo = now.strftime("%Y%m%d%H%M%S")
        hora = now.strftime("%H:%M:%S")
        fecha_entrada = formatear_fecha(now.strftime("%Y-%m-%d"))
        fecha = now.strftime("%Y-%m-%d")

        def imprimir_ticket_y_guardar(codigo, fecha, hora, tipo):
            if not state["printer"]:
                message("No hay impresora configurada. No se registró la entrada.")
                return False
            try:
                precio = 0.0

                if tipo == "Boleto normal":
                    es_jueves = datetime.now().weekday() == 3
                    _, precio = get_price_by_day(es_jueves)
                    costo = "MXN / Hora"
                    titulo = "Boleto de Entrada"
                elif tipo == "Boleto Pensión":
                    _, precio = get_price_by_type("pension")
                    costo = "MXN / DIA"
                    titulo = "Boleto Pensión"

                
                data = {
                    "placa": codigo,
                    "fecha_entrada": fecha_entrada,
                    "hora_entrada": hora,
                    "tipo": tipo,
                    "precio": f"{float(precio):.2f} {costo}",
                    "titulo": titulo
                }
                print_ticket_usb(printer_name=state["printer"], data=data)

                insert_entry(
                    codigo=codigo,
                    hora_entrada=hora,
                    fecha_entrada=fecha,
                    hora_salida=None,
                    fecha_salida=None,
                    type_entry=tipo,
                    precio=0,
                    status="Entrada"
                )
                read_qr.value = ""

                getBD()

                # ✅ Mensaje de confirmación
                texto = f"Boleto impreso correctamente a las {hora} del {fecha}"
                page.open(ft.SnackBar(ft.Text(texto)))
                return True
            except Exception as ex:
                message(f"Error al imprimir: {ex}")
                return False


        if valor == "autonuevo":
            imprimir_ticket_y_guardar(codigo, fecha, hora, "Boleto normal")

        elif valor == "pension":
            imprimir_ticket_y_guardar(codigo, fecha, hora, "Boleto Pensión")

        elif valor == "airbnb":
            if not state["printer"]:
                message("No hay impresora configurada. No se registró la entrada.")
                return
            else:
                alert.open = True
            page.update()

        elif valor == "extraviado":
            _, precio_unitario = get_price_by_type("extraviado")
            message(f"Boleto extraviado. Tarifa aplicada: ${precio_unitario:.2f}")
            if not state["printer"]:
                message("No hay impresora configurada. No se imprimió el ticket.")
                return
            print_ticket_usb(
                printer_name=state["printer"],
                data={"placa": codigo, "fecha_entrada": fecha_entrada, "hora_entrada": hora, "tipo": "Boleto extraviado","precio": f"{float(precio_unitario):.2f} MXN ", "titulo":"Boleto Extraviado"}
            )
            insert_entry(
                codigo=codigo,
                hora_entrada=hora,
                fecha_entrada=fecha,
                hora_salida=None,
                fecha_salida=None,
                type_entry="Boleto extraviado",
                precio=precio_unitario,
                status="Entrada"
            )

        else:
            code = get_entry_by_code(e.control.value)
            if code is None:
                message()
            else:
                if code[6] == "Boleto AirBnb":
                    airBnbOut(code)
                else:
                    createOut(code)
        read_qr.value = ""
        read_qr.focus()
        page.update()

    def onChangePage(e):
        # Página pública
        if e == 0:
            show_page(0)
        # Páginas protegidas
        elif e in [1, 2]:
            handle_menu_protected(e)

    ############################################################################################################

    # ONCLICKS

    def abrir_config_cajones():
        show_password_alert("Acceso a configuración", lambda: open_cajones_config())

    def download_report_secure(e):
        show_password_alert("Descargar reporte", lambda: download_report_csv(e))

    def delete_registers_secure(e):
        show_password_alert("Borrar registros", lambda: delete_registers(e))


    def open_cajones_config():
        input_normal_boxes.value = str(state["nBoxes"])
        input_airbnb_boxes.value = str(state["nBoxesAirBnb"])
        alert_config_cajones.open = True
        page.update()

    def delete_registers(e):
        alert_delete_registers.open = True
        page.update()

    def closeAlertRegisters(e):
        alert_delete_registers.open = False
        page.update()

    def close_alert(e):
        alert.open = False
        page.update()

    def handle_change_date(e):
        global fecha_seleccionada
        rangeDate.visible = False
        textDate.text = f'Fecha de salida: {str(date_picker.value)[:10]}'
        textDate.visible = True
        fecha_seleccionada = True
        page.update()
    
    def handle_change_time(e):
        global hora_seleccionada
        rangeTime.visible = False
        textTime.text = f'Hora de salida: {time_picker.value}'
        textTime.visible = True
        hora_seleccionada = True
        page.update()

    def handle_accept_airbnb(e):
        import re
        
        placa = plateField.value.strip().upper()
        if not placa:
            message("Debes ingresar la placa")
            return
        if not re.match(r"^[A-Z0-9]{5,8}$", placa):
            message("Placa inválida. Usa de 5 a 8 caracteres alfanuméricos")
            return
        if  hora_seleccionada == False  or  fecha_seleccionada == False:
            message("Debes seleccionar fecha y hora de salida")
            return
        
        addAirBnb(plate=placa)        
        getBD()
        alert.open = False
        
        page.update()


    def save_fee(e):
        set_all_prices(
            name_fee_normal.value, float(price_fee_normal.value),
            name_fee_jueves.value, float(price_fee_jueves.value),
            name_fee_pension.value, float(price_fee_pension.value),
            name_fee_extraviado.value, float(price_fee_extraviado.value)
                )
        show_page(0)
        page.update()

    def show_lost_ticket_dialog():
        entradas = get_all_entries()
        botones = []

        for entrada in entradas:
            texto = f"{entrada[1]} - {entrada[3]} {entrada[2]} - {entrada[6]}"
            boton = ft.TextButton(
                text=texto,
                on_click=lambda e, code=entrada: confirm_lost_ticket_exit(code),
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5))
            )
            botones.append(boton)

        alert_lost_ticket.content = ft.Column([
            ft.Text("Selecciona la entrada extraviada:", size=16),
            *botones
        ], scroll=True, height=300)
        alert_lost_ticket.open = True
        page.update()

    def confirm_lost_ticket_exit(code):
        _, precio_unitario = get_price_by_type("extraviado")
        hora = datetime.now().strftime("%H:%M:%S")
        fecha = datetime.now().strftime("%Y-%m-%d")
        insert_out(code[1], code[2], code[3], hora, fecha, "Boleto Extraviado", precio_unitario, precio_unitario)
        delete_entry(code[1])
        update_boxes_view()
        message(f"Boleto extraviado cerrado. Total: ${precio_unitario:.2f}")
        alert_lost_ticket.open = False
        getBD()
        page.update()



    def close_alert_lost():
        alert_lost_ticket.open = False
        page.update()


    ############################################################################################################


 
    # PAGES
    input_normal_boxes = TextField(label="Cajones normales", keyboard_type=ft.KeyboardType.NUMBER).build()
    input_airbnb_boxes = TextField(label="Cajones AirBnb", keyboard_type=ft.KeyboardType.NUMBER).build()
    plateField = TextField(label="Placa").build()

    alert_password = ft.AlertDialog(
    title=ft.Text("Autenticación requerida"),
    content=ft.Text("Cargando..."),
    actions=[
        ft.TextButton("Cancelar", on_click=lambda e: close_password_alert())
    ], shape=ft.RoundedRectangleBorder(radius=10)
)


    alert_lost_ticket = Alert(
        title="Boleto Extraviado",
        content=ft.Text("Cargando..."),
        onCancel=lambda e: close_alert_lost(),
        height=400,
        width=450
    ).build()




    alert_config_cajones = Alert(
        title="Editar número de cajones",
        content=ft.Column([
            input_normal_boxes,
            input_airbnb_boxes
        ]),
        action="Guardar",
        onAdd=guardar_cajones,
        onCancel=close_alert_cajones,
        cancel="Cancelar",
        width=400,
        height=150
    ).build()
    alert_config_cajones.open = False

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
            plateField,
            textTime,
            rangeTime,
            rangeDate,
            textDate,
        ], expand=True
    )
    read_qr = TextField(label="Leer QR", keyboard_type=ft.KeyboardType.NUMBER, onSubmit=onSubmitReadQr).build()
    filtro_tipo = ft.Dropdown(
    label="Filtrar por tipo",
    options=[
        ft.dropdown.Option("Todos"),
        ft.dropdown.Option("Boleto normal"),
        ft.dropdown.Option("Boleto Pensión"),
        ft.dropdown.Option("Boleto Extraviado"),
        ft.dropdown.Option("Boleto AirBnb")
    ],
    value="Todos",
    on_change=lambda e: getBD(filtro=e.control.value), border_color=ft.Colors.WHITE
)

    download_report = Button(text="DESCARGAR REPORTE", on_click=download_report_secure).build()
    delete_registers_button = Button(text="BORRAR REGISTROS", bgcolor=ft.Colors.RED_400, icon=ft.Icons.DELETE, on_click=delete_registers_secure).build()
    alert_delete_registers = Alert(content=ft.Text("Seguro que desea borrar los registros?"), action="Borrar", onAdd=delete_all, onCancel=closeAlertRegisters).build()
    alert_delete_registers.open = False
    boxs = ft.Text("19", size=44, text_align=ft.TextAlign.CENTER, expand=True)
    boxsText_airbnb = ft.Text("2", size=44, text_align=ft.TextAlign.CENTER, expand=True)
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
            ft.Row([
                ft.Text("CAJONES DISPONIBLES", size=16, weight=ft.FontWeight.BOLD, expand=True),
                ft.IconButton(icon=ft.Icons.SETTINGS, icon_color=ft.Colors.GREY_500, tooltip="Editar cajones", on_click=lambda e: abrir_config_cajones())
            ]),
            ft.Row([
                boxs
            ], expand=True, alignment=ft.MainAxisAlignment.CENTER
            )
        ]
    )
    boxs_airbnb = ft.Column(
        [
            ft.Row([
                ft.Text("CAJONES DISPONIBLES AIRBNB", size=16, weight=ft.FontWeight.BOLD, expand=True),
                ft.IconButton(icon=ft.Icons.SETTINGS, icon_color=ft.Colors.GREY_500, tooltip="Editar cajones", on_click=lambda e: abrir_config_cajones())
            ]),
            ft.Row([
                boxsText_airbnb
            ], expand=True, alignment=ft.MainAxisAlignment.CENTER
            )
        ]
    )
    containerBoxs = Container(business_name=state["business_name"], content=last_entry, height=130).build()
    containerBoxs_airbnb = Container(business_name=state["business_name"], content=boxs_airbnb, height=130).build()

    registers_database = ft.DataTable(
    columns= columns,
    rows=datacells,
    expand=True,
    )

    alert_airbnb_pending = Alert(
        title="Boletos AirBnb Pendientes",
        content=ft.Text(""),
        onCancel=close_alert_airbnb_pending,
        action=None,
        height=250,
        width=300
    ).build()
    alert_airbnb_pending.open = False

    alert_clean_outs = Alert(
        title="¿Limpiar base de datos de salidas?",
        content=ft.Text("¿Deseas borrar todos los registros de salidas después de descargar el reporte?"),
        onAdd=lambda e: limpiar_salidas(),
        onCancel=close_alert_outs,
        action="Sí, borrar",
        cancel="No borrar",
        height=300,
        width=400
    ).build()
    alert_clean_outs.open = False

    btn_extraviado_manual = Button(
    text="DAR SALIDA POR EXTRAVÍO",
    icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
    bgcolor=ft.Colors.ORANGE_300,
    on_click=lambda e: show_lost_ticket_dialog()
).build()




    page_0 = ft.Row(
        [
            ft.Column(
                [
                    Container(height=200, business_name=state["business_name"], content=content_data).build(),
                    containerBoxs,
                    containerBoxs_airbnb,
                    btn_extraviado_manual
                    
                ], width=350
            ),
            ft.Column([ 
                    Container(
                        business_name=state["business_name"],
                        content=ft.Row(
                            [registers_database], expand=True
                        ),
                        height=None, expand=True
                         
                    ).build()
                ],
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                alignment=ft.MainAxisAlignment.START,
            ),

        ], expand=True,vertical_alignment=ft.CrossAxisAlignment.START
    )

    ###########################################################################################################
    # page 1

    usb_selector = ft.Dropdown(
        label="Impresoras USB",
        width=300, border_color=ft.Colors.WHITE,
    )

    config_container = Container(
        business_name=state["business_name"],
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
    name_fee_normal = TextField(label="Nombre tarifa normal", width=300).build()
    price_fee_normal = TextField(label="Precio tarifa normal", keyboard_type=ft.KeyboardType.NUMBER, width=300).build()

    name_fee_jueves = TextField(label="Nombre tarifa jueves", width=300).build()
    price_fee_jueves = TextField(label="Precio tarifa jueves", keyboard_type=ft.KeyboardType.NUMBER, width=300).build()

    name_fee_pension = TextField(label="Nombre tarifa pensión", width=300).build()
    price_fee_pension = TextField(label="Precio tarifa pensión", keyboard_type=ft.KeyboardType.NUMBER, width=300).build()

    name_fee_extraviado = TextField(label="Nombre tarifa extraviado", width=300).build()
    price_fee_extraviado = TextField(label="Precio tarifa extraviado", keyboard_type=ft.KeyboardType.NUMBER, width=300).build()


    fee_container = Container(
        business_name=state["business_name"],
        content=ft.Column(
            [
                ft.Text("CONFIGURACIÓN DE TARIFA", size=26, weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        ft.Column([
                    name_fee_normal,
                    price_fee_normal,
                ]),
                ft.Column([
                    name_fee_jueves,
                    price_fee_jueves,
                ]),
                    ft.Column([name_fee_pension, price_fee_pension]),
                    ft.Column([name_fee_extraviado, price_fee_extraviado]),
                    ], expand=True, alignment=ft.MainAxisAlignment.CENTER
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

    loading_indicator = ft.ProgressRing(width=60, height=60)
    loading_text = ft.Text("Cargando sistema, por favor espera...", size=16)
    loading_screen = ft.Column(
        [loading_indicator, loading_text],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True
    )

    page.add(loading_screen)
    page.update()


    import threading

    def load_background_data():
        init_db()  # crea DB si no existe

        # Configuración impresora
        impresora_config = get_config("impresora")
        if impresora_config:
            try:
                config = json.loads(impresora_config)
                state["config"] = config
                state["printer"] = config.get("valor", None)
            except:
                pass

        load_boxes_config()
        update_boxes_view()
        getBD()

        # Cargar entradas y refrescar tabla
        state["entries"] = get_all_entries()
        datacells = getDatacell(state["entries"])
        registers_database.rows.clear()
        registers_database.rows = datacells

        check_airbnb_pending()

        # ✅ Ocultar pantalla de carga y mostrar interfaz real
        page.controls.clear()
        page.appbar = AppBar(business_name=state["business_name"], onChange=onChangePage, filters= filtro_tipo ).build()
        page.add(
            ft.SafeArea(
                ft.Column(
                    [
                        page_0,
                        page_1,
                        page_2,
                        alert,
                        alert_config_cajones,
                        alert_password,
                        alert_airbnb_pending,
                        alert_clean_outs,
                        alert_lost_ticket
                    ], expand=True
                ), expand=True
            )
        )
        read_qr.focus()
        page.update()

    # Lanzar en segundo plano después de mostrar loading
    threading.Thread(target=load_background_data).start()

    ############################################################################################################
    
    
ft.app(main)
