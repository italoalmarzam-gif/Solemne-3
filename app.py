import io
from pathlib import Path
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

LINKS_JUGADORES = {
    158023: "https://cdn.sofifa.net/players/158/023/22_120.png",
    231747: "https://cdn.sofifa.net/players/231/747/22_120.png",
    20801: "https://cdn.sofifa.net/players/020/801/22_120.png",
}


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
      "player_face_url",
  ]
  df = pd.read_csv(
      ruta_csv, usecols=lambda col: col in columnas_utiles, low_memory=False
  )

  duplicados_antes = int(df.duplicated().sum())
  df = df.drop_duplicates().copy()

  if Path("fotos_jugadores_fifa22.csv").exists():
    df_fotos = pd.read_csv(
        "fotos_jugadores_fifa22.csv",
        usecols=["sofifa_id", "player_face_url"],
        low_memory=False,
    ).drop_duplicates(subset=["sofifa_id"])
    df = df.drop(columns=["player_face_url"], errors="ignore").merge(
        df_fotos, on="sofifa_id", how="left"
    )

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


@st.cache_data(show_spinner=False)
def descargar_imagen_bytes(url: str):
  """Intenta descargar bytes de imagen desde una URL directa."""
  if not url or not url.startswith("http"):
    return None
  try:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://sofifa.com/",
        },
    )
    with urllib.request.urlopen(req, timeout=6) as resp:
      return resp.read()
  except Exception:
    return None


def mostrar_foto_jugador(fila_jugador: pd.Series, link_manual: str = "") -> None:
  """Muestra foto desde link manual, archivo local en fotos/, o URL del CSV."""
  sid = int(fila_jugador["sofifa_id"])
  nombre = str(fila_jugador["short_name"])

  if link_manual.startswith("http"):
    try:
      st.image(link_manual, caption=nombre, width=150)
      return
    except Exception:
      st.warning("No se pudo cargar la imagen desde el link pegado.")

  for ext in ["png", "jpg", "jpeg", "webp"]:
    ruta_local = Path("fotos") / f"{sid}.{ext}"
    if ruta_local.exists():
      st.image(str(ruta_local), caption=nombre, width=150)
      return

  link_por_defecto = LINKS_JUGADORES.get(sid) or str(
      fila_jugador.get("player_face_url", "")
  ).strip()

  img_bytes = descargar_imagen_bytes(link_por_defecto)
  if img_bytes:
    st.image(io.BytesIO(img_bytes), caption=nombre, width=150)
    return

  if link_por_defecto.startswith("http"):
    try:
      st.image(link_por_defecto, caption=nombre, width=150)
      return
    except Exception:
      pass

  st.caption("Foto no disponible en este momento.")


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
