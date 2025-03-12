import streamlit as st
st.set_page_config(layout='wide')
import login
import pandas as pd

st.title("Pagina administrativa de GrupoGon!")
login.generarLogin()
# Inicializar las bases de datos
if 'usuario' in st.session_state:
    if st.session_state['user_data']['permisos'].iloc[0]=='admin':
        login.cargar_reportes()
    st.switch_page("pages/clientes.py")