import sqlite3
from datetime import datetime
import pandas as pd

def create_connection():
    conn = sqlite3.connect("visitas.db")
    return conn

def init_db():
    conn = create_connection()
    cursor = conn.cursor()

    # Tabla de entradas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entradas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL,
            hora_entrada TEXT NOT NULL,
            fecha_entrada TEXT NOT NULL,
            hora_salida TEXT,             -- SIN NOT NULL
            fecha_salida TEXT,            -- SIN NOT NULL
            type_entry TEXT NOT NULL,
            precio REAL NOT NULL,
            status TEXT NOT NULL
        )

    """)

    # Tabla de salidas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS salidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL,
            hora_entrada TEXT NOT NULL,
            fecha_entrada TEXT NOT NULL,
            hora_salida TEXT NOT NULL,
            fecha_salida TEXT NOT NULL,
            type_entry TEXT NOT NULL,
            precio REAL NOT NULL,
            total REAL NOT NULL
        )
    """)

    # Tabla de configuraciones (igual que antes)
    # Tabla de configuraciones (corregida)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS configuraciones (
        clave TEXT PRIMARY KEY,
        valor TEXT
    )
    """)


    # Tabla de precios (opcional si aún la necesitas)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL
        )
    """)

  

    conn.commit()
    conn.close()


def insert_entry(codigo, hora_entrada, fecha_entrada, hora_salida=None, fecha_salida=None,type_entry=None, precio=0, status=""):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO entradas (codigo, hora_entrada, fecha_entrada, hora_salida, fecha_salida, type_entry, precio, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (codigo, hora_entrada, fecha_entrada, hora_salida, fecha_salida,type_entry, precio, status))
    conn.commit()
    conn.close()

def insert_out(codigo, hora_entrada, fecha_entrada, hora_salida, fecha_salida, type_entry, precio, total):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO salidas (codigo, hora_entrada, fecha_entrada, hora_salida, fecha_salida, type_entry, precio, total)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (codigo, hora_entrada, fecha_entrada, hora_salida, fecha_salida, type_entry, precio, total))
    conn.commit()
    conn.close()

def delete_entry(codigo):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM entradas WHERE codigo=?", (codigo,))
    conn.commit()
    conn.close()

def get_all_entries():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM entradas")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_outs():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM salidas")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_prices():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM prices")
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_prices_from_excel(path_excel):
    """
    path_excel: ruta al archivo Excel.
    El Excel debe tener columnas: Codigo, Nombre, Precio
    """
    df = pd.read_excel(path_excel)

    conn = create_connection()
    cursor = conn.cursor()

    # Borra todos los usuarios anteriores
    cursor.execute("DELETE FROM prices")

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO prices (id, hora, precio)
            VALUES (?, ?, ?)
        """, (
            str(row['Codigo']).strip(),
            str(row['Nombre']).strip(),
            str(row['Precio']).strip()
        ))

    conn.commit()
    conn.close()


def get_config(clave):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM configuraciones WHERE clave=?", (clave,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def set_config(clave, valor):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO configuraciones (clave, valor)
        VALUES (?, ?)
        ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor
    """, (clave, valor))
    conn.commit()
    conn.close()

def get_price_unique():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, precio FROM prices WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    return row if row else ("", "")


def set_price(name, price):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO prices (id, nombre, precio)
        VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET nombre=excluded.nombre, precio=excluded.precio
    """, (name, price))
    conn.commit()
    conn.close()


def get_entry_by_code(code):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM entradas WHERE codigo=?", (code,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_entry_by_type(type_entry):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM entradas WHERE type_entry=?", (type_entry,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_all_outs():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM salidas")
    conn.commit()
    conn.close()


