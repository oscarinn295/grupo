import streamlit as st
import login
import datetime as dt
import pandas as pd

# Verificación de sesión y redirección
if 'usuario' not in st.session_state:
    st.switch_page('inicio.py')

# Módulo de login
login.generarLogin()

# Título de la página
st.title('Reporte general')

# Carga de datos y manejo de errores
try:
    login.cargar_clientes()
    prestamos = st.session_state.get('prestamos', pd.DataFrame())
    clientes = st.session_state.get('clientes', pd.DataFrame())
    cobranzas = st.session_state.get('cobranzas', pd.DataFrame())
    usuarios = st.session_state.get('usuarios', pd.DataFrame())
    
    if any(df.empty for df in [prestamos, clientes, cobranzas, usuarios]):
        st.error("No se pudieron cargar todos los datos necesarios.")
        st.stop()
    
    # Preprocesamiento de tipos de datos
    for df, col, dtype in [
        (cobranzas, 'amortizacion', float),
        (cobranzas, 'pago', float),
        (cobranzas, 'intereses', float),
        (cobranzas, 'iva', float),
        (cobranzas, 'vencimiento', 'datetime64[ns]'),
        (prestamos, 'fecha', 'datetime64[ns]'),
        (cobranzas, 'fecha_cobro', 'datetime64[ns]')
    ]:
        df[col] = pd.to_numeric(df[col], errors='coerce') if dtype == float else pd.to_datetime(df[col], format='%d-%m-%Y', errors='coerce')

except Exception as e:
    st.error(f"Error al cargar o procesar datos: {str(e)}")
    st.stop()

# Métricas clave
prestamos_activos = prestamos[prestamos['estado'] == 'liquidado']
prestamos_vigentes = prestamos_activos.shape[0]
moras = cobranzas[cobranzas['estado'] == 'En mora']
cartones_morosos = prestamos[prestamos['id'].isin(moras['prestamo_id'].unique())]
morosos = clientes[clientes['nombre'].isin(cartones_morosos['nombre'].unique())]

# Dashboard de métricas
col1, col2 = st.columns(2)
with col1:
    st.metric("Préstamos vigentes", prestamos_vigentes)

# Análisis por vendedor
vendedores = ['johnny', 'david', 'guillermo', 'francisco']
df_vendedores = pd.DataFrame({
    'Vendedor': vendedores,
    'Clientes': [clientes[clientes['vendedor'] == v].shape[0] for v in vendedores],
    'Préstamos': [prestamos[prestamos['vendedor'] == v].shape[0] for v in vendedores],
    'Morosos': [morosos[morosos['vendedor'] == v].shape[0] for v in vendedores]
})
with st.container(border=True):
    st.subheader('Datos por vendedor')
    st.dataframe(df_vendedores, use_container_width=True)

# Preparación de datos de cobranzas totales
df2 = login.load_data(st.secrets['urls']['finalizados'])

missing_cols = [col for col in cobranzas.columns if col not in df2.columns]
for col in missing_cols:
    df2[col] = pd.NA

df2 = login.filter_valid_dates(df2)

cobranzas_total = pd.concat([cobranzas, df2], ignore_index=True)

for col in ['amortizacion', 'pago', 'intereses', 'iva']:
    cobranzas_total[col] = pd.to_numeric(cobranzas_total[col], errors='coerce')
cobranzas_total['fecha_cobro'] = pd.to_datetime(cobranzas_total['fecha_cobro'], format='%d-%m-%Y', errors='coerce')

# Configuración del calendario de cobros
st.subheader("Calendario de Cobros")
current_year = dt.date.today().year
current_month = dt.date.today().month

with st.container(border=True):
    st.write("### Filtros")
    col1, col2 = st.columns(2)
    with col1:
        selected_month = st.selectbox("Mes", range(1, 13), index=current_month-1)
        selected_year = st.selectbox("Año", [2024, 2025], index=0 if current_year == 2024 else 1)
    with col2:
        aplicar_fecha = st.checkbox("Filtrar por rango de fechas")
        if aplicar_fecha:
            desde = st.date_input("Desde", value=dt.date.today())
            hasta = st.date_input("Hasta", value=dt.date.today())
        else:
            desde, hasta = None, None
        reset = st.button("Resetear filtros")

# Aplicar filtros
cobranzas_valid = cobranzas_total.dropna(subset=['fecha_cobro'])
cobranzas_filtrado = cobranzas_valid.copy()
if not reset and aplicar_fecha and desde and hasta:
    cobranzas_filtrado = cobranzas_filtrado[
        (cobranzas_filtrado['fecha_cobro'] >= pd.Timestamp(desde)) &
        (cobranzas_filtrado['fecha_cobro'] <= pd.Timestamp(hasta))
    ]
    
# Determinar datos para tabla y métricas
if aplicar_fecha and desde and hasta:
    month_data = cobranzas_filtrado
else:
    month_data = cobranzas_valid[
        (cobranzas_valid['fecha_cobro'].dt.month == selected_month) &
        (cobranzas_valid['fecha_cobro'].dt.year == selected_year)
    ]

# Layout de calendario y filtros
col_filtros, col_calendario = st.columns(2)

with col_calendario:
    def create_payment_calendar(df_data, month, year):
        month_data = df_data[
            (df_data['fecha_cobro'].dt.month == month) &
            (df_data['fecha_cobro'].dt.year == year)
        ]
        payment_counts = month_data['fecha_cobro'].dt.day.value_counts().to_dict()
        last_day = pd.Timestamp(year=year, month=month, day=1) + pd.offsets.MonthEnd(1)
        num_days = last_day.day
        first_day = pd.Timestamp(year=year, month=month, day=1).weekday()
        
        month_names = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                       7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
        st.write(f"### Cobros - {month_names[month]} {year}")
        
        cols = st.columns(7)
        for i, day in enumerate(["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]):
            cols[i].markdown(f"<div style='text-align: center; font-weight: bold;'>{day}</div>", unsafe_allow_html=True)
        
        day = 1
        for week in range(6):
            cols = st.columns(7)
            for i in range(7):
                if week == 0 and i < first_day:
                    cols[i].write("")
                    continue
                if day > num_days:
                    break
                count = payment_counts.get(day, 0)
                bg_color = "#f0f0f0" if count == 0 else "#cce5ff" if count <= 3 else "#6699cc" if count <= 5 else "#0056b3"
                text_color = "#333333" if count == 0 else "#0056b3" if count <= 3 else "#ffffff"
                cols[i].markdown(
                    f"<div style='background-color: {bg_color}; color: {text_color}; border-radius: 5px; padding: 10px; text-align: center; border: 1px solid #ddd;'>"
                    f"<div style='font-weight: bold;'>{day}</div><div>{count} cobros</div></div>",
                    unsafe_allow_html=True
                )
                day += 1
            if day > num_days:
                break
    
    create_payment_calendar(cobranzas_total, selected_month, selected_year)

with col_filtros:
    st.write("### Datos Filtrados")
    display_data = month_data.copy()
    display_data['fecha_cobro'] = display_data['fecha_cobro'].dt.strftime('%d-%m-%Y')
    st.dataframe(display_data[['nombre', 'vendedor', 'n_cuota', 'fecha_cobro', 'pago', 'amortizacion', 'intereses', 'iva']], use_container_width=True)

# Resumen de métricas
with st.container(border=True):
    total_cobros = len(month_data)
    total_pago = month_data['pago'].sum()
    total_amortizaciones = month_data['amortizacion'].sum()
    total_intereses = month_data['intereses'].sum()
    total_iva = month_data['iva'].sum()


    prestamos_filtrado=prestamos[
        (prestamos['fecha']>= pd.Timestamp(desde)) &
        (prestamos['fecha']<= pd.Timestamp(hasta))
    ]
    prestamos_guillermo=prestamos_filtrado[prestamos_filtrado['vendedor']=='guillermo']
    prestamos_francisco=prestamos_filtrado[prestamos_filtrado['vendedor']=='francisco']
    prestamos_johnny=prestamos_filtrado[prestamos_filtrado['vendedor']=='johnny']
    prestamos_david=prestamos_filtrado[prestamos_filtrado['vendedor']=='david']
    creditos_per_vendedor=pd.DataFrame(columns=['vendedor','cantidad de creditos'])
    creditos_per_vendedor['vendedor']=pd.Series(['guillermo','francisco','david','johnny'])
    creditos_per_vendedor['cantidad de creditos']=pd.Series([prestamos_guillermo.shape[0], prestamos_francisco.shape[0], prestamos_david.shape[0], prestamos_johnny.shape[0]])
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.subheader("Resumen de cobranzas")
        st.subheader("Resumen de ventas")
    with col2:
        st.markdown(f"De {total_cobros} cobros recaudado: ${total_pago:,.2f} \n",unsafe_allow_html=True)
        st.write(f"De {creditos_per_vendedor['cantidad de creditos'].sum()} se entrego: ${prestamos_filtrado['capital'].sum()}")
    with col3:
        st.markdown(f"Amortizaciones: ${total_amortizaciones:,.2f}\n",unsafe_allow_html=True)
        st.dataframe(creditos_per_vendedor)
    with col4:
        st.markdown(f"Intereses : ${total_intereses:,.2f}\n",unsafe_allow_html=True)
    with col5:
        st.markdown(f"IVA: ${total_iva:,.2f}\n",unsafe_allow_html=True)