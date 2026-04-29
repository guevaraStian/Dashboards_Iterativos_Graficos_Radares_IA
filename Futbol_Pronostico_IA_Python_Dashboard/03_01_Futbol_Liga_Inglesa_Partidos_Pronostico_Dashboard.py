# Dashboard con informacion de equipos de la liga inglesa, con IA
# Se solicita la informacion a una API web con todos los datos del equipo y con eso se crea
# Una tabla, una grafica y un  pronostico del siguiente numero
# pip install flask pandas requests lxml beautifulsoup4
# pip 25.3.1
# Python 3.13.1

import requests
import pandas as pd
import numpy as np
from dash import Dash, html, dcc, Output, Input, dash_table
from sklearn.neural_network import MLPRegressor

# --- Obtener datos JSON ---
url = "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/en.1.json"
response = requests.get(url)
data = response.json()

matches = data.get("matches", [])
df = pd.DataFrame(matches)

# --- Procesar columnas ---
df['Team1'] = df['team1'].apply(lambda x: x if isinstance(x, str) else x.get('name', ''))
df['Team2'] = df['team2'].apply(lambda x: x if isinstance(x, str) else x.get('name', ''))
df['Date'] = pd.to_datetime(df['date'], errors='coerce')
df['Score'] = df['score'].apply(lambda s: f"{s.get('ft')[0]} - {s.get('ft')[1]}" if s else None)
df[['Goals1', 'Goals2']] = df['Score'].str.split(' - ', expand=True).astype(float)
df.dropna(subset=['Goals1','Goals2'], inplace=True)

# Lista de equipos
equipos = sorted(set(df['Team1']).union(set(df['Team2'])))

# --- Crear Dash ---
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Premier League 2024-25 - Predicción de Partidos por Equipo"),
    html.Label("Selecciona un equipo:"),
    dcc.Dropdown(
        id='dropdown-equipo',
        options=[{'label': e, 'value': e} for e in equipos],
        value=equipos[0]
    ),
    html.Div(id='prediccion-output', style={'marginTop': 20}),
    html.Hr(),
    html.H3("Histórico de Partidos del Equipo"),
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
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'center', 'padding': '5px'},
        style_header={'backgroundColor': 'lightblue', 'fontWeight': 'bold'}
    )
])

# --- Callback ---
@app.callback(
    [Output('prediccion-output', 'children'),
     Output('tabla-partidos', 'data')],
    Input('dropdown-equipo', 'value')
)
def actualizar_dashboard(equipo):
    # Filtrar partidos del equipo
    mask = (df['Team1'] == equipo) | (df['Team2'] == equipo)
    df_equipo = df[mask].copy()
    
    if df_equipo.empty:
        return "No hay datos para este equipo.", []

    # Preparar datos para la tabla
    tabla_data = []
    for _, row in df_equipo.iterrows():
        if row['Team1'] == equipo:
            gf = row['Goals1']
            gc = row['Goals2']
            rival = row['Team2']
            home_away = "Local"
        else:
            gf = row['Goals2']
            gc = row['Goals1']
            rival = row['Team1']
            home_away = "Visitante"
        tabla_data.append({
            "Date": row['Date'].strftime("%Y-%m-%d"),
            "Home/Away": home_away,
            "Rival": rival,
            "GF": gf,
            "GC": gc
        })
    
    # --- Predicción de próximo partido ---
    # Features simples: partido número
    X = np.arange(len(df_equipo)).reshape(-1,1)
    Y_GF = df_equipo.apply(lambda row: row['Goals1'] if row['Team1']==equipo else row['Goals2'], axis=1)
    Y_GC = df_equipo.apply(lambda row: row['Goals2'] if row['Team1']==equipo else row['Goals1'], axis=1)
    
    model_GF = MLPRegressor(hidden_layer_sizes=(10,5), max_iter=1000, random_state=42)
    model_GF.fit(X, Y_GF)
    model_GC = MLPRegressor(hidden_layer_sizes=(10,5), max_iter=1000, random_state=42)
    model_GC.fit(X, Y_GC)
    
    proximo_index = np.array([[len(df_equipo)]])
    pred_GF = round(model_GF.predict(proximo_index)[0],1)
    pred_GC = round(model_GC.predict(proximo_index)[0],1)
    
    pred_texto = html.Div([
        html.H3(f"Predicción del próximo partido de {equipo}: {pred_GF} - {pred_GC} (Goles a favor - Goles en contra)")
    ])
    
    return pred_texto, tabla_data

# --- Ejecutar servidor ---
if __name__ == "__main__":
    app.run(debug=True)
