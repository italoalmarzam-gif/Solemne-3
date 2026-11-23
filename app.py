import io
import urllib.request
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Solemne 3 — FIFA 22 Analytics",
    layout="wide",
)

SOURCE_NAME = "FIFA 22 complete player dataset (Kaggle)"
SOURCE_URL = "https://www.kaggle.com/datasets/stefanoleone992/fifa-22-complete-player-dataset"


@st.cache_data
def cargar_y_preparar_datos(ruta_csv: str) -> tuple[pd.DataFrame, dict]:
  """Carga el CSV local, revisa duplicados/nulos y prepara columnas clave."""
  columnas_utiles = [
      "sofifa_id",
      "short_name",
      "long_name",
      "age",
      "overall",
      "potential",
      "club_name",
      "league_name",
      "nationality_name",
      "player_positions",
      "preferred_foot",
      "value_eur",
      "wage_eur",
      "pace",
      "shooting",
      "passing",
      "dribbling",
      "defending",
      "physic",
      "player_face_url",
  ]
  df = pd.read_csv(
      ruta_csv, usecols=lambda col: col in columnas_utiles, low_memory=False
  )

  duplicados_antes = int(df.duplicated().sum())
  df = df.drop_duplicates().copy()

  df["club_name"] = df["club_name"].fillna("Sin club").astype(str)
  df["league_name"] = df["league_name"].fillna("Sin liga").astype(str)
  df["nationality_name"] = (
      df["nationality_name"].fillna("Desconocida").astype(str)
  )

  for col in ["age", "overall", "potential", "value_eur", "wage_eur"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

  df["crecimiento_potencial"] = df["potential"] - df["overall"]

  resumen_calidad = {
      "filas_finales": len(df),
      "columnas_utilizadas": df.shape[1],
      "duplicados_eliminados": duplicados_antes,
      "nulos_valor_eur": int(df["value_eur"].isna().sum()),
  }
  return df, resumen_calidad


def filtrar_jugadores(
    df: pd.DataFrame,
    nombre: str,
    nacionalidad: str,
    pie: str,
    rango_overall: tuple[int, int],
    rango_edad: tuple[int, int],
) -> pd.DataFrame:
  """Aplica filtros efectivos sobre el DataFrame según la selección del usuario."""
  df_filtrado = df[
      (df["overall"] >= rango_overall[0])
      & (df["overall"] <= rango_overall[1])
      & (df["age"] >= rango_edad[0])
      & (df["age"] <= rango_edad[1])
  ].copy()

  if nacionalidad != "Todas":
    df_filtrado = df_filtrado[df_filtrado["nationality_name"] == nacionalidad]

  if pie != "Todos":
    df_filtrado = df_filtrado[df_filtrado["preferred_foot"] == pie]

  if nombre:
    df_filtrado = df_filtrado[
        df_filtrado["short_name"].str.contains(nombre, case=False, na=False)
    ]

  return df_filtrado


def graficar_top_overall(df_sel: pd.DataFrame) -> plt.Figure:
  """Gráfico 1 (Barras): Top 10 jugadores por valoración general."""
  top10 = df_sel.sort_values("overall", ascending=False).head(10)
  fig, ax = plt.subplots(figsize=(7, 4))
  ax.barh(
      top10["short_name"][::-1],
      top10["overall"][::-1],
      color="#1f77b4",
      label="Overall (0-100)",
  )
  ax.set_title("Top 10 jugadores según valoración general")
  ax.set_xlabel("Valoración general (puntos, escala 0-100)")
  ax.set_ylabel("Jugador")
  ax.legend(loc="lower right")
  plt.tight_layout()
  return fig


def graficar_edad_vs_overall(df_sel: pd.DataFrame) -> plt.Figure:
  """Gráfico 2 (Dispersión): Relación entre edad y valoración general."""
  fig, ax = plt.subplots(figsize=(7, 4))
  ax.scatter(
      df_sel["age"],
      df_sel["overall"],
      alpha=0.55,
      color="#ff7f0e",
      label="Jugadores filtrados",
  )
  ax.set_title("Edad vs. valoración general")
  ax.set_xlabel("Edad (años)")
  ax.set_ylabel("Valoración general (puntos, escala 0-100)")
  ax.legend(loc="best")
  plt.tight_layout()
  return fig


def graficar_distribucion_potencial(df_sel: pd.DataFrame) -> plt.Figure:
  """Gráfico 3 (Histograma): Distribución del potencial de jugadores."""
  fig, ax = plt.subplots(figsize=(7, 4))
  ax.hist(
      df_sel["potential"].dropna(),
      bins=15,
      color="#2ca02c",
      edgecolor="white",
      label="Frecuencia de jugadores",
  )
  ax.set_title("Distribución del potencial de jugadores")
  ax.set_xlabel("Potencial (puntos, escala 0-100)")
  ax.set_ylabel("Cantidad de jugadores")
  ax.legend(loc="upper left")
  plt.tight_layout()
  return fig


st.title("Explorador de Jugadores FIFA 22 — Solemne 3")
st.markdown(
    "**Propósito:** Analizar el rendimiento (`overall`, `potential`), edad y"
    " valoración de mercado (`value_eur` / `wage_eur`) de jugadores del"
    " videojuego FIFA 22 para comparar planteles, nacionalidades y perfiles."
)
st.markdown(
    f"**Fuente de datos:** [{SOURCE_NAME}]({SOURCE_URL}) — Cada fila"
    " representa un jugador; valores monetarios en euros (€), edad en años y"
    " valoraciones en escala de 0 a 100."
)
st.info(
    "**Instrucciones de uso:** 1) Ajusta los filtros en la barra lateral"
    " (nacionalidad, pie preferido, valoración, edad y búsqueda). 2) Revisa"
    " los indicadores, la ficha con foto al costado y los gráficos que se"
    " actualizan automáticamente. 3) Explora o descarga la tabla resultante."
)

df_jugadores, calidad = cargar_y_preparar_datos("players_22.csv")

with st.expander("Revisión de datos y calidad (pandas)"):
  st.write(
      "Registros listos: **"
      + f"{calidad['filas_finales']:,}"
      + "** | Columnas activas: **"
      + str(calidad["columnas_utilizadas"])
      + "** | Duplicados eliminados: **"
      + str(calidad["duplicados_eliminados"])
      + "** | Nulos en `value_eur`: **"
      + str(calidad["nulos_valor_eur"])
      + "**."
  )
  st.dataframe(df_jugadores.head(10), use_container_width=True)

# --- Barra lateral: Filtros interactivos ---
st.sidebar.header("Filtros de exploración")

filtro_nombre = st.sidebar.text_input(
    "Buscar jugador por nombre corto",
    placeholder="Ej: Messi, Haaland...",
).strip()

min_ovr, max_ovr = (
    int(df_jugadores["overall"].min()),
    int(df_jugadores["overall"].max()),
)
filtro_overall = st.sidebar.slider(
    "Rango de valoración general (overall)",
    min_value=min_ovr,
    max_value=max_ovr,
    value=(75, max_ovr),
)

min_age, max_age = (
    int(df_jugadores["age"].min()),
    int(df_jugadores["age"].max()),
)
filtro_edad = st.sidebar.slider(
    "Rango de edad (años)",
    min_value=min_age,
    max_value=max_age,
    value=(min_age, max_age),
)

opciones_nacion = ["Todas"] + sorted(
    df_jugadores["nationality_name"].dropna().unique().tolist()
)
filtro_nacion = st.sidebar.selectbox("Nacionalidad", opciones_nacion)

opciones_pie = ["Todos"] + sorted(
    df_jugadores["preferred_foot"].dropna().unique().tolist()
)
filtro_pie = st.sidebar.selectbox("Pie preferido", opciones_pie)

df_filtrado = filtrar_jugadores(
    df_jugadores,
    nombre=filtro_nombre,
    nacionalidad=filtro_nacion,
    pie=filtro_pie,
    rango_overall=filtro_overall,
    rango_edad=filtro_edad,
)

# --- Indicadores calculados (KPIs) ---
st.subheader("Indicadores principales según selección")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Jugadores filtrados", f"{len(df_filtrado):,}")
col2.metric(
    "Overall promedio",
    f"{df_filtrado['overall'].mean():.1f}" if not df_filtrado.empty else "—",
)
col3.metric(
    "Potencial promedio",
    f"{df_filtrado['potential'].mean():.1f}"
    if not df_filtrado.empty
    else "—",
)
col4.metric(
    "Valor de mercado promedio (€)",
    f"€{df_filtrado['value_eur'].mean():,.0f}"
    if not df_filtrado.empty and df_filtrado["value_eur"].notna().any()
    else "—",
)

st.divider()

if df_filtrado.empty:
  st.warning(
      "No hay jugadores que coincidan con los filtros actuales. Ajusta algún"
      " criterio en la barra lateral."
  )
else:
  # --- Ficha con foto al costado del jugador filtrado ---
  st.subheader("Detalle y foto del jugador")
  opciones_jugadores = {
      f"{row['short_name']} — {row['club_name']} (ID {int(row['sofifa_id'])})": (
          idx
      )
      for idx, row in df_filtrado.iterrows()
  }
  jugador_elegido = st.selectbox(
      "Jugador seleccionado del filtro",
      list(opciones_jugadores.keys()),
      index=0,
  )
  fila_jugador = df_filtrado.loc[opciones_jugadores[jugador_elegido]]

  col_foto, col_info = st.columns([1, 3])
  with col_foto:
    foto_url = str(fila_jugador.get("player_face_url", "")).strip()
    mostrada = False
    if foto_url.startswith("http"):
      try:
        req = urllib.request.Request(
            foto_url,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
          img_bytes = resp.read()
        st.image(
            io.BytesIO(img_bytes),
            caption=fila_jugador["short_name"],
            width=150,
        )
        mostrada = True
      except Exception:
        pass

    if not mostrada and foto_url.startswith("http"):
      try:
        st.image(
            foto_url,
            caption=fila_jugador["short_name"],
            width=150,
        )
        mostrada = True
      except Exception:
        pass

    if not mostrada:
      st.warning("No se pudo cargar la foto desde la URL.")

  with col_info:
    st.markdown(f"### {fila_jugador['long_name']}")
    st.write(f"**Club:** {fila_jugador['club_name']}")
    st.write(f"**Nacionalidad:** {fila_jugador['nationality_name']}")
    st.write(f"**Posiciones:** {fila_jugador['player_positions']}")
    valor_str = (
        f"€{fila_jugador['value_eur']:,.0f}"
        if pd.notna(fila_jugador["value_eur"])
        else "N/D"
    )
    st.write(
        f"**Edad:** {int(fila_jugador['age'])} años | **Overall:**"
        f" {int(fila_jugador['overall'])} | **Potencial:**"
        f" {int(fila_jugador['potential'])} | **Valor:** {valor_str}"
    )

  st.divider()

  # --- Tres gráficos distintos ---
  st.subheader("Visualizaciones de análisis")
  g1, g2 = st.columns(2)
  with g1:
    st.pyplot(graficar_top_overall(df_filtrado))
  with g2:
    st.pyplot(graficar_edad_vs_overall(df_filtrado))

  st.pyplot(graficar_distribucion_potencial(df_filtrado))

  # --- Tabla detallada y descarga ---
  st.subheader("Tabla de jugadores filtrados")
  columnas_tabla = [
      "short_name",
      "age",
      "nationality_name",
      "club_name",
      "player_positions",
      "overall",
      "potential",
      "value_eur",
      "wage_eur",
  ]
  st.dataframe(df_filtrado[columnas_tabla], use_container_width=True)

  st.download_button(
      label="Descargar datos filtrados en CSV",
      data=df_filtrado[columnas_tabla].to_csv(index=False).encode("utf-8"),
      file_name="jugadores_fifa22_filtrados.csv",
      mime="text/csv",
  )
