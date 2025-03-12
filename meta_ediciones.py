import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import datetime as dt
import login

def load_data(url):
    return pd.read_excel(url,engine='openpyxl')

st.session_state["clientes"] = load_data(st.secrets['urls']['clientes'])
st.session_state["cobranzas"] = load_data(st.secrets['urls']['cobranzas'])
st.session_state["prestamos"] = load_data(st.secrets['urls']['prestamos'])
def recalcular_y_guardar_recargos():
    st.session_state["clientes"] = load_data(st.secrets['urls']['clientes'])
    st.session_state["cobranzas"] = load_data(st.secrets['urls']['cobranzas'])
    st.session_state["prestamos"] = load_data(st.secrets['urls']['prestamos'])
    # Cargar datos de préstamos y cobranzas
    prestamos = st.session_state['prestamos']
    cobranzas = st.session_state['cobranzas']
    def calcular_recargo(cobranza):

        # Convertir la columna 'vencimiento' a datetime para trabajar con fechas
        try:
            cobranzas['vencimiento'] = pd.to_datetime(cobranzas['vencimiento'], format='%d-%m-%Y', errors='coerce')
        except:
            return pd.Series([cobranza['dias_mora'], cobranza['mora'], cobranza['monto_recalculado_mora']],
                            index=['dias_mora', 'mora', 'monto_recalculado_mora'])
        # Definir la fecha de hoy
        hoy_date = dt.date.today()

        # Actualizar el estado:
        # • Si el vencimiento es posterior a hoy, se marca como "Pendiente de pago".
        # • Si ya pasó y aún está como "Pendiente de pago", se cambia a "En mora".
        # • Para "Pago total" se conservan los valores.
        cobranzas.loc[cobranzas['vencimiento'].dt.date > hoy_date, 'estado'] = 'Pendiente de pago'
        cobranzas.loc[(cobranzas['vencimiento'].dt.date <= hoy_date) & (cobranzas['estado'] == 'Pendiente de pago'), 'estado'] = 'En mora'

        # Convertir nuevamente 'vencimiento' a string (para poder formatearlo o subirlo)
        try:
            cobranzas['vencimiento'] = cobranzas['vencimiento'].dt.strftime('%d-%m-%Y')
        except:
            pass
        # Si el estado es "Pago total" o "Pendiente de pago", se conservan los valores existentes.
        if cobranza['estado'] in ['Pago total', 'Pendiente de pago']:
            return pd.Series([cobranza['dias_mora'], cobranza['mora'], cobranza['monto_recalculado_mora']],
                            index=['dias_mora', 'mora', 'monto_recalculado_mora'])
        
        # Convertir monto a float (si no puede, se usa 0)
        try:
            monto = float(cobranza['monto'])
        except:
            pass

        # Buscar el préstamo correspondiente
        prestamo = prestamos[prestamos['id'] == cobranza['prestamo_id']]
        if pd.isna(cobranza['prestamo_id']) or prestamo.empty:
            # Si no se encontró, se mantienen los valores existentes
            return pd.Series([cobranza['dias_mora'], cobranza['mora'], cobranza['monto_recalculado_mora']],
                            index=['dias_mora', 'mora', 'monto_recalculado_mora'])

        # Diccionario con tasas de interés diarias
        tipo_prestamo = {
            'Mensual: 1-10': 500,
            'Mensual: 10-20': 500,
            'Mensual: 20-30': 500,
            'Quincenal': 400,
            'Semanal: lunes': 300,
            'Semanal: martes': 300,
            'Semanal: miercoles': 300,
            'Semanal: jueves': 300,
            'Semanal: viernes': 300,
            'Semanal: sabado': 300,
            'indef': 0
        }
        
        cobranza_vencimiento = datetime.strptime(cobranza['vencimiento'],'%d-%m-%Y')
        if pd.isna(cobranza_vencimiento):
            return pd.Series([cobranza['dias_mora'], cobranza['mora'], cobranza['monto_recalculado_mora']],
                            index=['dias_mora', 'mora', 'monto_recalculado_mora'])
        
        hoy_ts = pd.Timestamp(date.today())
        dias_mora = (hoy_ts - cobranza_vencimiento).days

        # Si el número de días de mora es menor o igual a 0 se mantienen los valores originales
        if dias_mora <= 0:
            return pd.Series([cobranza['dias_mora'], cobranza['mora'], cobranza['monto_recalculado_mora']],
                            index=['dias_mora', 'mora', 'monto_recalculado_mora'])
        
        # Obtener el tipo de préstamo y la tasa (las claves deben coincidir con los valores de la columna 'vence')
        tipo = prestamo['vence'].iloc[0]
        interes = tipo_prestamo.get(tipo, 0)  # Si no se encuentra, se asume 0

        interes_por_mora = interes * dias_mora
        monto_recalculado = monto + interes_por_mora

        return pd.Series([dias_mora, interes_por_mora, monto_recalculado],
                        index=['dias_mora', 'mora', 'monto_recalculado_mora'])
    
    
    """
    Esta función:
      1. Carga los datos de cobranzas y préstamos.
      2. Actualiza el estado de las cobranzas según la fecha de vencimiento.
      3. Aplica el cálculo de recargo de mora para cada cobranza.
      4. Reordena y formatea las columnas según se requiera.
      5. Sobrescribe la hoja de cobranzas con los cambios realizados.
    """


    # Convertir la columna 'vencimiento' a datetime
    cobranzas['vencimiento'] = pd.to_datetime(cobranzas['vencimiento'], format='%d-%m-%Y', errors='coerce')
    hoy_date = dt.date.today()

    # Actualizar el estado de las cobranzas:
    # - Si el vencimiento es posterior a hoy, se marca como "Pendiente de pago".
    # - Si ya pasó y estaba en "Pendiente de pago", se cambia a "En mora".
    cobranzas.loc[cobranzas['vencimiento'].dt.date > hoy_date, 'estado'] = 'Pendiente de pago'
    cobranzas.loc[(cobranzas['vencimiento'].dt.date <= hoy_date) & (cobranzas['estado'] == 'Pendiente de pago'), 'estado'] = 'En mora'

    # Convertir 'vencimiento' a string para que el formato sea consistente al subir los datos
    cobranzas['vencimiento'] = cobranzas['vencimiento'].dt.strftime('%d-%m-%Y')

    # Aplicar la función de cálculo a cada fila para actualizar los recargos
    cobranzas[['dias_mora', 'mora', 'monto_recalculado_mora']] = cobranzas.apply(calcular_recargo, axis=1)

    # Opcional: Reordenar las columnas según el formato requerido.
    # Ajusta 'column_order' según las columnas que realmente tengas en el DataFrame.
    column_order = ['id', 'prestamo_id', 'entregado', 'tnm', 'cantidad de cuotas',
                    'vendedor', 'nombre', 'n_cuota', 'monto', 'vencimiento', 
                    'dias_mora', 'mora','discrepancia', 'capital', 'cuota pura', 'intereses',
                    'amortizacion', 'iva', 'monto_recalculado_mora', 'pago', 'estado', 
                    'medio de pago', 'cobrador', 'fecha_cobro','obs']
    cols_present = [col for col in column_order if col in cobranzas.columns]
    cobranzas = cobranzas[cols_present]

    # Reemplazar valores NaN y nulos por cadena vacía para evitar errores en la carga
    cobranzas = cobranzas.fillna("")
    # Preparar los datos para sobrescribir la hoja:
    # La primera fila contiene los encabezados, seguido de los registros
    data_to_upload = [cobranzas.columns.tolist()] + cobranzas.astype(str).values.tolist()

    # Obtener el ID de la hoja de cobranzas
    sheet_id = st.secrets['ids']['cobranzas']
    # Sobrescribir la hoja con los datos actualizados
    login.overwrite_sheet(data_to_upload, sheet_id)
    
    st.success("Recargos recalculados y cambios guardados correctamente.")
recalcular_y_guardar_recargos()