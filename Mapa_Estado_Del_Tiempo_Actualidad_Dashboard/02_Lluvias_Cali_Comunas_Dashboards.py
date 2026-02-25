# Ejemplo Dashboard con mapa de cali y sus comunas con 
# Un punto amarillo en la comuna que no llueve y 
# un punto azul en la comuna que llueve
# pip install pandas requests dash
# pip 25.3.1
# Python 3.13.1

import requests 
import pandas as pd
import dash
from dash import html, dcc, dash_table
import dash_leaflet as dl
from datetime import datetime

# En la siguientes lineas se muestra
# Diccionario con 22 comunas y coordenadas aproximadas
comunas = {
    "Comuna 1": {"lat": 3.45, "lon": -76.53},
    "Comuna 2": {"lat": 3.46, "lon": -76.53},
    "Comuna 3": {"lat": 3.44, "lon": -76.53},
    "Comuna 4": {"lat": 3.46, "lon": -76.50},
    "Comuna 5": {"lat": 3.47, "lon": -76.51},
    "Comuna 6": {"lat": 3.43, "lon": -76.50},
    "Comuna 7": {"lat": 3.42, "lon": -76.50},
    "Comuna 8": {"lat": 3.45, "lon": -76.51},
    "Comuna 9": {"lat": 3.43, "lon": -76.52},
    "Comuna 10": {"lat": 3.41, "lon": -76.51},
    "Comuna 11": {"lat": 3.42, "lon": -76.53},
    "Comuna 12": {"lat": 3.43, "lon": -76.54},
    "Comuna 13": {"lat": 3.46, "lon": -76.54},
    "Comuna 14": {"lat": 3.44, "lon": -76.49},
    "Comuna 15": {"lat": 3.40, "lon": -76.50},
    "Comuna 16": {"lat": 3.41, "lon": -76.51},
    "Comuna 17": {"lat": 3.39, "lon": -76.52},
    "Comuna 18": {"lat": 3.42, "lon": -76.54},
    "Comuna 19": {"lat": 3.43, "lon": -76.55},
    "Comuna 20": {"lat": 3.41, "lon": -76.55},
    "Comuna 21": {"lat": 3.42, "lon": -76.51},
    "Comuna 22": {"lat": 3.3533, "lon": -76.5354},
}

# Se consulta una base de datos de una api y se guardan los datos en variables
def obtener_clima_actual(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}"
        f"&longitude={lon}"
        f"&current_weather=true"
        f"&hourly=precipitation"
        f"&timezone=auto"
    )
    try:
        response = requests.get(url, timeout=5)
        data = response.json()

        current = data.get("current_weather", {})
        hourly = data.get("hourly", {})

        hora_actual = current.get("time")
        precipitacion = 0

        if "time" in hourly and hora_actual in hourly["time"]:
            index = hourly["time"].index(hora_actual)
            precipitacion = hourly["precipitation"][index]

        return {
            "temperatura": current.get("temperature", 0),
            "viento": current.get("windspeed", 0),
            "weathercode": current.get("weathercode", 0),
            "precipitacion": precipitacion
        }

    except:
        return None

# Consultar clima
resultados = []

for comuna, coord in comunas.items():
    clima = obtener_clima_actual(coord["lat"], coord["lon"])
    
    if clima:
        resultados.append({
            "Comuna": comuna,
            "Lat": coord["lat"],
            "Lon": coord["lon"],
            "Temperatura (°C)": clima["temperatura"],
            "Viento (km/h)": clima["viento"],
            "Lluvia (mm)": clima["precipitacion"],
            "WeatherCode": clima["weathercode"]
        })

df = pd.DataFrame(resultados)

# FUNCIÓN DE COLOR POR WEATHERCODE

def color_weathercode(code, max_code=95):
    """
    0  -> Amarillo (255,255,0)
    95 -> Azul oscuro (0,0,139)
    """
    ratio = min(max(code / max_code, 0), 1)

    # Amarillo
    r1, g1, b1 = 255, 255, 0
    # Azul oscuro
    r2, g2, b2 = 0, 0, 139

    r = int(r1 + (r2 - r1) * ratio)
    g = int(g1 + (g2 - g1) * ratio)
    b = int(b1 + (b2 - b1) * ratio)

    return f"rgb({r},{g},{b})"

#  Crear marcadores usando WeatherCode

markers = [
    dl.CircleMarker(
        center=(row["Lat"], row["Lon"]),
        radius=10,
        color=color_weathercode(row["WeatherCode"]),
        fill=True,
        fillColor=color_weathercode(row["WeatherCode"]),
        fillOpacity=0.8,
        children=dl.Tooltip(
            f"{row['Comuna']} | "
            f"WeatherCode: {row['WeatherCode']} | "
            f"{row['Temperatura (°C)']}°C"
        )
    )
    for _, row in df.iterrows()
]

# Inicializar Dash

app = dash.Dash(__name__)

fecha_hora_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

app.layout = html.Div(
    style={'backgroundColor': 'black', 'color': 'red', 'padding': '20px', 'fontFamily': 'Arial'},
    children=[
        html.H1("Clima Actual en Comunas de Santiago de Cali"),
        html.Div(f"Última actualización: {fecha_hora_actual}",
                 style={'marginBottom': '20px', 'fontSize': 16}),
        
        html.H2("Tabla de clima actual por comuna"),
        dash_table.DataTable(
            id='tabla-clima',
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict('records'),
            style_table={'overflowX': 'auto'},
            style_header={
                'backgroundColor': 'black',
                'color': 'red',
                'fontWeight': 'bold',
                'textAlign': 'center'
            },
            style_cell={
                'textAlign': 'center',
                'backgroundColor': 'black',
                'color': 'red'
            }
        ),
        
        html.H2("Mapa climático según WeatherCode"),
        dl.Map(
            children=[
                dl.TileLayer(),
                dl.LayerGroup(markers)
            ],
            center=(3.43722, -76.5225),
            zoom=11,
            style={'width': '100%', 'height': '600px'}
        )
    ]
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2345, debug=True)