# Dashboard con informacion de homicidios en colombia por departamento del pais y el mes de cada año, con IA y machine learning
# Se solicita la informacion a una API web con los datos de los homicidios en colombia y e crea
# Una tabla, una grafica, mapa, calendario y un pronostico del siguiente numero, por departamento y dia
# pip install flask pandas requests dash
# pip 25.3.1
# Python 3.13.1

import pandas as pd        
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
import numpy as np
import calendar
import requests

# Se guardan las siguientes variables relacionadas a la consulta a la api
URL = "https://www.datos.gov.co/resource/m8fd-ahd9.json"
params = {"$limit": 1000000}
response = requests.get(URL, params=params)
response.raise_for_status()
data = response.json()
df = pd.DataFrame(data)

# Se asignan las variables de las fechas
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

# Luego se crea el dashboard con la informacion ingresada
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
        html.Div(id="tabla-homicidios"),

        html.Hr(),
        html.H3("Homicidios por día"),
        dcc.Graph(id="grafica-barras"),

        html.Hr(),
        html.H3("Calendario de homicidios"),
        html.Div(id="calendario"),

        html.Hr(),
        html.H3("Pronóstico de homicidios para 2026"),
        html.Div(id="tabla-pronosticos")
    ]
)

# Posteriormente creamos los callback con los select
@app.callback(
    Output("select-mes", "options"),
    Output("select-mes", "value"),
    Input("select-anio", "value")
)
def actualizar_meses(anio):
    meses = sorted(df[df["anio"] == anio]["mes"].unique())
    return [{"label": m, "value": m} for m in meses], meses[0]

@app.callback(
    Output("tabla-homicidios", "children"),
    Output("grafica-barras", "figure"),
    Output("calendario", "children"),
    Output("tabla-pronosticos", "children"),
    Input("select-anio", "value"),
    Input("select-mes", "value"),
    Input("select-departamento", "value")
)
def actualizar_dashboard(anio, mes, departamento):
    # La tabla de homicidios se muestra a continuacion
    df_f = df[(df["anio"] == anio) & (df["mes"] == mes) & (df["departamento"] == departamento)]
    tabla_hijos = html.Table([
        html.Thead(html.Tr([html.Th(c) for c in df_f.columns], style={"backgroundColor":"red","color":"black"})),
        html.Tbody([
            html.Tr([html.Td(row[c], style={"backgroundColor":"lightgray","color":"black"}) for c in df_f.columns])
            for idx, row in df_f.iterrows()
        ])
    ], style={"width":"100%", "border":"1px solid white", "borderCollapse":"collapse"})

    # La grafica de barras se crea con el siguiente codigo
    conteo_dias = df_f.groupby("dia").size().reset_index(name="cantidad")
    fig_barras = go.Figure()
    colors = px.colors.qualitative.Plotly
    for i, row in enumerate(conteo_dias.itertuples()):
        fig_barras.add_trace(go.Bar(
            x=[row.dia], y=[row.cantidad],
            text=[row.cantidad], textposition='inside',
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

    # Con el siguiente codigo se crea el calendario con colores especificos
    _, num_dias_mes = calendar.monthrange(anio, mes)
    dias_mes = list(range(1, num_dias_mes + 1))
    df_conteo = df_f.groupby("dia").size().reindex(dias_mes, fill_value=0)
    max_homicidios = df_conteo.max()
    min_homicidios = df_conteo.min()
    first_weekday = calendar.monthrange(anio, mes)[0]
    dias = [""] * first_weekday + dias_mes

    tabla_calendario = html.Table([
        html.Thead(html.Tr([html.Th(day) for day in ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]])),
        html.Tbody([
            html.Tr([
                html.Td(
                    html.Div(f"{dia}\n{df_conteo[dia] if dia!='' else ''}", 
                             style={
                                "backgroundColor": f"rgb({int(255*((df_conteo[dia]-min_homicidios)/(max_homicidios-min_homicidios) if max_homicidios!=min_homicidios else 0))},0,{int(255*(1-((df_conteo[dia]-min_homicidios)/(max_homicidios-min_homicidios) if max_homicidios!=min_homicidios else 0)))})" if dia!="" else "black",
                                "color":"white",
                                "height":"80px",
                                "whiteSpace":"pre-line",
                                "textAlign":"center",
                                "verticalAlign":"top"
                             })
                ) for dia in dias[i:i+7]
            ]) for i in range(0, len(dias), 7)
        ])
    ], style={"width":"100%", "border":"1px solid white", "borderCollapse":"collapse", "color":"white"})

    # Los siguientes codigos son para lograr el pronostico de la ultima tabla
    df_hist = df[(df["mes"] == mes) & (df["departamento"] == departamento)]
    if df_hist.empty:
        tabla_forecast = html.Div("No hay datos históricos")
    else:
        # Preparar datos
        X = df_hist[["anio", "dia"]]
        y = df_hist.groupby(["anio", "dia"]).size().reindex(
            pd.MultiIndex.from_frame(X), fill_value=0
        ).values
        # Modelo Random Forest
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        dias_mes_hist = sorted(df_hist["dia"].unique())
        X_pred = pd.DataFrame({"anio": 2026, "dia": dias_mes_hist})
        y_pred = model.predict(X_pred)
        y_pred = np.round(y_pred).astype(int)
        # Tabla pronóstico
        tabla_forecast = html.Table([
            html.Thead(html.Tr([html.Th("Día"), html.Th("Pronóstico")], style={"backgroundColor":"red","color":"black"})),
            html.Tbody([
                html.Tr([html.Td(dia, style={"backgroundColor":"lightgray","color":"black"}),
                         html.Td(pred, style={"backgroundColor":"lightgray","color":"black"})])
                for dia, pred in zip(dias_mes_hist, y_pred)
            ])
        ], style={"width":"100%", "border":"1px solid white", "borderCollapse":"collapse"})

    return tabla_hijos, fig_barras, tabla_calendario, tabla_forecast

# En el siguiente codigo se ejecuta el main
if __name__ == "__main__":
    app.run(debug=True)
