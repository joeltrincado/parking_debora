import sqlite3
import pandas as pd

def create_connection():
    return sqlite3.connect("visitas.db")

def init_db():
    
    with create_connection() as conn:
        cursor = conn.cursor()

        # Tabla de entradas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entradas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL,
                hora_entrada TEXT NOT NULL,
                fecha_entrada TEXT NOT NULL,
                hora_salida TEXT,
                fecha_salida TEXT,
                type_entry TEXT NOT NULL,
                precio REAL NOT NULL,
                status TEXT NOT NULL
            )
        """)

        # Índices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_codigo_entrada ON entradas(codigo)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_type_entry ON entradas(type_entry)")

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

        # Tabla de configuraciones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuraciones (
                clave TEXT PRIMARY KEY,
                valor TEXT
            )
        """)

        # Tabla de precios
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            tipo TEXT NOT NULL
        )
    """)

        conn.commit()

    if get_config("cajones_normales") is None:
        set_config("cajones_normales", "19")
    if get_config("cajones_airbnb") is None:
        set_config("cajones_airbnb", "4")

def insert_entry(codigo, hora_entrada, fecha_entrada, hora_salida=None, fecha_salida=None, type_entry=None, precio=0, status=""):
    try:
        with create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO entradas (codigo, hora_entrada, fecha_entrada, hora_salida, fecha_salida, type_entry, precio, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (codigo, hora_entrada, fecha_entrada, hora_salida, fecha_salida, type_entry, precio, status))
            conn.commit()
    except sqlite3.Error as e:
        print(f"[DB] Error insert_entry: {e}")

def insert_out(codigo, hora_entrada, fecha_entrada, hora_salida, fecha_salida, type_entry, precio, total):
    try:
        with create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO salidas (codigo, hora_entrada, fecha_entrada, hora_salida, fecha_salida, type_entry, precio, total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (codigo, hora_entrada, fecha_entrada, hora_salida, fecha_salida, type_entry, precio, total))
            conn.commit()
    except sqlite3.Error as e:
        print(f"[DB] Error insert_out: {e}")

def delete_entry(codigo):
    try:
        with create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM entradas WHERE codigo=?", (codigo,))
            conn.commit()
    except sqlite3.Error as e:
        print(f"[DB] Error delete_entry: {e}")

def get_all_entries():
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entradas")
        return cursor.fetchall()

def get_all_outs():
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM salidas")
        return cursor.fetchall()

def get_all_prices():
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM prices")
        return cursor.fetchall()

def get_config(clave):
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT valor FROM configuraciones WHERE clave=?", (clave,))
        row = cursor.fetchone()
        return row[0] if row else None

def set_config(clave, valor):
    try:
        with create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO configuraciones (clave, valor)
                VALUES (?, ?)
                ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor
            """, (clave, valor))
            conn.commit()
    except sqlite3.Error as e:
        print(f"[DB] Error set_config: {e}")

def get_price_unique():
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, precio FROM prices WHERE id = 1")
        row = cursor.fetchone()
        return row if row else ("", "")

def set_price(name, price):
    try:
        with create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO prices (id, nombre, precio)
                VALUES (1, ?, ?)
                ON CONFLICT(id) DO UPDATE SET nombre=excluded.nombre, precio=excluded.precio
            """, (name, price))
            conn.commit()
    except sqlite3.Error as e:
        print(f"[DB] Error set_price: {e}")

def get_entry_by_code(code):
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entradas WHERE codigo=?", (code,))
        return cursor.fetchone()

def get_entry_by_type(type_entry):
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entradas WHERE type_entry=?", (type_entry,))
        return cursor.fetchall()

def delete_all_outs():
    try:
        with create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM salidas")
            conn.commit()
    except sqlite3.Error as e:
        print(f"[DB] Error delete_all_outs: {e}")

def add_prices_from_excel(path_excel):
    """
    path_excel: ruta al archivo Excel.
    El Excel debe tener columnas: Código, Nombre, Empresa
    """
    df = pd.read_excel(path_excel)

    conn = create_connection()
    cursor = conn.cursor()

    # Borra todos los usuarios anteriores
    cursor.execute("DELETE FROM usuarios")

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO prices (tiempo, tarifa)
            VALUES (?, ?, )
        """, (
            str(row['Tiempo']).strip(),
            str(row['Tarifa']).strip(),
        ))

    conn.commit()
    conn.close()

def set_all_prices(normal_name, normal_price, jueves_name, jueves_price, pension_name, pension_price, extraviado_name, extraviado_price):
    try:
        with create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO prices (id, nombre, precio, tipo)
                VALUES (1, ?, ?, 'normal')
                ON CONFLICT(id) DO UPDATE SET nombre=excluded.nombre, precio=excluded.precio, tipo='normal'
            """, (normal_name, normal_price))

            cursor.execute("""
                INSERT INTO prices (id, nombre, precio, tipo)
                VALUES (2, ?, ?, 'jueves')
                ON CONFLICT(id) DO UPDATE SET nombre=excluded.nombre, precio=excluded.precio, tipo='jueves'
            """, (jueves_name, jueves_price))

            cursor.execute("""
                INSERT INTO prices (id, nombre, precio, tipo)
                VALUES (3, ?, ?, 'pension')
                ON CONFLICT(id) DO UPDATE SET nombre=excluded.nombre, precio=excluded.precio, tipo='pension'
            """, (pension_name, pension_price))

            cursor.execute("""
                INSERT INTO prices (id, nombre, precio, tipo)
                VALUES (4, ?, ?, 'extraviado')
                ON CONFLICT(id) DO UPDATE SET nombre=excluded.nombre, precio=excluded.precio, tipo='extraviado'
            """, (extraviado_name, extraviado_price))

            conn.commit()
    except sqlite3.Error as e:
        print(f"[DB] Error set_all_prices: {e}")

def get_price_by_type(tipo):
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, precio FROM prices WHERE tipo=?", (tipo,))
        row = cursor.fetchone()
        return row if row else ("", 0.0)

def get_price_by_day(is_jueves=False):
    with create_connection() as conn:
        cursor = conn.cursor()
        tipo = 'jueves' if is_jueves else 'normal'
        cursor.execute("SELECT nombre, precio FROM prices WHERE tipo=?", (tipo,))
        row = cursor.fetchone()
        return row if row else ("", 0.0)
