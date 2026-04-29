# Dashboard con informacion de equipos de 5 ligas de futbol europeo, con IA
# Se solicita la informacion a una API web con todos los datos del equipo y con eso se crea
# Una tabla, una grafica y un pronostico del siguiente numero
# pip install flask pandas requests lxml beautifulsoup4
# pip 25.3.1
# Python 3.13.1

import os
import requests
import pandas as pd
import numpy as np
from dash import Dash, html, dcc, dash_table
from dash.dependencies import Output, Input
from sklearn.neural_network import MLPRegressor
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Se crea la carpeta Archivos
if not os.path.exists("Archivos"):
    os.makedirs("Archivos")

# Se guarda en una variable, la fecha y hora actual
fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Ligas disponibles
LIGAS = {
    "Premier League (ING)": "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/en.1.json",
    "La Liga (ESP)": "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/es.1.json",
    "Serie A (ITA)": "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/it.1.json",
    "Bundesliga (GER)": "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/de.1.json",
    "Ligue 1 (FRA)": "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/fr.1.json"
}

# La siguiente funcion se carga la liga escogida
def cargar_liga(url):
    response = requests.get(url)
    data = response.json()

    matches = data.get("matches", [])
    df = pd.DataFrame(matches)

    df['Team1'] = df['team1'].apply(lambda x: x if isinstance(x, str) else x.get('name', ''))
    df['Team2'] = df['team2'].apply(lambda x: x if isinstance(x, str) else x.get('name', ''))
    df['Date'] = pd.to_datetime(df['date'], errors='coerce')
    df['Score'] = df['score'].apply(lambda s: f"{s.get('ft')[0]} - {s.get('ft')[1]}" if s else None)
    df[['Goals1', 'Goals2']] = df['Score'].str.split(' - ', expand=True).astype(float)
    df.dropna(subset=['Goals1', 'Goals2'], inplace=True)

    return df

# Con el siguiente codigo, se construye el dashboard
app = Dash(__name__)

app.layout = html.Div(
    style={'backgroundColor': 'black', 'color': 'red', 'padding': '10px', 'fontFamily': 'Arial'},
    children=[

        html.H1("Predicción de Partidos por Liga y Equipo", style={'textAlign': 'center'}),
        html.H4(f"Fecha y hora actual: {fecha_actual}", style={'textAlign': 'center'}),

        # El codigo a continuacion es un Select de html en dashboard
        html.Div([
            html.Label("Selecciona una liga:", style={'color': 'red'}),
            dcc.Dropdown(
                id='dropdown-liga',
                options=[{'label': k, 'value': k} for k in LIGAS.keys()],
                value=list(LIGAS.keys())[0],
                style={'color': 'black'}
            )
        ], style={'maxWidth': '400px', 'margin': 'auto'}),

        html.Br(),

        # Ejemplo de select en dashboar de equipos de la liga escogida anteriormente 
        html.Div([
            html.Label("Selecciona un equipo:", style={'color': 'red'}),
            dcc.Dropdown(id='dropdown-equipo', style={'color': 'black'})
        ], style={'maxWidth': '400px', 'margin': 'auto'}),

        html.Div(id='prediccion-output', style={'marginTop': 20, 'textAlign': 'center'}),

        html.Hr(style={'borderColor': 'red'}),

        html.H3("Histórico de Partidos del Equipo", style={'textAlign': 'center'}),
        dash_table.DataTable(
            id='tabla-partidos',
            columns=[
                {"name": "Fecha", "id": "Date"},
                {"name": "Local/Visitante", "id": "Home/Away"},
                {"name": "Rival", "id": "Rival"},
                {"name": "Goles a Favor", "id": "GF"},
                {"name": "Goles en Contra", "id": "GC"},
            ],
            page_size=10,
            style_cell={'textAlign': 'center', 'backgroundColor': 'gray', 'color': 'black'},
            style_header={'backgroundColor': 'red', 'fontWeight': 'bold'}
        ),

        html.Hr(style={'borderColor': 'red'}),

        dcc.Graph(id='bar-goles'),
        dcc.Graph(id='pie-goles-favor'),
        dcc.Graph(id='pie-goles-contra')
    ]
)

# Posteriormente se crean las funciones de callbacks
@app.callback(
    Output('dropdown-equipo', 'options'),
    Output('dropdown-equipo', 'value'),
    Input('dropdown-liga', 'value')
)
def actualizar_equipos(liga):
    df = cargar_liga(LIGAS[liga])
    equipos = sorted(set(df['Team1']).union(df['Team2']))
    return [{'label': e, 'value': e} for e in equipos], equipos[0]

# Callback principañ
@app.callback(
    Output('prediccion-output', 'children'),
    Output('tabla-partidos', 'data'),
    Output('bar-goles', 'figure'),
    Output('pie-goles-favor', 'figure'),
    Output('pie-goles-contra', 'figure'),
    Input('dropdown-liga', 'value'),
    Input('dropdown-equipo', 'value')
)
def actualizar_dashboard(liga, equipo):

    df = cargar_liga(LIGAS[liga])
    df_equipo = df[(df['Team1'] == equipo) | (df['Team2'] == equipo)]

    if df_equipo.empty:
        return "No hay datos disponibles.", [], {}, {}, {}

    tabla, gf_list, gc_list, rivales = [], [], [], []

    for _, r in df_equipo.iterrows():
        if r['Team1'] == equipo:
            gf, gc, rival, ha = r['Goals1'], r['Goals2'], r['Team2'], "Local"
        else:
            gf, gc, rival, ha = r['Goals2'], r['Goals1'], r['Team1'], "Visitante"

        tabla.append({
            "Date": r['Date'].strftime("%Y-%m-%d"),
            "Home/Away": ha,
            "Rival": rival,
            "GF": gf,
            "GC": gc
        })

        gf_list.append(gf)
        gc_list.append(gc)
        rivales.append(rival)

    # Lineas de codigo para crear la prediccion con machine learnig inteligencia artificial
    X = np.arange(len(df_equipo)).reshape(-1, 1)
    model = MLPRegressor(max_iter=1000, random_state=42)
    model.fit(X, gf_list)
    pred = round(model.predict([[len(df_equipo)]])[0], 1)

    pred_text = f"Predicción del próximo partido de {equipo}: {pred} goles"

    # Cracion del grafico d barras
    equipos = sorted(set(df['Team1']).union(df['Team2']))
    total_GF = [
        df.apply(lambda r: r['Goals1'] if r['Team1'] == e else r['Goals2'], axis=1).sum()
        for e in equipos
    ]

    fig_bar = px.bar(x=equipos, y=total_GF, title="Total de Goles por Equipo")
    fig_gf = px.pie(names=rivales, values=gf_list, title="Goles a Favor")
    fig_gc = px.pie(names=rivales, values=gc_list, title="Goles en Contra")

    return pred_text, tabla, fig_bar, fig_gf, fig_gc

# Main de ejecucion
if __name__ == "__main__":
    app.run(debug=True)
