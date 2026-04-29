# Dashboard con informacion de homicidios en colombia por departamento del pais y el mes de cada año, con IA y machine learning
# Se solicita la informacion a una API web con los datos de los homicidios en colombia y e crea
# Una tabla, una grafica, mapa y un pronostico del siguiente numero, por departamento y dia
# pip install flask pandas requests dash
# pip 25.3.1
# Python 3.13.1

import requests 
import pandas as pd
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
import numpy as np

# Se guardan la variables relacionadas a la api
URL = "https://www.datos.gov.co/resource/m8fd-ahd9.json"
params = {"$limit": 1000000}

response = requests.get(URL, params=params)
response.raise_for_status()

data = response.json()
df = pd.DataFrame(data)

# Se limpian los datos relacionados a la fecha
posibles_fechas = ["fecha_hecho", "fecha", "fecha_del_hecho"]
col_fecha = next((c for c in posibles_fechas if c in df.columns), None)

if col_fecha is None:
    raise Exception("(-) No se encontró columna de fecha en el dataset")

df.rename(columns={col_fecha: "fecha_hecho"}, inplace=True)
df["fecha_hecho"] = pd.to_datetime(df["fecha_hecho"], errors="coerce")

df["anio"] = df["fecha_hecho"].dt.year
df["mes"] = df["fecha_hecho"].dt.month
df["dia"] = df["fecha_hecho"].dt.day
df["departamento"] = df["departamento"].str.upper()

df = df.dropna(subset=["anio", "mes", "dia", "departamento"])
df[["anio", "mes", "dia"]] = df[["anio", "mes", "dia"]].astype(int)

anios_disponibles = sorted(df["anio"].unique())
departamentos_disponibles = sorted(df["departamento"].unique())

# Ubicacion de cada departamento en colombia
centroides_departamentos = {
    "AMAZONAS": [-69.9333, -1.4433],
    "ANTIOQUIA": [-75.5636, 6.2518],
    "ARAUCA": [-70.7333, 7.0833],
    "ATLANTICO": [-75.5247, 10.4230],
    "BOLIVAR": [-75.5000, 10.4000],
    "BOYACA": [-73.3500, 5.5500],
    "CALDAS": [-75.5138, 5.0703],
    "CAQUETA": [-75.6667, 1.5833],
    "CASANARE": [-71.7333, 5.3667],
    "CAUCA": [-76.0000, 2.5000],
    "CESAR": [-73.2500, 10.9833],
    "CHOCO": [-76.6413, 5.6936],
    "CORDOBA": [-75.8800, 8.7700],
    "CUNDINAMARCA": [-74.0758, 4.5981],
    "GUAINIA": [-69.7500, 2.5667],
    "GUAVIARE": [-72.6333, 2.5667],
    "HUILA": [-75.2800, 2.9300],
    "LA GUAJIRA": [-72.9000, 11.5400],
    "MAGDALENA": [-74.2500, 10.5000],
    "META": [-73.6140, 4.1560],
    "NARIÑO": [-77.2719, 1.2141],
    "NORTE DE SANTANDER": [-72.4967, 7.8891],
    "PUTUMAYO": [-76.5417, 0.1521],
    "QUINDIO": [-75.7688, 4.5617],
    "RISARALDA": [-75.6946, 4.8517],
    "SAN ANDRES Y PROVIDENCIA": [-81.7000, 12.5847],
    "SANTANDER": [-73.1198, 7.1254],
    "SUCRE": [-75.3977, 9.3070],
    "TOLIMA": [-75.2322, 4.4359],
    "VALLE DEL CAUCA": [-76.5225, 3.4372],
    "VAUPES": [-70.2500, 1.5833],
    "VICHADA": [-69.1000, 4.6000],
}

# Se procede a crear el dashboard
app = dash.Dash(__name__)

fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

app.layout = html.Div(
    style={
        "width": "95%",
        "margin": "auto",
        "backgroundColor": "black",
        "color": "red",
        "padding": "15px"
    },
    children=[
        html.H1("Homicidios en Colombia (Filtros por Fecha y Departamento)", style={"textAlign": "center"}),
        html.H4(f"Fecha y hora actual: {fecha_actual}", style={"textAlign": "center"}),

        html.Label("Seleccione el año:"),
        dcc.Dropdown(
            id="select-anio",
            options=[{"label": str(a), "value": a} for a in anios_disponibles],
            value=anios_disponibles[0],
            clearable=False
        ),

        html.Label("Seleccione el mes:"),
        dcc.Dropdown(id="select-mes", clearable=False),

        html.Label("Seleccione el departamento:"),
        dcc.Dropdown(
            id="select-departamento",
            options=[{"label": d, "value": d} for d in departamentos_disponibles],
            value=departamentos_disponibles[0],
            clearable=False
        ),

        html.Hr(),

        html.H3("Tabla de homicidios filtrada"),
        dash_table.DataTable(
            id="tabla-homicidios",
            page_size=10,
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": "red",
                "color": "black",
                "fontWeight": "bold"
            },
            style_cell={
                "backgroundColor": "lightgray",
                "color": "black",
                "textAlign": "left",
                "fontFamily": "Arial",
                "fontSize": "12px"
            }
        ),

        html.Hr(),

        html.H3("Homicidios por día"),
        dcc.Graph(id="grafica-barras"),

        html.Hr(),

        html.H3("Pronóstico de homicidios para 2026"),
        dash_table.DataTable(
            id="tabla-pronosticos",
            page_size=100,  # Mostrar todo en una sola página
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": "red",
                "color": "black",
                "fontWeight": "bold"
            },
            style_cell={
                "backgroundColor": "lightgray",
                "color": "black",
                "textAlign": "center",
                "fontFamily": "Arial",
                "fontSize": "12px"
            }
        )
    ]
)

# Se crean los callback
@app.callback(
    Output("select-mes", "options"),
    Output("select-mes", "value"),
    Input("select-anio", "value")
)
def actualizar_meses(anio):
    meses = sorted(df[df["anio"] == anio]["mes"].unique())
    return [{"label": m, "value": m} for m in meses], meses[0]

@app.callback(
    Output("tabla-homicidios", "data"),
    Output("tabla-homicidios", "columns"),
    Output("grafica-barras", "figure"),
    Output("tabla-pronosticos", "data"),
    Output("tabla-pronosticos", "columns"),
    Input("select-anio", "value"),
    Input("select-mes", "value"),
    Input("select-departamento", "value")
)
def actualizar_dashboard(anio, mes, departamento):
    # Se guardan los datos de la tabla general
    df_f = df[(df["anio"] == anio) & (df["mes"] == mes) & (df["departamento"] == departamento)]
    columnas = [{"name": c, "id": c} for c in df_f.columns]
    data_tabla = df_f.to_dict("records")

    # Se crea la grafica de barras
    conteo_dias = df_f.groupby("dia").size().reset_index(name="cantidad")
    fig_barras = go.Figure()
    colors = px.colors.qualitative.Plotly
    for i, row in enumerate(conteo_dias.itertuples()):
        fig_barras.add_trace(go.Bar(
            x=[row.dia],
            y=[row.cantidad],
            text=[row.cantidad],
            textposition='inside',
            marker_color=colors[i % len(colors)],
            name=f'Día {row.dia}'
        ))
    fig_barras.update_layout(
        title=f"Homicidios en {departamento} - {mes}/{anio}",
        xaxis_title="Día",
        yaxis_title="Cantidad",
        template="plotly_dark",
        showlegend=False
    )

    # A continuacion la logica del pronostico con machine learning
    # Construir dataset diario histórico para el departamento y mes seleccionado
    df_hist = df[(df["mes"] == mes) & (df["departamento"] == departamento)]
    if df_hist.empty:
        df_forecast = pd.DataFrame({"Día": [], "Pronóstico": []})
    else:
        X = df_hist[["anio", "dia"]]
        y = df_hist.groupby(["anio", "dia"]).size().reindex(
            pd.MultiIndex.from_frame(X), fill_value=0
        ).values
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)

        dias_mes = sorted(df_hist["dia"].unique())
        X_pred = pd.DataFrame({"anio": 2026, "dia": dias_mes})
        y_pred = model.predict(X_pred)
        y_pred = np.round(y_pred).astype(int)
        df_forecast = pd.DataFrame({"Día": dias_mes, "Pronóstico": y_pred})

    columnas_forecast = [{"name": c, "id": c} for c in df_forecast.columns]
    data_forecast = df_forecast.to_dict("records")

    return data_tabla, columnas, fig_barras, data_forecast, columnas_forecast

# Se crea el main de ejecucion
if __name__ == "__main__":
    app.run(debug=True)
