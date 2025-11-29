import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
import os

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
DB_FILE = "sig_transportes.db"
DOCS_FOLDER = "documentos"
os.makedirs(DOCS_FOLDER, exist_ok=True)

# -----------------------------
# BASE DE DATOS
# -----------------------------
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

# Usuarios
c.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    rol TEXT
)
''')

# Documentos
c.execute('''
CREATE TABLE IF NOT EXISTS documentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT,
    area TEXT,
    fecha_creacion TEXT,
    tipo TEXT,
    archivo TEXT
)
''')

# Registros
c.execute('''
CREATE TABLE IF NOT EXISTS registros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT,
    area TEXT,
    fecha_creacion TEXT,
    contenido TEXT
)
''')

conn.commit()

# -----------------------------
# FUNCIONES
# -----------------------------
def login(username,password):
    c.execute("SELECT rol FROM usuarios WHERE username=? AND password=?", (username,password))
    res = c.fetchone()
    return res[0] if res else None

def add_user(username,password,rol):
    try:
        c.execute("INSERT INTO usuarios (username,password,rol) VALUES (?,?,?)",(username,password,rol))
        conn.commit()
    except:
        pass

def add_documento(titulo,area,tipo,archivo):
    fecha = datetime.now().strftime("%Y-%m-%d")
    c.execute("INSERT INTO documentos (titulo,area,fecha_creacion,tipo,archivo) VALUES (?,?,?,?,?)",(titulo,area,fecha,tipo,archivo))
    conn.commit()

def list_documentos():
    df = pd.read_sql("SELECT * FROM documentos", conn)
    return df

def add_registro(titulo,area,contenido):
    fecha = datetime.now().strftime("%Y-%m-%d")
    c.execute("INSERT INTO registros (titulo,area,fecha_creacion,contenido) VALUES (?,?,?,?)",(titulo,area,fecha,contenido))
    conn.commit()

def list_registros():
    df = pd.read_sql("SELECT * FROM registros", conn)
    return df

def send_email(remitente,destinatario,asunto,mensaje,smtp_server="smtp.gmail.com",smtp_port=587,usuario="",password=""):
    try:
        msg = EmailMessage()
        msg.set_content(mensaje)
        msg['Subject'] = asunto
        msg['From'] = remitente
        msg['To'] = destinatario

        server = smtplib.SMTP(smtp_server,smtp_port)
        server.starttls()
        server.login(usuario,password)
        server.send_message(msg)
        server.quit()
        st.success("Correo enviado")
    except Exception as e:
        st.error(f"No se pudo enviar correo: {e}")

# -----------------------------
# CREAR USUARIOS DE PRUEBA
# -----------------------------
add_user("admin","admin123","Admin")
add_user("supervisor","super123","Supervisor")
add_user("empleado","emple123","Empleado")

# -----------------------------
# APP
# -----------------------------
def main():
    st.set_page_config(page_title="SIG Transportes",layout="wide")
    st.title("Sistema Integrado de Gestión - Empresa de Transportes")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.rol = None
        st.session_state.username = None

    if not st.session_state.logged_in:
        st.subheader("Login")
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña",type="password")
        if st.button("Ingresar"):
            rol = login(username,password)
            if rol:
                st.session_state.logged_in = True
                st.session_state.rol = rol
                st.session_state.username = username
                st.success(f"Bienvenido {username} ({rol})")
            else:
                st.error("Usuario o contraseña incorrectos")
    else:
        menu = ["Dashboard","Documentos","Registros","Alertas y Notificaciones","Cerrar Sesión"]
        choice = st.sidebar.selectbox("Menú",menu)

        # -----------------------------
        # DASHBOARD
        # -----------------------------
        if choice=="Dashboard":
            st.subheader("Dashboard de Documentos")
            df = list_documentos()
            if not df.empty:
                # Corregimos columnas ausentes
                if 'area' not in df.columns: df['area']='Sin Área'
                if 'fecha_creacion' not in df.columns: df['fecha_creacion']=''
                if 'tipo' not in df.columns: df['tipo']=''
                # Gráfico por Área
                fig_area = px.bar(df.groupby('area').size().reset_index(name='Cantidad'),x='area',y='Cantidad',title="Documentos por Área")
                st.plotly_chart(fig_area,use_container_width=True)
                # Gráfico por Fecha
                df['fecha_creacion'] = pd.to_datetime(df['fecha_creacion'],errors='coerce')
                fig_fecha = px.line(df.groupby('fecha_creacion').size().reset_index(name='Cantidad'),x='fecha_creacion',y='Cantidad',title="Documentos por Fecha")
                st.plotly_chart(fig_fecha,use_container_width=True)
            else:
                st.info("No hay documentos cargados aún.")

        # -----------------------------
        # DOCUMENTOS
        # -----------------------------
        elif choice=="Documentos":
            st.subheader("Gestión de Documentos")
            df = list_documentos()
            if not df.empty:
                for idx,row in df.iterrows():
                    area = row.get('area','Sin Área')
                    fecha = row.get('fecha_creacion','')
                    tipo = row.get('tipo','')
                    archivo = row.get('archivo','')
                    st.markdown(f"**{row.get('titulo','Sin título')} ({area}) - {fecha} [{tipo}]**")
                    st.write(f"Archivo: {archivo}")
            st.subheader("Agregar Documento")
            titulo = st.text_input("Título del documento")
            area = st.selectbox("Área",["Calidad","Medio Ambiente","Seguridad"],key="area_doc")
            tipo = st.selectbox("Tipo",["PDF","Word","Excel","TXT"])
            archivo = st.file_uploader("Subir archivo",type=['pdf','docx','xlsx','txt'])
            if st.button("Agregar Documento"):
                if archivo and titulo:
                    save_path = os.path.join(DOCS_FOLDER,archivo.name)
                    with open(save_path,"wb") as f:
                        f.write(archivo.getbuffer())
                    add_documento(titulo,area,tipo,save_path)
                    st.success("Documento agregado")
                else:
                    st.error("Debe subir un archivo y poner título")

        # -----------------------------
        # REGISTROS
        # -----------------------------
        elif choice=="Registros":
            st.subheader("Registros del SIG")
            df = list_registros()
            if not df.empty:
                for idx,row in df.iterrows():
                    area = row.get('area','Sin Área')
                    fecha = row.get('fecha_creacion','')
                    titulo = row.get('titulo','Sin Título')
                    contenido = row.get('contenido','')
                    st.markdown(f"**{titulo} ({area}) - {fecha}**")
                    st.markdown(contenido)
            st.subheader("Agregar Registro")
            titulo = st.text_input("Título del registro")
            area = st.selectbox("Área", ["Calidad","Medio Ambiente","Seguridad"], key="area_reg")
            contenido = st.text_area("Contenido (Markdown/HTML)")
            if st.button("Agregar Registro"):
                if titulo and contenido:
                    add_registro(titulo,area,contenido)
                    st.success("Registro agregado")
                else:
                    st.error("Debe ingresar título y contenido")

        # -----------------------------
        # ALERTAS Y NOTIFICACIONES
        # -----------------------------
        elif choice=="Alertas y Notificaciones":
            st.subheader("Enviar Notificación")
            remitente = st.text_input("Correo remitente")
            destinatario = st.text_input("Correo destinatario")
            asunto = st.text_input("Asunto")
            mensaje = st.text_area("Mensaje")
            if st.button("Enviar Correo"):
                if remitente and destinatario and asunto and mensaje:
                    # SMTP vacío por ahora, configurar si se desea
                    send_email(remitente,destinatario,asunto,mensaje)
                else:
                    st.error("Complete todos los campos")

        elif choice=="Cerrar Sesión":
            st.session_state.logged_in=False
            st.session_state.rol=None
            st.session_state.username=None
            st.experimental_rerun()

if __name__=="__main__":
    main()
