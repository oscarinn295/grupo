#aca es donde quiero hacer un poco de magia
#quiero que al buscar al cliente, se cree un objeto tomando todos sus datos del excel y que de ahi se hagan todos los calculos necesarios
import streamlit as st
import pandas as pd

def load_data_vendedores(url):
    df=pd.read_excel(url,engine='openpyxl')
    if st.session_state['user_data']['permisos'].iloc[0]!='admin':
        df=df[df['vendedor']==st.session_state['usuario']]
    return df


if "clientes" not in st.session_state:
    st.session_state["clientes"] = load_data_vendedores(st.secrets['urls']['clientes'])
if "cobranzas" not in st.session_state:
    st.session_state["cobranzas"] = load_data_vendedores(st.secrets['urls']['cobranzas'])
if "prestamos" not in st.session_state:
    st.session_state["prestamos"] = load_data_vendedores(st.secrets['urls']['prestamos'])


clientes= st.session_state['clientes']
cobranzas= st.session_state["cobranzas"]
prestamos= st.session_state["prestamos"]

class Cliente:
    def __init__(self, nombre):
        self.nombre = nombre
        self.cliente = self.datos_cliente(st.session_state['urls']['clientes'])
        self.prestamos = self.datos_prestamos(st.session_state['urls']['prestamos'])
        self.cobranzas = self.datos_cobranzas(st.session_state['urls']['cobranzas'])

    def datos_cliente(self):

        return clientes[clientes['nombre']==self.nombre]
    
    def datos_prestamos(self, ruta):
        
        return prestamos[prestamos['nombre']==self.nombre]

    def datos_cobranzas(self, ruta):
        
        return cobranzas[cobranzas['prestamo_id'].isin(prestamos['id'].unique)]


# Verificar si el cliente ya está en session_state
if "cliente" not in st.session_state:
    st.session_state["cliente"] = Cliente(
        id_cliente=123,  # Podrías recibir este ID del usuario
        ruta_clientes="clientes.xlsx",
        ruta_prestamos="prestamos.xlsx",
        ruta_cobranzas="cobranzas.xlsx"
    )

cliente = st.session_state["cliente"]

st.write("Datos del cliente:", cliente.datos_cliente)
st.write("Préstamos:", cliente.prestamos)
st.write("Cobranzas:", cliente.cobranzas)
def save_data(id_value, column_name, new_value, sheet_id):
    import pandas as pd
    import time
    
    # Obtener el worksheet del sheet principal
    worksheet = get_worksheet(sheet_id)
    
    # Obtener la URL y ID del DataFrame de control de procesos
    procesos_url = st.secrets['urls']['procesos']
    procesos_id = st.secrets['ids']['procesos']
    
    # Leer el DataFrame de control de procesos
    df_procesos = pd.read_csv(procesos_url)
    
    # Verificar si el sistema está disponible para actualizar
    ultimo_estado = df_procesos['estado'].iloc[-1] if not df_procesos.empty else None
    
    # Si el estado es "en proceso", esperar hasta que cambie a "disponible"
    max_intentos = 30  # Límite para evitar bucles infinitos
    intentos = 0
    
    while ultimo_estado == "en proceso" and intentos < max_intentos:
        st.info("Sistema ocupado. Esperando a que se complete otro proceso...")
        time.sleep(5)  # Esperar 5 segundos antes de verificar nuevamente
        # Recargar el DataFrame para ver si el estado cambió
        df_procesos = pd.read_csv(procesos_url)
        ultimo_estado = df_procesos['estado'].iloc[-1] if not df_procesos.empty else None
        intentos += 1
    
    if intentos >= max_intentos:
        st.error("Tiempo de espera agotado. El sistema sigue ocupado después de varios intentos.")
        return
    
    # Marcar el inicio del proceso de actualización
    # Añadir una nueva fila al DataFrame con estado "en proceso"
    nueva_fila = pd.DataFrame({
        'timestamp': [pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")],
        'accion': [f"Actualización de {column_name} para ID {id_value}"],
        'estado': ["en proceso"]
    })
    
    df_procesos = pd.concat([df_procesos, nueva_fila], ignore_index=True)
    
    # Guardar el DataFrame actualizado
    worksheet_procesos = get_worksheet(procesos_id)
    actualizar_worksheet_desde_df(worksheet_procesos, df_procesos)
    
    # Continuar con la lógica original de actualización
    try:
        # Obtener nombres de las columnas
        col_labels = worksheet.row_values(1)
        if column_name not in col_labels:
            st.error(f"La columna '{column_name}' no existe en la hoja.")
            # Actualizar estado a "disponible" en caso de error
            marcar_disponible(df_procesos, worksheet_procesos)
            return

        # Índice de las columnas
        try:
            id_col_index = col_labels.index("ID_Personalizado") + 1
            col_index = col_labels.index(column_name) + 1
        except ValueError:
            st.error("No se encontró la columna de ID o la columna objetivo.")
            # Actualizar estado a "disponible" en caso de error
            marcar_disponible(df_procesos, worksheet_procesos)
            return

        # Obtener todas las filas de la columna de ID
        id_column = worksheet.col_values(id_col_index)

        # Buscar la fila correspondiente al ID
        try:
            row_index = id_column.index(str(id_value)) + 1
        except ValueError:
            st.error(f"ID {id_value} no encontrado en la columna 'ID_Personalizado'.")
            # Actualizar estado a "disponible" en caso de error
            marcar_disponible(df_procesos, worksheet_procesos)
            return

        # Actualizar la celda
        worksheet.update_cell(row_index, col_index, new_value)
        st.success(f"Valor '{new_value}' guardado en fila {row_index}, columna '{column_name}'.")
        
        # Actualizar estado a "disponible" tras éxito
        marcar_disponible(df_procesos, worksheet_procesos)
        
    except Exception as e:
        st.error(f"Error al actualizar datos: {str(e)}")
        # Actualizar estado a "disponible" en caso de excepción
        marcar_disponible(df_procesos, worksheet_procesos)

def marcar_disponible(df_procesos, worksheet_procesos):
    """Función auxiliar para marcar el estado como disponible"""
    import pandas as pd
    
    # Añadir una nueva fila con estado "disponible"
    nueva_fila = pd.DataFrame({
        'timestamp': [pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")],
        'accion': ["Proceso completado"],
        'estado': ["disponible"]
    })
    
    df_actualizado = pd.concat([df_procesos, nueva_fila], ignore_index=True)
    
    # Actualizar el worksheet con el DataFrame actualizado
    actualizar_worksheet_desde_df(worksheet_procesos, df_actualizado)

def actualizar_worksheet_desde_df(worksheet, df):
    """Función auxiliar para actualizar un worksheet desde un DataFrame"""
    # Convertir DataFrame a lista de listas
    valores = [df.columns.tolist()] + df.values.tolist()
    
    # Actualizar todas las celdas a la vez
    worksheet.update('A1', valores)