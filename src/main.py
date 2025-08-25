import flet as ft
from datetime import datetime
import json

from database import (
    init_db, get_all_entries, insert_entry, delete_entry,
    get_entry_by_code, get_price_by_day, get_price_by_type,
    insert_out, set_all_prices, get_all_outs, set_config,
    delete_all_outs, get_config, get_entry_by_type,set_price_dollar, get_dollar_price
)

hora_seleccionada = False
fecha_seleccionada = False

from helpers.helpers import (
    getDatacell, getDataColumns, 
    print_ticket_usb  
)

def main(page: ft.Page):
    from components.Container import Container
    from components.Button import Button
    from components.TextField import TextField
    from components.Alert import Alert
    from components.AppBar import AppBar
    init_db()

    

    state = {
    "current_tab": 0,
    "business_name": "Estacionamiento CECI",
    "entries": [],   
    "entries_all": [],     
    "nBoxes": 19,
    "nBoxesHospedaje": 2,
    "config": None,
    "printer": None,
    "pending_checkout": None,
    "dolar_price": None
}


    datacells = getDatacell(state["entries"])
    columns = getDataColumns(["FOLIO", "CÓDIGO", "FECHA", "HORA", "TIPO DE ENTRADA"])
    PASSWORD = "H0608"  # Puedes cambiarla o hacerla configurable
    
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

        # === Cajones disponibles por tipo + alerta no bloqueante ===
    def _disponibles_por_tipo(tipo: str) -> int:
        tipo = (tipo or "").strip()

        actuales_normales = len([e for e in state["entries_all"] if e[6] in ("Boleto normal", "Boleto Pensión")])
        actuales_hosp = len([e for e in state["entries_all"] if e[6] == "Boleto Hospedaje"])

        if tipo in ("Boleto normal", "Boleto Pensión"):
            return max(state["nBoxes"] - actuales_normales, 0)
        elif tipo == "Boleto Hospedaje":
            return max(state["nBoxesHospedaje"] - actuales_hosp, 0)
        # Por defecto tratamos como normal
        return max(state["nBoxes"] - actuales_normales, 0)


    def update_boxes_view():
        total_normales = state["nBoxes"]
        total_hosp = state["nBoxesHospedaje"]

        # Cuenta SIEMPRE sobre TODAS las entradas
        actuales_normales = len([e for e in state["entries_all"] if e[6] in ("Boleto normal", "Boleto Pensión")])
        actuales_hosp    = len([e for e in state["entries_all"] if e[6] == "Boleto Hospedaje"])

        disponibles_normales = max(total_normales - actuales_normales, 0)
        disponibles_hosp     = max(total_hosp - actuales_hosp, 0)

        boxs.value = str(disponibles_normales)
        boxsText_hospedaje.value = str(disponibles_hosp)
        page.update()



    def warn_if_full(tipo: str):
        """Muestra alerta si no hay espacio disponible, pero NO bloquea el flujo."""
        disponibles = _disponibles_por_tipo(tipo)
        if disponibles <= 0:
            mensaje = "No hay espacio disponible para este tipo de boleto.\nSe imprimirá el boleto de todas formas."
            open_full_alert(mensaje)



    def handle_menu_protected(target_index):
        def go():
            show_page(target_index, callback=load_config if target_index == 1 else load_prices if target_index == 2 else None)

        show_password_alert("Acceso restringido", go)


    def show_password_alert(title, on_success):

        def validate_password(e):
            if password_field.value == PASSWORD:
                password_field.value = ""
                alert_password.open = False
                
                page.update()
                on_success()
            else:
                password_field.error_text = "Contraseña incorrecta"
                page.update()

        password_field = ft.TextField(label="Contraseña", password=True, width=300, on_submit=validate_password)
        alert_password.title = ft.Text(title)
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
            state["nBoxesHospedaje"] = int(input_hospedaje_boxes.value)  # antes input_hospedaje_boxes
            set_config("cajones_normales", str(state["nBoxes"]))
            set_config("cajones_hospedaje", str(state["nBoxesHospedaje"]))  # antes cajones_hospedaje
            update_boxes_view()
            alert_config_cajones.open = False
            page.open(ft.SnackBar(ft.Text("Configuración actualizada")))
        except ValueError:
            page.open(ft.SnackBar(ft.Text("Valores inválidos")))
        page.update()




    def load_boxes_config():
        try:
            cajones = get_config("cajones_normales")
            hosp = get_config("cajones_hospedaje")   # antes cajones_hospedaje
            state["nBoxes"] = int(cajones) if cajones else 19
            state["nBoxesHospedaje"] = int(hosp) if hosp else 2
        except:
            state["nBoxes"] = 19
            state["nBoxesHospedaje"] = 2



    def close_alert_outs(e):
        alert_clean_outs.open = False
        page.update()

    def get_plain_data():
        registros = get_all_outs()
        return [
            [r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]]
            for r in registros
        ]
    
    progress_ring = ft.ProgressRing()

    # Crear un Alert que contendrá el ProgressRing
    alert_ring = ft.AlertDialog(
        modal=True,
        shape=ft.RoundedRectangleBorder(radius=5),
        title=ft.Text("Generando reporte..."),
        content=ft.Row(
            [
                progress_ring
            ], width=50, height=50, alignment=ft.MainAxisAlignment.CENTER
        ), alignment=ft.alignment.center
    )
    alert_ring.open = False
    
    def send_email(file: str):
        # --- Imports locales para no contaminar el resto del módulo ---
        import flet as ft
        from datetime import datetime
        from pathlib import Path
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.application import MIMEApplication
        import smtplib
        import os

        # --- Config SMTP (hardcoded) ---
        SMTP_HOST = "smtp.gmail.com"
        SMTP_PORT = 587
        SMTP_USER = "reportestectronic@gmail.com"
        # ¡OJO! Los app passwords de Gmail van sin espacios:
        SMTP_PASS = "tdllhiwbqmrzpqec"
        USE_SSL = False
        USE_STARTTLS = True

        # --- Datos de correo (hardcoded) ---
        # Por políticas de Gmail, conviene que el From sea el mismo usuario autenticado.
        EMAIL_FROM = SMTP_USER
        EMAIL_REPLY_TO = "debora.cecilia.hc@gmail.com"   # aparecerá como dirección de respuesta
        EMAIL_TO = ["debora.cecilia.hc@gmail.com"]
        SUBJECT_PREFIX = "Reporte de salidas"
        BODY_TEXT = "Reporte de Usuarios"

        # --- Componer mensaje ---
        message = MIMEMultipart()
        message["From"] = EMAIL_FROM
        message["To"] = ", ".join(EMAIL_TO)
        message["Subject"] = f"{SUBJECT_PREFIX} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        message["Reply-To"] = EMAIL_REPLY_TO
        message.attach(MIMEText(BODY_TEXT, "plain", "utf-8"))

        # Adjuntar archivo (CSV u otro)
        try:
            with open(file, "rb") as f:
                attachment = MIMEApplication(f.read(), _subtype="octet-stream")
            attachment.add_header("Content-Disposition", "attachment", filename=Path(file).name)
            message.attach(attachment)
        except Exception as e:
            snack_bar = ft.SnackBar(
                ft.Text(f"No se pudo adjuntar el archivo: {e}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_400, duration=ft.Duration(seconds=4)
            )
            page.open(snack_bar)
            page.update()
            return

        # --- Envío ---
        try:
            if USE_SSL:
                with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
                    server.login(SMTP_USER, SMTP_PASS)
                    server.sendmail(EMAIL_FROM, EMAIL_TO, message.as_string())
            else:
                with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                    if USE_STARTTLS:
                        server.starttls()
                    server.login(SMTP_USER, SMTP_PASS)
                    server.sendmail(EMAIL_FROM, EMAIL_TO, message.as_string())

            snack_bar = ft.SnackBar(
                ft.Text("Correo enviado correctamente", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.GREEN_400, duration=ft.Duration(seconds=3)
            )
            page.open(snack_bar)
        except Exception as e:
            snack_bar = ft.SnackBar(
                ft.Text(f"Error al enviar el correo: {e}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_400, duration=ft.Duration(seconds=4)
            )
            page.open(snack_bar)
        finally:
            page.update()



    def download_report_csv(e):
        import pandas as pd
        import os

        plain_data = get_plain_data()
        registros = []

        # Tipo de cambio actual (MXN por 1 USD)
        try:
            tc = float(get_dollar_price() or 0.0)
        except:
            tc = 0.0

        for r in plain_data:
            # r: [id, codigo, hora_ent, fecha_ent, hora_sal, fecha_sal, tipo, precio, total]
            try:
                entrada = datetime.strptime(f"{r[3]} {r[2]}", "%Y-%m-%d %H:%M:%S")
                salida = datetime.strptime(f"{r[5]} {r[4]}", "%Y-%m-%d %H:%M:%S")
            except:
                entrada = salida = datetime.now()

            duracion = salida - entrada
            duracion_min = int(duracion.total_seconds() // 60)
            duracion_hrs = round(duracion_min / 60, 2)

            dias_semana = {
                "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
                "Thursday": "Jueves", "Friday": "Viernes",
                "Saturday": "Sábado", "Sunday": "Domingo"
            }
            dia_semana = dias_semana.get(salida.strftime('%A'), salida.strftime('%A'))

            # Etiqueta de cobro
            if r[6] == "Boleto normal":
                cobro = f"Normal ({duracion_min} min)" + (" + adicional" if duracion_min > 60 else "")
            elif r[6] == "Boleto Pensión":
                cobro = "Pensión diaria"
            elif r[6] == "Boleto Extraviado":
                cobro = "Tarifa fija por extravío"
            else:
                cobro = "Hospedaje"

            # Moneda usada (si no existe, asumimos MXN)
            moneda_key = f"moneda:{r[1]}:{r[4]}:{r[5]}"
            moneda_usada = get_config(moneda_key) or "MXN"

            # Totales (usamos el total guardado en BD para MXN y convertimos a USD)
            try:
                total_mxn = float(r[8] or 0.0)
            except:
                total_mxn = 0.0
            total_usd = round((total_mxn / tc), 2) if tc > 0 else 0.0

            registros.append([
                r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7],  # hasta Precio unitario
                duracion_min, duracion_hrs, dia_semana, cobro,   # métricas
                round(total_mxn, 2), total_usd, moneda_usada     # columnas nuevas
            ])

        columnas = [
            "ID", "Código", "Hora entrada", "Fecha entrada", "Hora salida", "Fecha salida",
            "Tipo", "Precio unitario",
            "Duración (min)", "Duración (horas)",
            "Día de la semana", "Cobro aplicado",
            "Total (MXN)", "Total (USD)", "Moneda utilizada"
        ]

        df = pd.DataFrame(registros, columns=columnas)
        alert_ring.open = True
        page.update()
        try:
            df.to_csv(path_or_buf='reporte.csv', index=False, encoding="utf-8-sig")
            send_email(file=str(os.getcwd()) + "/reporte.csv")
            page.open(ft.SnackBar(ft.Text(f"Reporte guardado en {os.getcwd()}")))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text("Error al guardar el reporte: " + str(ex))))
        alert_ring.open = False
        alert_clean_outs.open = True
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

    def getBD(filtro=None):
        # 1) Cargar SIEMPRE todas las entradas
        entradas_all = get_all_entries()
        state["entries_all"] = entradas_all

        # 2) Determinar filtro actual (si no te pasan uno)
        if filtro is None:
            try:
                filtro = filtro_tipo.value or "Todos"
            except:
                filtro = "Todos"

        # 3) Generar las entradas visibles para la tabla según filtro
        if filtro != "Todos":
            entradas_visibles = [e for e in entradas_all if e[6] == filtro]
        else:
            entradas_visibles = entradas_all

        state["entries"] = entradas_visibles
        state["dolar_price"] = float(get_dollar_price() or 20.0)

        # 4) Refrescar la tabla con las visibles
        datacells = getDatacell(state["entries"])
        registers_database.rows.clear()
        registers_database.rows = datacells

        # 5) Actualizar los contadores de cajones usando entries_all
        update_boxes_view()
        page.update()




    def close_alert_hospedaje_pending (e):
        alert_hospedaje_pending .open = False
        page.update()

    def open_currency_dialog(payload):
        state["pending_checkout"] = payload

        mxn_total = float(payload["total_mxn"] or 0.0)
        price_mxn = float(payload.get("price_mxn", 0.0))
        title_override = payload.get("title")
        show_dual = bool(payload.get("show_dual", False))

        # Lee TC (MXN por 1 USD)
        try:
            _, tc_raw = get_price_by_type("dolar")
            tc = float(tc_raw or 0.0)
        except:
            tc = 0.0

        usd_total = (mxn_total / tc) if tc > 0 else None
        price_usd = (price_mxn / tc) if tc > 0 else None

        # ---- UI controls ----
        currency_group = ft.RadioGroup(
            value="MXN",
            content=ft.Row(
                [
                    ft.Radio(value="MXN", label="MXN"),
                    ft.Radio(value="USD", label="USD", disabled=(tc <= 0)),
                ]
            )
        )

        tc_text = ft.Text(
            f"TC: {tc:.4f} MXN por 1 USD" if tc > 0 else "TC no configurado (habilita USD guardando un TC > 0)"
        )
        total_text = ft.Text("")      
        change_text = ft.Text("")
        dual_text = ft.Text("")            
        unit_text = ft.Text("")          

        amount_field = ft.TextField(
            label="Monto entregado",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: update_totals(),
            on_submit=lambda e: on_confirm(),
            autofocus=True,
            width=250,
        )

        btn_cancel = ft.TextButton("Cancelar", on_click=lambda e: close_currency_dialog())
        btn_ok = ft.FilledButton("Cobrar e imprimir", on_click=lambda e: on_confirm())
        btn_ok.disabled = True

        def _current_total_and_currency():
            curr = currency_group.value
            if curr == "USD" and usd_total is not None:
                return round(usd_total, 2), "USD"
            return round(mxn_total, 2), "MXN"

        def parse_amount():
            try:
                return float((amount_field.value or "").strip())
            except:
                return 0.0

        def update_totals():
            total, curr = _current_total_and_currency()
            total_text.value = f"Total a pagar: ${total:.2f} {curr}"

            pay = parse_amount()
            change = pay - total

            if curr == "USD" and tc > 0:
                pay_mxn = pay * tc
                change_mxn = pay_mxn - mxn_total
                change_text.value = f"Cambio: ${change:.2f} USD (≈ ${change_mxn:.2f} MXN)" if pay >= 0 else f"Cambio: -- USD (≈ -- MXN)"
            else:
                change_text.value = f"Cambio: ${change:.2f} {curr}" if pay >= 0 else f"Cambio: -- {curr}"

            # Mostrar ambos totales y precio unitario si aplica
            if show_dual:
                if tc > 0:
                    dual_text.value = f"Total: ${mxn_total:.2f} MXN  (≈ ${mxn_total/tc:.2f} USD)"
                    unit_text.value = f"Tarifa: ${price_mxn:.2f} MXN  (≈ ${price_usd:.2f} USD)"
                else:
                    dual_text.value = f"Total: ${mxn_total:.2f} MXN"
                    unit_text.value = f"Tarifa: ${price_mxn:.2f} MXN"

            btn_ok.disabled = pay < total
            page.update()

        def on_confirm():
            total, curr = _current_total_and_currency()
            pay = parse_amount()
            change = max(pay - total, 0.0)

            salida_data = payload["salida_data"]
            salida_data["paga"] = f"{pay:.2f} {curr}"
            salida_data["cambio"] = f"{change:.2f} {curr}"

            # Si cobran en USD, agrega también los equivalentes en MXN (útil para ticket)
            if curr == "USD" and tc > 0:
                paga_mxn = pay * tc
                cambio_mxn = max(paga_mxn - mxn_total, 0.0)
                salida_data["paga_mxn"] = f"{paga_mxn:.2f} MXN"
                salida_data["cambio_mxn"] = f"{cambio_mxn:.2f} MXN"

            handle_currency_select(curr)

        currency_group.on_change = lambda e: update_totals()

        # Armar diálogo (con título custom si viene)
        currency_alert.title = ft.Text(title_override or "Selecciona la moneda y captura el pago")
        content_children = [currency_group, tc_text, total_text]
        if show_dual:
            content_children.extend([dual_text, unit_text])
        content_children.extend([amount_field, change_text])

        currency_alert.content = ft.Column(
            content_children,
            spacing=8,
            tight=True,
            width=380
        )
        currency_alert.actions = [btn_cancel, btn_ok]
        currency_alert.open = True

        update_totals()
        page.update()

    def close_currency_dialog():
        currency_alert.open = False
        state["pending_checkout"] = None
        page.update()

    def handle_currency_select(moneda):
        data = state.get("pending_checkout")
        if not data:
            close_currency_dialog()
            return

        code = data["code"]
        price_mxn = float(data["price_mxn"] or 0.0)
        total_mxn = float(data["total_mxn"] or 0.0)
        salida_data = data["salida_data"]
        tiempo_texto = data.get("tiempo_texto", "")

        # Strings por defecto (MXN)
        total_str = f"{total_mxn:.2f} MXN"
        precio_unit_str = f"{price_mxn:.2f} MXN"

        # Tipo de cambio
        try:
            _, tc_raw = get_price_by_type("dolar")
            tc = float(tc_raw or 0.0)
        except:
            tc = 0.0

        # Si pagan en USD, TOTAL y TARIFA salen en formato dual "USD / MXN"
        if moneda == "USD" and tc > 0:
            usd_total = total_mxn / tc
            usd_unit = (price_mxn / tc) if price_mxn else 0.0

            # ✅ TOTAL dual para el ticket
            total_str = f"{usd_total:.2f} USD / {total_mxn:.2f} MXN"

            # ✅ TARIFA dual (opcional). Si NO quieres dual en tarifa, deja: precio_unit_str = f"{usd_unit:.2f} USD"
            precio_unit_str = f"{usd_unit:.2f} USD / {price_mxn:.2f} MXN"

            salida_data["tc"] = f"TC: {tc:.4f}"

        salida_data["total"] = total_str
        salida_data["precio_unitario"] = precio_unit_str
        salida_data["moneda"] = "USD" if (moneda == "USD" and tc > 0) else "MXN"

        # === Rama especial: Boleto Extraviado sin entrada previa ===
        if data.get("mode") == "extraviado":
            hora_ent_iso = data["entrada_hora_iso"]
            fecha_ent_iso = data["entrada_fecha_iso"]
            hora_sal_iso = data["salida_hora_iso"]
            fecha_sal_iso = data["salida_fecha_iso"]
            placa = code.get("placa")

            # Guardar salida en BD (siempre valores MXN)
            insert_out(
                placa,
                hora_ent_iso, fecha_ent_iso,
                hora_sal_iso, fecha_sal_iso,
                "Boleto Extraviado",
                price_mxn, total_mxn
            )
            set_config(f"moneda:{placa}:{hora_sal_iso}:{fecha_sal_iso}", salida_data["moneda"])

            # Imprimir ticket
            if state["printer"]:
                print_ticket_usb(printer_name=state["printer"], data=salida_data, entrada=False)

            getBD()
            message(f"Pago por extravío registrado. Total mostrado: {salida_data['total']}")
            close_currency_dialog()
            return
        # === Fin rama extraviado ===

        # ---- Flujo normal (hay entrada en BD) ----
        insert_out(
            code[1], code[2], code[3],
            salida_data["hora_salida"], datetime.now().strftime("%Y-%m-%d"),
            code[6], price_mxn, total_mxn
        )

        fecha_salida_iso = datetime.now().strftime("%Y-%m-%d")
        set_config(f"moneda:{code[1]}:{salida_data['hora_salida']}:{fecha_salida_iso}", salida_data["moneda"])

        delete_entry(code[1])

        if state["printer"]:
            print_ticket_usb(printer_name=state["printer"], data=salida_data, entrada=False)

        getBD()
        message(f"Boleto de salida generado. Total mostrado: {salida_data['total']}{tiempo_texto}")
        close_currency_dialog()



    def start_extraviado_flow(codigo: str):
       
        _, precio_unitario = get_price_by_type("extraviado")
        price_mxn = float(precio_unitario or 0.0)

        # Tiempos (sin entrada real: usamos la misma hora/fecha)
        now = datetime.now()
        hora_iso = now.strftime("%H:%M:%S")
        fecha_iso = now.strftime("%Y-%m-%d")

        # Datos para ticket (fecha con formato bonito)
        salida_data = {
            "placa": codigo,
            "hora_entrada": hora_iso,  
            "fecha_entrada": formatear_fecha(fecha_iso), 
            "hora_salida": hora_iso,
            "fecha_salida": formatear_fecha(fecha_iso),
            "tipo": "Boleto Extraviado",
            "total": "",
        }

        # Reusar el mismo diálogo de cobro que usas para normales/pensión
        # con banderas para mostrar ambos precios (MXN y USD) en la UI.
        open_currency_dialog({
            "mode": "extraviado",          
            "code": {"placa": codigo},   
            "price_mxn": price_mxn,
            "total_mxn": price_mxn,
            "salida_data": salida_data,
            "tiempo_texto": " | Tarifa Extraviado aplicada",
            "title": "Cobro boleto extraviado",
            "show_dual": True,            
            "entrada_hora_iso": hora_iso,
            "entrada_fecha_iso": fecha_iso,
            "salida_hora_iso": hora_iso,
            "salida_fecha_iso": fecha_iso,
        })


    def createOut(code):
        # Tomamos un 'now' único para consistencia
        now = datetime.now()
        fecha_salida_formato = formatear_fecha(now.strftime("%Y-%m-%d"))
        out_time = now.strftime("%H:%M:%S")

        if es_hospedaje(code[6]):
            salida_data = {
                "placa": code[1],
                "hora_entrada": code[2],
                "fecha_entrada": code[3],
                "hora_salida": out_time,
                "fecha_salida": fecha_salida_formato,
                "tipo": code[6],
                "total": "0.00 MXN",
                "precio_unitario": "0.00 MXN",
                "moneda": "MXN",
            }
            insert_out(
                code[1], code[2], code[3],
                out_time, now.strftime("%Y-%m-%d"),
                code[6], 0.0, 0.0
            )
            set_config(f"moneda:{code[1]}:{out_time}:{now.strftime('%Y-%m-%d')}", "MXN")
            delete_entry(code[1])
            if state["printer"]:
                print_ticket_usb(printer_name=state["printer"], data=salida_data, entrada=False)
            getBD()
            message("Boleto de Hospedaje cerrado. Total: $0.00 MXN")
            return

        tiempo_texto = ""
        price_mxn = 0.0
        total_mxn = 0.0

        if code[6] == "Boleto normal":
            entrada = datetime.strptime(f"{code[3]} {code[2]}", "%Y-%m-%d %H:%M:%S")
            salida = now
            duracion = salida - entrada
            tiempo_total_segundos = duracion.total_seconds()
            horas = int(tiempo_total_segundos // 3600)
            minutos = int((tiempo_total_segundos % 3600) // 60)
            tiempo_texto = f" | Tiempo: {horas}h {minutos}min"

            if tiempo_total_segundos >= 36000:  # 10 horas → pensión diaria
                _, precio_unitario = get_price_by_type("pension")
                price_mxn = float(precio_unitario or 0.0)
                total_mxn = price_mxn
                tiempo_texto += " | Tarifa tipo pensión aplicada"
            else:
                # ✅ Decidir tarifa por la HORA DE ENTRADA (jueves 15:00–21:59)
                aplicar_tarifa_especial = (entrada.weekday() == 3) and (15 <= entrada.hour < 22)

                _, precio_unitario = get_price_by_day(aplicar_tarifa_especial)
                try:
                    price_mxn = float(precio_unitario)
                except:
                    price_mxn = 0.0

                # 1a hora
                total_mxn = price_mxn
                if horas >= 1:
                    horas_restantes = horas - 1
                    total_mxn += horas_restantes * price_mxn
                    if minutos > 0:
                        total_mxn += (price_mxn / 2) if (minutos <= 30) else price_mxn

        elif code[6] == "Boleto Pensión":
            # --- Días + horas extra (hasta 6h a tarifa normal/jueves; >6h = +1 día) ---
            entrada = datetime.strptime(f"{code[3]} {code[2]}", "%Y-%m-%d %H:%M:%S")
            salida = now
            duracion = salida - entrada

            # Precio de la pensión (por día)
            _, precio_pension = get_price_by_type("pension")
            pension_dia = float(precio_pension or 0.0)

            # Días base cobrados
            if duracion.days == 0:
                dias_cobrados = 1
                extra_seg = 0
            else:
                dias_cobrados = duracion.days
                extra_seg = duracion.seconds  # resto por encima de días completos

            total_mxn = pension_dia * max(dias_cobrados, 1)
            texto_extra = ""

            # Si hay remanente sobre días completos, evaluar cargos extra
            if extra_seg > 0:
                extra_horas = int(extra_seg // 3600)
                extra_min = int((extra_seg % 3600) // 60)

                # Si excede 6h exactas, se considera otro día completo de pensión
                if (extra_horas > 6) or (extra_horas == 6 and extra_min > 0):
                    total_mxn += pension_dia
                    texto_extra = " | +1 día por excedente > 6h"
                else:
                    # ✅ Extras decididos por HORA DE ENTRADA (jueves 15:00–21:59)
                    aplicar_tarifa_especial = (entrada.weekday() == 3) and (15 <= entrada.hour < 22)

                    _, precio_normal = get_price_by_day(aplicar_tarifa_especial)
                    precio_normal = float(precio_normal or 0.0)

                    extra_cargo = 0.0
                    if extra_horas == 0:
                        if extra_min > 0:
                            extra_cargo += (precio_normal / 2) if extra_min <= 30 else precio_normal
                    else:
                        # primera hora
                        extra_cargo += precio_normal
                        # horas adicionales
                        if extra_horas > 1:
                            extra_cargo += (extra_horas - 1) * precio_normal
                        # minutos
                        if extra_min > 0:
                            extra_cargo += (precio_normal / 2) if extra_min <= 30 else precio_normal

                    total_mxn += extra_cargo
                    etiqueta = "jueves" if aplicar_tarifa_especial else "normal"
                    texto_extra = f" | Extras: {extra_horas}h {extra_min}min a tarifa {etiqueta}"

            tiempo_texto = f" | Tarifa Pensión aplicada ({max(dias_cobrados,1)} día(s)){texto_extra}"
            price_mxn = pension_dia  # precio unitario de referencia (por día)

        elif code[6] == "Boleto Extraviado":
            _, precio_unitario = get_price_by_type("extraviado")
            price_mxn = float(precio_unitario or 0.0)
            total_mxn = price_mxn
            tiempo_texto = " | Tarifa Extraviado aplicada"

        # 2) Datos base del ticket (el total se llenará tras elegir moneda)
        salida_data = {
            "placa": code[1],
            "hora_entrada": code[2],
            "fecha_entrada": code[3],
            "hora_salida": out_time,
            "fecha_salida": fecha_salida_formato,
            "total": "",
            "tipo": code[6],
        }

        # 3) Abrir diálogo de moneda y finalizar según selección
        open_currency_dialog({
            "code": code,
            "price_mxn": price_mxn,
            "total_mxn": total_mxn,
            "salida_data": salida_data,
            "tiempo_texto": tiempo_texto
        })





    def delete_all(e):
        delete_all_outs()
        alert_delete_registers.open = False
        snack_bar = ft.SnackBar(ft.Text("Se han borrado los registros de salidas."))
        page.open(snack_bar)
        page.update()

    def check_hospedaje_pending():
        boletos = get_entry_by_type("Boleto Hospedaje")
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
            show_pending_hospedaje_alert(pendientes)

    def show_pending_hospedaje_alert(pendientes):
        botones = []

        for boleto in pendientes:
            texto = f"{boleto[1]} - Sale {boleto[5]}"
            boton = ft.ElevatedButton(
                text=texto,
                on_click=lambda e, b=boleto: handle_hospedaje_exit_from_alert(b), height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5))
            )
            botones.append(boton)

        alert_hospedaje_pending .content = ft.Column([
            ft.Text("Boletos tipo hospedaje pendientes de salida:", height=50),
            *botones
        ], height=200, scroll=True)
        alert_hospedaje_pending .open = True
        page.update()

    def handle_hospedaje_exit_from_alert(boleto):
        createOut(boleto)
        alert_hospedaje_pending .open = False
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

    def addHospedaje(plate=""):
        global hora_seleccionada, fecha_seleccionada 

        import re
        if not re.match(r"^[A-Z0-9]{5,8}$", plate):
            message("Placa inválida")
            return
        if  hora_seleccionada == False  or  fecha_seleccionada == False:
            message("Debes seleccionar fecha y hora de salida")
            return
        ex = get_entry_by_code(plate)
        if ex and ex[6] == "Boleto Hospedaje":
            message("Esta placa ya fue registrada como Boleto Hospedaje")
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
            "tipo": "Boleto Hospedaje",
            "precio": "Precio Especial",
            "titulo": "  Hospedaje"
        }
        warn_if_full("Boleto Hospedaje")
        insert_entry(entry["codigo"], entry["hora_entrada"], entry["fecha"],
                    entry["hora_salida"], entry["fecha_salida"],
                    "Boleto Hospedaje", entry["precio"], "Boleto Hospedaje")
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



    def hospedajeOut(code):
        try:
            entry_date = datetime.strptime(code[5], "%Y-%m-%d").date()
        except Exception:
            message("Fecha de salida inválida en el boleto")
            return

        today = datetime.now().date()
        if today >= entry_date:
            createOut(code)
        else:
            message(f"El boleto con placa {code[1]} no puede salir hoy")

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
                warn_if_full(tipo)

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

        elif valor == "hospedaje":
            warn_if_full("Boleto Hospedaje")
            if not state["printer"]:
                message("No hay impresora configurada. No se registró la entrada.")
                return
            else:
                alert.open = True
            page.update()

        elif valor == "extraviado":
            start_extraviado_flow(codigo)

        else:
            code = get_entry_by_code(e.control.value)
            if code is None:
                message()
            else:
                if code[6] == "Boleto Hospedaje":
                     hospedajeOut(code)
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
        show_password_alert("Acceso a configuración", lambda: abrir_dialog_config())

    def download_report_secure(e):
        show_password_alert("Descargar reporte", lambda: download_report_csv(e))

    def delete_registers_secure(e):
        show_password_alert("Borrar registros", lambda: delete_registers(e))

    def abrir_dialog_config():
        input_normal_boxes.value = str(state["nBoxes"])
        input_hospedaje_boxes.value = str(state["nBoxesHospedaje"])
        page.open(alert_config_cajones)
        page.update()
    def es_hospedaje(tipo: str) -> bool:
        return (tipo or "").strip().lower() == "boleto hospedaje"
    
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

    def handle_accept_hospedaje(e):
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
        
        addHospedaje(plate=placa)        
        getBD()
        alert.open = False
        
        page.update()


    def save_fee(e):
        set_all_prices(
            name_fee_normal.value, float(price_fee_normal.value),
            name_fee_jueves.value, float(price_fee_jueves.value),
            name_fee_pension.value, float(price_fee_pension.value),
            name_fee_extraviado.value, float(price_fee_extraviado.value),
                )
        show_page(0)
        page.update() 

    def show_lost_ticket_dialog():
        # Solo entradas elegibles (NO Boleto Hospedaje)
        entradas = [e for e in get_all_entries() if not es_hospedaje(e[6])]

        if not entradas:
            page.open(ft.SnackBar(ft.Text("No hay boletos elegibles para salida por extravío.")))
            return

        botones = []
        for entrada in entradas:
            texto = f"{entrada[1]} - {entrada[3]} {entrada[2]} - {entrada[6]}"
            boton = ft.TextButton(
                text=texto,
                on_click=lambda e, code=entrada: confirm_lost_ticket_exit(code),
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5))
            )
            botones.append(boton)

        alert_lost_ticket.content = ft.Column(
            [
                ft.Text("Selecciona la entrada extraviada (Boleto hospedaje no permitido):", size=16),
                *botones
            ],
            scroll=True, height=300
        )
        alert_lost_ticket.open = True
        page.update()
    def confirm_lost_ticket_exit(code):
    # Bloquear hospedaje por seguridad
        if es_hospedaje(code[6]):
            message("Los boletos de hospedaje no pueden salir por extravío. Solo en la fecha de salida o después.")
            alert_lost_ticket.open = False
            page.update()
            return

        # SOLO borrar la entrada (nada de insert_out ni impresión)
        delete_entry(code[1])
        update_boxes_view()
        alert_lost_ticket.open = False
        getBD()
        page.open(ft.SnackBar(ft.Text("Salida por extravío completada (sin ticket ni registro en salidas).")))
        page.update()



    def close_alert_lost():
        alert_lost_ticket.open = False
        page.update()

    def save_price_dolar(e):
        try:
            price_dolar = float(price_fee_dolar.value)
        except:
            page.open(ft.SnackBar(ft.Text("Ingresa un número válido para el dólar")))
            return
        set_price_dollar(price_dolar)
        state["dolar_price"] = price_dolar
        page.open(ft.SnackBar(ft.Text("Tipo de cambio guardado")))
        show_page(0)
        page.update()

    
        # Alerta informativa de estacionamiento lleno (no bloqueante)
    def close_full_alert(e=None):
        alert_full.open = False
        page.update()

    def open_full_alert(msg: str):
        alert_full.title = ft.Text("Estacionamiento lleno")
        alert_full.content = ft.Text(msg)
        alert_full.actions = [ft.TextButton("Entendido", on_click=close_full_alert)]
        alert_full.open = True
        page.update()

    ############################################################################################################
 
    # PAGES
    input_normal_boxes = TextField(label="Cajones normales", keyboard_type=ft.KeyboardType.NUMBER).build()
    input_hospedaje_boxes = TextField(label="Cajones de hospedaje", keyboard_type=ft.KeyboardType.NUMBER).build()
    plateField = TextField(label="Placa").build()

    alert_full = ft.AlertDialog(
        modal=False,
        title=ft.Text("Estacionamiento lleno"),
        content=ft.Text(""),
        actions=[ft.TextButton("Entendido", on_click=close_full_alert)],
        shape=ft.RoundedRectangleBorder(radius=8),
    )
    alert_full.open = False


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

    currency_alert = ft.AlertDialog(
        modal=True,
        title=ft.Text("Moneda"),
        content=ft.Text(""),
        actions=[],
        shape=ft.RoundedRectangleBorder(radius=8),
    )
    currency_alert.open = False

    alert_config_cajones = ft.AlertDialog(
        modal=True,
        title=ft.Text("Editar número de cajones"),
        content=ft.Container(
        content=ft.Column([
            
            input_normal_boxes,
            input_hospedaje_boxes
        ], spacing=10),
        width=400,
        height=150,
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: close_alert_cajones(e)),
            ft.TextButton("Guardar", on_click=lambda e: guardar_cajones(e)),
        ],
    )

    time_picker = ft.TimePicker(
        confirm_text="Confirmar",
        cancel_text="Cancelar",
        error_invalid_text="Tiempo fuera de rango",
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
    read_qr = TextField(label="Leer QR o comando",keyboard_type=ft.KeyboardType.TEXT,onSubmit=onSubmitReadQr).build()

    filtro_tipo = ft.Dropdown(
    label="Filtrar por tipo",
    options=[
        ft.dropdown.Option("Todos"),
        ft.dropdown.Option("Boleto normal"),
        ft.dropdown.Option("Boleto Pensión"),
        ft.dropdown.Option("Boleto Hospedaje")
    ],
    value="Todos",
    on_change=lambda e: getBD(filtro=e.control.value), border_color=ft.Colors.WHITE
)

    download_report = Button(text="DESCARGAR REPORTE", on_click=download_report_secure).build()
    delete_registers_button = Button(text="BORRAR REGISTROS", bgcolor=ft.Colors.RED_400, icon=ft.Icons.DELETE, on_click=delete_registers_secure).build()
    alert_delete_registers = Alert(content=ft.Text("Seguro que desea borrar los registros?"), action="Borrar", onAdd=delete_all, onCancel=closeAlertRegisters).build()
    alert_delete_registers.open = False
    boxs = ft.Text("19", size=44, text_align=ft.TextAlign.CENTER, expand=True)
    boxsText_hospedaje = ft.Text("2", size=44, text_align=ft.TextAlign.CENTER, expand=True)
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
    boxs_hospedaje = ft.Column(
        [
            ft.Row([
                ft.Text("CAJONES DISPONIBLE HOSPEDAJE", size=16, weight=ft.FontWeight.BOLD, expand=True),
                ft.IconButton(icon=ft.Icons.SETTINGS, icon_color=ft.Colors.GREY_500, tooltip="Editar cajones", on_click=lambda e: abrir_config_cajones())
            ]),
            ft.Row([
                boxsText_hospedaje
            ], expand=True, alignment=ft.MainAxisAlignment.CENTER
            )
        ]
    )
    containerBoxs = Container(business_name=state["business_name"], content=last_entry, height=130).build()
    containerBoxs_hospedaje = Container(business_name=state["business_name"], content=boxs_hospedaje, height=130).build()

    registers_database = ft.DataTable(
    columns= columns,
    rows=datacells,
    expand=True,
    )

    alert_hospedaje_pending  = Alert(
        title="Boletos hospedaje Pendientes",
        content=ft.Text(""),
        onCancel=close_alert_hospedaje_pending ,
        action=None,
        height=250,
        width=300
    ).build()
    alert_hospedaje_pending .open = False

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
    
    
    price_fee_dolar = TextField(label="Precio dolar", keyboard_type=ft.KeyboardType.NUMBER, width=180).build()
    btn_dolar = Button(text="GUARDAR", on_click=lambda e: save_price_dolar(e), width=120, icon=ft.Icons.SAVE).build()

    page_0 = ft.Row(
        [
            ft.Column(
                [
                    Container(height=200, business_name=state["business_name"], content=content_data).build(),
                    containerBoxs,
                    containerBoxs_hospedaje,
                    btn_extraviado_manual,
                    ft.Row(
                    [
                        ft.Column([ft.Text("Precio dolar:"),
                                   ft.Row(
                                       [
                                           price_fee_dolar,
                                           btn_dolar
                                       ]
                                   )]),
                    ], expand=True, alignment=ft.MainAxisAlignment.CENTER
                ),
                    
                ], width=350, scroll=ft.ScrollMode.AUTO
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

        ], expand=True,vertical_alignment=ft.CrossAxisAlignment.START,
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
    alert = Alert(content=contentAlert, action="Aceptar", onCancel=close_alert, title="Boleto Hospedaje", height=200, width=500, onAdd=handle_accept_hospedaje).build()
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

        # Cargar límites de cajones (no actualiza contadores aquí)
        load_boxes_config()

        # Reemplazar pantalla de carga por la UI real
        page.controls.clear()
        page.appbar = AppBar(
            business_name=state["business_name"],
            onChange=onChangePage,
            filters=filtro_tipo
        ).build()
        page.add(
            ft.SafeArea(
                ft.Column(
                    [
                        page_0,
                        page_1,
                        page_2,
                        alert,
                        alert_password,
                        alert_hospedaje_pending,
                        alert_clean_outs,
                        alert_lost_ticket,
                        alert_ring,
                        currency_alert,
                        alert_full,
                    ],
                    expand=True,
                ),
                expand=True,
            )
        )

        # Poblar datos (tabla visible + contadores) en base a TODAS las entradas
        try:
            filtro_actual = filtro_tipo.value or "Todos"
        except:
            filtro_actual = "Todos"
        getBD(filtro=filtro_actual)  # esto también llama update_boxes_view() internamente

        # Reflejar tipo de cambio en el input (state["dolar_price"] lo setea getBD)
        price_fee_dolar.value = str(state["dolar_price"] or "")
        page.update()

        # Revisar hospedajes pendientes (ya con UI montada)
        check_hospedaje_pending()

        # Focus al lector
        read_qr.focus()
        page.update()


    # Lanzar en segundo plano después de mostrar loading
    threading.Thread(target=load_background_data).start()

    ############################################################################################################
    
    
ft.app(main)
