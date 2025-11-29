import sqlite3

def get_connection():
    conn = sqlite3.connect("sig_transportes.db")
    return conn

def initialize_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabla de Calidad
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calidad (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            documento TEXT,
            descripcion TEXT,
            responsable TEXT
        )
    """)
    
    # Tabla de Medio Ambiente
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ambiente (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            actividad TEXT,
            impacto TEXT,
            responsable TEXT
        )
    """)
    
    # Tabla de Seguridad
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seguridad (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            incidente TEXT,
            riesgo TEXT,
            responsable TEXT
        )
    """)
    
    conn.commit()
    conn.close()
