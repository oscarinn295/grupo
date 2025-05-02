import streamlit as st
import login
import datetime as dt
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
import pandas as pd
import math

#inicializando los datos de los prestamos
idc=st.secrets['ids']['prestamos']
url=st.secrets['urls']['prestamos']
st.session_state['cliente']=None


def load():
    return login.load_data(url)

def delete(index):#borra una fila completa y acomoda el resto de la hoja para que no quede el espacio en blanco
    login.delete_data(index,idc)
def save(id,column,data):#modifica un solo dato
    login.save_data(id,column,data,idc)
def new(data):#añade una columna entera de datos
    login.append_data(data,idc)
    st.session_state['prestamos']=load()


if 'usuario' not in st.session_state:
    st.switch_page('inicio.py')
login.generarLogin()
login.cargar_clientes()


cobranzas=st.session_state["cobranzas"]
clientes=st.session_state["clientes"]



#funciones que generan datos fuera de esta pagina
def generar_fechas_prestamos(fecha_registro:str, frecuencia:str, cuotas:int):
    """
    Genera fechas de pago a partir de las condiciones dadas.
    :param fecha_registro: que originalmente es un datetime pero como que no me estaba dejando guardar datetime
        así que primero son los strings que salen de eso
        los string de fecha para este caso tienen que venir con este formato %d/%m/%Y
    :param frecuencia: Frecuencia de pago ('semanal', 'quincenal', 'mensual')
    :param cuotas: Número de cuotas
    :return: Lista de fechas de pago (list of datetime.date)
    """
    fecha_registro=datetime.strptime(fecha_registro, "%d-%m-%Y")
    fecha_actual=fecha_registro
    fechas=[]

    semanales={
        'Semanal: lunes':0,
        'Semanal: martes':1,
        'Semanal: miercoles':2,
        'Semanal: jueves':3,
        'Semanal: viernes':4,
        'Semanal: sabado':5}
    
    if frecuencia=='Mensual: 1-10':
        fecha_actual+=dt.timedelta(days=10-date.today().day)
        for _ in range(cuotas):
            fecha_actual+=relativedelta(months=1)
            fechas.append(fecha_actual.strftime("%d-%m-%Y"))

    elif frecuencia=='Mensual: 10-20':
        fecha_actual+=dt.timedelta(days=20-date.today().day)
        for _ in range(cuotas):
            fecha_actual+=relativedelta(months=1)
            fechas.append(fecha_actual.strftime("%d-%m-%Y"))


    elif frecuencia=='Mensual: 20-30':
        fecha_actual+=dt.timedelta(days=30-date.today().day)
        for _ in range(cuotas):
            fecha_actual+=relativedelta(months=1)
            fechas.append(fecha_actual.strftime("%d-%m-%Y"))

    elif frecuencia=='Quincenal':
        for _ in range(cuotas):
            fecha_actual+=dt.timedelta(weeks=2)
            fechas.append(fecha_actual.strftime("%d-%m-%Y"))

    elif frecuencia in semanales:
        dia_objetivo = semanales[frecuencia]
        while fecha_actual.weekday() != dia_objetivo:
            fecha_actual += dt.timedelta(days=1)
        for _ in range(cuotas):
            fecha_actual+=dt.timedelta(weeks=1)
            fechas.append(fecha_actual.strftime("%d-%m-%Y"))
    else:
        return date.today().strftime("%d-%m-%Y")
    return fechas



import math


def redondear_mil_condicional(numero, umbral=50):
    resto = numero % 1000  # Obtiene los últimos tres dígitos
    if resto < umbral:
        redondeo=int(math.floor(numero / 100) * 100)
        return redondeo,numero-redondeo  # Redondea hacia abajo
    else:
        redondeo=int(math.ceil(numero / 100) * 100)
        return redondeo, redondeo-numero   # Redondea hacia arriba



def crear_cobranzas(data,redondeo):
    #sacar los datos del prestamo
    id=data[0]
    fecha_entrega=data[1]
    nombre=data[2]
    vendedor=data[3]
    cantidad_cuotas=data[4]
    entregado=data[5]
    frecuencia=data[6]
    TNM=data[9]
    monto_por_cuota=float(data[10])
    
    fechas=generar_fechas_prestamos(fecha_entrega,frecuencia, cantidad_cuotas)

    tasa_decimal = TNM / 100
    capital=entregado

    cuota_pura=capital*((((1+tasa_decimal)**cantidad_cuotas)*tasa_decimal)/(((1+tasa_decimal)**cantidad_cuotas)-1))

    interes=capital*tasa_decimal

    amortizacion=cuota_pura-interes

    iva=cuota_pura*0.21

    


    montos=[[interes,amortizacion]]

    i=0
    for fecha in fechas:
        interes=montos[i][0]
        amortizacion=montos[i][1]
        discrepancia=redondeo+monto_por_cuota-(amortizacion+interes+iva)
        nueva_cobranza=[
            str(st.session_state['cobranzas']['id'].astype(int).max()+i+1),
            id,
            entregado,
            tasa_decimal,
            cantidad_cuotas,
            vendedor,
            nombre,
            i+1,
            monto_por_cuota,
            fecha,
            0,
            0,
            discrepancia
            ,
            capital,
            cuota_pura,
            interes,
            amortizacion,
            iva,
            monto_por_cuota,
            0,
            'Pendiente de pago',
            '',
            '',
            ''
            ]
        capital-=amortizacion
        interes=capital*tasa_decimal
        amortizacion=cuota_pura-interes
        i+=1
        montos.append([interes,amortizacion])
        login.append_data(nueva_cobranza,st.secrets['ids']['cobranzas'])
        st.session_state['cobranzas']=login.load_data(st.secrets['urls']['cobranzas'])

def egreso_caja(data):
    fecha_entrega=data[1]
    cantidad_cuotas=data[4]
    entregado=data[5]
    monto_por_cuota=float(data[10])

    caja=st.session_state["mov"]
    caja['saldo'] = pd.to_numeric(caja['saldo'], errors='coerce')
    mov=[
        fecha_entrega,
        f"ENTREGA {entregado}, PLAN {cantidad_cuotas} CUOTAS DE {monto_por_cuota}",
        0,
        entregado,
        -entregado,
        caja['saldo'].sum()-entregado
        ]
    login.append_data(mov,st.secrets['ids']['flujo_caja'])


def reporte_venta(data):
    id=data[0]
    fecha_entrega=data[1]
    nombre=data[2]
    vendedor=data[3]
    cantidad_cuotas=data[4]
    entregado=data[5]
    TNM=data[9]

    venta=[
        vendedor,
        fecha_entrega,
        nombre,
        id,
        cantidad_cuotas,
        entregado
        ]
    login.append_data(venta,st.secrets['ids']['repo_ventas'])




if 'pagina_actual' not in st.session_state:
    st.session_state['pagina_actual'] = 1



vendedores=st.session_state['usuarios']['usuario'].tolist()



#formulario para crear prestamo
def crear(): 
    coll1,coll2=st.columns(2)
    IVA=0.21
    if "init" not in st.session_state:
        capital=0
        st.session_state["init"]=0
    def show1():
        st.session_state["init"]=1
    with coll1:
        cantidad_cuotas = st.number_input("Cantidad de Cuotas*",
                                                    min_value=1,
                                                    step=1,key='cant')
        capital = st.number_input("Capital:", min_value=0.0,step=1000.0, format="%.2f",on_change=show1)
        if st.session_state['init']==1:
            st.write(f"${capital:,.0f}")
    with coll2:
        tipo=st.selectbox('Tasa nominal (%):',['mensual','quincenal','semanal','otra tasa'])
        if tipo=='mensual':
            TNM=18
        elif tipo=='quincenal':
            TNM=14
        elif tipo=='semanal':
            TNM=6.5
        else:
            TNM = st.number_input("Tasa nominal mensual (%):", min_value=1.0, step=0.01, format="%.2f")
        if tipo in ['mensual','quincenal','semanal']:
            st.write(f"Tasa nominal (%): {TNM}")
        tasa_decimal = TNM / 100
        cuota_pura=capital*((((1+tasa_decimal)**cantidad_cuotas)*tasa_decimal)/(((1+tasa_decimal)**cantidad_cuotas)-1))
        iva=cuota_pura*IVA
        interes=capital*tasa_decimal
        amortizacion=cuota_pura-interes
        monto=0.0
        if st.checkbox('calcular monto por cuota'):
            monto_final=interes+amortizacion+iva
            if cantidad_cuotas==1:
                monto_final,redondeo=redondear_mil_condicional(capital*(1+tasa_decimal))
            elif cantidad_cuotas==2:
                monto_final,redondeo=redondear_mil_condicional((capital*(1+(tasa_decimal))**2)/2)
            else:
                monto_final,redondeo=redondear_mil_condicional(interes+amortizacion+iva)
            redondeo=math.trunc(redondeo)
            st.write(f'Monto Fijo por Cuota: ${monto_final:,.0f}, Redondeo: ${redondeo:,.0f}')
        else:
            monto_final=st.number_input('Monto Fijo por Cuota',min_value=0.0, step=1000.0,key='monto',value=monto, format="%.2f")
    with st.form('crear_prestamo'):
        fecha =  date.today()
        col1, col2 = st.columns(2)
        lista=['seleccione un cliente']
        for nombre in clientes['nombre']:
            lista.append(nombre)
        with col1:
            nombre_cliente = st.selectbox('Cliente',lista)
            producto_asociado=st.text_input('Producto Asociado*',key='producto')
            estado = st.selectbox(
                "Estado*",
                ["Seleccione una opción",
                "pendiente",
                "aceptado",
                "liquidado",
                "al dia",
                "En mora",
                "en juicio",
                "cancelado",
                "finalizado"
                ],key='estadoo')     
        with col2:
            vendedor=st.selectbox('vendedor',vendedores)
            venc=st.selectbox("Selecciona un tipo de vencimiento", ['Mensual: 1-10',
                                                                              'Mensual: 10-20',
                                                                              'Mensual: 20-30',
                                                                              'Quincenal',
                                                                              'Semanal: lunes',
                                                                              'Semanal: martes',
                                                                              'Semanal: miercoles',
                                                                              'Semanal: jueves',
                                                                              'Semanal: viernes',
                                                                              'Semanal: sabado',
                                                                              'indef']) 
        obs=st.text_input('Observaciones',key='obss')
        col1, col2 = st.columns(2)
        submit_button=st.form_submit_button('crear')
    
    if submit_button:
        nuevo_prestamo = [max(st.session_state['prestamos']['id']) + 1,
            fecha.strftime('%d-%m-%Y'),
            nombre_cliente,
            vendedor,
            cantidad_cuotas,
            capital,
            venc,
            estado,
            producto_asociado,
            TNM,
            monto_final,
            redondeo,
            obs]
        new(nuevo_prestamo)
        egreso_caja(nuevo_prestamo)
        reporte_venta(nuevo_prestamo)
        crear_cobranzas(nuevo_prestamo,redondeo)
        login.historial(['nuevo prestamo','fecha','nombre','vendedor','cantidad','capital','vence','estado','asociado','tnm','monto','redondeo','obs'],nuevo_prestamo)


import numpy as np
def display_table():
    df = st.session_state["prestamos"]
    col1,col2,col3,col4=st.columns(4)
    with col1:
        with st.expander('Ver mensuales'):
            if st.button('1 al 10'):
                df=df[df['vence']=='Mensual: 1-10']
            if st.button('10 al 20'):
                df=df[df['vence']=='Mensual: 10-20']
            if st.button('20 al 30'):
                df=df[df['vence']=='Mensual: 20-30']
    with col2:
        with st.expander('Ver semanales'):
            if st.button('lunes'):
                df=df[df['vence']=='Semanal: lunes']
            if st.button('martes'):
                df=df[df['vence']=='Semanal: martes']
            if st.button('miercoles'):
                df=df[df['vence']=='Semanal: miercoles']
            if st.button('jueves'):
                df=df[df['vence']=='Semanal: jueves']
            if st.button('viernes'):
                df=df[df['vence']=='Semanal: viernes']
            if st.button('sabado'):
                df=df[df['vence']=='Semanal: sabado']
    with col3:
        if st.button('Ver quincenales'):
            df=df[df['vence']=='Quincenal']
    with col4:
        if st.button('Ver todos'):
            df = st.session_state["prestamos"]
    lista=['seleccione un cliente']
    lista2=['seleccione un vendedor']
    for nombre in vendedores:
        lista2.append(nombre)
    for nombre in clientes['nombre']:
        lista.append(nombre)
    nombre_cliente = st.selectbox('Cliente',lista,index=0)
    vendedor=st.selectbox('vendedor',lista2,index=0)
    if nombre_cliente!='seleccione un cliente':
        st.session_state["prestamos_df"]=df[df['nombre']==nombre_cliente]
        df=st.session_state["prestamos_df"]
    if vendedor!='seleccione un vendedor':
        st.session_state["prestamos_df"]=df[df['vendedor']==vendedor]
        df=st.session_state["prestamos_df"]


    # Configuración de paginación
    ITEMS_POR_PAGINA = 10
    # Paginación
    total_paginas = (len(df) // ITEMS_POR_PAGINA) + (1 if len(df) % ITEMS_POR_PAGINA > 0 else 0)
    inicio = (st.session_state['pagina_actual'] - 1) * ITEMS_POR_PAGINA
    fin = inicio + ITEMS_POR_PAGINA
    df_paginado = df.iloc[inicio:fin]
    if not df.empty:
        for idx, row in df_paginado.iterrows():
            if row['fecha']==str:
                pass
            else:
                try:
                    row['fecha']=row['fecha'].strftime('%d-%m-%Y')
                except:
                    pass

            with st.container(border=True):
                col1, col2, col3,col4 = st.columns(4)
                with col1:
                    st.write(f"**Fecha:** {row['fecha']} \n", unsafe_allow_html=True)
                    st.write(f"**Concepto:** {row['asociado']} \n", unsafe_allow_html=True)
                    st.write(f"**Capital:** ${row['capital']:,.0f} \n ", unsafe_allow_html=True)
                    st.write(f"**Monto por cuota:** ${row['monto']:,.0f} \n ", unsafe_allow_html=True)
                    if not(row['redondeo'] in [np.nan,'',0]):
                        st.write(f"**Redondeo:** ${row['redondeo']:,.0f}", unsafe_allow_html=True)
                with col2:
                    st.write(f"**Cliente:** {row['nombre']}\n", unsafe_allow_html=True)
                    st.write(f"**Nro de cuotas:** {int(row['cantidad'])}")
                with col3:
                    st.write(f"vendedor:{row['vendedor']}\n", unsafe_allow_html=True)
                    st.write(f"vencimiento:{row['vence']}")
                with col4:
                    st.write(f'{row["estado"]}')
                    if st.button("ver detalles",key=f'cliente_{idx}'):
                                st.session_state['credito']=row
                                st.switch_page("pages/por_credito.py")
                    #with st.popover(f'✏️ Editar'):
                        #editar(row)
    else:
        st.warning("No se encontraron resultados.")
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
        st.write(f"Se muestran de {inicio + 1} a {min(fin, len(df))} de {len(df)} resultados")
        items_seleccionados = st.selectbox("Por página", [10, 25, 50, 100], index=[10, 25, 50, 100].index(ITEMS_POR_PAGINA))
        if items_seleccionados != ITEMS_POR_PAGINA:
            ITEMS_POR_PAGINA = items_seleccionados
            st.session_state['pagina_actual'] = 1
            st.rerun()
    with st.expander('datos filtrados'):
        st.subheader("Datos filtrados")
        st.dataframe(df)
    with st.expander('ver morosos'):
        st.subheader("morosos")
        moras=cobranzas[cobranzas['estado']=='En mora']
        morosos=df[df['id'].isin(moras['prestamo_id'].unique())]
        st.dataframe(morosos)

col1,col2=st.columns(2)
with col1:
    st.title("Prestamos")
with col2:
    if st.session_state['user_data']['permisos'].iloc[0]=='admin':
        # Botón para crear un nuevo préstamo
        with st.popover("Crear Préstamo 💲",use_container_width=False):
            crear()
    st.page_link('pages/simulador_creditos.py',label='Simulador de creditos', icon=":material/sell:")
if st.button("Reiniciar datos"):
        login.cargar_clientes(forzado=True)
with st.container(border=True):
    display_table()
with st.expander('Ver cobranzas de creditos finalizados'):
    st.dataframe(login.load_data(st.secrets['urls']['finalizados']))