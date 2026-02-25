# Ejemplo Dashboard con mapa de Valle del cauca y sus municipios
# Un punto amarillo en el municipio que no llueve y
# un punto azul en el municipio que llueve
# pip install dash pandas requests dash_leaflet
# pip 25.3.1
# Python 3.13.1
import requests 
import pandas as pd
import dash
from dash import html, dcc, dash_table
import dash_leaflet as dl
from datetime import datetime

# Diccionario con los 42 municipios del Valle del Cauca y coordenadas aproximadas
municipios = {
    "Cali": {"lat": 3.4516, "lon": -76.5320},
    "Palmira": {"lat": 3.5394, "lon": -76.3036},
    "Buenaventura": {"lat": 3.8801, "lon": -77.0312},
    "Tuluá": {"lat": 4.0847, "lon": -76.1954},
    "Cartago": {"lat": 4.7464, "lon": -75.9117},
    "Buga": {"lat": 3.9009, "lon": -76.2978},
    "Jamundí": {"lat": 3.2607, "lon": -76.5343},
    "Yumbo": {"lat": 3.5823, "lon": -76.4915},
    "Candelaria": {"lat": 3.4067, "lon": -76.3482},
    "Florida": {"lat": 3.3273, "lon": -76.2348},
    "Pradera": {"lat": 3.4211, "lon": -76.2447},
    "El Cerrito": {"lat": 3.6855, "lon": -76.3137},
    "Ginebra": {"lat": 3.7243, "lon": -76.2665},
    "Guacarí": {"lat": 3.7647, "lon": -76.3329},
    "Yotoco": {"lat": 3.8590, "lon": -76.3842},
    "Restrepo": {"lat": 3.8233, "lon": -76.5225},
    "La Cumbre": {"lat": 3.6489, "lon": -76.5691},
    "Dagua": {"lat": 3.6561, "lon": -76.6905},
    "Calima (El Darién)": {"lat": 3.9330, "lon": -76.4850},
    "Vijes": {"lat": 3.6986, "lon": -76.4428},
    "San Pedro": {"lat": 3.9944, "lon": -76.2286},
    "Trujillo": {"lat": 4.2122, "lon": -76.3189},
    "Riofrío": {"lat": 4.1570, "lon": -76.2885},
    "Andalucía": {"lat": 4.1703, "lon": -76.1665},
    "Bugalagrande": {"lat": 4.2117, "lon": -76.1550},
    "Zarzal": {"lat": 4.3953, "lon": -76.0715},
    "La Unión": {"lat": 4.5323, "lon": -76.1030},
    "Roldanillo": {"lat": 4.4138, "lon": -76.1546},
    "Bolívar": {"lat": 4.3381, "lon": -76.1840},
    "Toro": {"lat": 4.6111, "lon": -76.0814},
    "La Victoria": {"lat": 4.5237, "lon": -75.9671},
    "Obando": {"lat": 4.5950, "lon": -75.9486},
    "Ansermanuevo": {"lat": 4.7972, "lon": -75.9950},
    "Argelia": {"lat": 4.7286, "lon": -76.1214},
    "El Águila": {"lat": 4.9130, "lon": -76.0463},
    "El Cairo": {"lat": 4.7472, "lon": -76.2448},
    "Alcalá": {"lat": 4.6740, "lon": -75.7823},
    "Ulloa": {"lat": 4.7081, "lon": -75.7395},
    "Versalles": {"lat": 4.6646, "lon": -76.2525},
    "Caicedonia": {"lat": 4.3337, "lon": -75.8266},
    "Sevilla": {"lat": 4.2647, "lon": -75.9289},
    "El Dovio": {"lat": 4.5075, "lon": -76.2362}
}

# Función para obtener clima
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

for municipio, coord in municipios.items():
    clima = obtener_clima_actual(coord["lat"], coord["lon"])
    
    if clima:
        resultados.append({
            "Municipio": municipio,
            "Lat": coord["lat"],
            "Lon": coord["lon"],
            "Temperatura (°C)": clima["temperatura"],
            "Viento (km/h)": clima["viento"],
            "Lluvia (mm)": clima["precipitacion"],
            "WeatherCode": clima["weathercode"]
        })

df = pd.DataFrame(resultados)

# Función de color por WeatherCode
def color_weathercode(code, max_code=95):
    ratio = min(max(code / max_code, 0), 1)
    r1, g1, b1 = 255, 255, 0
    r2, g2, b2 = 0, 0, 139
    r = int(r1 + (r2 - r1) * ratio)
    g = int(g1 + (g2 - g1) * ratio)
    b = int(b1 + (b2 - b1) * ratio)
    return f"rgb({r},{g},{b})"

# Crear marcadores
markers = [
    dl.CircleMarker(
        center=(row["Lat"], row["Lon"]),
        radius=8,
        color=color_weathercode(row["WeatherCode"]),
        fill=True,
        fillColor=color_weathercode(row["WeatherCode"]),
        fillOpacity=0.8,
        children=dl.Tooltip(
            f"{row['Municipio']} | "
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
        html.H1("Clima Actual en Municipios del Valle del Cauca"),
        html.Div(f"Última actualización: {fecha_hora_actual}",
                 style={'marginBottom': '20px', 'fontSize': 16}),
        
        html.H2("Tabla de clima actual por municipio"),
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
            center=(3.8, -76.5),
            zoom=8,
            style={'width': '100%', 'height': '600px'}
        )
    ]
)

# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4321, debug=True)