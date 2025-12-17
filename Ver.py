import streamlit as st
import matplotlib.pyplot as plt
import os
import pandas as pd
import numpy as np
import base64
import calendar
import io
from io import BytesIO
from datetime import datetime, timedelta
import time
import locale

# =====================================================
# IMPORTANTE: set_page_config DEBE IR ANTES DE CUALQUIER st.*
# =====================================================
st.set_page_config(
    page_title="CEDCO AGENDAS",  # NOMBRE DE LA PAGINA
    page_icon="🗓️",             # ICONO DE LA PAGINA
    layout="wide",
    initial_sidebar_state="expanded"
)

try:
    locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
except locale.Error:
    locale.setlocale(locale.LC_TIME, "")

# =====================================================
# ESTILOS (incluye tu estilo original + tabs)
# =====================================================
st.markdown(
    """
    <style>
    .fixed-header {
        position: fixed;
        top: 0;
        left: 305px;
        width: 100%;
        background-color: #445a14;
        color: white;
        padding: 10px;
        z-index: 999;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .fixed-header img {
        position: absolute;
        right: 500px;
    }
    .fixed-header h2{
        font-size: 50px;
        font-weight: bold;
        font-family: Verdana;
        margin : 0;
    }
    .main {
        padding-top: 70px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #223A70;
        color: white;
    }
    section[data-testid="stSidebar"] .css-1d391kg {
        color: white;
    }
    section[data-testid="stSidebar"] label {
        color: white;
    }

    /* Tabs centradas */
    .stTabs [data-baseweb="tab-list"] {
        justify-content: space-evenly;
    }
    .stTabs [data-baseweb="tab"] {
        flex-grow: 1;
        text-align: center;
    }
    .stTabs [data-baseweb="tab"] > div{
        font-size: 21px;
        font-family: Verdana;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.title("Opciones")
opcion = st.sidebar.radio("Selecciona una opción:", ["Correr modelo", "Leer modelo"])

# =====================================================
# FECHAS (DOMINGOS / SABADOS)
# =====================================================
anual = list(range(2025, 2040))
meses = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre",
    "Diciembre"
]
anio = st.selectbox("Seleccione el año", anual)
mes = st.selectbox("Seleccione el mes: ", meses)
numero_mes = meses.index(mes) + 1
_, num_dias = calendar.monthrange(anio, numero_mes)

domingos = [dia for dia in range(1, num_dias + 1) if calendar.weekday(anio, numero_mes, dia) == 6]
sabados  = [dia for dia in range(1, num_dias + 1) if calendar.weekday(anio, numero_mes, dia) == 5]
lunes    = [dia for dia in range(1, num_dias + 1) if calendar.weekday(anio, numero_mes, dia) == 0]

# =====================================================
# CARGAR ARCHIVO
# =====================================================
PARAMETROS = st.file_uploader("Suba el archivo PARAMETROS.xlsx", type=['xlsx'])

if PARAMETROS is not None:
    SERVICIOS = pd.read_excel(PARAMETROS, sheet_name="Servicios", header=None, names=["Codigo", "Servicio"])
    TRABAJADORES = pd.read_excel(PARAMETROS, sheet_name="Trabajadores", header=None, names=["Codigo", "Nombre"])
    CONSULTORIOS = pd.read_excel(PARAMETROS, sheet_name="Consultorios", header=0, index_col=0)
    AUX = pd.read_excel(PARAMETROS, sheet_name="AUX", header=0, index_col=0)

    # =====================================================
    # PÁGINA: CORRER MODELO
    # =====================================================
    if opcion == "Correr modelo":
        st.header("Correr modelo")

        tab1, tab2 = st.tabs(["Parámetros", "Ejecutar"])

        with tab1:
            @st.cache_data
            def cargar_parametros(PARAMETROS):
                # Leer DataFrames
                D22_si = pd.read_excel(PARAMETROS, sheet_name="DEMANDA", header=0, index_col=0)
                D2_si = D22_si.values

                # TJ_tdj
                TJ_tdj1 = pd.read_excel(PARAMETROS, sheet_name="TJ_tdj1", header=0, index_col=0)
                TJ_tdj2 = pd.read_excel(PARAMETROS, sheet_name="TJ_tdj2", header=0, index_col=0)
                TJ_tdj = np.stack([TJ_tdj1.values, TJ_tdj2.values], axis=0)
                TJ_tdj = np.transpose(TJ_tdj, (1, 2, 0))

                # AD_tis
                AD_list = []
                for i in range(1, 6):
                    df = pd.read_excel(PARAMETROS, sheet_name=f"AD_tis{i}", header=0, index_col=0)
                    AD_list.append(df.values)
                AD_tis = np.stack(AD_list, axis=0)
                AD_tis = np.transpose(AD_tis, (1, 2, 0))

                # C_ics
                C_list = []
                for i in range(1, 6):
                    df = pd.read_excel(PARAMETROS, sheet_name=f"C_ics{i}", header=0, index_col=0)
                    C_list.append(df.values)
                C_ics = np.stack(C_list, axis=0)
                C_ics = np.transpose(C_ics, (2, 1, 0))

                # TA_tis
                TA_tis1 = pd.read_excel(PARAMETROS, sheet_name="TA_tis1", header=0, index_col=0)
                TA_tis2 = pd.read_excel(PARAMETROS, sheet_name="TA_tis2", header=0, index_col=0)
                TA_tis3 = pd.read_excel(PARAMETROS, sheet_name="TA_tis3", header=0, index_col=0)
                TA_tis4 = pd.read_excel(PARAMETROS, sheet_name="TA_tis4", header=0, index_col=0)
                TA_tis5 = pd.read_excel(PARAMETROS, sheet_name="TA_tis5", header=0, index_col=0)
                TA_tis = np.stack([TA_tis1.values, TA_tis2.values, TA_tis3.values, TA_tis4.values, TA_tis5.values], axis=0)
                TA_tis = np.transpose(TA_tis, (1, 2, 0))

                # A2tsdji = TJtdj*TA_tis (OJO: este bloque estaba indexando con -1; lo dejo igual que lo tenías)
                A2tsdji = np.zeros(shape=(38, 5, 30, 2, 51))
                for t in range(38):
                    for s in range(5):
                        for d in range(30):
                            for j in range(2):
                                for i in range(51):
                                    A2tsdji[t-1, s-1, d-1, j-1, i-1] = np.floor(
                                        TJ_tdj[t-1, d-1, j-1] / TA_tis[t-1, i-1, s-1]
                                    )

                TD_tdj1 = pd.read_excel(PARAMETROS, sheet_name="TD_tdj1", header=0, index_col=0)
                TD_tdj2 = pd.read_excel(PARAMETROS, sheet_name="TD_tdj2", header=0, index_col=0)
                TD_tdj = np.stack([TD_tdj1, TD_tdj2], axis=0)
                TD_tdj = np.transpose(TD_tdj, (1, 2, 0))

                return SERVICIOS, TRABAJADORES, CONSULTORIOS, AUX, D22_si, A2tsdji, AD_tis, C_ics, D2_si, TD_tdj

            (
                SERVICIOS,
                TRABAJADORES,
                CONSULTORIOS,
                AUX,
                D22_si,
                A2tsdji,
                AD_tis,
                C_ics,
                D2_si,
                TD_tdj,
            ) = cargar_parametros(PARAMETROS)

            filtros = {
                "SERVICIOS": SERVICIOS,
                "TRABAJADORES": TRABAJADORES,
                "CONSULTORIOS": CONSULTORIOS,
                "DEMANDA": D22_si,
                "AUXILIARES": AUX,
            }
            opcion_tabla = st.selectbox("Visualización de información:", list(filtros.keys()))
            st.subheader(f"Tabla: {opcion_tabla}")
            st.write(filtros[opcion_tabla])

        with tab2:
            st.write("Aquí colocas el botón para ejecutar el modelo.")
            st.header("Ejecutar modelo")
            if st.button("▶️ **Ejecutar modelo**"):
                with st.spinner("🔄 Ejecutando modelo, por favor espera..."):
                    print("modelo")

    # =====================================================
    # PÁGINA: LEER MODELO
    # =====================================================
    elif opcion == "Leer modelo":
        st.header("Leer modelo")

        tab1, tab2 = st.tabs(["Visualización", "Estadísticas"])

        # =====================================================
        # TAB 1: VISUALIZACIÓN (IGUAL A COMO LO TENÍAS)
        # =====================================================
        with tab1:
            st.write("Asignación")
            archivo = "Xtsdji.csv"
            archivo2 = "Ptcsdji.csv"

            if os.path.exists(archivo) and os.path.exists(archivo2):

                SEDES = pd.DataFrame(
                    [
                        ["S1", "Sede Principal"],
                        ["S2", "Sede Administrativa"],
                        ["S3", "Sede Piedecuesta"],
                        ["S4", "Sede Barranca"],
                        ["S5", "UIS"],
                    ],
                    columns=["Codigo", "Nombre"],
                )

                JORNADAS = pd.DataFrame(
                    [
                        ["J1", "AM"],
                        ["J2", "PM"],
                    ],
                    columns=["Codigo", "Nombre"],
                )

                servicios_tmp = SERVICIOS.reset_index(drop=True).copy()
                servicios_tmp["idx"] = np.arange(1, len(servicios_tmp) + 1)
                servicio_map = dict(zip(servicios_tmp["idx"], servicios_tmp["Servicio"]))

                def obtener_fecha(row):
                    try:
                        fecha = datetime(anio, numero_mes, int(row["d"]))
                        return fecha.strftime("%Y-%m-%d %A")
                    except ValueError:
                        return "Fecha inválida"

                # =========================
                # Xtsdji
                # =========================
                Xtsdji = pd.read_csv(archivo)

                Xtsdji["Trabajador"] = "T" + Xtsdji["t"].astype(str)
                Xtsdji = Xtsdji.merge(
                    TRABAJADORES,
                    left_on="Trabajador",
                    right_on="Codigo",
                    how="left",
                )
                Xtsdji = Xtsdji.drop(columns=["Trabajador", "Codigo", "t", "valor"])
                Xtsdji = Xtsdji.rename(columns={"Nombre": "Trabajador"})

                Xtsdji["Sedes"] = "S" + Xtsdji["s"].astype(str)
                Xtsdji["Consultorio"] = None
                Xtsdji = Xtsdji.merge(
                    SEDES,
                    left_on="Sedes",
                    right_on="Codigo",
                    how="left",
                )
                Xtsdji = Xtsdji.drop(columns=["Sedes", "Codigo", "s"])
                Xtsdji = Xtsdji.rename(columns={"Nombre": "Sede"})

                Xtsdji["día"] = Xtsdji.apply(obtener_fecha, axis=1)
                Xtsdji = Xtsdji.drop(columns=["d"])
                Xtsdji = Xtsdji.rename(columns={"día": "Fecha"})

                Xtsdji["Jornada"] = "J" + Xtsdji["j"].astype(str)
                Xtsdji = Xtsdji.merge(
                    JORNADAS,
                    left_on="Jornada",
                    right_on="Codigo",
                    how="left",
                )
                Xtsdji = Xtsdji.drop(columns=["Jornada", "Codigo", "j"])
                Xtsdji = Xtsdji.rename(columns={"Nombre": "Jornada"})

                Xtsdji["Especialidad"] = Xtsdji["i"].map(servicio_map)
                Xtsdji = Xtsdji[~Xtsdji["Especialidad"].isna()].copy()
                Xtsdji = Xtsdji.drop(columns=["i"])

                Xtsdji["Fecha"] = pd.to_datetime(Xtsdji["Fecha"].str[:10])
                Xtsdji["Día"] = Xtsdji["Fecha"].dt.strftime("%A")

                # =========================
                # Ptcsdji
                # =========================
                Ptcsdji = pd.read_csv(archivo2)

                Ptcsdji["Trabajador"] = "T" + Ptcsdji["t"].astype(str)
                Ptcsdji = Ptcsdji.merge(
                    TRABAJADORES,
                    left_on="Trabajador",
                    right_on="Codigo",
                    how="left",
                )
                Ptcsdji = Ptcsdji.drop(columns=["Trabajador", "Codigo", "t", "valor"])
                Ptcsdji = Ptcsdji.rename(columns={"Nombre": "Trabajador"})

                Ptcsdji["c"] = "C" + Ptcsdji["c"].astype(str)
                Ptcsdji["s"] = "S" + Ptcsdji["s"].astype(str)

                CONSULTORIOS.columns = CONSULTORIOS.columns.astype(str)
                CONSULTORIOS.index = CONSULTORIOS.index.astype(str)

                def obtener_consultorio(row):
                    try:
                        return CONSULTORIOS.loc[row["c"], row["s"]]
                    except KeyError:
                        return "No encontrado"

                Ptcsdji["Consultorio"] = Ptcsdji.apply(obtener_consultorio, axis=1)

                Ptcsdji["día"] = Ptcsdji.apply(obtener_fecha, axis=1)
                Ptcsdji = Ptcsdji.drop(columns=["d"])
                Ptcsdji = Ptcsdji.rename(columns={"día": "Fecha"})

                Ptcsdji["Sedes"] = Ptcsdji["s"].astype(str)
                Ptcsdji = Ptcsdji.merge(
                    SEDES,
                    left_on="Sedes",
                    right_on="Codigo",
                    how="left",
                )
                Ptcsdji = Ptcsdji.drop(columns=["Sedes", "Codigo", "s", "c"])
                Ptcsdji = Ptcsdji.rename(columns={"Nombre": "Sede"})

                Ptcsdji["Jornada"] = "J" + Ptcsdji["j"].astype(str)
                Ptcsdji = Ptcsdji.merge(
                    JORNADAS,
                    left_on="Jornada",
                    right_on="Codigo",
                    how="left",
                )
                Ptcsdji = Ptcsdji.drop(columns=["Jornada", "Codigo", "j"])
                Ptcsdji = Ptcsdji.rename(columns={"Nombre": "Jornada"})

                Ptcsdji["Especialidad"] = Ptcsdji["i"].map(servicio_map)
                Ptcsdji = Ptcsdji[~Ptcsdji["Especialidad"].isna()].copy()
                Ptcsdji = Ptcsdji.drop(columns=["i"])

                Ptcsdji["Fecha"] = pd.to_datetime(Ptcsdji["Fecha"].str[:10])
                Ptcsdji["Día"] = Ptcsdji["Fecha"].dt.strftime("%A")

                nuevo_orden = [
                    "Trabajador",
                    "Consultorio",
                    "Sede",
                    "Fecha",
                    "Jornada",
                    "Especialidad",
                    "Día",
                ]
                Ptcsdji = Ptcsdji[nuevo_orden]

                # =========================
                # Filtros en Streamlit
                # =========================
                rango = st.date_input(
                    "Selecciona un rango de fechas",
                    [Xtsdji["Fecha"].min(), Xtsdji["Fecha"].max()],
                )

                if len(rango) == 2:
                    inicio, fin = pd.to_datetime(rango[0]), pd.to_datetime(rango[1])

                    trabajadores = Xtsdji["Trabajador"].unique()
                    sedes = Xtsdji["Sede"].unique()
                    jornadas = Xtsdji["Jornada"].unique()
                    servicios = Xtsdji["Especialidad"].unique()

                    trabajador_sel = st.selectbox("Selecciona el trabajador", ["Todos"] + sorted(trabajadores.tolist()))
                    sede_sel = st.selectbox("Selecciona la sede", ["Todos"] + sorted(sedes.tolist()))
                    jornada_sel = st.selectbox("Selecciona la jornada", ["Todos"] + sorted(jornadas.tolist()))
                    servicio_sel = st.selectbox("Selecciona el servicio", ["Todos"] + sorted(servicios.tolist()))

                    filtrado_X = Xtsdji[(Xtsdji["Fecha"] >= inicio) & (Xtsdji["Fecha"] <= fin)].copy()
                    filtrado_P = Ptcsdji[(Ptcsdji["Fecha"] >= inicio) & (Ptcsdji["Fecha"] <= fin)].copy()

                    if trabajador_sel != "Todos":
                        filtrado_X = filtrado_X[filtrado_X["Trabajador"] == trabajador_sel]
                        filtrado_P = filtrado_P[filtrado_P["Trabajador"] == trabajador_sel]

                    if jornada_sel != "Todos":
                        filtrado_X = filtrado_X[filtrado_X["Jornada"] == jornada_sel]
                        filtrado_P = filtrado_P[filtrado_P["Jornada"] == jornada_sel]

                    if servicio_sel != "Todos":
                        filtrado_X = filtrado_X[filtrado_X["Especialidad"] == servicio_sel]
                        filtrado_P = filtrado_P[filtrado_P["Especialidad"] == servicio_sel]

                    # LÓGICA UIS MANTENIDA
                    if sede_sel == "UIS":
                        resultado = filtrado_X[filtrado_X["Sede"] == "UIS"]
                    elif sede_sel in ["Sede Principal", "Sede Administrativa", "Sede Piedecuesta", "Sede Barranca"]:
                        resultado = filtrado_P[filtrado_P["Sede"] == sede_sel]
                    elif sede_sel == "Todos":
                        resultado = pd.concat(
                            [
                                filtrado_P[filtrado_P["Sede"] != "UIS"],
                                filtrado_X[filtrado_X["Sede"] == "UIS"],
                            ]
                        )
                    else:
                        resultado = pd.DataFrame()

                    st.write(resultado)

                    if not resultado.empty:
                        buffer = BytesIO()
                        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                            resultado.to_excel(writer, index=False, sheet_name="Resultado")
                        st.download_button(
                            label="📥 Descargar resultados",
                            data=buffer.getvalue(),
                            file_name="resultados_filtrados.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                    else:
                        st.info("No hay datos para mostrar con los filtros seleccionados.")

        # =====================================================
        # TAB 2: ESTADÍSTICAS (DISEÑO ACTUAL + CANTIDADES + CÓDIGO)
        # =====================================================
        with tab2:
            st.write("Estadísticas")
            archivo = "D_si_ajust.csv"

            if os.path.exists(archivo):

                # -----------------------------
                # DEMANDA total desde Excel
                # -----------------------------
                DEMANDA2 = pd.read_excel(
                    PARAMETROS,
                    sheet_name="DEMANDA",
                    header=0,
                    index_col=0
                )
                DEMANDA2.index = np.arange(1, DEMANDA2.shape[0] + 1)
                DEMANDA2.columns = np.arange(1, DEMANDA2.shape[1] + 1)

                df_dem = DEMANDA2.stack().reset_index()
                df_dem.columns = ["s", "i", "demanda_total"]

                # -----------------------------
                # D_si_ajust (faltante) desde CSV
                # -----------------------------
                df_ajust = pd.read_csv(archivo)
                df_ajust.columns = ["s", "i", "demanda_faltante"]

                # -----------------------------
                # Unir y calcular CANTIDADES
                # -----------------------------
                df = df_dem.merge(df_ajust, on=["s", "i"], how="left")
                df["demanda_faltante"] = df["demanda_faltante"].fillna(0)
                df["demanda_atendida"] = df["demanda_total"] - df["demanda_faltante"]

                # -----------------------------
                # Nombres de sedes y servicios
                # -----------------------------
                sedes_map = {
                    1: "Sede Principal",
                    2: "Sede Administrativa",
                    3: "Sede Piedecuesta",
                    4: "Sede Barranca",
                    5: "UIS",
                }
                df["Sede"] = df["s"].map(sedes_map)

                # idx = 1..N para mapear i
                servicios_tmp = SERVICIOS.reset_index(drop=True).copy()
                servicios_tmp["idx"] = np.arange(1, len(servicios_tmp) + 1)

                codigo_map = dict(zip(servicios_tmp["idx"], servicios_tmp["Codigo"]))
                servicio_map = dict(zip(servicios_tmp["idx"], servicios_tmp["Servicio"]))

                df["Código"] = df["i"].map(codigo_map)
                df["Servicio"] = df["i"].map(servicio_map)

                # -----------------------------
                # Filtro por sede
                # -----------------------------
                sedes_nombres = sorted(df["Sede"].dropna().unique().tolist())
                sede_sel = st.selectbox("Selecciona la sede", ["Todas"] + sedes_nombres)

                if sede_sel != "Todas":
                    df_mostrar = df[df["Sede"] == sede_sel].copy()
                else:
                    df_mostrar = df.copy()

                # Ocultar filas completamente en cero
                df_mostrar = df_mostrar[
                    ~((df_mostrar["demanda_total"] == 0) &
                      (df_mostrar["demanda_atendida"] == 0) &
                      (df_mostrar["demanda_faltante"] == 0))
                ].copy()

                # -----------------------------
                # TABLA + TORTA (DISEÑO ACTUAL)
                # -----------------------------
                st.subheader("Cumplimiento de demanda (cantidades)")

                df_view = df_mostrar[[
                    "Sede", "Código", "Servicio",
                    "demanda_total", "demanda_atendida", "demanda_faltante"
                ]].rename(columns={
                    "demanda_total": "Demanda total",
                    "demanda_atendida": "Atendido",
                    "demanda_faltante": "Faltante",
                })

                # Colores tipo “semáforo” por Faltante
                def color_faltante(v):
                    if v <= 0:
                        return "background-color:#2e7d32;color:white"   # verde
                    elif v <= 5:
                        return "background-color:#81c784"             # verde claro
                    elif v <= 20:
                        return "background-color:#fff176"             # amarillo
                    else:
                        return "background-color:#ef5350;color:white" # rojo

                styled = (
                    df_view.style
                    .applymap(color_faltante, subset=["Faltante"])
                    .format("{:,.0f}", subset=["Demanda total", "Atendido", "Faltante"])
                )

                # Totales para torta
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

                # Métricas globales (cantidad)
                c1, c2, c3 = st.columns(3)
                c1.metric("Demanda total", f"{int(total_dem):,}")
                c2.metric("Atendido", f"{int(total_atend):,}")
                c3.metric("Faltante", f"{int(total_falt):,}")

            else:
                st.warning("No se encontró el archivo D_si_ajust.csv")

            # =====================================================
            # AUXILIARES (TU BLOQUE ORIGINAL, SIN CAMBIOS)
            # =====================================================
            st.subheader("Auxiliares requeridos por día y sede")

            capacidad = st.number_input(
                "Capacidad total de auxiliares (pool sedes 1–3)",
                min_value=1,
                max_value=100,
                value=34,
                step=1,
            )

            Ptcsdji_aux = pd.read_csv("Ptcsdji.csv")

            if "valor" in Ptcsdji_aux.columns:
                Ptcsdji_aux = Ptcsdji_aux[Ptcsdji_aux["valor"] != 0]

            trabajadores_excluir = [18, 19, 20]
            cirugia_min, cirugia_max = 39, 47

            mask_excluir = (
                Ptcsdji_aux["t"].isin(trabajadores_excluir) &
                Ptcsdji_aux["i"].between(cirugia_min, cirugia_max)
            )
            Ptcsdji_aux = Ptcsdji_aux[~mask_excluir]

            sedes_map = {
                1: "Sede Principal",
                2: "Sede Administrativa",
                3: "Sede Piedecuesta",
                4: "Sede Barranca",
                5: "UIS",
            }
            Ptcsdji_aux["Sede"] = Ptcsdji_aux["s"].map(sedes_map)

            sedes_validas = ["Sede Principal", "Sede Administrativa", "Sede Piedecuesta"]
            Ptcsdji_aux = Ptcsdji_aux[Ptcsdji_aux["Sede"].isin(sedes_validas)]

            Ptcsdji_aux["Fecha"] = Ptcsdji_aux["d"].apply(lambda d: datetime(anio, numero_mes, int(d)))

            jornada_map = {1: "AM", 2: "PM"}
            Ptcsdji_aux["Jornada"] = Ptcsdji_aux["j"].map(jornada_map)

            # 1) Consultorio 12 sede 1 no contar doble
            if "c" in Ptcsdji_aux.columns:
                mask_c12_s1 = (Ptcsdji_aux["s"] == 1) & (Ptcsdji_aux["c"] == 12)
                df_c12 = Ptcsdji_aux.loc[mask_c12_s1].drop_duplicates(subset=["s", "c", "Fecha", "Jornada", "i"])
                df_rest = Ptcsdji_aux.loc[~mask_c12_s1]
                Ptcsdji_aux = pd.concat([df_rest, df_c12], ignore_index=True)

            # 2) Servicios 14 y 15 no contar doble mismo t/s/d/j
            mask_1415 = Ptcsdji_aux["i"].isin([14, 15])
            df_1415 = Ptcsdji_aux.loc[mask_1415].drop_duplicates(subset=["t", "s", "Fecha", "Jornada"])
            df_rest2 = Ptcsdji_aux.loc[~mask_1415]
            Ptcsdji_aux = pd.concat([df_rest2, df_1415], ignore_index=True)

            jornadas_opts = ["Todas"] + sorted(Ptcsdji_aux["Jornada"].dropna().unique().tolist())
            jornada_sel = st.selectbox("Selecciona la jornada (para auxiliares)", jornadas_opts)

            if jornada_sel != "Todas":
                Ptcsdji_aux = Ptcsdji_aux[Ptcsdji_aux["Jornada"] == jornada_sel]

            AUX_df = AUX.copy().reset_index()
            AUX_df.rename(columns={"index": "i"}, inplace=True)

            aux_merge = Ptcsdji_aux.merge(AUX_df, on="i", how="left")

            cols_aux = AUX_df.columns.drop("i")

            aux_diario = (
                aux_merge
                .groupby(["Sede", "Fecha", "Jornada"], as_index=False)[cols_aux]
                .sum()
            )

            aux_diario["Total_aux_sede"] = aux_diario[cols_aux].sum(axis=1)

            total_pool = (
                aux_diario
                .groupby(["Fecha", "Jornada"], as_index=False)["Total_aux_sede"]
                .sum()
                .rename(columns={"Total_aux_sede": "Total_aux_3sedes"})
            )

            aux_diario = aux_diario.merge(total_pool, on=["Fecha", "Jornada"], how="left")

            capacidad_total = capacidad
            aux_diario["Capacidad_pool"] = capacidad_total

            aux_diario["% ocupación_pool"] = (aux_diario["Total_aux_3sedes"] / aux_diario["Capacidad_pool"]) * 100
            aux_diario["% desocupación_pool"] = np.where(
                aux_diario["Total_aux_3sedes"] < aux_diario["Capacidad_pool"],
                (1 - aux_diario["Total_aux_3sedes"] / aux_diario["Capacidad_pool"]) * 100,
                0
            )

            aux_cols = cols_aux.tolist()
            aux_diario = aux_diario[
                [
                    "Sede",
                    "Fecha",
                    "Jornada",
                    "Total_aux_sede",
                    "Total_aux_3sedes",
                    "Capacidad_pool",
                    "% ocupación_pool",
                    "% desocupación_pool",
                ] + aux_cols
            ]

            aux_diario["Fecha"] = pd.to_datetime(aux_diario["Fecha"]).dt.date

            def color_ocupacion(v):
                if v >= 100:
                    return "background-color:#b71c1c;color:white"
                elif v >= 80:
                    return "background-color:#ef9a9a"
                elif v >= 60:
                    return "background-color:#fff176"
                elif v >= 40:
                    return "background-color:#aed581"
                else:
                    return "background-color:#2e7d32;color:white"

            styled_aux = aux_diario.round(2).style.applymap(color_ocupacion, subset=["% ocupación_pool"])

            st.dataframe(styled_aux, use_container_width=True, height=450)

            sobrecupo_mask = aux_diario["Total_aux_3sedes"] > aux_diario["Capacidad_pool"]
            n_sobrecupo = (
                aux_diario.loc[sobrecupo_mask, ["Fecha", "Jornada"]]
                .drop_duplicates()
                .shape[0]
            )

            st.markdown(f"**Días/jornadas con sobreocupación del pool de auxiliares (3 sedes):** {int(n_sobrecupo)}")
