import pandas as pd
import login
import streamlit as st

if 'usuario' not in st.session_state:
    st.switch_page('inicio.py')
login.cargar_clientes()
idc=st.secrets['ids']['clientes']
url = st.secrets['urls']['clientes']
st.session_state['cliente']=None


def load():
    return login.load_data(url)

def save(id,column,data):#modifica un solo dato
    login.save_data(id,column,data,idc)
    
def new(data):#añade una fila entera de datos
    login.append_data(data,idc)
login.generarMenu1()
st.session_state['clientes']=load() 

cobranzas=st.session_state['cobranzas']
prestamos=st.session_state['prestamos']
vendedores=st.session_state['usuarios']['usuario'].tolist()


if 'pagina_actual' not in st.session_state:
    st.session_state['pagina_actual'] = 1


# Función para mostrar la tabla con filtro de búsqueda
from datetime import date
def editar(cliente):
    idx=cliente['id']
    col1,col2,col3,col4=st.columns(4)
    with col1:
        st.subheader("Editar Cliente: ")
    with st.form(f'editar_cliente_{cliente['id']}'):
        st.session_state["dni"] = cliente["dni"]
        st.session_state["nombre"] = cliente["nombre"]
        st.session_state["direccion"] = cliente["direccion"]
        st.session_state["celular"] = cliente["celular"]
        st.session_state["vendedor"] = cliente["vendedor"]
        st.session_state['scoring']= cliente['scoring']
        if cliente['fecha_nac'] is not None:
            st.session_state['fecha_nac']=cliente['fecha_nac']
        else:
            st.session_state['fecha_nac']=date.today().strftime('%d/%m/%Y')
        st.session_state['mail']=cliente['mail']

        col1,col2=st.columns(2)
        with col1:
            dni = st.text_input("DNI", value=st.session_state.get("dni", ""),key=f'dni_{idx}')
            nombre = st.text_input("Nombre", value=st.session_state.get("nombre", ""),key=f'nombre_{idx}')
            if isinstance(st.session_state['fecha_nac'], str):
                try:
                    fecha_nac_value = pd.to_datetime(st.session_state['fecha_nac'], format="%d/%m/%Y")
                except Exception:
                    fecha_nac_value = None
            else:
                fecha_nac_value = st.session_state['fecha_nac']

            fecha_nac = st.date_input("Fecha", value=fecha_nac_value if fecha_nac_value and not pd.isna(fecha_nac_value) else date.today(), key=f'fecha_{idx}')
            vendedor=st.selectbox('vendedor',vendedores,key=f'vendedor_{idx}')
        with col2:
            direccion = st.text_input("Dirección", value=st.session_state.get("direccion", ""),key=f'direccion_{idx}')
            celular = st.text_input("Celular", value=st.session_state.get("celular", ""),key=f'celular_{idx}')
            mail=st.text_input("Mail", value=st.session_state.get("mail", ""),key=f'mail_{idx}')
            scoring= st.text_input("Scoring", value=st.session_state.get("scoring", ""),key=f'scoring_{idx}')
        submit_button=st.form_submit_button('guardar')
    if submit_button:
        datos= [(nombre,'nombre'),
                (vendedor,'vendedor'),
                (scoring,'scoring'),
                (direccion,'direccion'),
                (fecha_nac.strftime("%d-%m-%Y"), 'fecha_nac'),
                (dni,'dni'),
                (celular,'celular'),
                (mail,'mail')]
        for dato,col in datos:
            save(idx,col,dato)
            login.cargar_clientes(forzado=True)
        st.success("cambios guardados")

def crear():
    st.title('Crear Cliente: ')
    with st.form("form_crear_cliente"):
        col1, col2 = st.columns(2)
        
        with col1:
            dni = st.text_input("DNI")
            nombre = st.text_input("Apellido y Nombre")
            fecha_nac = st.date_input("Fecha",format="DD/MM/YYYY")
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
                max(st.session_state['clientes']['id'])+1,
                nombre,
                vendedor,
                scoring,
                direccion,
                fecha_nac.strftime("%d-%m-%Y"),
                dni,
                celular,
                mail
            ]
            new(nuevo_cliente)
            login.cargar_clientes(forzado=True)
            st.success('Cliente guardado correctamente')
            login.historial(['id','nombre','vendedor', 'scoring', 'direccion', 'fecha_nac', 'dni', 'celular', 'mail'],nuevo_cliente)

def display_table():
    df = st.session_state['clientes']
    lista = ['seleccione un cliente']
    for nombre in df['nombre'].values.tolist():
        lista.append(nombre)
    
    nombre_cliente = st.selectbox('Cliente', lista, index=0)
    if nombre_cliente != 'seleccione un cliente':
        df = df[df['nombre'] == nombre_cliente]
    lista2 = ['seleccione un vendedor']

    for nombre in vendedores:
        lista2.append(nombre)

    vendedor = st.selectbox('vendedor', lista2, index=0)
    
    if vendedor != 'seleccione un vendedor':
        st.session_state['clientes_df'] = df[df['vendedor'] == vendedor]
        df = st.session_state["clientes_df"]
    
    # Configuración de paginación
    ITEMS_POR_PAGINA = 10
    
    # Calculamos cuántos elementos mostrar en cada columna (la mitad del total por página)
    ITEMS_POR_COLUMNA = ITEMS_POR_PAGINA // 2
    
    # Paginación
    total_paginas = (len(df) // ITEMS_POR_PAGINA) + (1 if len(df) % ITEMS_POR_PAGINA > 0 else 0)
    inicio = (st.session_state['pagina_actual'] - 1) * ITEMS_POR_PAGINA
    fin = inicio + ITEMS_POR_PAGINA
    df_paginado = df.iloc[inicio:fin]
    
    # División del dataframe en dos columnas
    mitad = len(df_paginado) // 2
    if mitad == 0 and len(df_paginado) > 0:
        mitad = 1  # Asegurar al menos un elemento en la primera columna si hay datos
    
    # Crear tabla con botones, ahora en dos columnas
    if not df.empty:
        col_izquierda, col_derecha = st.columns(2)
        
        if st.session_state['user_data']['permisos'].iloc[0] == 'admin':
            # Columna izquierda
            with col_izquierda:
                for idx, row in df_paginado.iloc[:mitad].iterrows():
                    with st.container(border=True):
                        st.markdown(f"**Nombre**: {row['nombre']}\n",unsafe_allow_html=True)
                        st.markdown(f"**Dirección**: {row['direccion']}\n",unsafe_allow_html=True)
                        st.markdown(f"**Vendedor**: {row['vendedor']} - **DNI**: {row['dni']} - **Celular**: {row['celular']}",unsafe_allow_html=True)
                        if st.button("ver detalles", key=f'cliente_izq_{idx}'):
                            st.session_state['cliente'] = row
                            st.switch_page("pages/por_cliente.py")
                        with st.popover(f'✏️ Editar'):
                            editar(row)
            
            # Columna derecha
            with col_derecha:
                for idx, row in df_paginado.iloc[mitad:].iterrows():

                    with st.container(border=True):
                        st.markdown(f"**Nombre**: {row['nombre']}\n",unsafe_allow_html=True)
                        st.markdown(f"**Dirección**: {row['direccion']}\n",unsafe_allow_html=True)
                        st.markdown(f"**Vendedor**: {row['vendedor']} - **DNI**: {row['dni']} - **Celular**: {row['celular']}",unsafe_allow_html=True)
                        if st.button("ver detalles", key=f'cliente_izq_{idx}'):
                            st.session_state['cliente'] = row
                            st.switch_page("pages/por_cliente.py")
                        with st.popover(f'✏️ Editar'):
                            editar(row)
        else:
            # Columna izquierda (usuarios no admin)
            with col_izquierda:
                for idx, row in df_paginado.iloc[:mitad].iterrows():
                    with st.container(border=True):
                        st.markdown(f"**Nombre**: {row['nombre']}\n",unsafe_allow_html=True)
                        st.markdown(f"**Dirección**: {row['direccion']}\n",unsafe_allow_html=True)
                        st.markdown(f"**DNI**: {row['dni']} - **Celular**: {row['celular']}",unsafe_allow_html=True)
                        if st.button("ver detalles", key=f'cliente_izq_{idx}'):
                            st.session_state['cliente'] = row
                            st.switch_page("pages/por_cliente.py")
                        
            
            # Columna derecha (usuarios no admin)
            with col_derecha:
                for idx, row in df_paginado.iloc[mitad:].iterrows():
                    with st.container(border=True):
                        st.markdown(f"**Nombre**: {row['nombre']}\n",unsafe_allow_html=True)
                        st.markdown(f"**Dirección**: {row['direccion']}\n",unsafe_allow_html=True)
                        st.markdown(f"**DNI**: {row['dni']} - **Celular**: {row['celular']}",unsafe_allow_html=True)
                        if st.button("ver detalles", key=f'cliente_izq_{idx}'):
                            st.session_state['cliente'] = row
                            st.switch_page("pages/por_cliente.py")
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
        items_seleccionados = st.selectbox("Por página", [10, 20, 30, 50, 100], index=[10, 20, 30, 50, 100].index(ITEMS_POR_PAGINA) if ITEMS_POR_PAGINA in [10, 20, 30, 50, 100] else 0, key='seleccionados')
        if items_seleccionados != ITEMS_POR_PAGINA:
            ITEMS_POR_PAGINA = items_seleccionados
            st.session_state['pagina_actual'] = 1
            st.rerun()



# Página de lista de clientes
st.title("Clientes")
col1,col2,col3,col4=st.columns(4)
with col4:
    if st.session_state['user_data']['permisos'].iloc[0]=='admin':
        # Botón para crear un nuevo cliente
        with st.popover("Crear cliente"):
            crear()
with col1:
    # Botón para reiniciar datos
    if st.button("Reiniciar datos"):
        login.cargar_clientes(forzado=True)
with col2:
    if st.button('ver morosos'):
        st.switch_page('pages/morosos.py')
with st.container(border=True):
    display_table()
    with st.expander('Ver todos los datos'):
        st.dataframe(st.session_state["clientes"])

