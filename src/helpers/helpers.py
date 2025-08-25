import flet as ft


def getDatacell(data=None):
    if not data:
        return []
    return [
        ft.DataRow(cells=[
            ft.DataCell(ft.Text(value=str(row[0]), selectable=True)),
            ft.DataCell(ft.Text(value=row[1], selectable=True)),
            ft.DataCell(ft.Text(value=row[3], selectable=True)),
            ft.DataCell(ft.Text(value=row[2], selectable=True)),
            ft.DataCell(ft.Text(value=row[6], selectable=True)),
        ])
        for row in data
    ]


def getDataColumns(data=None):
    if not data:
        return []
    return [ft.DataColumn(label=ft.Text(col)) for col in data]


def print_ticket_usb(printer_name=None,data=None, error=None, err_printer=None, entrada=True):
    import win32print
    if entrada:
        zpl_code = f"""
            ^XA
            ~JSN
            ^LT0
            ^LH0,0
            ^JMA
            ^PR5,10
            ~SD15
            ^JUS
            ^LRN
            ^CI27
            ^PA0,1,1,0
            ^MMT
            ^PW607
            ^LL815
            ^LS0
            ^FO123,48^GFA,1081,3237,39,:Z64:eJzFljFr20AYhu98MRcsV3IgpYtCAl2MO6SjyRDLlNLVBZcuAZN/cCZpCyUhwl1MAvZfEPEivGQVaUll6A9wIWOgAi8CDU1LoMINup5lR0gXV76hUC0ni8ePXt336U4ZIHRAMUzShTBsC2HIEcOuxbBAF8HwraBNDKNCmER1EQxTW+ymjhgmNHGI+iIY/qc2RG9EMIkKlQFToaIiMRuiQkVlNl0Aw6I2oRYRzCaJ2f5LtoSt3zL7hpkxzb5uFnO6mWsdm+Zyn/1k2ewIO8x+/Ta4zt6Shk1UbB/gAR4StTE8nNiMCHvfNS96vmJe/3b8suJsK6Ou6W+d9TwDxW1kCazC2kNACNkvZLV9ZgMHqxhWbSmOuTKQkbUNXNcKyrIbKF5XD4rySctJZCMY5KGqgqZdqKt57e0DZqurGAM7mU0xZHReBntG2dsqOaUnva7hbckKcBLZ3sHaElYLoKkVnhVUsrdSxWR3YtMSWNDy5U7HAp5jeZblex9HXdf7JHd0LhvYyeOdMFv1SiXNlyzb7tW9bASUZSXYBj+dsuNX/MfMBpyxjFrTbCsRpi7h1+pk3jTyhjR/MBs5wBCG88be1XaIjTuWLHe7pjt2XX9suZ7Hzm/lk+9hTRuUDqc1fT7Mqzh7xWqq7RCVDAb4UlMxDGvao5SOQ6x0bORKmZa5UdKNopHbOD1l58UMKE2wFwxb1HSITg83HcMzbChmG4thC9YlaYYteL/usi3YHu5uumB7iLD0R40wPzVclC39USNb+hKMxGzRvCWX4GW9DdqxK1G2ZI9kq/VsTZtz02QZNkeB4jsc9qpxRKkWx9aq2lqBswXmGV8G/4N+0Y5dmWS7AZAvKoF2HcSuoGnnfuZsDjLKgMvG/rVOk7u0BocExLJJ02dUaHKXdlDgx214OmOYs9nwknDZgunA2e5lm1QTHiWLSiB4Gs+GZp3GtYjfa/PzFobibIfVL2u1ZLYQ42yVUbDJ1XSeDcI6jHeINJv+StLG+m2Z67cwwnp6+6L5tjnYzJa6xN1hlfTvESxsCy2bi7L9CsdHs/EvR67f12djGvYHwMs5aA==:7D39
            
            ^FT158,199^A0N,39,38^FH\^CI28^FD{data["titulo"]}^FS^CI27

            ^FO14,147^GB569,0,2^FS
            ^FO14,272^GB569,0,2^FS
            ^FT130,251^A0N,39,38^FH\^CI28^FD{data["fecha_entrada"]}^FS^CI27
            ^FT166,336^A0N,39,38^FH\^CI28^FDdesde: {data["hora_entrada"]}^FS^CI27
            ^FO43,310^GFA,145,464,16,:Z64:eJxjYIADDgZUwIPG50Pj86PzG9D4B4AE1yo4WP8AyJf/Xw+HH4B8+/8I8AMsjwB/0OT/ocn/R+c3oPEPoOr//4CAPLp+Avb/QeOjux/kPyYlONB/gCV88IUfgfBHjx9w/AEAt8bEKg==:CBE4
            ^FT200,610^BQN,2,9
            ^FH\^FDLA,{data["placa"]}^FS
            ^FT23,653^A0N,14,18^FH\^CI28^FDLa entrega del automovil se hará solamente al portador del presente, ^FS^CI27
            ^FT23,671^A0N,14,18^FH\^CI28^FDen caso de perdida debe ser reportado de inmediato  y deberá^FS^CI27
            ^FT23,689^A0N,14,18^FH\^CI28^FDacreditar la propiedad del mismo. Si el auto permanece fuera^FS^CI27
            ^FT23,707^A0N,14,18^FH\^CI28^FDdel horario de cierre se cobrará pensión. No nos hacemos^FS^CI27
            ^FT23,725^A0N,14,18^FH\^CI28^FDresponsables por: Robo parcial, piezas del vehículo. Fallas^FS^CI27
            ^FT23,743^A0N,14,18^FH\^CI28^FDmecanicas. Daños causados por naturaleza, clima, vandalismo . ^FS^CI27
            ^FT23,761^A0N,14,18^FH\^CI28^FDObjetos dejados en el interior sin ser inventariados. Choques entre ^FS^CI27
            ^FT23,779^A0N,14,18^FH\^CI28^FDparticulares se arregla entre ellos mismos.^FS^CI27
            ^FT166,392^A0N,39,38^FH\^CI28^FD$ {data["precio"]} ^FS^CI27
            ^FO14,629^GB569,0,2^FS

            ^XZ
            """
    else:
        zpl_code = f"""
        ^XA
        ~JSN
        ^LT0
        ^LH0,0
        ^JMA
        ^PR5,10
        ~SD15
        ^JUS
        ^LRN
        ^CI27
        ^PA0,1,1,0
        ^MMT
        ^PW607
        ^LL815
        ^LS0
        ^FO123,48^GFA,1081,3237,39,:Z64:eJzFljFr20AYhu98MRcsV3IgpYtCAl2MO6SjyRDLlNLVBZcuAZN/cCZpCyUhwl1MAvZfEPEivGQVaUll6A9wIWOgAi8CDU1LoMINup5lR0gXV76hUC0ni8ePXt336U4ZIHRAMUzShTBsC2HIEcOuxbBAF8HwraBNDKNCmER1EQxTW+ymjhgmNHGI+iIY/qc2RG9EMIkKlQFToaIiMRuiQkVlNl0Aw6I2oRYRzCaJ2f5LtoSt3zL7hpkxzb5uFnO6mWsdm+Zyn/1k2ewIO8x+/Ta4zt6Shk1UbB/gAR4StTE8nNiMCHvfNS96vmJe/3b8suJsK6Ou6W+d9TwDxW1kCazC2kNACNkvZLV9ZgMHqxhWbSmOuTKQkbUNXNcKyrIbKF5XD4rySctJZCMY5KGqgqZdqKt57e0DZqurGAM7mU0xZHReBntG2dsqOaUnva7hbckKcBLZ3sHaElYLoKkVnhVUsrdSxWR3YtMSWNDy5U7HAp5jeZblex9HXdf7JHd0LhvYyeOdMFv1SiXNlyzb7tW9bASUZSXYBj+dsuNX/MfMBpyxjFrTbCsRpi7h1+pk3jTyhjR/MBs5wBCG88be1XaIjTuWLHe7pjt2XX9suZ7Hzm/lk+9hTRuUDqc1fT7Mqzh7xWqq7RCVDAb4UlMxDGvao5SOQ6x0bORKmZa5UdKNopHbOD1l58UMKE2wFwxb1HSITg83HcMzbChmG4thC9YlaYYteL/usi3YHu5uumB7iLD0R40wPzVclC39USNb+hKMxGzRvCWX4GW9DdqxK1G2ZI9kq/VsTZtz02QZNkeB4jsc9qpxRKkWx9aq2lqBswXmGV8G/4N+0Y5dmWS7AZAvKoF2HcSuoGnnfuZsDjLKgMvG/rVOk7u0BocExLJJ02dUaHKXdlDgx214OmOYs9nwknDZgunA2e5lm1QTHiWLSiB4Gs+GZp3GtYjfa/PzFobibIfVL2u1ZLYQ42yVUbDJ1XSeDcI6jHeINJv+StLG+m2Z67cwwnp6+6L5tjnYzJa6xN1hlfTvESxsCy2bi7L9CsdHs/EvR67f12djGvYHwMs5aA==:7D39
        ^FT158,199^A0N,39,38^FH\^CI28^FDBoleto de salida^FS^CI27
        ^FO14,147^GB569,0,2^FS
        ^FO14,272^GB569,0,2^FS
        ^FT130,251^A0N,39,38^FH\^CI28^FD{data["fecha_salida"]}^FS^CI27
        ^FT166,326^A0N,39,38^FH\^CI28^FDdesde: {data["hora_entrada"]}^FS^CI27
        ^FO43,301^GFA,145,464,16,:Z64:eJxjYIADDgZUwIPG50Pj86PzG9D4B4AE1yo4WP8AyJf/Xw+HH4B8+/8I8AMsjwB/0OT/ocn/R+c3oPEPoOr//4CAPLp+Avb/QeOjux/kPyYlONB/gCV88IUfgfBHjx9w/AEAt8bEKg==:CBE4
        ^FT235,661^BQN,2,7
        ^FH\^FDLA,{data["placa"]}^FS
        ^FO9,671^GB569,0,2^FS
        ^FT166,381^A0N,39,38^FH\^CI28^FDhasta: {data["hora_salida"]}^FS^CI27
        ^FT52,744^A0N,40,40^FH\^CI28^FDTOTAL: $ {data["total"]} ^FS^CI27
        ^FO43,350^GFA,145,464,16,:Z64:eJxjYIADDgZUwIPG50Pj86PzG9D4B4AE1yo4WP8AyJf/Xw+HH4B8+/8I8AMsjwB/0OT/ocn/R+c3oPEPoOr//4CAPLp+Avb/QeOjux/kPyYlONB/gCV88IUfgfBHjx9w/AEAt8bEKg==:CBE4
        ^FO67,396^GB472,66,2^FS
        ^FT168,444^A0N,39,38^FH\^CI28^FD{data["tipo"]}^FS^CI27

        ^XZ
    """ 
    if printer_name:
        try:
            printer_handle = win32print.OpenPrinter(printer_name)
            job = win32print.StartDocPrinter(printer_handle, 1, ("Ticket Lote", None, "RAW"))
            win32print.StartPagePrinter(printer_handle)
            win32print.WritePrinter(printer_handle, zpl_code.encode("utf-8"))
            win32print.EndPagePrinter(printer_handle)
            win32print.EndDocPrinter(printer_handle)
            win32print.ClosePrinter(printer_handle)
        except Exception as e:
            return error if error else print("Error al imprimir:", e)
    else:
        return err_printer if err_printer else print("No se ha seleccionado una impresora")