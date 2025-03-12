import streamlit as st
import login
if 'usuario' not in st.session_state:
    st.switch_page('inicio.py')
login.generarLogin()

import math


def redondear_mil_condicional(numero, umbral=50):
    redondeo=int(math.ceil(numero / 100) * 100)
    return redondeo, redondeo-numero   # Redondea hacia arriba

st.title("Simulador de créditos")
# Entrada de datos
if 'init' not in st.session_state:
    monto_total=0
    st.session_state['init']=0

col1,col2=st.columns(2)
def show1():
    st.session_state['init']=1
with col1:
    monto_total = st.number_input("Monto total ($):", min_value=0.0, step=100.0,on_change=show1)
    plazo = st.number_input('cantidad de cuotas',min_value=1,step=1)
with col2:
    if st.session_state['init']==1:
        st.subheader(f"${monto_total:,.0f}")
    tipo=st.selectbox('Tasa nominal (%):',['mensual','quincenal','semanal','otra tasa'])
    if tipo=='mensual':
        tasa_nominal_mensual=18
    elif tipo=='quincenal':
        tasa_nominal_mensual=14
    elif tipo=='semanal':
        tasa_nominal_mensual=6.5
    else:
        tasa_nominal_mensual = st.number_input("Tasa nominal (%):", min_value=0.0, step=0.01, format="%.2f")
    if tipo in ['mensual','quincenal','semanal']:
        st.write(f"Tasa nominal (%): {tasa_nominal_mensual}")
# Cálculo de la cuota fija mensual usando la fórmula de anualidades
IVA=0.21
if monto_total > 0 and tasa_nominal_mensual > 0 and plazo > 0:
    tasa_decimal = tasa_nominal_mensual / 100
    cuota_pura=monto_total*((((1+tasa_decimal)**plazo)*tasa_decimal)/(((1+tasa_decimal)**plazo)-1))
    iva=cuota_pura*IVA
    interes=monto_total*tasa_decimal
    amortizacion=cuota_pura-interes
    if plazo==1:
        cuota_mensual,redondeo=redondear_mil_condicional(monto_total*(1+tasa_decimal))
    elif plazo==2:
        cuota_mensual,redondeo=redondear_mil_condicional((monto_total*(1+(tasa_decimal))**2)/2)
    else:
        cuota_mensual,redondeo=redondear_mil_condicional(interes+amortizacion+iva)
    # Resultados
    st.subheader("Resultados:")
    st.write(f"Monto fijo por cuota: ${cuota_mensual:,.0f}")
    st.write(f"redondeando: ${redondeo:,.0f}")
else:
    cuota_mensual = 0.0
with st.expander('simulador inverso'):
    pc=st.number_input('monto por cuota')
    tn=st.number_input('tasa nominal')
    td=tn / 100
    p=st.number_input('cantidad de cuotas')
    try:
        mt = (pc / (1 + IVA)) * (( (1 + td) ** p - 1 ) / ( (1 + td) ** p * td ))
        st.subheader(f'monto financiado: {mt}')
    except:
        pass