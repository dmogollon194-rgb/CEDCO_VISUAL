import streamlit as st
import matplotlib.pyplot as plt
import os
import pandas as pd
import numpy as np
import calendar
from io import BytesIO
from datetime import datetime
import locale

try:
    locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
except locale.Error:
    locale.setlocale(locale.LC_TIME, "")

# =========================
# CONFIG + ESTILOS
# =========================
st.set_page_config(
    page_title="CEDCO AGENDAS",
    page_icon="🗓️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] {
        background-color: #223A70;
        color: white;
    }
    section[data-testid="stSidebar"] label {
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar
st.sidebar.title("Opciones")
opcion = st.sidebar.radio("Selecciona una opción:", ["Correr modelo", "Leer modelo"])

# =========================
# FECHAS
# =========================
anual = list(range(2025, 2040))
meses = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]
anio = st.selectbox("Seleccione el año", anual)
mes = st.selectbox("Seleccione el mes: ", meses)
numero_mes = meses.index(mes) + 1
_, num_dias = calendar.monthrange(anio, numero_mes)

# =========================
# CARGA ARCHIVO
# =========================
PARAMETROS = st.file_uploader("Suba el archivo PARAMETROS.xlsx", type=["xlsx"])

if PARAMETROS is not None:
    SERVICIOS = pd.read_excel(PARAMETROS, sheet_name="Servicios", header=None, names=["Codigo", "Servicio"])
    TRABAJADORES = pd.read_excel(PARAMETROS, sheet_name="Trabajadores", header=None, names=["Codigo", "Nombre"])
    CONSULTORIOS = pd.read_excel(PARAMETROS, sheet_name="Consultorios", header=0, index_col=0)
    AUX = pd.read_excel(PARAMETROS, sheet_name="AUX", header=0, index_col=0)

    # =========================
    # CORRER MODELO (SIN CAMBIOS REALES)
    # =========================
    if opcion == "Correr modelo":
        st.header("Correr modelo")
        tab1, tab2 = st.tabs(["Parámetros", "Ejecutar"])

        with tab1:
            st.subheader("Parámetros cargados")
            filtros = {
                "SERVICIOS": SERVICIOS,
                "TRABAJADORES": TRABAJADORES,
                "CONSULTORIOS": CONSULTORIOS,
                "AUXILIARES": AUX,
            }
            opcion_tabla = st.selectbox("Visualización de información:", list(filtros.keys()))
            st.write(filtros[opcion_tabla])

        with tab2:
            st.header("Ejecutar modelo")
            if st.button("▶️ **Ejecutar modelo**"):
                with st.spinner("🔄 Ejecutando modelo, por favor espera..."):
                    st.write("modelo")

    # =========================
    # LEER MODELO
    # =========================
    elif opcion == "Leer modelo":
        st.header("Leer modelo")

        tab1, tab2 = st.tabs(["Visualización", "Estadísticas"])

        # =========================
        # TAB 1: VISUALIZACIÓN (placeholder)
        # =========================
        with tab1:
            st.write("Aquí va tu visualización (Xtsdji/Ptcsdji).")

        # =========================
        # TAB 2: ESTADÍSTICAS (TABLA POR CANTIDAD + CÓDIGO)
        # =========================
        with tab2:
            st.write("Estadísticas")
            archivo = "D_si_ajust.csv"

            if os.path.exists(archivo):

                # -------------------------
                # DEMANDA total (Excel)
                # -------------------------
                DEMANDA2 = pd.read_excel(PARAMETROS, sheet_name="DEMANDA", header=0, index_col=0)
                DEMANDA2.index = np.arange(1, DEMANDA2.shape[0] + 1)
                DEMANDA2.columns = np.arange(1, DEMANDA2.shape[1] + 1)

                df_dem = DEMANDA2.stack().reset_index()
                df_dem.columns = ["s", "i", "demanda_total"]

                # -------------------------
                # NO satisfecho (CSV)
                # -------------------------
                df_ajust = pd.read_csv(archivo)
                df_ajust.columns = ["s", "i", "demanda_faltante"]

                # -------------------------
                # Unir y calcular cantidades
                # -------------------------
                df = df_dem.merge(df_ajust, on=["s", "i"], how="left")
                df["demanda_faltante"] = df["demanda_faltante"].fillna(0)
                df["demanda_atendida"] = df["demanda_total"] - df["demanda_faltante"]

                # -------------------------
                # Map sedes
                # -------------------------
                sedes_map = {
                    1: "Sede Principal",
                    2: "Sede Administrativa",
                    3: "Sede Piedecuesta",
                    4: "Sede Barranca",
                    5: "UIS",
                }
                df["Sede"] = df["s"].map(sedes_map)

                # -------------------------
                # Map servicios: CÓDIGO + NOMBRE
                # idx = 1..N (coincide con i)
                # -------------------------
                servicios_tmp = SERVICIOS.reset_index(drop=True).copy()
                servicios_tmp["idx"] = np.arange(1, len(servicios_tmp) + 1)

                codigo_map = dict(zip(servicios_tmp["idx"], servicios_tmp["Codigo"]))
                servicio_map = dict(zip(servicios_tmp["idx"], servicios_tmp["Servicio"]))

                df["Código"] = df["i"].map(codigo_map)
                df["Servicio"] = df["i"].map(servicio_map)

                # -------------------------
                # Filtro por sede
                # -------------------------
                sedes_nombres = sorted(df["Sede"].dropna().unique().tolist())
                sede_sel = st.selectbox("Selecciona la sede", ["Todas"] + sedes_nombres)

                if sede_sel != "Todas":
                    df_mostrar = df[df["Sede"] == sede_sel].copy()
                else:
                    df_mostrar = df.copy()

                # Ocultar filas sin nada
                df_mostrar = df_mostrar[
                    ~((df_mostrar["demanda_total"] == 0) &
                      (df_mostrar["demanda_atendida"] == 0) &
                      (df_mostrar["demanda_faltante"] == 0))
                ].copy()

                # -------------------------
                # TABLA (con Código)
                # -------------------------
                st.subheader("Cumplimiento de demanda (cantidades)")

                df_view = df_mostrar[[
                    "Sede", "Código", "Servicio",
                    "demanda_total", "demanda_atendida", "demanda_faltante"
                ]].copy()

                df_view = df_view.rename(columns={
                    "demanda_total": "Demanda total",
                    "demanda_atendida": "Atendido",
                    "demanda_faltante": "Faltante",
                })

                def color_faltante(v):
                    if v <= 0:
                        return "background-color:#2e7d32;color:white"
                    elif v <= 5:
                        return "background-color:#81c784"
                    elif v <= 20:
                        return "background-color:#fff176"
                    else:
                        return "background-color:#ef5350;color:white"

                styled = (
                    df_view.style
                    .applymap(color_faltante, subset=["Faltante"])
                    .format({
                        "Demanda total": "{:,.0f}",
                        "Atendido": "{:,.0f}",
                        "Faltante": "{:,.0f}",
                    })
                )

                # -------------------------
                # Pie global (Atendido vs Faltante)
                # -------------------------
                total_dem = df_mostrar["demanda_total"].sum()
                total_falt = df_mostrar["demanda_faltante"].sum()
                total_atend = total_dem - total_falt

                col_tabla, col_pie = st.columns([3, 1])

                with col_tabla:
                    st.dataframe(styled, use_container_width=True, height=450)

                with col_pie:
                    st.markdown("### Distribución")

                    def autopct_format(values):
                        def _inner(pct):
                            total = sum(values)
                            val = int(round(pct * total / 100.0))
                            return f"{pct:.1f}%\n({val:,})"
                        return _inner

                    valores = [total_atend, total_falt]

                    fig, ax = plt.subplots()
                    ax.pie(
                        valores,
                        labels=["Atendido", "Faltante"],
                        autopct=autopct_format(valores),
                        startangle=90,
                    )
                    ax.axis("equal")
                    st.pyplot(fig)

                c1, c2, c3 = st.columns(3)
                c1.metric("Demanda total", f"{int(total_dem):,}")
                c2.metric("Atendido", f"{int(total_atend):,}")
                c3.metric("Faltante", f"{int(total_falt):,}")

            else:
                st.warning("No se encontró el archivo D_si_ajust.csv")
