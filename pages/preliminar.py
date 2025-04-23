import login
import pandas as pd
import streamlit as st
from datetime import datetime
from datetime import date
import datetime as dt
from dateutil.relativedelta import relativedelta


if 'usuario' not in st.session_state:
    st.switch_page('inicio.py')
# Llamar al módulo de login
login.generarLogin()

clientes=st.session_state['clientes']
vendedores=st.session_state['usuarios']['usuario'].tolist()
prestamos=login.load_data(st.secrets['urls']['prestamos'])

if st.session_state['user_data']['permisos'].iloc[0]!='admin':
    prestamos=prestamos[prestamos['vendedor']==st.session_state['usuario']]
    clientes=clientes[clientes['vendedor']==st.session_state['usuario']]

clientes=st.session_state['clientes']['nombre'].tolist()

st.title("Actualizaciones preliminares")
st.write('el chiste de esta parte es que vayan poniendo todo lo que no estén seguros si está o no en el sistema o no tienen permisos de editar entonces va por acá tambien')
st.write('entonces, quedan distintos formularios por cada posible nuevo dato a añadir durante el dia')

def actualizacion(cols,values):
    """
    Registra en una hoja de Google Sheets un cambio en los datos.
    :param sheet_id: ID de la hoja de cálculo en Google Sheets.
    :param old_values: Lista con los valores anteriores.
    :param new_values: Lista con los valores nuevos.
    """
    worksheet = login.get_worksheet(st.secrets['ids']['temporal'])

    # Obtener la cantidad de filas actuales para generar el índice numérico
    existing_data = worksheet.get_all_values()
    index = len(existing_data)  # Nueva fila será una más que las actuales

    # Obtener la fecha y hora actual
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    # Obtener el usuario actual
    usuario = st.session_state.get("usuario", "Desconocido")

    # Crear las filas con la estructura: [Fecha, Usuario, Índice, Valores...]
    row_cols = [timestamp, usuario, index] + cols
    row_values = [timestamp, usuario, index + 1] + values

    # Agregar ambas filas a la hoja
    worksheet.append_row(row_cols)
    worksheet.append_row(row_values)


def cliente():
    st.title('Crear Cliente: ')
    with st.form("form_crear_cliente"):
        col1, col2 = st.columns(2)
        
        with col1:
            dni = st.text_input("DNI")
            nombre = st.text_input("Nombre")
            fecha_nac = st.date_input("Fecha")
            vendedor = st.selectbox('Vendedor', vendedores, key='vendedores')
        
        with col2:
            direccion = st.text_input("Dirección")
            celular = st.text_input("Celular")
            mail = st.text_input("Mail")
            scoring = st.text_input("Scoring")

        # Botón de guardar dentro del formulario
        submit_button = st.form_submit_button("Guardar")
        
        if submit_button:
            nuevo_cliente = [
                'nuevo cliente',
                nombre,
                vendedor,
                scoring,
                direccion,
                fecha_nac.strftime("%d-%m-%Y"),
                dni,
                celular,
                mail
            ]
            actualizacion(['','nombre','vendedor','scoring','direccion','fecha_nac','dni','celular','mail'],nuevo_cliente)
            st.success('Cliente guardado correctamente')

import math
def redondear_mil_condicional(numero, umbral=50):
    resto = numero % 1000  # Obtiene los últimos tres dígitos
    if resto < umbral:
        return int(math.floor(numero / 100) * 100)  # Redondea hacia abajo
    else:
        return int(math.ceil(numero / 100) * 100)   # Redondea hacia arriba
    

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
def crear_cobranzas(data):
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
    i=0
    for fecha in fechas:
        nueva_cobranza=['cobranza generada por prestamo',
            id,
            entregado,
            TNM,
            cantidad_cuotas,
            vendedor,
            nombre,
            i,
            monto_por_cuota,
            fecha
            ]
        i+=1
        actualizacion([st.session_state['usuario'],'prestamo_id','entregado','tnm','cantidad de cuotas','vendedor','nombre','n_cuota','monto','vencimiento'],nueva_cobranza)
def prestamo(): 
    col1,col2=st.columns(2)
    IVA=0.21
    with col1:
        cantidad_cuotas = st.number_input("Cantidad de Cuotas*",
                                                    min_value=1,
                                                    step=1,key='cant')
        capital = st.number_input("Capital*", min_value=0.0, step=1000.0,key='capital')
    with col2:
        TNM=st.number_input('T.N.M*', min_value=0.1, step=0.1,key='tnm')
        tasa_decimal = TNM / 100
        cuota_pura=capital*((((1+tasa_decimal)**cantidad_cuotas)*tasa_decimal)/(((1+tasa_decimal)**cantidad_cuotas)-1))
        iva=cuota_pura*IVA
        interes=capital*tasa_decimal
        amortizacion=cuota_pura-interes
        monto=0.0
        if st.checkbox('calcular monto por cuota'):
            monto_final=interes+amortizacion+iva
            monto_final=redondear_mil_condicional(monto_final)
            st.write(monto_final)
        else:
            monto_final=st.number_input('Monto Cuota',min_value=0.0, step=1000.0,key='monto',value=monto)
    with st.form('crear_prestamo'):
        fecha =  date.today()
        col1, col2 = st.columns(2)
        with col1:
            nombre_cliente = st.selectbox('Cliente',clientes)
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
            venc_dia=st.selectbox("Selecciona un tipo de vencimiento", ['Mensual: 1-10',
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
        nuevo_prestamo = ['nuevo prestamo',
            fecha.strftime('%d-%m-%Y'),
            nombre_cliente,
            vendedor,
            cantidad_cuotas,
            capital,
            venc_dia,
            estado,
            producto_asociado,
            TNM,
            monto_final,
            obs]
        
        actualizacion(['','fecha','nombre','vendedor','cantidad','capital','vence','estado','asociado','tnm','monto','obs'],nuevo_prestamo)


lista_clientes2 = ['no registrado'] + clientes

prestamos['fecha']=pd.to_datetime(prestamos['fecha'], format='%d-%m-%Y').dt.strftime('%d-%m-%Y')
lista_prestamos=prestamos[['fecha','nombre','vence','cantidad','capital']].values.tolist()
def registrar_cobranza():
    prest1=st.selectbox('prestamo',['no registrado','existente'])
    if prest1=='no registrado':
        fecha=st.date_input('fecha de entrega')
        client1=st.selectbox('cliente',lista_clientes2)
        client=client1
        if client1=='no registrado':
            client2=st.text_input('nombre del cliente')
            client=client2
        else:
            st.write(f'cliente: {client1}')
        n_cuotas=st.number_input('cantidad de cuotas',min_value=1)
        entregado=st.number_input('monto entregado',min_value=0.0)
        frecuencia=st.selectbox('tipo de prestamo',['Mensual: 1-10','Mensual: 10-20','Mensual: 20-30','Quincenal','Semanal: lunes',
                                                    'Semanal: martes','Semanal: miercoles','Semanal: jueves',
                                                    'Semanal: viernes','Semanal: sabado','indef'])
    else:
        prest2=st.selectbox('prestamos registrados',lista_prestamos)
        fecha=prest2[0]
        client=prest2[1]
        frecuencia=prest2[2]
        n_cuotas=prest2[3]
        entregado=prest2[4]
    prestamox=[fecha,client,frecuencia,n_cuotas,entregado]
    registro=st.selectbox('monto',['Pago total','Pago parcial'])
    monto = st.number_input("Monto", min_value=0.0, step=1000.0)
    medio_pago = st.selectbox('Seleccione una opción', ['Seleccione una opción', 'efectivo', 'transferencia'])

    with st.form("registrar_pago"):
        cobrador = st.selectbox('Cobrador', vendedores)
        submit_button = st.form_submit_button("Registrar")

    if submit_button:
        values=['nueva cobranza']+prestamox+[monto,registro,cobrador,date.today().strftime('%d-%m-%Y'),medio_pago]
        if medio_pago != 'Seleccione una opción' and monto > 0:
            actualizacion(['','fecha','cliente','cantidad de cuotas','monto entregado','tipo de prestamo','pago','estado','cobrador','fecha_cobro','medio de pago'],values)
        else:
            st.warning('Faltan datos')

st.subheader('nuevo cliente: ')
cliente()
st.subheader('nuevo prestamo: ')
prestamo()
st.subheader('cobranza registrada: ')
registrar_cobranza()