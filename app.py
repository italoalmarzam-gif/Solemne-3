
Italo Almarza <italo.almarza.m@gmail.com>
15:34 (hace 13 minutos)
para mí


import streamlit as st
import pandas as pd

# Configurar la pagina
st.set_page_config(
page_title="FIFA 22 Analytics",
page_icon="⚽",
layout="wide"
)

# Funcion para cargar la base de datos
@st.cache_data
def cargar_datos():
df = pd.read_csv("datos/players_22.csv", low_memory=False)
return df

df = cargar_datos()

# Titulo principal
st.title("⚽ FIFA 22 Analytics")
st.write("Dashboard interactivo de jugadores de FIFA 22")

# Filtros
st.sidebar.header("Filtros")

pais = st.sidebar.selectbox(
"Selecciona una nacionalidad",
["Todas"] + sorted(df["nationality_name"].dropna().unique().tolist())
)

valoracion = st.sidebar.slider(
"Valoracion minima",
40, 100, 40
)

# Aplicar filtros
df_filtrado = df[df["overall"] >= valoracion]

if pais != "Todas":
df_filtrado = df_filtrado[
df_filtrado["nationality_name"] == pais
]

# Indicadores
col1, col2 = st.columns(2)

with col1:
st.metric("Total de jugadores", len(df_filtrado))

with col2:
promedio = df_filtrado["overall"].mean()
st.metric(
"Valoracion promedio",
round(promedio, 1) if not pd.isna(promedio) else "Sin datos"
)

# Tabla
st.subheader("Jugadores FIFA 22")

columnas = [
"short_name",
"age",
"nationality_name",
"club_name",
"overall",
"potential"
]

st.dataframe(
df_filtrado[columnas],
use_container_width=True,
hide_index=True
)

# Grafico
st.subheader("Top 10 nacionalidades")

conteo = df_filtrado["nationality_name"].value_counts().head(10)
st.bar_chart(conteo)

st.caption(
"Fuente: FIFA 22 Complete Player Dataset - Kaggle"
)
