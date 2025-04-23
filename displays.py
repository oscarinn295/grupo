
def display_cobranzas(cobranzas_df):
    import datetime as dt
    # Cargar datos
    idcc = st.secrets['ids']['cobranzas']
    urlc = st.secrets['urls']['cobranzas']
    vendedores =['']
    for vendedor in st.session_state['usuarios']['usuario'].tolist():
        vendedores.append(vendedor)

    def save(id,column,data):#modifica un solo dato
        save_cobb(id,column,data,idcc)

    def ingreso(cobranza,descripcion):
        st.session_state["mov"]=load_data(st.secrets['urls']['flujo_caja'])
        caja=st.session_state["mov"]
        caja['saldo'] = pd.to_numeric(caja['saldo'], errors='coerce')
        saldo_total = caja['saldo'].sum() if not caja['saldo'].isnull().all() else 0
        mov = [
            dt.date.today().strftime("%d-%m-%Y"),
            f"COBRANZA CUOTA NRO: {cobranza['n_cuota']}, {descripcion}",
            cobranza['pago'],
            0,
            cobranza['pago'],
            saldo_total + cobranza['pago']
        ]
        append_data(mov,st.secrets['ids']['flujo_caja'])


    def registrar(cobranza):
        fecha_cobro = st.selectbox(
            'Fecha de cobro',
            ['Seleccionar fecha', 'Hoy', 'Otra fecha'],
            index=0,
            key=f"vencimientoo{cobranza['id']}"
        )

        fecha_cobro = (
            dt.date.today().strftime("%d-%m-%Y")
            if fecha_cobro == 'Hoy'
            else st.date_input('Fecha del cobro', key=f"cobro{cobranza['id']}").strftime("%d-%m-%Y")
            if fecha_cobro == 'Otra fecha'
            else None
        )

        cobranza['monto_recalculado_mora'] = float(cobranza['monto_recalculado_mora'])
        cobranza['monto'] = float(cobranza['monto'])

        pago = st.selectbox(
            'Monto',
            ['Pago', "Pago total", 'Otro monto'],
            index=0,
            key=f"pago{cobranza['id']}"
        )
        if "init" not in st.session_state:
            monto=0
            st.session_state["init"]=0
        def show1():
            st.session_state["init"]=1
        col1,col2=st.columns(2)
        with col1:
            monto = (
                cobranza['monto_recalculado_mora']
                if pago == "Pago total"
                else st.number_input(
                    "Monto",
                    min_value=0,
                    value=0,
                    step=1000,
                    key=f"monto_{cobranza['id']}"
                ,on_change=show1)
                if pago == 'Otro monto'
                else 0
            )
        with col2:
            if st.session_state['init']==1:
                st.write(f"${monto:,.0f}")

            medio_pago = st.selectbox(
            'Medio de pago', 
            ['Seleccione una opción', 'Efectivo', 'Transferencia', 'Mixto'], 
            key=f"medio_{cobranza['id']}"
            )
            
        registro = 'Pago total' if monto >= cobranza['monto_recalculado_mora'] else 'Pago parcial'


        with st.form(f"registrar_pago{cobranza['id']}"):
            cobrador = st.selectbox('Cobrador', vendedores,placeholder='', key=f"cobradores_{cobranza['id']}")
            obs = st.text_input('Observación', key=f'observacion_{cobranza["id"]}')
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
                save(cobranza['id'], campo, valor)
            cargar_clientes(forzado=True) 
            st.rerun()



    def registrar_moroso(cobranza):
        morosos=load_data(st.secrets['urls']['repo_morosos'])
        int(st.session_state['cobranzas']['id'].max())
        moroso=[
                int(morosos['id'].max()),
                cobranza['nombre'],
                st.session_state['clientes'][st.session_state['clientes']['nombre']==cobranza['nombre']]['dni'],
                cobranza['n_cuota'],
                cobranza['monto'],
                cobranza['monto_recalculado_mora'],
                cobranza['dias_mora'],
                cobranza['mora']
            ]
        append_data(moroso,st.secrets['ids']['repo_morosos'])

    def no_abono(cobranza):
        import numpy as np
        with st.form(f'no abono{cobranza['id']}'):
            st.text_input('obs',key=f"no abono_{cobranza['id']}")
            submit_button=st.form_submit_button('registrar')
        if submit_button:
            cobranza['vencimiento'] = str(cobranza['vencimiento'])
            cobranza = cobranza.replace({np.nan: ""}) 
            save(cobranza['id'],'estado','En mora')
            st.session_state['cobranzas']=load_data(urlc)
            cobranza.fillna('')

    st.session_state['cobranzas']['id'] = pd.to_numeric(st.session_state['cobranzas']['id'], errors='coerce').astype('Int64')

    cobranzas_df['vencimiento']=cobranzas_df['vencimiento'].dt.strftime('%d-%m-%Y')
    def display_table():
        df=cobranzas_df
        # Crear una copia del DataFrame original  
        with st.container(border=True): 
            if not df.empty:
                for idx, row in df.iterrows():
                    with st.container(border=True):
                        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)

                        with col1:
                            st.write(f"**Vencimiento**:")
                            st.write(f"{row['vencimiento']}")
                        
                        with col2:
                            st.write(f"**Vendedor**: {row['vendedor']}")
                            st.write(f"**Cliente**: \n",unsafe_allow_html=True)
                            st.write(f"{row['nombre']}")

                        with col3:
                            st.write(f"**Cuota**: {row['n_cuota']}")
                            st.write(f"**Monto**: ${float(row['monto']):,.0f}")

                        with col4:
                            st.write(f"**Amortización**: ${float(row['amortizacion']):,.0f}")
                            st.write(f"**Intereses**: ${float(row['intereses']):,.0f}")
                            st.write(f"**IVA**: ${float(row['iva']):,.0f}")

                        with col5:
                            if row['estado']!='Pendiente de pago':
                                st.write(f"**Dias de mora**: {row['dias_mora']}")
                                st.write(f"**Monto a pagar**: ${row['monto_recalculado_mora']:,.0f}")

                        with col6:
                            if not(row['estado'] in ['Pendiente de Pago','En mora']):
                                st.write(f"**Monto Pago**: ${float(row['pago']):,.0f}")
                                st.write(f"**Fecha del pago**: {row['fecha_cobro']}")
                        with col7:
                            st.write(f"**Estado**: \n", unsafe_allow_html=True)
                            st.write(f"{row['estado']}")

                        with col8:
                            with st.expander('Actualizar: '):
                                with st.popover('Registrar pago'):
                                    registrar(row)
                                with st.popover('No abonó'):
                                    no_abono(row)
            else:
                st.warning("No se encontraron resultados.")
    display_table()


