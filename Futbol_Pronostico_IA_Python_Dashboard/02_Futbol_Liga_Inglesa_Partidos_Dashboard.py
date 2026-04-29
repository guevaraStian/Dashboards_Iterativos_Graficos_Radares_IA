# Dashboard con informacion de equipos de la liga inglesa, con IA
# Se solicita la informacion a una API web con todos los datos del equipo y con eso se crea
# Una tabla, una grafica y un  pronostico del siguiente numero
# pip install flask pandas requests lxml beautifulsoup4
# pip 25.3.1
# Python 3.13.1

import requests
import pandas as pd
from dash import Dash, html, dash_table

# URL del JSON público de Premier League 2024-25
url = "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/en.1.json"

# Obtener datos
try:
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.RequestException as e:
    print("Error al obtener datos:", e)
    data = {}

# Extraer los partidos
matches = data.get("matches", [])

# Crear DataFrame
df = pd.DataFrame(matches)

# Algunos campos pueden estar anidados; ajustamos columnas
# Por ejemplo, "team1" y "team2" contienen nombres de los equipos
if not df.empty:
    df['Team1'] = df['team1'].apply(lambda x: x if isinstance(x, str) else x.get('name', ''))
    df['Team2'] = df['team2'].apply(lambda x: x if isinstance(x, str) else x.get('name', ''))
    df['Date'] = pd.to_datetime(df['date'], errors='coerce')
    df['Score'] = df['score'].apply(lambda s: f"{s.get('ft')[0]} - {s.get('ft')[1]}" if s else "")
    # Seleccionamos columnas para la tabla
    df_table = df[['Date', 'Team1', 'Team2', 'Score']]

# El siguiente codigo es para crear el dashboard Dash
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Premier League 2024-25 - Tabla de Partidos"),
    dash_table.DataTable(
        id='tabla-partidos',
        columns=[{"name": i, "id": i} for i in df_table.columns],
        data=df_table.to_dict('records'),
        page_size=20,            # mostrar 20 filas por página
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'center', 'padding': '5px'},
        style_header={'backgroundColor': 'lightblue', 'fontWeight': 'bold'}
    )
])

if __name__ == "__main__":
    app.run(debug=True)
