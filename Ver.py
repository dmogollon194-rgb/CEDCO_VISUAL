# =====================================================
# CEDCO AGENDAS – APP COMPLETA Y FUNCIONAL
# =====================================================

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import calendar
import os
from datetime import datetime
from io import BytesIO
import locale

# =====================================================
# CONFIGURACIÓN (DEBE SER LO PRIMERO)
# =====================================================
st.set_page_config(
    page_title="CEDCO AGENDAS",
    page_icon="🗓️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================
# ESTILOS GLOBALES
# =====================================================
st.markdown("""
<style>
section[data-testid="stSidebar"] {
    background-color: #223A70;
    color: white;
}
section[data-testid="stSidebar"] label {
    color: white;
}
.stTabs [data-baseweb="tab-list"] {
    justify-content: space-evenly;
}
.stTabs [data-baseweb="tab"] {
    flex-grow: 1;
    text-align: center;
}
.stTabs [data-baseweb="tab"] > div {
    font-size: 21px;
    font-family: Verdana;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# LOCALE
# =====================================================
try:
    locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
except locale.Error:
    locale.setlocale(locale.LC_TIME, "")

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.title("Opciones")
opcion = st.sidebar.radio(
    "Selecciona una opción:",
    ["Correr modelo", "Leer modelo"]
)

# =====================================================
# SELECTORES GLOBALES
# =====================================================
anual = list(range(2025, 2040))
meses = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

anio = st.selectbox("Seleccione el año", anual)
mes = st.selectbox("Seleccione el mes:", meses)
numero_mes = meses.index(mes) + 1

PARAMETROS = st.file_uploader(
    "Suba el archivo PARAMETROS.xlsx",
    type=["xlsx"]
)

# =====================================================
# CARGA DE PARÁMETROS
# =====================================================
if PARAMETROS is not None:

    SERVICIOS = pd.read_excel(
        PARAMETROS,
        sheet_name="Servicios",
        header=None,
        names=["Codigo", "Servicio"]
    )

    TRABAJADORES = pd.read_excel(
        PARAMETROS,
        sheet_name="Trabajadores",
        header=None,
        names=["Codigo", "Nombre"]
    )

    # =====================================================
    # CORRER MODELO
    # =====================================================
    if opcion == "Correr modelo":
        st.header("Correr modelo")
        st.info("Aquí va tu lógica de ejecución del modelo.")

    # =====================================================
    # LEER MODELO
    # =====================================================
    elif opcion == "Leer modelo":

        st.header("Leer modelo")

        tab_vis, tab_est = st.tabs(["Visualización", "Estadísticas"])

        # =================================================
        # TAB 1 – VISUALIZACIÓN (LECTURA REAL DE CSV)
        # =================================================
        with tab_vis:

            st.subheader("Visualización de asignaciones")

            archivo_X = "Xtsdji.csv"
            archivo_P = "Ptcsdji.csv"

            if not (os.path.exists(archivo_X) and os.path.exists(archivo_P)):
                st.warning("No se encontraron Xtsdji.csv y/o Ptcsdji.csv")
            else:
                # -------------------------------
                # LEER CSV
                # -------------------------------
                Xtsdji = pd.read_csv(archivo_X)
                Ptcsdji = pd.read_csv(archivo_P)

                # -------------------------------
                # MAPEO DE SERVICIOS
                # -------------------------------
                servicios_tmp = SERVICIOS.reset_index(drop=True).copy()
                servicios_tmp["idx"] = np.arange(1, len(servicios_tmp) + 1)
                servicio_map = dict(zip(servicios_tmp["idx"], servicios_tmp["Servicio"]))

                # -------------------------------
                # Xtsdji
                # -------------------------------
                Xtsdji["Servicio"] = Xtsdji["i"].map(servicio_map)
                Xtsdji["Fecha"] = Xtsdji["d"].apply(
                    lambda d: datetime(anio, numero_mes, int(d))
                )

                st.markdown("### Asignaciones Xtsdji")
                st.dataframe(
                    Xtsdji[
                        ["t", "s", "Fecha", "j", "Servicio"]
                    ].sort_values(["Fecha", "t"]),
                    use_container_width=True,
                    height=350,
                )

                # -------------------------------
                # Ptcsdji
                # -------------------------------
                Ptcsdji["Servicio"] = Ptcsdji["i"].map(servicio_map)
                Ptcsdji["Fecha"] = Ptcsdji["d"].apply(
                    lambda d: datetime(anio, numero_mes, int(d))
                )

                st.markdown("### Asignaciones Ptcsdji (consultorios)")
                st.dataframe(
                    Ptcsdji[
                        ["t", "c", "s", "Fecha", "j", "Servicio"]
                    ].sort_values(["Fecha", "t"]),
                    use_container_width=True,
                    height=350,
                )

        # =================================================
        # TAB 2 – ESTADÍSTICAS (CANTIDAD + CÓDIGO)
        # =================================================
        with tab_est:

            archivo = "D_si_ajust.csv"

            if not os.path.exists(archivo):
                st.warning("No se encontró el archivo D_si_ajust.csv")
            else:

                # -------------------------------
                # DEMANDA TOTAL
                # -------------------------------
                DEMANDA = pd.read_excel(
                    PARAMETROS,
                    sheet_name="DEMANDA",
                    header=0,
                    index_col=0
                )
                DEMANDA.index = np.arange(1, DEMANDA.shape[0] + 1)
                DEMANDA.columns = np.arange(1, DEMANDA.shape[1] + 1)

                df_dem = DEMANDA.stack().reset_index()
                df_dem.columns = ["s", "i", "demanda_total"]

                # -------------------------------
                # DEMANDA FALTANTE
                # -------------------------------
                df_falt = pd.read_csv(archivo)
                df_falt.columns = ["s", "i", "demanda_faltante"]

                # -------------------------------
                # UNIR
                # -------------------------------
                df = df_dem.merge(df_falt, on=["s", "i"], how="left")
                df["demanda_faltante"] = df["demanda_faltante"].fillna(0)
                df["demanda_atendida"] = df["demanda_total"] - df["demanda_faltante"]

                # -------------------------------
                # MAPEO SEDES
                # -------------------------------
                sedes_map = {
                    1: "Sede Principal",
                    2: "Sede Administrativa",
                    3: "Sede Piedecuesta",
                    4: "Sede Barranca",
                    5: "UIS",
                }
                df["Sede"] = df["s"].map(sedes_map)

                # -------------------------------
                # MAPEO SERVICIOS
                # -------------------------------
                servicios_tmp = SERVICIOS.reset_index(drop=True).copy()
                servicios_tmp["idx"] = np.arange(1, len(servicios_tmp) + 1)

                codigo_map = dict(zip(servicios_tmp["idx"], servicios_tmp["Codigo"]))
                servicio_map = dict(zip(servicios_tmp["idx"], servicios_tmp["Servicio"]))

                df["Código"] = df["i"].map(codigo_map)
                df["Servicio"] = df["i"].map(servicio_map)

                # -------------------------------
                # FILTRO POR SEDE
                # -------------------------------
                sede_sel = st.selectbox(
                    "Selecciona la sede",
                    ["Todas"] + sorted(df["Sede"].dropna().unique())
                )

                if sede_sel != "Todas":
                    df = df[df["Sede"] == sede_sel]

                # -------------------------------
                # TABLA
                # -------------------------------
                st.subheader("Cumplimiento de demanda (cantidades)")

                df_view = df[
                    ["Sede", "Código", "Servicio",
                     "demanda_total", "demanda_atendida", "demanda_faltante"]
                ].rename(columns={
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
                    .format("{:,.0f}", subset=["Demanda total", "Atendido", "Faltante"])
                )

                col_tabla, col_pie = st.columns([3, 1])

                with col_tabla:
                    st.dataframe(styled, use_container_width=True, height=450)

                # -------------------------------
                # PIE GLOBAL
                # -------------------------------
                total_dem = df["demanda_total"].sum()
                total_falt = df["demanda_faltante"].sum()
                total_atend = total_dem - total_falt

                with col_pie:
                    fig, ax = plt.subplots()
                    ax.pie(
                        [total_atend, total_falt],
                        labels=["Atendido", "Faltante"],
                        autopct=lambda p: f"{p:.1f}%\n({int(p*total_dem/100):,})",
                        startangle=90,
                    )
                    ax.axis("equal")
                    st.pyplot(fig)

                c1, c2, c3 = st.columns(3)
                c1.metric("Demanda total", f"{int(total_dem):,}")
                c2.metric("Atendido", f"{int(total_atend):,}")
                c3.metric("Faltante", f"{int(total_falt):,}")
