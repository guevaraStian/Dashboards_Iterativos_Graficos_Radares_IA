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

# Asignacion de variables
if not os.path.exists("Archivos"):
    os.makedirs("Archivos")
fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# JSON de liga europea con su respectivo URL API
LIGAS = {
    "Premier League (ING)": "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/en.1.json",
    "La Liga (ESP)": "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/es.1.json",
    "Serie A (ITA)": "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/it.1.json",
    "Bundesliga (GER)": "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/de.1.json",
    "Ligue 1 (FRA)": "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/fr.1.json"
}

# Se consulta la liga que el usuario escogio y se guardan las variables en el data frame
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

# Codigo para crear el dashboard
app = Dash(__name__)

app.layout = html.Div(
    style={'backgroundColor': 'black', 'color': 'red', 'padding': '10px', 'font-family': 'Arial', 'width': '100%'},
    children=[

        html.H1("Predicción de Partidos por Liga y Equipo (IA)", style={'textAlign':'center'}),
        html.H4(f"Fecha y hora actual: {fecha_actual}", style={'textAlign':'center'}),

        # -------- SELECT LIGA --------
        html.Div([
            html.Label("Selecciona una liga:", style={'color':'red'}),
            dcc.Dropdown(
                id='dropdown-liga',
                options=[{'label': k, 'value': k} for k in LIGAS.keys()],
                value=list(LIGAS.keys())[0],
                style={'color':'black'}
            )
        ], style={'maxWidth':'400px', 'margin':'auto'}),

        html.Br(),

        # -------- SELECT EQUIPO --------
        html.Div([
            html.Label("Selecciona un equipo:", style={'color':'red'}),
            dcc.Dropdown(id='dropdown-equipo', style={'color':'black'})
        ], style={'maxWidth':'400px', 'margin':'auto'}),

        html.Div(id='prediccion-output', style={'marginTop': 20, 'color':'red', 'textAlign':'center'}),
        html.Hr(style={'borderColor':'red'}),

        html.H3("Histórico de Partidos del Equipo", style={'textAlign':'center'}),
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
            style_table={'overflowX': 'auto', 'width':'100%'},
            style_cell={'textAlign': 'center', 'padding': '5px', 'color':'black', 'backgroundColor':'gray'},
            style_header={'backgroundColor': 'red', 'color':'black', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'row_index': 'odd'}, 'backgroundColor':'#555555'},
                {'if': {'row_index': 'even'}, 'backgroundColor':'#777777'}
            ]
        ),

        html.Hr(style={'borderColor':'red'}),

        html.H3("Total de Goles por Equipo (Acumulado)", style={'textAlign':'center'}),
        dcc.Graph(id='bar-goles', style={'width':'100%', 'height':'500px'}),

        html.Hr(style={'borderColor':'red'}),

        html.Div([
            html.Div(dcc.Graph(id='pie-goles-favor', style={'height':'400px'}), style={'width':'48%'}),
            html.Div(dcc.Graph(id='pie-goles-contra', style={'height':'400px'}), style={'width':'48%'})
        ], style={'display':'flex', 'justifyContent':'space-between'})
    ]
)

# Creacion de callback de el dashboard
@app.callback(
    Output('dropdown-equipo', 'options'),
    Output('dropdown-equipo', 'value'),
    Input('dropdown-liga', 'value')
)
def actualizar_equipos(liga):
    df = cargar_liga(LIGAS[liga])
    equipos = sorted(set(df['Team1']).union(df['Team2']))
    return [{'label': e, 'value': e} for e in equipos], equipos[0]

# Callback principal
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
        return "No hay datos para este equipo.", [], {}, {}, {}

    tabla_data, gf_list, gc_list, pie_labels = [], [], [], []

    for _, row in df_equipo.iterrows():
        if row['Team1'] == equipo:
            gf, gc, rival, ha = row['Goals1'], row['Goals2'], row['Team2'], "Local"
        else:
            gf, gc, rival, ha = row['Goals2'], row['Goals1'], row['Team1'], "Visitante"

        tabla_data.append({
            "Date": row['Date'].strftime("%Y-%m-%d"),
            "Home/Away": ha,
            "Rival": rival,
            "GF": gf,
            "GC": gc
        })

        gf_list.append(gf)
        gc_list.append(gc)
        pie_labels.append(rival)

    # Se escogen variables de el dataframe para luego meterlo la red neuronal
    X = np.arange(len(df_equipo)).reshape(-1, 1)

    Y_GF = np.array(gf_list)
    Y_GC = np.array(gc_list)

    model_GF = MLPRegressor(hidden_layer_sizes=(10,5), max_iter=1000, random_state=42)
    model_GC = MLPRegressor(hidden_layer_sizes=(10,5), max_iter=1000, random_state=42)

    model_GF.fit(X, Y_GF)
    model_GC.fit(X, Y_GC)

    proximo_index = np.array([[len(df_equipo)]])

    pred_GF = round(model_GF.predict(proximo_index)[0], 1)
    pred_GC = round(model_GC.predict(proximo_index)[0], 1)

    pred_texto = f"Predicción del próximo partido de {equipo}: {pred_GF} - {pred_GC}"

    equipos = sorted(set(df['Team1']).union(df['Team2']))
    total_GF, total_GC = [], []

    for e in equipos:
        df_team = df[(df['Team1'] == e) | (df['Team2'] == e)]
        total_GF.append(df_team.apply(lambda r: r['Goals1'] if r['Team1']==e else r['Goals2'], axis=1).sum())
        total_GC.append(df_team.apply(lambda r: r['Goals2'] if r['Team1']==e else r['Goals1'], axis=1).sum())

    fig_bar = go.Figure(data=[
        go.Bar(name='Goles a favor', x=equipos, y=total_GF, marker_color='green', text=total_GF, textposition='auto'),
        go.Bar(name='Goles en contra', x=equipos, y=total_GC, marker_color='red', text=total_GC, textposition='auto')
    ])
    fig_bar.update_layout(
        barmode='group',
        title="Total de Goles por Equipo",
        font_color='red',
        plot_bgcolor='black',
        paper_bgcolor='black'
    )

    # Creacion de la grafica
    fig_GF = px.pie(names=pie_labels, values=gf_list, hole=0.3,
                    title=f"Goles a favor por partido de {equipo}")
    fig_GF.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='red')

    fig_GC = px.pie(names=pie_labels, values=gc_list, hole=0.3,
                    title=f"Goles en contra por partido de {equipo}")
    fig_GC.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='red')

    return pred_texto, tabla_data, fig_bar, fig_GF, fig_GC

# Main de ejecutar para que flask cree la pagina web
if __name__ == "__main__":
    app.run(debug=True)
