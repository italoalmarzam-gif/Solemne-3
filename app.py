from pathlib import Path
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
def cargar_y_preparar_datos(ruta_csv: str):
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
    rango_overall: tuple,
    rango_edad: tuple,
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
    " los indicadores, el detalle del jugador y los gráficos que se"
    " actualizan automáticamente. 3) Explora o descarga la tabla resultante."
)

ruta_csv = "players_22.csv"
if not Path(ruta_csv).exists():
  st.error(
      "No se encontró `players_22.csv` en la carpeta principal del"
      " repositorio."
  )
  st.stop()

df_jugadores, calidad = cargar_y_preparar_datos(ruta_csv)

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
  st.dataframe
