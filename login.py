import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
import pandas as pd
import time
# Ocultar el botón de Deploy con CSS
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

def authenticate():
    """Autentica con Google Sheets y guarda el cliente en la sesión."""
    if "gspread_client" not in st.session_state:
        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
        st.session_state["gspread_client"] = gspread.authorize(creds)

def get_worksheet(sheet_id):
    """Obtiene la hoja de cálculo reutilizando la autenticación."""
    authenticate()  # Asegura que `st.session_state["gspread_client"]` está disponible
    client = st.session_state["gspread_client"]
    spreadsheet = client.open_by_key(sheet_id)
    return spreadsheet.worksheet("Sheet1")

def overwrite_sheet(new_data, sheet_id):
    """
    Sobrescribe toda la hoja de cálculo con los nuevos datos.
    
    :param new_data: Lista de listas, donde cada sublista representa una fila.
    :param sheet_id: ID de la hoja de cálculo en Google Sheets.
    """
    worksheet = get_worksheet(sheet_id)
    worksheet.clear()  # Borra todo el contenido de la hoja
    worksheet.update("A1", new_data)  # Escribe los nuevos datos desde A1


def delete_data(id_value, sheet_id, column_index=1):
    """Elimina todas las filas donde id_value esté presente en la columna especificada."""
    worksheet = get_worksheet(sheet_id)
    
    try:
        cells = worksheet.findall(str(id_value), in_column=column_index)  # Busca en una columna específica
        if not cells:
            return f"ID {id_value} no encontrado en la columna {column_index}."
        
        row_indices = sorted(set(cell.row for cell in cells), reverse=True)
        for row in row_indices:
            worksheet.delete_rows(row)
        
        return f"Se eliminaron {len(row_indices)} fila(s) con ID {id_value}."
    
    except Exception as e:
        return f"Error al eliminar datos: {e}"




def save_data(id_value, column_name, new_value, sheet_id):
    worksheet = get_worksheet(sheet_id)

    # Obtener nombres de las columnas
    col_labels = worksheet.row_values(1)
    if column_name not in col_labels:
        st.error(f"La columna '{column_name}' no existe en la hoja.")
        return

    # Índice de las columnas
    try:
        id_col_index = col_labels.index("id") + 1  # Cambia el nombre si es diferente
        col_index = col_labels.index(column_name) + 1
    except ValueError:
        st.error("No se encontró la columna de ID o la columna objetivo.")
        return

    # Obtener todas las filas de la columna de ID
    id_column = worksheet.col_values(id_col_index)

    # Buscar la fila correspondiente al ID
    try:
        row_index = id_column.index(str(id_value)) + 1  # +1 porque Google Sheets usa base 1
    except ValueError:
        st.error(f"ID {id_value} no encontrado en la columna 'ID_Personalizado'.")
        return

    # Actualizar la celda
    worksheet.update_cell(row_index, col_index, new_value)
    st.success(f"Valor '{new_value}' guardado en fila {row_index}, columna '{column_name}'.")

def append_data(new_values, sheet_id):
    worksheet = get_worksheet(sheet_id)
    worksheet.append_row(new_values)

def load_data(url):
    return pd.read_excel(url,engine='openpyxl')


def save_nuevo(id_value, column_name, new_value, sheet_id):
    """
    Guarda un nuevo valor en una celda específica basada en un ID y nombre de columna.
    
    :param id_value: Valor del ID a buscar.
    :param column_name: Nombre de la columna donde se guardará el nuevo valor.
    :param new_value: Valor a guardar.
    :param sheet_id: ID de la hoja de Google Sheets.
    :return: True si se guardó correctamente, False si hubo un error.
    """
    try:
        # Obtener la hoja de trabajo
        worksheet = get_worksheet(sheet_id)

        # Obtener nombres de las columnas (fila 1)
        col_labels = worksheet.row_values(1)
        if not col_labels:
            st.error("La hoja está vacía o no tiene encabezados.")
            return False

        # Verificar si la columna existe
        if column_name not in col_labels:
            st.error(f"La columna '{column_name}' no existe en la hoja.")
            return False

        # Obtener índices de columnas (base 1 para Google Sheets)
        id_col_name = "id"  # Personaliza este nombre si es necesario
        if id_col_name not in col_labels:
            st.error(f"La columna de ID '{id_col_name}' no existe en la hoja.")
            return False

        id_col_index = col_labels.index(id_col_name) + 1
        col_index = col_labels.index(column_name) + 1

        # Obtener todos los valores de la columna de ID
        id_column = worksheet.col_values(id_col_index)
        if not id_column:
            st.error(f"La columna '{id_col_name}' está vacía.")
            return False

        # Buscar la fila correspondiente al ID
        id_value_str = str(id_value)  # Convertir a string para búsqueda consistente
        try:
            row_index = id_column.index(id_value_str) + 1  # +1 porque Google Sheets usa base 1
        except ValueError:
            st.error(f"ID '{id_value}' no encontrado en la columna '{id_col_name}'.")
            return False

        # Actualizar la celda
        worksheet.update_cell(row_index, col_index, new_value)
        return True

    except Exception as e:
        st.error(f"Error al guardar los datos: {e}")
        return False



def load_data_vendedores(url):
    df=pd.read_excel(url,engine='openpyxl')
    if st.session_state['user_data']['permisos'].iloc[0]!='admin':
        df=df[df['vendedor']==st.session_state['usuario']]
    return df
def load_data1(url):
    return pd.read_csv(url)

def delete(index):#borra una fila completa y acomoda el resto de la hoja para que no quede el espacio en blanco
    delete_data(index,st.secrets['ids']['clientes'])
def save(id,column,data):#modifica un solo dato
    save_data(id,column,data,st.secrets['ids']['clientes'])
def new(data):#añade una columna entera de datos
    append_data(data,st.secrets['ids']['clientes'])




st.session_state['usuarios']=load_data1(st.secrets['urls']['usuarios'])


def guardar_log(usuario):

    worksheet = get_worksheet(st.secrets['ids']['logs'])

    # Obtener la cantidad de filas actuales para generar el índice numérico
    existing_data = worksheet.get_all_values()
    index = len(existing_data)  # Nueva fila será una más que las actuales

    # Obtener la fecha y hora actual
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    # Crear las filas con la estructura: [Fecha, Usuario, Índice, Valores...]
    row_old = [timestamp, str(usuario), str(index)]

    # Agregar ambas filas a la hoja
    worksheet.append_row(row_old)



# Validación simple de usuario y clave con un archivo CSV
def validarUsuario(usuario, clave):
    st.session_state['usuarios']=load_data1(st.secrets['urls']['usuarios'])
    """
    Permite la validación de usuario y clave.
    :param usuario: Usuario ingresado
    :param clave: Clave ingresada
    :return: True si el usuario y clave son válidos, False en caso contrario
    """
    try:
        dfusuarios = st.session_state['usuarios']  # Carga el archivo CSV
        # Verifica si existe un usuario y clave que coincidan
        if len(dfusuarios[(dfusuarios['usuario'] == usuario) & (dfusuarios['clave'] == clave)]) > 0:
            guardar_log(usuario)  # Registrar el inicio de sesión en logs
            return True
    except FileNotFoundError:
        st.error("El archivo 'usuarios.csv' no se encontró.")
    except Exception as e:
        st.error(f"Error al validar usuario: {e}")
    return False

def generarMenu(usuario,permiso):
    st.session_state['usuarios']=load_data1(st.secrets['urls']['usuarios'])
    """
    Genera el menú en la barra lateral dependiendo del usuario.
    :param usuario: Usuario autenticado
    """
    with st.sidebar:
        try:
            dfusuarios = st.session_state['usuarios']
            dfUsuario = dfusuarios[dfusuarios['usuario'] == usuario]
            nombre = dfUsuario['nombre'].iloc[0]

            # Bienvenida al usuario
            st.write(f"### Bienvenido/a, **{nombre}**")
            st.divider()
            st.page_link("pages/clientes.py", label="Clientes", icon=":material/sell:")
            st.page_link("pages/prestamos.py", label="Préstamos", icon=":material/sell:")

            # Administración
            if permiso=='admin':
                st.page_link('pages/reporte_general.py', label="Reporte General", icon=":material/group:")

            # Botón de cierre de sesión
            if st.button("Salir"):
                del st.session_state['usuario']
                st.switch_page('inicio.py')
                

        except FileNotFoundError:
            st.error("El archivo 'usuarios.csv' no se encontró.")
        except Exception as e:
            st.error(f"Error al generar el menú: {e}")


from datetime import datetime

def historial(old_values, new_values):
    """
    Registra en una hoja de Google Sheets un cambio en los datos.

    :param old_values: Lista con los valores anteriores.
    :param new_values: Lista con los valores nuevos.
    """
    worksheet = get_worksheet(st.secrets['ids']['historial'])

    # Obtener la cantidad de filas actuales para generar el índice numérico
    existing_data = worksheet.get_all_values()
    index = len(existing_data)  # Nueva fila será una más que las actuales

    # Obtener la fecha y hora actual
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    # Obtener el usuario actual
    usuario = st.session_state.get("usuario", "Desconocido")

    # Crear las filas con la estructura: [Fecha, Usuario, Índice, Valores...]
    row_old = [timestamp, usuario, index] + old_values
    row_new = [timestamp, usuario, index + 1] + new_values

    # Agregar ambas filas a la hoja
    worksheet.append_row(row_old)
    worksheet.append_row(row_new)


def generarLogin():
    # Ocultar el menú y el pie de página de Streamlit
    hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    st.session_state['usuarios'] = load_data1(st.secrets['urls']['usuarios'])
    usuarios = st.session_state['usuarios']

    if 'usuario' in st.session_state:
        generarMenu(st.session_state['usuario'], st.session_state['user_data']['permisos'].iloc[0])
    else:
        try:
            with st.form('frmLogin'):
                parUsuario = st.text_input('Usuario')
                parPassword = st.text_input('Password', type='password')
                if st.form_submit_button('Ingresar'):
                    if validarUsuario(parUsuario, parPassword):
                        st.session_state['usuario'] = parUsuario
                        usuario = usuarios[usuarios['usuario'] == st.session_state['usuario']]
                        st.session_state['user_data'] = usuario
                        st.switch_page('inicio.py')
                    else:
                        st.error("Usuario o clave inválidos")
        except:
            st.switch_page('inicio.py')


from datetime import datetime,date

def cargar_clientes(forzado=False):
    try:
        if forzado==True:
            st.session_state["clientes"] = load_data_vendedores(st.secrets['urls']['clientes'])
            st.session_state["cobranzas"] = load_data_vendedores(st.secrets['urls']['cobranzas'])
            st.session_state["prestamos"] = load_data_vendedores(st.secrets['urls']['prestamos'])
        else:
            if "clientes" not in st.session_state:
                st.session_state["clientes"] = load_data_vendedores(st.secrets['urls']['clientes'])
            if "cobranzas" not in st.session_state:
                st.session_state["cobranzas"] = load_data_vendedores(st.secrets['urls']['cobranzas'])
            if "prestamos" not in st.session_state:
                st.session_state["prestamos"] = load_data_vendedores(st.secrets['urls']['prestamos'])
    except:
        pass


def cargar_reportes(forzado=False):
    try:
        if forzado==True:
            st.session_state["mov"] = load_data(st.secrets['urls']['flujo_caja'])
            st.session_state['repo_cobranzas']=load_data(st.secrets['urls']['repo_cobranzas'])
            st.session_state['comisiones']=load_data(st.secrets['urls']['repo_comision'])
            st.session_state["repo_mensual"] = load_data(st.secrets['urls']['repo_mensual'])
            st.session_state["morosos"] = load_data(st.secrets['urls']['repo_morosos'])
            st.session_state['repo_ventas']=load_data(st.secrets['urls']['repo_ventas'])       
        else:
            if "mov" not in st.session_state:
                st.session_state["mov"] = load_data(st.secrets['urls']['flujo_caja'])
            if 'repo_cobranzas' not in st.session_state:
                st.session_state['repo_cobranzas']=load_data(st.secrets['urls']['repo_cobranzas'])
            if 'comisiones' not in st.session_state:
                st.session_state['comisiones']=load_data(st.secrets['urls']['repo_comision'])
            if "repo_mensual" not in st.session_state:
                st.session_state["repo_mensual"] = load_data(st.secrets['urls']['repo_mensual'])
            if "morosos" not in st.session_state:
                st.session_state["morosos"] = load_data(st.secrets['urls']['repo_morosos'])
            if 'repo_ventas' not in st.session_state:
                st.session_state['repo_ventas']=load_data(st.secrets['urls']['repo_ventas'])
    except:
        pass

import datetime as dt
# Cargar datos
idcc = st.secrets['ids']['cobranzas']
urlc = st.secrets['urls']['cobranzas']
vendedores =['']
for vendedor in st.session_state['usuarios']['usuario'].tolist():
    vendedores.append(vendedor)
def display_cobranzas(cobranzas_df):

    def registrar(cobranza,id):
        fecha_cobro = st.selectbox(
            'Fecha de cobro',
            ['Seleccionar fecha', 'Hoy', 'Otra fecha'],
            index=0,
            key=f"vencimientoo{id}"
        )

        fecha_cobro = (
            dt.date.today().strftime("%d-%m-%Y")
            if fecha_cobro == 'Hoy'
            else st.date_input('Fecha del cobro', key=f"cobro{id}").strftime("%d-%m-%Y")
            if fecha_cobro == 'Otra fecha'
            else None
        )

        cobranza['monto_recalculado_mora'] = float(cobranza['monto_recalculado_mora'])
        cobranza['monto'] = float(cobranza['monto'])


        if "init" not in st.session_state:
            monto=0
            st.session_state["init"]=0
        def show1():
            st.session_state["init"]=1
        col1,col2=st.columns(2)
        with col1:
            monto = st.number_input(
                    "Monto",
                    min_value=0,
                    value=0,
                    step=1000,
                    key=f"monto_{id}"
                ,on_change=show1)
        with col1:
            if st.session_state['init']==1:
                st.write(f"${monto:,.0f}")
        with col2:   
            medio_pago = st.selectbox(
            'Medio de pago', 
            ['Seleccione una opción', 'Efectivo', 'Transferencia', 'Mixto'], 
            key=f"medio_{id}"
            )
            
        registro = 'Pago total' if monto >= cobranza['monto_recalculado_mora'] else 'Pago parcial'
        if fecha_cobro!='Seleccionar fecha' and medio_pago!='Seleccione una opción' :
            with st.form(f"registrar_pago{id}"):
                cobrador = st.selectbox('Cobrador', vendedores,placeholder='', key=f"cobradores_{id}")
                obs = st.text_input('Observación', key=f'observacion_{id}')
                submit_button = st.form_submit_button("Registrar")

            if submit_button:
                cobranza['vencimiento'] = str(cobranza['vencimiento'])
                campos = [
                    ('cobrador', cobrador),
                    ('pago', monto),
                    ('estado', registro),
                    ('medio de pago', medio_pago),
                    ('fecha_cobro', fecha_cobro),
                    ('obs', obs)]
                
                for campo, valor in campos:
                    save_nuevo(cobranza['id'], campo, valor,st.secrets['ids']['cobranzas'])
                cargar_clientes(forzado=True)
                st.rerun()


    cobranzas_df['vencimiento_str']=pd.to_datetime(cobranzas_df['vencimiento'], format='%d-%m-%Y').dt.strftime('%d-%m-%Y')
    # At the beginning of display_cobranzas function, add:
    cobranzas_df['fecha_cobro'] = pd.to_datetime(cobranzas_df['fecha_cobro'], format='%d-%m-%Y', errors='coerce')
    def display_table():
        df=cobranzas_df
        # Crear una copia del DataFrame original  
        with st.container(border=True): 
            if not df.empty:
                for idx, row in df.iterrows():
                    with st.container(border=True):
                        col1, col2, col3, col4, col5 = st.columns(5)

                        with col1:
                            st.write(f"**Cliente**: \n",unsafe_allow_html=True)
                            st.write(f"{row['nombre']}")
                            st.write(f"**Vencimiento**:")
                            st.write(f"{row['vencimiento_str']}")
                        
                        with col2:
                            st.write(f"**Cuota**: {row['n_cuota']}")
                            st.write(f"**Estado**: \n", unsafe_allow_html=True)
                            st.write(f"{row['estado']}")
                        with col3:
                            st.write(f"**Amortización**: ${float(row['amortizacion']):,.0f}")
                            st.write(f"**Intereses**: ${float(row['intereses']):,.0f}")
                            st.write(f"**IVA**: ${float(row['iva']):,.0f}")
                        with col4:
                            if not(row['estado'] in ['Pendiente de Pago','En mora']):
                                st.write(f"**Cobrador**: {row['cobrador']}")
                                st.write(f"**Monto Pago**: ${float(row['pago']):,.0f}")
                                st.markdown(f"**Fecha del pago**: \n", unsafe_allow_html=True)
                                # Format the date correctly
                                if pd.notna(row['fecha_cobro']):
                                    formatted_date = row['fecha_cobro'].strftime('%d-%m-%Y')
                                    st.write(formatted_date)
                                else:
                                    st.write("No registrada")

                        with col5:
                            st.markdown(f"**Monto**: ${float(row['monto']):,.0f}\n", unsafe_allow_html=True)
                            with st.expander('Actualizar: '):
                                with st.popover('Registrar pago'):
                                    registrar(row,idx)
            else:
                st.warning("No se encontraron resultados.")
    display_table()

def append_data2(df, sheet_id):
    """Añade un DataFrame a Google Sheets."""
    worksheet = get_worksheet(sheet_id)
    # Convertir DataFrame a lista de listas
    values = df.values.tolist()
    # Si la hoja está vacía, añadir encabezados
    if worksheet.row_count == 1 and worksheet.col_count == 1:
        worksheet.append_row(df.columns.tolist())
    # Añadir todas las filas
    worksheet.append_rows(values)
def delete_data2(id_to_delete, sheet_id):
    """
    Elimina una fila de Google Sheets basada en el ID, sin importar el orden de los IDs.
    
    :param id_to_delete: ID a buscar para eliminar la fila correspondiente.
    :param sheet_id: ID de la hoja de cálculo en Google Sheets.
    :return: Mensaje de confirmación o error.
    """
    try:
        # Obtener la hoja de trabajo
        worksheet = get_worksheet(sheet_id)
        
        # Obtener todos los datos
        data = worksheet.get_all_records()
        
        # Verificar si hay datos
        if not data:
            return "Error: No hay datos en la hoja"
        
        # Verificar si el ID existe en las columnas
        if 'id' not in data[0]:
            return "Error: La columna 'id' no existe en la hoja"
        
        # Encontrar el índice de la fila a eliminar
        row_to_delete = None
        for i, row in enumerate(data):
            # Convertir ambos a string para comparar
            if str(row['id']) == str(id_to_delete):
                # +2 porque en Google Sheets, la primera fila es 1 (no 0) y hay encabezados
                row_to_delete = i + 2
                break
        
        if row_to_delete is None:
            return f"Error: No se encontró el ID {id_to_delete}"
        
        # Eliminar la fila
        worksheet.delete_rows(row_to_delete)
        
        return f"Fila con ID {id_to_delete} eliminada exitosamente"
    
    except Exception as e:
        return f"Error al eliminar datos: {str(e)}"
def finalizar(id):
    try:
        # Cargar y filtrar cobranzas desde Excel
        cobranzas = load_data(st.secrets['urls']['cobranzas'])
        cobranzas = cobranzas[cobranzas['prestamo_id'] == id]
        
        if not cobranzas.empty:
            # Formatear fechas
            cobranzas['vencimiento'] = cobranzas['vencimiento'].apply(
                lambda x: x.strftime('%d-%m-%Y') if pd.notna(x) and hasattr(x, 'strftime') else str(x)
            )
            cobranzas['fecha_cobro'] = cobranzas['fecha_cobro'].apply(
                lambda x: x.strftime('%d-%m-%Y') if pd.notna(x) and hasattr(x, 'strftime') else str(x)
            )
            
            # Lista de columnas numéricas únicas para convertir a string
            numeric_columns = [
                'entregado', 'tnm', 'cantidad de cuotas', 'n_cuota',
                'monto', 'dias_mora', 'mora', 'discrepancia',
                'capital', 'cuota pura', 'intereses',
                'amortizacion', 'iva', 'monto_recalculado_mora'
            ]
            
            # Convertir columnas numéricas a string
            for col in numeric_columns:
                if col in cobranzas.columns:
                    cobranzas[col] = cobranzas[col].astype(str)
            
            # Reemplazar NaN con string vacío
            cobranzas = cobranzas.fillna('')
            
            # Preparar datos para exportar
            export_data = cobranzas.drop(columns=['id', 'prestamo_id','estado'], axis=1, errors='ignore')
            
            # Añadir a finalizados (asumiendo que debería ser append_data)
            append_data2(export_data, st.secrets['ids']['finalizados'])
            
            # Eliminar de préstamos
            delete_result = delete_data(id, st.secrets['ids']['prestamos'])
            if "Error" in delete_result:
                st.error(f"Error al eliminar préstamo: {delete_result}")
                return
            
            # Eliminar cada cobranza
            for idx, row in cobranzas.iterrows():
                delete_result = delete_data2(row['id'], st.secrets['ids']['cobranzas'])
                if "Error" in delete_result:
                    st.error(f"Error al eliminar cobranza {row['id']}: {delete_result}")
                    return
            st.switch_page("pages/prestamos.py")
            st.session_state['credito']=None
            cargar_clientes(forzado=True)
            st.success("Proceso completado exitosamente")
        else:
            st.warning('No se encontraron las cobranzas correspondientes, revisar excel')
            
    except Exception as e:
        st.error(f"Error en el proceso: {str(e)}")
        st.warning('No se pudo exportar al excel de finalizados, intente de nuevo o exporte manualmente')

def filter_valid_dates(df):
    """
    Filtra un DataFrame para mantener solo filas con fechas válidas en 'vencimiento' y 'fecha_cobro'
    en formato '%d-%m-%Y'.
    
    Args:
        df: DataFrame con columnas 'vencimiento' y 'fecha_cobro'
    
    Returns:
        DataFrame filtrado
    """
    # Convertir las columnas a string para asegurar consistencia
    df['fecha_cobro'] = df['fecha_cobro'].astype(str)
    
    # Función para validar fechas
    def is_valid_date(date_str):
        date_str = date_str.strip()  # Eliminar espacios en blanco
        if date_str == '' or date_str.lower() == 'nan':  # Manejar vacíos y 'nan'
            return False
        try:
            datetime.strptime(date_str, '%d-%m-%Y')
            return True
        except ValueError:
            return False
    
    # Crear la máscara y filtrar
    mask = (df['fecha_cobro'].apply(is_valid_date))
    
    return df[mask]