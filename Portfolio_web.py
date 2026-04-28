import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px  # <-- ¡AÑADE ESTA LÍNEA!
from supabase import create_client, Client
from datetime import datetime

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Crypto Tracker", page_icon="🚀", layout="wide")

# 2. CONEXIÓN DIRECTA (Usando la caja fuerte de Streamlit)
try:
    # Ahora lee las claves ocultas en la nube
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Restaurar la sesión para no perder el login
    if 'access_token' in st.session_state and 'refresh_token' in st.session_state:
        supabase.auth.set_session(st.session_state['access_token'], st.session_state['refresh_token'])
        
    conexion_exitosa = True
except Exception as e:
    conexion_exitosa = False
    st.error(f"Error técnico o claves no encontradas: {e}")

# --- NUEVO: SISTEMA DE SESIONES Y LOGIN ---
if 'usuario' not in st.session_state:
    st.session_state['usuario'] = None

def cerrar_sesion():
    supabase.auth.sign_out()
    st.session_state['usuario'] = None
    st.session_state.pop('access_token', None)
    st.session_state.pop('refresh_token', None)

# Si no hay usuario logueado, mostramos el formulario y DETENEMOS la app
if st.session_state['usuario'] is None:
    
    # --- NUEVO DISEÑO: PANTALLA DIVIDIDA ---
    # col_izq ocupa un poco menos (1) y col_der un poco más (1.2)
    col_izq, col_der = st.columns([1, 1.2], gap="large")
    
    with col_izq:
        st.markdown("<br><br>", unsafe_allow_html=True) # Espacio para centrar verticalmente
        st.title("Inicia sesión")
        
        # 1. Fila de botones sociales (Iconos cuadrados simulados)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.button("📘", use_container_width=True, disabled=True, help="Facebook (Próximamente)")
        with c2:
            # ⚠️ IMPORTANTE: Pon aquí tu URL real de Streamlit
            url_retorno = "TU_URL_DE_STREAMLIT_AQUI" 
            if st.button("🇬", use_container_width=True, help="Continuar con Google"):
                try:
                    auth_url = supabase.auth.sign_in_with_oauth({
                        "provider": "google",
                        "options": {"redirect_to": url_retorno}
                    })
                    st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url.url}">', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error conectando con Google: {e}")
        with c3:
            st.button("🍎", use_container_width=True, disabled=True, help="Apple (Próximamente)")
        with c4:
            st.button("👾", use_container_width=True, disabled=True, help="Discord (Próximamente)")

        st.markdown("<p style='text-align: center; color: gray;'>— o —</p>", unsafe_allow_html=True)
        
        # 2. Login tradicional (He metido el registro en pestañas limpias)
        tab_login, tab_registro = st.tabs(["Ingresar", "¿No tienes cuenta? Regístrate"])
        
        with tab_login:
            email_login = st.text_input("Email", key="log_email")
            pass_login = st.text_input("Contraseña", type="password", key="log_pass")
            
            # El type="primary" hace que el botón pille el color principal de la web y destaque
            if st.button("Iniciar sesión", type="primary", use_container_width=True):
                try:
                    respuesta = supabase.auth.sign_in_with_password({"email": email_login, "password": pass_login})
                    st.session_state['usuario'] = respuesta.user
                    st.session_state['access_token'] = respuesta.session.access_token
                    st.session_state['refresh_token'] = respuesta.session.refresh_token
                    st.rerun()
                except Exception as e:
                    st.error("❌ Correo o contraseña incorrectos.")
                    
        with tab_registro:
            email_reg = st.text_input("Nuevo Email", key="reg_email")
            pass_reg = st.text_input("Contraseña (mín. 6 caracteres)", type="password", key="reg_pass")
            
            if st.button("Crear cuenta gratis", use_container_width=True):
                try:
                    supabase.auth.sign_up({"email": email_reg, "password": pass_reg})
                    st.success("✅ Cuenta creada. ¡Ve a la pestaña 'Ingresar' para entrar!")
                except Exception as e:
                    st.error(f"❌ Error al crear cuenta: {e}")

    with col_der:
        # 3. La imagen de la derecha (Puedes cambiar esta URL por la imagen que más te guste)
        imagen_crypto_url = "https://images.unsplash.com/photo-1621416894569-0f39ed31d247?q=80&w=1000&auto=format&fit=crop"
        st.image(imagen_crypto_url, use_container_width=True)
        
    st.stop() # ¡MAGIA! Esta función evita que se cargue el resto de la app
# ------------------------------------------
# ------------------------------------------

# (A partir de aquí, todo tu código original del Menú Lateral y Páginas...)

# TRUCO PRO: Añade esto justo debajo de st.sidebar.header("Menú Principal") 
# para que el usuario sepa que está logueado y pueda salir:
st.sidebar.success(f"👤 {st.session_state['usuario'].email}")
st.sidebar.button("Cerrar Sesión", on_click=cerrar_sesion)
st.sidebar.markdown("---")

# 3. MENÚ LATERAL Y DONACIONES
# (Deja el resto de tu código exactamente igual a partir de aquí)
st.sidebar.header("Menú Principal")
opcion = st.sidebar.selectbox(
    "Navegación:",
    ["🏠 Resumen General", "➕ Añadir Operación", "📊 Ver Portfolio"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("☕ Apoya este proyecto")
# Pon aquí la dirección de tu Wallet real
st.sidebar.code("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", language="text")
st.sidebar.caption("Red: Bitcoin (BTC)")

# 4. PÁGINAS PRINCIPALES

if opcion == "🏠 Resumen General":
    st.subheader("🏠 Panel de Control de Rendimiento")
    
    if not conexion_exitosa:
        st.error("No hay conexión con la base de datos.")
    else:
        try:
            # 1. Obtener datos
            respuesta = supabase.table("operaciones").select("*").order("fecha").execute()
            df_raw = pd.DataFrame(respuesta.data)
            
            if df_raw.empty:
                st.info("📭 Aún no tienes operaciones para mostrar estadísticas.")
            else:
                df_raw['fecha'] = pd.to_datetime(df_raw['fecha']).dt.tz_localize(None) # Quitar zona horaria para emparejar
                activos = df_raw['activo'].unique()
                resumen_actual = []
                
                # Para la línea temporal combinada
                fecha_inicio_global = df_raw['fecha'].min()
                fechas_mercado = pd.date_range(start=fecha_inicio_global, end=pd.Timestamp.now(), freq='D')
                df_historial_total = pd.DataFrame({'Fecha': fechas_mercado})
                df_historial_total['PnL Acumulado'] = 0.0

                with st.spinner("Descargando histórico de mercado y calculando volatilidad... ⏳"):
                    for activo in activos:
                        df_act = df_raw[df_raw['activo'] == activo]
                        fecha_primera_compra = df_act['fecha'].min()
                        
                        # --- CÁLCULO DE LA DISTRIBUCIÓN ACTUAL (DONUT) ---
                        unidades = df_act[df_act['tipo'].isin(['COMPRA', 'AIRDROP', 'STAKING'])]['cantidad'].sum() - \
                                   df_act[df_act['tipo'] == 'VENTA']['cantidad'].sum()
                        
                        # Intentar descargar histórico desde Yahoo Finance
                        historial_precios = pd.DataFrame()
                        precio_actual_activo = df_act['precio_usd'].mean() # Fallback
                        
                        try:
                            # Descargar histórico desde la primera compra
                            ticker = yf.Ticker(activo)
                            hist = ticker.history(start=fecha_primera_compra.strftime('%Y-%m-%d'))
                            if not hist.empty:
                                historial_precios = hist[['Close']].reset_index()
                                historial_precios['Date'] = pd.to_datetime(historial_precios['Date']).dt.tz_localize(None)
                                precio_actual_activo = hist['Close'].iloc[-1]
                        except Exception as e:
                            st.warning(f"No se pudo descargar el histórico de {activo}.")

                        if unidades > 0:
                            resumen_actual.append({
                                "Activo": activo,
                                "Valor Actual (USD)": unidades * precio_actual_activo
                            })

                        # --- CÁLCULO DEL HISTÓRICO CON VOLATILIDAD DIARIA ---
                        if not historial_precios.empty:
                            # Creamos un DF temporal para este activo día a día
                            df_diario_activo = pd.DataFrame({'Fecha': fechas_mercado})
                            
                            # --- LA SOLUCIÓN MAGICA AQUÍ ---
                            # Forzamos que ambas columnas de fecha tengan exactamente el mismo tipo (nanosegundos)
                            df_diario_activo['Fecha'] = df_diario_activo['Fecha'].astype('datetime64[ns]')
                            historial_precios['Date'] = historial_precios['Date'].astype('datetime64[ns]')
                            # -------------------------------
                            
                            # Mezclamos con los precios reales, rellenando los huecos
                            df_diario_activo = pd.merge_asof(
                                df_diario_activo, 
                                historial_precios, 
                                left_on='Fecha', 
                                right_on='Date', 
                                direction='backward'
                            )
                            df_diario_activo.rename(columns={'Close': 'Precio'}, inplace=True)
                            
                            # Ahora, calculamos cuántas unidades teníamos CADA DÍA y su coste
                            unidades_acumuladas = []
                            coste_acumulado = []
                            u_actual = 0.0
                            c_actual = 0.0
                            
                            for fecha in df_diario_activo['Fecha']:
                                # Operaciones hasta esa fecha
                                ops_pasadas = df_act[df_act['fecha'] <= fecha]
                                
                                # Compras hasta la fecha
                                compras = ops_pasadas[ops_pasadas['tipo'].isin(['COMPRA', 'AIRDROP', 'STAKING'])]
                                ventas = ops_pasadas[ops_pasadas['tipo'] == 'VENTA']
                                
                                u_actual = compras['cantidad'].sum() - ventas['cantidad'].sum()
                                
                                # Coste simplificado: suma de lo pagado menos (precio medio * vendidas)
                                coste_compras = (compras['cantidad'] * compras['precio_usd']).sum()
                                precio_medio = coste_compras / compras['cantidad'].sum() if compras['cantidad'].sum() > 0 else 0
                                coste_ventas = ventas['cantidad'].sum() * precio_medio
                                
                                c_actual = coste_compras - coste_ventas
                                
                                unidades_acumuladas.append(u_actual)
                                coste_acumulado.append(c_actual)
                                
                            df_diario_activo['Unidades'] = unidades_acumuladas
                            df_diario_activo['Coste'] = coste_acumulado
                            
                            # PnL Diario = (Unidades * Precio Hoy) - Coste Total
                            df_diario_activo['PnL Activo'] = (df_diario_activo['Unidades'] * df_diario_activo['Precio']) - df_diario_activo['Coste']
                            
                            # Sumamos el PnL de este activo al Total global
                            df_historial_total['PnL Acumulado'] += df_diario_activo['PnL Activo'].fillna(0)

                # --- RENDERIZADO DE GRÁFICAS ---
                st.markdown("---")
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown("##### 🍩 Distribución")
                    if resumen_actual:
                        fig_donut = px.pie(
                            pd.DataFrame(resumen_actual), 
                            values='Valor Actual (USD)', 
                            names='Activo', 
                            hole=0.6,
                            color_discrete_sequence=px.colors.qualitative.Set2
                        )
                        fig_donut.update_traces(textposition='inside', textinfo='percent+label')
                        fig_donut.update_layout(
                            margin=dict(t=10, b=10, l=10, r=10), 
                            showlegend=False,
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig_donut, use_container_width=True)
                    else:
                        st.write("Sin distribución actual.")

                with col2:
                    st.markdown("##### 📈 Evolución Histórica del PnL (USD)")
                    # Filtramos ceros iniciales antes de la primera compra
                    df_grafico = df_historial_total[df_historial_total['PnL Acumulado'] != 0.0]
                    
                    if not df_grafico.empty:
                        fig_line = px.line(
                            df_grafico, 
                            x="Fecha", 
                            y="PnL Acumulado",
                            markers=False 
                        )
                        
                        # Coloreamos según si terminamos en ganancia (verde) o pérdida (rojo)
                        color_linea = '#00e676' if df_grafico['PnL Acumulado'].iloc[-1] >= 0 else '#ff1744'
                        
                        fig_line.update_traces(line_color=color_linea, fill='tozeroy')
                        fig_line.update_layout(
                            margin=dict(t=10, b=10, l=10, r=10),
                            xaxis_title="",
                            yaxis_title="Ganancia / Pérdida ($)",
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            hovermode="x unified" 
                        )
                        st.plotly_chart(fig_line, use_container_width=True)
                    else:
                        st.write("No hay histórico suficiente para mostrar.")
                    
        except Exception as e:
            st.error(f"❌ Error visualizando el Dashboard: {e}")

elif opcion == "📊 Ver Portfolio":
    st.subheader("📊 Tu Portfolio en Vivo")
    
    if not conexion_exitosa:
        st.error("No hay conexión con la base de datos.")
    else:
        try:
            # 1. Leer los datos crudos de Supabase
            respuesta = supabase.table("operaciones").select("*").execute()
            df_raw = pd.DataFrame(respuesta.data)
            
            if not df_raw.empty:
                # 2. Motor de cálculo (Agrupar por activo)
                resumen = []
                activos = df_raw['activo'].unique()
                
                with st.spinner("Descargando precios en vivo del mercado... ⏳"):
                    for activo in activos:
                        df_activo = df_raw[df_raw['activo'] == activo]
                        
                        # Cálculos de compras
                        compras = df_activo[df_activo['tipo'] == 'COMPRA']
                        unidades_compradas = compras['cantidad'].sum()
                        coste_compras = (compras['cantidad'] * compras['precio_usd']).sum()
                        precio_medio = coste_compras / unidades_compradas if unidades_compradas > 0 else 0
                        
                        # Cálculos de ventas y extras
                        ventas = df_activo[df_activo['tipo'] == 'VENTA']
                        unidades_vendidas = ventas['cantidad'].sum()
                        ingresos_ventas = (ventas['cantidad'] * ventas['precio_usd']).sum()
                        
                        extras = df_activo[df_activo['tipo'].isin(['AIRDROP', 'STAKING'])]
                        unidades_extras = extras['cantidad'].sum()
                        
                        # Unidades actuales
                        unidades_actuales = unidades_compradas - unidades_vendidas + unidades_extras
                        
                        # Comisiones totales pagadas por este activo
                        comisiones_totales = df_activo['comision_usd'].sum()
                        
                        # PnL Realizado (Ganancia/Pérdida de lo que ya has vendido)
                        coste_de_lo_vendido = unidades_vendidas * precio_medio
                        pnl_realizado = ingresos_ventas - coste_de_lo_vendido - comisiones_totales
                        
                        if unidades_actuales > 0 or pnl_realizado != 0:
                            # 3. Descargar precio actual de Yahoo Finance
                            precio_actual = 0.0
                            try:
                                ticker = yf.Ticker(activo) # Ej: BTC-USD
                                precio_actual = ticker.history(period="1d")['Close'].iloc[-1]
                            except:
                                precio_actual = precio_medio # Si falla internet, usamos el de compra por defecto
                            
                            # 4. Cálculos finales con el precio en vivo
                            valor_actual = unidades_actuales * precio_actual
                            valor_invertido_flotante = unidades_actuales * precio_medio
                            pnl_flotante = valor_actual - valor_invertido_flotante
                            pnl_porcentaje = (pnl_flotante / valor_invertido_flotante * 100) if valor_invertido_flotante > 0 else 0
                            
                            resumen.append({
                                "Activo": activo,
                                "Unidades": round(unidades_actuales, 4),
                                "Precio Medio": round(precio_medio, 2),
                                "Precio Actual": round(precio_actual, 2),
                                "Valor Actual": round(valor_actual, 2),
                                "PnL Flotante": round(pnl_flotante, 2),
                                "% PnL": round(pnl_porcentaje, 2),
                                "Realizado": round(pnl_realizado, 2)
                            })
                
                # 5. Crear la tabla final
                df_portfolio = pd.DataFrame(resumen)
                
                # --- RE-CALCULAMOS LOS TOTALES GLOBALES PARA EL RESUMEN ---
                total_valor = df_portfolio["Valor Actual"].sum()
                total_invertido = (df_portfolio["Unidades"] * df_portfolio["Precio Medio"]).sum()
                total_pnl = df_portfolio["PnL Flotante"].sum()
                total_pnl_pct = (total_pnl / total_invertido * 100) if total_invertido > 0 else 0
                
                # --- MOTOR DE ESTILOS VISUALES ---
                def pintar_numeros(val):
                    # Si el valor es mayor a 0, verde. Si es menor, rojo. Si es 0, gris.
                    color = '#00e676' if val > 0 else '#ff1744' if val < 0 else '#888888'
                    return f'color: {color}; font-weight: bold;'
                
                # Aplicamos el estilo de colores a las columnas clave y formateamos
                df_estilizado = df_portfolio.style.map(
                    pintar_numeros, 
                    subset=['PnL Flotante', '% PnL', 'Realizado']
                ).format({
                    "Unidades": "{:.4f}",
                    "Precio Medio": "${:,.2f}",
                    "Precio Actual": "${:,.2f}",
                    "Valor Actual": "${:,.2f}",
                    "PnL Flotante": "${:,.2f}",
                    "% PnL": "{:.2f}%",
                    "Realizado": "${:,.2f}"
                })
                
                # 6. PINTAR LA INTERFAZ
                st.dataframe(df_estilizado, hide_index=True, use_container_width=True)
                
                st.markdown("---")
                # El "Footer" con las estadísticas globales (Primero mostramos los totales)
                col1, col2, col3 = st.columns(3)
                col1.metric("VALOR TOTAL", f"${total_valor:,.2f}")
                col2.metric("INVERTIDO", f"${total_invertido:,.2f}")
                
                # Truco para la flechita y el color en el resumen global
                variacion = "🟢" if total_pnl >= 0 else "🔴"
                col3.metric("PnL NO REALIZADO", f"{variacion} ${total_pnl:,.2f}", f"{total_pnl_pct:.2f}%")
                
                # --- NUEVO: EDITOR ESTILO EXCEL / NOTION ---
                st.markdown("---")
                st.subheader("📝 Historial de Operaciones (Editable)")
                st.info("💡 **Doble clic** en cualquier celda para editarla. Para borrar una operación, selecciona la casilla de su izquierda y pulsa la tecla **Suprimir (Delete)**.")
                
                # Preparamos los datos crudos para que sean editables
                df_para_editar = df_raw[['id', 'fecha', 'activo', 'tipo', 'cantidad', 'precio_usd']].copy()
                # Limpiamos un poco la fecha para que no sea tan larga visualmente
                df_para_editar['fecha'] = df_para_editar['fecha'].astype(str).str.slice(0, 16) 
                
                # Desplegamos el editor mágico interactivo
                st.data_editor(
                    df_para_editar,
                    column_config={
                        "id": None, # Ocultamos el ID interno para no liar al usuario
                        "fecha": st.column_config.TextColumn("Fecha", disabled=True),
                        "activo": st.column_config.TextColumn("Activo (Ej: BTC-USD)"),
                        "tipo": st.column_config.SelectboxColumn("Tipo", options=["COMPRA", "VENTA", "AIRDROP", "STAKING"]),
                        "cantidad": st.column_config.NumberColumn("Cantidad", format="%.4f"),
                        "precio_usd": st.column_config.NumberColumn("Precio USD", format="%.2f")
                    },
                    hide_index=False, # Muestra la casilla para poder seleccionar y borrar
                    num_rows="dynamic", # Permite que la tabla encoja si borras filas
                    use_container_width=True,
                    key="editor_ops" # Etiqueta clave para capturar los cambios
                )
                
                # Botón para confirmar los cambios a la base de datos
                if st.button("💾 Guardar Cambios"):
                    cambios = st.session_state["editor_ops"]
                    hay_cambios = False
                    
                    try:
                        # 1. Procesar Borrados
                        if cambios.get("deleted_rows"):
                            for row_index in cambios["deleted_rows"]:
                                id_borrar = df_para_editar.loc[int(row_index), 'id']
                                supabase.table("operaciones").delete().eq("id", int(id_borrar)).execute()
                            hay_cambios = True
                            
                        # 2. Procesar Ediciones
                        if cambios.get("edited_rows"):
                            for row_index, valores_cambiados in cambios["edited_rows"].items():
                                id_editar = df_para_editar.loc[int(row_index), 'id']
                                # 'valores_cambiados' es un diccionario automático con lo que has tocado
                                supabase.table("operaciones").update(valores_cambiados).eq("id", int(id_editar)).execute()
                            hay_cambios = True
                            
                        if hay_cambios:
                            st.success("✅ Cambios sincronizados con la nube.")
                            st.rerun() # Recarga la pantalla para mostrar el resumen matemático actualizado
                        else:
                            st.info("No has realizado ningún cambio en la tabla.")
                            
                    except Exception as e:
                        st.error(f"❌ Error al intentar modificar la base de datos: {e}")
                # ------------------------------------------------
                
            else:
                st.info("📭 Tu portfolio está vacío. ¡Añade tu primera operación!")
                
        except Exception as e:
            st.error(f"❌ Error al calcular el portfolio: {e}")

elif opcion == "➕ Añadir Operación":
    st.subheader("Registrar nueva operación")
    with st.form("form_operacion"):
        col1, col2 = st.columns(2)
        with col1:
            tipo = st.selectbox("Tipo", ["COMPRA", "VENTA", "AIRDROP", "STAKING"])
            activo = st.text_input("Activo (Ej. BTC-USD)")
            cantidad = st.number_input("Cantidad", min_value=0.0, format="%f")
        with col2:
            precio = st.number_input("Precio USD", min_value=0.0, format="%f")
            comision = st.number_input("Comisión USD", min_value=0.0, format="%f")
            exchange = st.selectbox("Exchange", ["Binance", "CoinEx", "Kraken", "Otro"])
            tasa_eur = st.number_input("Tasa USD/EUR", value=0.95, format="%f")
            
        submit = st.form_submit_button("Guardar Operación")
        
        if submit:
            if not conexion_exitosa:
                st.error("No hay conexión con la base de datos.")
            else:
                nueva_operacion = {
                    "fecha": datetime.now().isoformat(),
                    "activo": activo.upper(),
                    "tipo": tipo,
                    "cantidad": cantidad,
                    "precio_usd": precio,
                    "comision_usd": comision,
                    "exchange": exchange,
                    "tasa_usdeur": tasa_eur, # <--- ¡AQUÍ ESTÁ LA COMA CORREGIDA!
                    "usuario_id": st.session_state['usuario'].id
                }
                
                try:
                    respuesta = supabase.table("operaciones").insert(nueva_operacion).execute()
                    st.success(f"✅ ¡Éxito! Has registrado {cantidad} de {activo.upper()} correctamente en la base de datos.")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Error al guardar en la base de datos: {e}")