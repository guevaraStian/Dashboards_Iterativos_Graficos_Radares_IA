# Dashboard con informacion de homicidios en colombia por departamento del pais, con IA
# Se solicita la informacion a una API web con los datos de los homicidios en colombia y e crea
# Una tabla, una grafica, mapa y un pronostico del siguiente numero, por departamento y año
# pip install flask pandas requests dash
# pip 25.3.1
# Python 3.13.1

import requests
import pandas as pd
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Se guardan los datos de la api
URL = "https://www.datos.gov.co/resource/m8fd-ahd9.json"
params = {"$limit": 10000000}

response = requests.get(URL, params=params)
response.raise_for_status()

data = response.json()
df = pd.DataFrame(data)

# De la informacion traida se extraen las columnas
posibles_fechas = ["fecha_hecho", "fecha", "fecha_del_hecho"]
col_fecha = None

for c in posibles_fechas:
    if c in df.columns:
        col_fecha = c
        break

if col_fecha is None:
    raise Exception("(-) No se encontraron columnas en la informacion")

df.rename(columns={col_fecha: "fecha_hecho"}, inplace=True)
df["fecha_hecho"] = pd.to_datetime(df["fecha_hecho"], errors="coerce")
df["anio"] = df["fecha_hecho"].dt.year
df["departamento"] = df["departamento"].str.upper()
df = df.dropna(subset=["anio", "departamento"])
df["anio"] = df["anio"].astype(int)
anios_disponibles = sorted(df["anio"].unique())

# Se indican coordenadas de departamentos en colombia
# Para indicar en el mapa
coords_departamentos = {
    "AMAZONAS": [-1.45, -70.23],
    "ANTIOQUIA": [7.13, -75.43],
    "ARAUCA": [7.08, -70.76],
    "ATLANTICO": [10.73, -74.92],
    "BOLIVAR": [10.05, -74.86],
    "BOYACA": [5.52, -73.36],
    "CALDAS": [5.3, -75.3],
    "CAQUETA": [1.81, -75.67],
    "CASANARE": [5.33, -71.42],
    "CAUCA": [2.57, -76.54],
    "CESAR": [10.33, -73.25],
    "CHOCO": [5.6, -76.67],
    "CORDOBA": [8.8, -75.88],
    "CUNDINAMARCA": [4.75, -74.05],
    "GUAINIA": [2.57, -69.75],
    "GUAVIARE": [2.57, -72.64],
    "HUILA": [2.78, -75.31],
    "LA_GUAJIRA": [11.38, -72.53],
    "MAGDALENA": [10.41, -74.45],
    "META": [4.25, -73.58],
    "NARIÑO": [1.21, -77.28],
    "NORTE_DE_SANTANDER": [7.86, -72.51],
    "PUTUMAYO": [0.21, -76.88],
    "QUINDIO": [4.56, -75.67],
    "RISARALDA": [5.2, -75.78],
    "SAN_ANDRES": [12.56, -81.71],
    "SANTANDER": [7.13, -73.12],
    "SUCRE": [9.25, -75.35],
    "TOLIMA": [4.09, -75.2],
    "VALLE_DEL_CAUCA": [3.45, -76.53],
    "VAUPES": [1.25, -70.3],
    "VICHADA": [5.35, -69.35]
}

# En el siguiente codigo se crea el dashboard
app = dash.Dash(__name__)

app.layout = html.Div(
    style={"width": "95%", "margin": "auto", "backgroundColor": "black", "color": "red", "minHeight": "100vh", "padding": "20px"},
    children=[
        html.H1(
            "Homicidios en Colombia (filtrado por año de fecha_hecho)",
            style={"textAlign": "center"}
        ),
        html.H4(
            f"Fecha de hoy: {datetime.now().strftime('%d-%m-%Y')}",
            style={"textAlign": "center", "color": "red"}
        ),

        html.Label("Seleccione el año (fecha_hecho):", style={"color": "red"}),
        dcc.Dropdown(
            id="select-anio",
            options=[{"label": str(a), "value": a} for a in anios_disponibles],
            value=anios_disponibles[0],
            clearable=False,
            style={"color": "black"}
        ),

        html.Hr(style={"borderColor": "red"}),

        html.H3("Tabla de homicidios del año seleccionado", style={"color": "red"}),
        dash_table.DataTable(
            id="tabla-homicidios",
            page_size=10,
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": "red",
                "color": "black",
                "fontWeight": "bold",
                "textAlign": "center"
            },
            style_cell={
                "textAlign": "left",
                "fontFamily": "Arial",
                "fontSize": "12px",
                "backgroundColor": "gray",
                "color": "black"
            }
        ),

        html.Hr(style={"borderColor": "red"}),

        html.H3("Homicidios por departamento", style={"color": "red"}),
        dcc.Graph(id="grafica-barras"),

        html.Hr(style={"borderColor": "red"}),

        html.H3("Mapa de homicidios por departamento", style={"color": "red"}),
        dcc.Graph(id="mapa-colombia", style={"height": "800px"})
    ]
)

# Con el siguiente codigo se crea el dashboard
@app.callback(
    [
        Output("tabla-homicidios", "data"),
        Output("tabla-homicidios", "columns"),
        Output("grafica-barras", "figure"),
        Output("mapa-colombia", "figure")
    ],
    Input("select-anio", "value")
)
def actualizar_dashboard(anio_seleccionado):
    # Filtrar por año
    df_anio = df[df["anio"] == anio_seleccionado]

    # Tabla
    columnas = [{"name": c, "id": c} for c in df_anio.columns]
    data_tabla = df_anio.to_dict("records")

    # Procedemos a crear la grafica de barras
    conteo_departamento = (
        df_anio.groupby("departamento")
        .size()
        .reset_index(name="cantidad_homicidios")
        .sort_values("cantidad_homicidios", ascending=False)
    )

    fig_barras = px.bar(
        conteo_departamento,
        x="departamento",
        y="cantidad_homicidios",
        color="departamento",
        title=f"Homicidios por departamento en {anio_seleccionado}",
        labels={"departamento": "Departamento", "cantidad_homicidios": "Cantidad de homicidios"}
    )

    fig_barras.update_layout(
        template="plotly_dark",
        xaxis_tickangle=-45,
        font_color="red",
        plot_bgcolor="black",
        paper_bgcolor="black",
        showlegend=False
    )

    # El mapa colombiano indica donde hubo mas homicidios
    conteo_departamento["lat"] = conteo_departamento["departamento"].map(lambda x: coords_departamentos.get(x, [None, None])[0])
    conteo_departamento["lon"] = conteo_departamento["departamento"].map(lambda x: coords_departamentos.get(x, [None, None])[1])

    total_homicidios = conteo_departamento["cantidad_homicidios"].sum()
    conteo_departamento["porcentaje"] = conteo_departamento["cantidad_homicidios"] / total_homicidios * 100
    conteo_departamento["tamano"] = conteo_departamento["porcentaje"] * 5  # escala visual

    fig_mapa = go.Figure()

    # Puntos
    fig_mapa.add_trace(go.Scattergeo(
        lon=conteo_departamento["lon"],
        lat=conteo_departamento["lat"],
        mode='markers+text',
        text=[f"{row['departamento']}<br>{row['cantidad_homicidios']}" for idx, row in conteo_departamento.iterrows()],
        textposition="bottom center",
        marker=dict(
            size=conteo_departamento["tamano"] + 5,
            color='red',
            line=dict(width=0.5, color='darkred')
        ),
        hoverinfo='text'
    ))

    fig_mapa.update_layout(
        geo=dict(
            scope='south america',
            showcountries=True,
            countrycolor="white",
            showland=True,
            landcolor="rgb(243, 243, 243)",
            showlakes=True,
            lakecolor="lightblue",
            projection_scale=6,
            center=dict(lat=4.5, lon=-74),
            bgcolor='black'
        ),
        template="plotly_dark",
        font_color="red",
        title=f"Homicidios por departamento en {anio_seleccionado}",
        height=800
    )

    return data_tabla, columnas, fig_barras, fig_mapa

# El main de ejecucion
if __name__ == "__main__":
    app.run(debug=True)
