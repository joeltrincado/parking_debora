import qrcode
from PIL import Image
import io
import base64
import flet as ft
import socket

def generate_qr_base64(data=None):
    # Generar el QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # Si quieres un margen extra:
    background = Image.new("RGB", (qr_img.width + 20, qr_img.height + 20), (255, 255, 255))
    background.paste(qr_img, (10, 10))

    # Convertir a buffer
    buffered = io.BytesIO()
    background.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()

    # Codificar a base64
    img_base64 = base64.b64encode(img_bytes).decode()

    # Retornar el Data URI
    return img_base64

def getDatacell(data=None):
    users = []
    for user in data:
        users.append(
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(selectable=True,value=str(user[0]))),  # id
                ft.DataCell(ft.Text(selectable=True,value=user[1])),       # nombre
                ft.DataCell(ft.Text(selectable=True,value=user[3])),       # fecha
                ft.DataCell(ft.Text(selectable=True,value=user[2])),       # hora
                ft.DataCell(ft.Text(selectable=True,value=user[6])),       # status
            ])
        )
    return users

def getDataColumns(data=None):
    columns = []
    for d in data:
        columns.append(ft.DataColumn(label=ft.Text(d,)))
    return columns

# def print_ticket_usb(printer_name=None, error=None, err_printer=None):
#     zpl_code = f"""
#             ^XA
#             ^MMT
#             ^PW609
#             ^LL609
#             ^LS0
#             ^CI27
#             ^PR4
#             ~SD20
#             ^MD0
#             ^FT20,339^A0N,18,18^FH\\^CI28^FDUPC^FS^CI27
#             ^FT200,339^A0N,18,18^FH\\^CI28^FDGen^FS^CI27
#             ^FT260,339^A0N,18,18^FH\\^CI28^FDTalla^FS^CI27
#             ^FT330,339^A0N,18,18^FH\\^CI28^FDColor^FS^CI27
#             ^FT420,339^A0N,18,18^FH\\^CI28^FDModelo^FS^CI27
#             ^FT520,339^A0N,18,18^FH\\^CI28^FDPzas^FS^CI27

#             ^FO11,349^GFA,49,304,76,:Z64:eJzj4KAWYGCQoRaQYGCwoRawYGAQoBpgYAAAAPcgWQ==:C91B
#             ^PQ1,0,1,Y
#             ^XZ
#             """
#     if printer_name:
#         try:
#             printer_handle = win32print.OpenPrinter(printer_name)
#             job = win32print.StartDocPrinter(printer_handle, 1, ("Ticket Lote", None, "RAW"))
#             win32print.StartPagePrinter(printer_handle)
#             win32print.WritePrinter(printer_handle, zpl_code.encode("utf-8"))
#             win32print.EndPagePrinter(printer_handle)
#             win32print.EndDocPrinter(printer_handle)
#             win32print.ClosePrinter(printer_handle)
#         except Exception as e:
#             return error if error else print("Error al imprimir:", e)
#     else:
#         return err_printer if err_printer else print("No se ha seleccionado una impresora")

def print_ticket_ethernet(ip=None, port=9100, error=None, err_printer=None, user=None, date=None, time=None):
    print(user)
    zpl_code = f"""
            ^XA
            ~TA000
            ~JSN
            ^LT0
            ^MNW
            ^MTT
            ^PON
            ^PMN
            ^LH0,0
            ^JMA
            ^PR8,8
            ~SD15
            ^JUS
            ^LRN
            ^CI27
            ^PA0,1,1,0
            ^MMT
            ^PW607
            ^LL408
            ^LS0
            ^FT33,77^A0N,28,28^FH\^CI28^FDNombre: {user[1]} ^FS^CI27
            ^FT33,149^A0N,28,28^FH\^CI28^FDFecha: {date}^FS^CI27
            ^FT33,188^A0N,28,28^FH\^CI28^FDHora: {time}^FS^CI27
            ^FT33,225^A0N,28,28^FH\^CI28^FDCódigo: {user[0]}^FS^CI27
            ^FT33,112^A0N,28,28^FH\^CI28^FDEmpresa: {user[2]}^FS^CI27
            ^FT366,375^BQN,2,8
            ^FH\^FDLA,12345^FS
            ^XZ
            """
    if ip:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, int(port)))
            sock.send(zpl_code.encode("utf-8"))
            sock.close()
        except Exception as e:
            return error if error else print("Error al imprimir:", e)
    else:
        return err_printer if err_printer else print("No se ha seleccionado una impresora")
