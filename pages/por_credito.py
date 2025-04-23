import streamlit as st
import login
import pandas as pd
import datetime as dt
# Verificar si 'cliente' está en session_state
if 'usuario' not in st.session_state:
    st.switch_page('inicio.py')
if 'credito' not in st.session_state:
    st.switch_page('inicio.py')
else:
    login.generarLogin()
    login.cargar_clientes()
    col1,col2,col3,col4,col5=st.columns(5)
    credito = st.session_state['credito']
    clientes=st.session_state['clientes']
    with col1:
        if st.button("Volver"):
            st.session_state['cliente']=next(clientes[clientes['nombre']==credito['nombre']].iterrows())[1]
            st.switch_page("pages/por_cliente.py")
    with col5:
        if st.button("Reiniciar datos"):
            login.cargar_clientes(forzado=True)
    

    # Cargar los datos de préstamos y cobranzas
    prestamos = login.load_data(st.secrets['urls']['prestamos'])
    cobranzas = login.load_data(st.secrets['urls']['cobranzas'])

    # Filtrar préstamos y cobranzas por el cliente seleccionado
    cobranzas_credito = cobranzas[cobranzas['prestamo_id'] == credito['id']]

    cobranzas_credito['vencimiento'] = pd.to_datetime(cobranzas_credito['vencimiento'], format='%d-%m-%Y', errors='coerce')
    credito['fecha']= pd.to_datetime(credito['fecha'], format='%d-%m-%Y', errors='coerce')

    # Obtener la fecha mínima y máxima de vencimiento, manejando NaT
    primer = credito['fecha']
    ultima = cobranzas_credito['vencimiento'].max()


    # Verificar si los valores son NaT antes de aplicar strftime
    primer = primer.strftime('%d-%m-%Y') if pd.notna(primer) else ""
    ultima = ultima.strftime('%d-%m-%Y') if pd.notna(ultima) else ""
    credito['fecha']=credito['fecha'].strftime('%d-%m-%Y')
    with st.container(border=True):
        col1,col2,col3,col4,col5=st.columns(5)
        with col1: 
            st.markdown(f"### {credito['nombre']}: {credito['id']}")
            st.write(f"📝 **Concepto:** {credito['asociado']}")
            st.write(f"📆 **Vencimiento:** {credito['vence']}")
        with col2:
            st.write(f"📅 **Fecha:** {credito['fecha']}")
            st.write(f"💰 **Capital:** ${credito['capital']:,.0f}")
        with col3:
            st.write(f"📌 **Cantidad de cuotas:** {credito['cantidad']}")
            st.write(f"💰 **Monto por cuota:** ${credito['monto']:,.0f}")
        with col4:
            st.write(f"📝 **Estado:** {credito['estado']}")
        with col5:
            estado=st.selectbox('Modificar estado',
                        ["Seleccione una opción", "pendiente", "aceptado", "liquidado", 
                        "al dia", "En mora", "en juicio", "cancelado", "finalizado"])
            if st.button('Guardar'):
                if estado=='finalizado':
                    try:
                        login.finalizar(credito['id'])
                    except:
                        credito['estado']='finalizado'
                        st.session_state['credito']=credito
                    st.rerun()
                else:
                    login.save_nuevo(st.session_state['credito']['id'],'estado',estado,st.secrets['ids']['prestamos'])
    with st.container(border=True):
        col1,col2,col3,col4=st.columns(4)
        with col1:
            #primer y ultima cobranza
            st.write(f"Fecha de entrega: {primer}")
            st.write(f"Ultimo vencimiento: {ultima}")

        with col2:
            #capital entregado
            entregado=credito['capital']
            st.write(f"capital entregado: {entregado}")


            #total de intereses
            mora=cobranzas_credito[cobranzas_credito['estado']=='en mora']['mora'].sum()
            st.write(f"total de intereses acumulados: {mora}")

        with col3:
            #total de deuda
            monto_mora=cobranzas_credito['monto_recalculado_mora'].sum()-cobranzas_credito['pago'].sum()
            st.write(f"total adeudado: {monto_mora}")

            #total pagado
            pagado=cobranzas_credito['pago'].sum()
            st.write(f"total pagado: {pagado}")



###----------------------------------------------------###
    login.display_cobranzas(cobranzas_credito)
    #with st.expander('ver pagados'):
    #    st.dataframe(credito[(credito['estado']=='Pago total') or (credito['estado']=='Pago parcial')])