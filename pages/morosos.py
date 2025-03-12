import pandas as pd
import login
import streamlit as st
login.generarLogin()

if 'usuario' not in st.session_state:
    st.switch_page('inicio.py')
login.cargar_clientes()
idc=st.secrets['ids']['clientes']
url = st.secrets['urls']['clientes']
def load():
    return login.load_data_vendedores(url)


st.session_state['clientes']=load() 
if 'pagina_actual' not in st.session_state:
        st.session_state['pagina_actual'] = 1
cobranzas=st.session_state['cobranzas']
prestamos=st.session_state['prestamos']
vendedores=st.session_state['usuarios']['usuario'].tolist()

import datetime as dt
def cartones_morosos(prestamos):
    for _, row in prestamos.iterrows():
        cobranzas_prestamo = cobranzas[cobranzas['prestamo_id'] == row['id']]
        cobranzas_prestamo=cobranzas_prestamo[cobranzas_prestamo['estado']=='En mora']
        if 'En mora' in cobranzas_prestamo['estado'].unique().tolist():
            with st.container(border=True):
                col1,col2,col3,col4=st.columns(4)
                with col1: 
                    st.markdown(f"### {row['nombre']}: {row['id']}")
                    st.write(f"📝 **Concepto:** {row['asociado']}")
                with col2:
                    st.write(f"📅 **Fecha:** {row['fecha']}")
                    st.write(f"💰 **Capital:** {row['capital']}")
                with col3:
                    st.write(f"📌 **Cantidad de cuotas:** {row['cantidad']}")
                    st.write(f"📆 **Vencimiento:** {row['vence']}")
                with col4:
                    st.write(f"📝 **Estado:** {row['estado']}")
                    if st.button('ver detalles',key=f'detalles_{row['id']}'):
                        st.session_state['credito']=row
                        st.switch_page('pages/por_credito.py')
                # Filtrar cobranzas relacionadas con este préstamo
                login.display_cobranzas(cobranzas_prestamo)


st.title("morosos")
moras=cobranzas[cobranzas['estado']=='En mora']
cartones_morososs=prestamos[prestamos['id'].isin(moras['prestamo_id'].unique())]
morosos=st.session_state['clientes'][st.session_state['clientes']['nombre'].isin(cartones_morososs['nombre'].unique())]

# Configuración de paginación
ITEMS_POR_PAGINA = 5
# Paginación
total_paginas = (len(morosos) // ITEMS_POR_PAGINA) + (1 if len(morosos) % ITEMS_POR_PAGINA > 0 else 0)
inicio = (st.session_state['pagina_actual'] - 1) * ITEMS_POR_PAGINA
fin = inicio + ITEMS_POR_PAGINA
df_paginado = morosos.iloc[inicio:fin]
for count,moroso in df_paginado.iterrows():
    prestamos_moroso=prestamos[prestamos['nombre']==moroso['nombre']]
    cartones_morosos(prestamos_moroso)
# Controles de paginación
with st.container(border=True):
    col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])
    with col_pag1:
        if st.session_state['pagina_actual'] > 1:
            if st.button("⬅ Anterior"):
                st.session_state['pagina_actual'] -= 1
                st.rerun()
    with col_pag3:
        if st.session_state['pagina_actual'] < total_paginas:
            if st.button("Siguiente ➡"):
                st.session_state['pagina_actual'] += 1
                st.rerun()
# Contador de registros y selector de cantidad por página
with st.container(border=True):
    st.write(f"Se muestran de {inicio + 1} a {min(fin, len(morosos))} de {len(morosos)} resultados")
    items_seleccionados = st.selectbox("Por página", [5, 10, 20, 50], index=[5, 10, 20, 50].index(ITEMS_POR_PAGINA),key='selects')
    if items_seleccionados != ITEMS_POR_PAGINA:
        ITEMS_POR_PAGINA = items_seleccionados
        st.session_state['pagina_actual'] = 1
        st.rerun()