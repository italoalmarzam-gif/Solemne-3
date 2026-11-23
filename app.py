# ============================================================
# TERCERA SOLEMNE - TALLER DE PROGRAMACION II
# Dashboard interactivo FIFA 22 con Streamlit
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ------------------------------------------------------------
# 1. CONFIGURACION GENERAL DE LA PAGINA
# ------------------------------------------------------------
st.set_page_config(
    page_title="FIFA 22 | Explorador de jugadores",
    page_icon="⚽",
    layout="wide"
)

# ------------------------------------------------------------
# 2. FUNCION PARA CARGAR LOS DATOS
# ------------------------------------------------------------
@st.cache_data
def cargar_datos():
    """Lee el CSV local y lo convierte en un DataFrame de pandas."""
    ruta_csv = Path(__file__).parent / "players_22.csv"
    datos = pd.read_csv(ruta_csv, low_memory=False)
    return datos


# ------------------------------------------------------------
# 3. FUNCION PARA PREPARAR Y LIMPIAR LOS DATOS
# ------------------------------------------------------------
def preparar_datos(datos):
    """Limpia columnas, elimina duplicados y prepara variables."""
    datos = datos.copy()

    # El identificador del jugador permite detectar registros repetidos.
    datos = datos.drop_duplicates(subset="sofifa_id")

    # Convertimos las columnas numéricas importantes al tipo adecuado.
    columnas_numericas = [
        "overall", "potential", "age", "value_eur", "wage_eur",
        "pace", "shooting", "passing", "dribbling", "defending",
        "physic", "height_cm", "weight_kg"
    ]

    for columna in columnas_numericas:
        datos[columna] = pd.to_numeric(datos[columna], errors="coerce")

    # Reemplazamos los valores faltantes de texto para facilitar los filtros.
    columnas_texto = [
        "short_name", "club_name", "league_name",
        "nationality_name", "player_positions", "preferred_foot"
    ]

    for columna in columnas_texto:
        datos[columna] = datos[columna].fillna("No informado")

    # Eliminamos jugadores sin datos esenciales para el análisis.
    datos = datos.dropna(subset=["overall", "potential", "age"])

    # Creamos una columna con la primera posición del jugador.
    datos["posicion_principal"] = (
        datos["player_positions"].str.split(",").str[0].str.strip()
    )

    return datos


# ------------------------------------------------------------
# 4. FUNCION PARA APLICAR LOS FILTROS
# ------------------------------------------------------------
def filtrar_jugadores(datos, nacionalidades, ligas, posiciones,
                      rango_edad, rango_valoracion, pie):
    """Devuelve solamente los jugadores que cumplen los filtros."""

    filtrados = datos.copy()

    if nacionalidades:
        filtrados = filtrados[
            filtrados["nationality_name"].isin(nacionalidades)
        ]

    if ligas:
        filtrados = filtrados[
            filtrados["league_name"].isin(ligas)
        ]

    if posiciones:
        filtrados = filtrados[
            filtrados["posicion_principal"].isin(posiciones)
        ]

    filtrados = filtrados[
        filtrados["age"].between(rango_edad[0], rango_edad[1])
    ]

    filtrados = filtrados[
        filtrados["overall"].between(
            rango_valoracion[0], rango_valoracion[1]
        )
    ]

    if pie != "Todos":
        filtrados = filtrados[filtrados["preferred_foot"] == pie]

    return filtrados


# ------------------------------------------------------------
# 5. CARGA Y PREPARACION INICIAL
# ------------------------------------------------------------
try:
    df_original = cargar_datos()
    df = preparar_datos(df_original)
except FileNotFoundError:
    st.error("No se encontró players_22.csv. Coloca el CSV en la misma carpeta que app.py.")
    st.stop()
except Exception as error:
    st.error(f"Ocurrió un problema al cargar los datos: {error}")
    st.stop()


# ------------------------------------------------------------
# 6. TITULO Y DESCRIPCION
# ------------------------------------------------------------
st.title("⚽ FIFA 22: Explorador de jugadores")
st.markdown(
    """
    Aplicación interactiva para explorar y comparar futbolistas de FIFA 22.
    Utiliza los filtros para analizar jugadores según su nacionalidad,
    liga, posición, edad, valoración y pie preferido.
    """
)

st.info(
    "Instrucciones: selecciona los filtros de la barra lateral. "
    "Los indicadores, la tabla y los gráficos se actualizarán automáticamente."
)

# ------------------------------------------------------------
# 7. BARRA LATERAL: FILTROS INTERACTIVOS
# ------------------------------------------------------------
st.sidebar.header("Filtros de búsqueda")
st.sidebar.write("Selecciona las características de los jugadores.")

lista_nacionalidades = sorted(df["nationality_name"].unique())
nacionalidades = st.sidebar.multiselect(
    "Nacionalidad",
    options=lista_nacionalidades,
    default=[]
)

lista_ligas = sorted(df["league_name"].unique())
ligas = st.sidebar.multiselect(
    "Liga",
    options=lista_ligas,
    default=[]
)

lista_posiciones = sorted(df["posicion_principal"].dropna().unique())
posiciones = st.sidebar.multiselect(
    "Posición principal",
    options=lista_posiciones,
    default=[]
)

edad_min = int(df["age"].min())
edad_max = int(df["age"].max())
rango_edad = st.sidebar.slider(
    "Rango de edad",
    min_value=edad_min,
    max_value=edad_max,
    value=(edad_min, edad_max)
)

rango_valoracion = st.sidebar.slider(
    "Valoración general",
    min_value=0,
    max_value=100,
    value=(50, 100)
)

pie = st.sidebar.radio(
    "Pie preferido",
    options=["Todos", "Right", "Left"],
    horizontal=True
)

# Botón adicional para mostrar u ocultar registros.
mostrar_datos_completos = st.sidebar.checkbox(
    "Mostrar más columnas en la tabla",
    value=False
)

# ------------------------------------------------------------
# 8. APLICAR FILTROS
# ------------------------------------------------------------
df_filtrado = filtrar_jugadores(
    df,
    nacionalidades,
    ligas,
    posiciones,
    rango_edad,
    rango_valoracion,
    pie
)

st.divider()
st.header("Resumen de los jugadores seleccionados")

# ------------------------------------------------------------
# 9. INDICADORES PRINCIPALES
# ------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

cantidad_jugadores = len(df_filtrado)

if cantidad_jugadores > 0:
    promedio_overall = df_filtrado["overall"].mean()
    promedio_potencial = df_filtrado["potential"].mean()
    promedio_edad = df_filtrado["age"].mean()

    col1.metric("Jugadores encontrados", f"{cantidad_jugadores:,}")
    col2.metric("Valoración promedio", f"{promedio_overall:.1f}")
    col3.metric("Potencial promedio", f"{promedio_potencial:.1f}")
    col4.metric("Edad promedio", f"{promedio_edad:.1f} años")
else:
    col1.metric("Jugadores encontrados", "0")
    col2.metric("Valoración promedio", "Sin datos")
    col3.metric("Potencial promedio", "Sin datos")
    col4.metric("Edad promedio", "Sin datos")
    st.warning("No hay jugadores que cumplan todos los filtros seleccionados.")

# ------------------------------------------------------------
# 10. PESTAÑAS PARA ORGANIZAR LA INTERFAZ
# ------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "Tabla de jugadores",
    "Gráficos",
    "Comparación",
    "Información del dataset"
])

# ------------------------------------------------------------
# PESTAÑA 1: TABLA DE JUGADORES
# ------------------------------------------------------------
with tab1:
    st.subheader("Listado de jugadores")

    columnas_tabla = [
        "short_name", "age", "nationality_name", "club_name",
        "player_positions", "overall", "potential",
        "value_eur", "preferred_foot"
    ]

    if mostrar_datos_completos:
        columnas_tabla += [
            "pace", "shooting", "passing", "dribbling",
            "defending", "physic"
        ]

    tabla = df_filtrado[columnas_tabla].copy()

    tabla = tabla.rename(columns={
        "short_name": "Jugador",
        "age": "Edad",
        "nationality_name": "Nacionalidad",
        "club_name": "Club",
        "player_positions": "Posiciones",
        "overall": "Valoración",
        "potential": "Potencial",
        "value_eur": "Valor (€)",
        "preferred_foot": "Pie preferido",
        "pace": "Velocidad",
        "shooting": "Tiro",
        "passing": "Pase",
        "dribbling": "Regate",
        "defending": "Defensa",
        "physic": "Físico"
    })

    st.dataframe(tabla, use_container_width=True, hide_index=True)

    st.caption(
        f"Se muestran {len(tabla):,} jugadores después de aplicar los filtros."
    )

# ------------------------------------------------------------
# PESTAÑA 2: GRAFICOS
# ------------------------------------------------------------
with tab2:
    st.subheader("Análisis visual de los jugadores")

    if not df_filtrado.empty:
        # GRAFICO 1: Barras - promedio de valoración por club.
        datos_clubes = (
            df_filtrado.groupby("club_name")["overall"]
            .mean()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )

        grafico_barras = px.bar(
            datos_clubes,
            x="club_name",
            y="overall",
            title="Top 10 clubes según valoración promedio",
            labels={
                "club_name": "Club",
                "overall": "Valoración promedio"
            }
        )
        st.plotly_chart(grafico_barras, use_container_width=True)

        # GRAFICO 2: Histograma - distribución de edades.
        grafico_histograma = px.histogram(
            df_filtrado,
            x="age",
            nbins=15,
            title="Distribución de edades de los jugadores",
            labels={"age": "Edad", "count": "Cantidad de jugadores"}
        )
        st.plotly_chart(grafico_histograma, use_container_width=True)

        # GRAFICO 3: Dispersión - valoración frente a potencial.
        grafico_dispersion = px.scatter(
            df_filtrado,
            x="overall",
            y="potential",
            color="age",
            hover_name="short_name",
            title="Relación entre valoración general y potencial",
            labels={
                "overall": "Valoración general",
                "potential": "Potencial",
                "age": "Edad"
            }
        )
        st.plotly_chart(grafico_dispersion, use_container_width=True)
    else:
        st.warning("No hay datos suficientes para generar los gráficos.")

# ------------------------------------------------------------
# PESTAÑA 3: COMPARACION DE JUGADORES
# ------------------------------------------------------------
with tab3:
    st.subheader("Comparar dos futbolistas")

    nombres_jugadores = sorted(df["short_name"].dropna().unique())

    if len(nombres_jugadores) >= 2:
        jugador_1 = st.selectbox(
            "Selecciona el primer jugador",
            options=nombres_jugadores,
            index=0
        )

        jugador_2 = st.selectbox(
            "Selecciona el segundo jugador",
            options=nombres_jugadores,
            index=1
        )

        datos_j1 = df[df["short_name"] == jugador_1].iloc[0]
        datos_j2 = df[df["short_name"] == jugador_2].iloc[0]

        comparacion = pd.DataFrame({
            "Estadística": [
                "Valoración", "Potencial", "Velocidad",
                "Tiro", "Pase", "Regate", "Defensa", "Físico"
            ],
            jugador_1: [
                datos_j1["overall"], datos_j1["potential"],
                datos_j1["pace"], datos_j1["shooting"],
                datos_j1["passing"], datos_j1["dribbling"],
                datos_j1["defending"], datos_j1["physic"]
            ],
            jugador_2: [
                datos_j2["overall"], datos_j2["potential"],
                datos_j2["pace"], datos_j2["shooting"],
                datos_j2["passing"], datos_j2["dribbling"],
                datos_j2["defending"], datos_j2["physic"]
            ]
        })

        st.dataframe(comparacion, use_container_width=True, hide_index=True)

        comparacion_larga = comparacion.melt(
            id_vars="Estadística",
            var_name="Jugador",
            value_name="Puntuación"
        )

        grafico_comparacion = px.bar(
            comparacion_larga,
            x="Estadística",
            y="Puntuación",
            color="Jugador",
            barmode="group",
            title="Comparación de estadísticas"
        )
        st.plotly_chart(grafico_comparacion, use_container_width=True)
    else:
        st.warning("No hay suficientes jugadores para realizar una comparación.")

# ------------------------------------------------------------
# PESTAÑA 4: INFORMACION Y CALIDAD DE LOS DATOS
# ------------------------------------------------------------
with tab4:
    st.subheader("Información general del conjunto de datos")

    col_a, col_b = st.columns(2)
    col_a.metric("Filas originales", f"{len(df_original):,}")
    col_b.metric("Filas después de limpieza", f"{len(df):,}")

    st.write("**Cantidad de columnas:**", df.shape[1])
    st.write("**Jugadores duplicados eliminados:**",
             len(df_original) - len(df))

    st.markdown("#### Valores faltantes en variables principales")
    columnas_revision = [
        "overall", "potential", "age", "value_eur",
        "pace", "shooting", "passing", "dribbling"
    ]

    faltantes = df_original[columnas_revision].isna().sum().reset_index()
    faltantes.columns = ["Variable", "Valores faltantes"]
    st.dataframe(faltantes, use_container_width=True, hide_index=True)

    st.markdown("#### Tipos de datos")
    tipos = df.dtypes.astype(str).reset_index()
    tipos.columns = ["Variable", "Tipo de dato"]
    st.dataframe(tipos, use_container_width=True, hide_index=True)

    st.markdown("#### Fuente de los datos")
    st.write("Archivo utilizado: `players_22.csv`")
    st.write(
        "Dataset de jugadores de FIFA 22. "
        "Referencia del conjunto de datos: "
        "[FIFA 22 Complete Player Dataset - Kaggle]"
        "(https://www.kaggle.com/datasets/stefanoleone992/fifa-22-complete-player-dataset)."
    )
    st.caption(
        "Los valores económicos corresponden al dataset de FIFA 22 y no "
        "representan necesariamente precios actuales del mercado."
    )

# ------------------------------------------------------------
# 11. PIE DE PAGINA
# ------------------------------------------------------------
st.divider()
st.caption(
    "Tercera Solemne | Taller de Programación II | "
    "Dashboard desarrollado con Streamlit y pandas."
)
