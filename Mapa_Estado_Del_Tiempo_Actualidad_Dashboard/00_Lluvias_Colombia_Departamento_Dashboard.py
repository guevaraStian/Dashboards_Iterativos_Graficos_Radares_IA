# Ejemplo Dashboard con mapa de Colombia y sus Departamentos
# Un punto amarillo en la comuna que no llueve y
# un punto azul en la comuna que llueve
# pip install dash pandas requests pydeck
# pip 25.3.1
# Python 3.13.1
import requests 
import pandas as pd
import dash
from dash import html, dcc, dash_table
import dash_leaflet as dl
from datetime import datetime

# Diccionario con los 32 departamentos de Colombia + Bogotá D.C.
# Coordenadas aproximadas de sus capitales

departamentos = {
    "Amazonas": {"lat": -4.2153, "lon": -69.9406},        # Leticia
    "Antioquia": {"lat": 6.2442, "lon": -75.5812},        # Medellín
    "Arauca": {"lat": 7.0847, "lon": -70.7591},           # Arauca
    "Atlántico": {"lat": 10.9685, "lon": -74.7813},       # Barranquilla
    "Bolívar": {"lat": 10.3910, "lon": -75.4794},         # Cartagena
    "Boyacá": {"lat": 5.5444, "lon": -73.3572},           # Tunja
    "Caldas": {"lat": 5.0703, "lon": -75.5138},           # Manizales
    "Caquetá": {"lat": 1.6144, "lon": -75.6062},          # Florencia
    "Casanare": {"lat": 5.3378, "lon": -72.3959},         # Yopal
    "Cauca": {"lat": 2.4448, "lon": -76.6147},            # Popayán
    "Cesar": {"lat": 10.4631, "lon": -73.2532},           # Valledupar
    "Chocó": {"lat": 5.6947, "lon": -76.6610},            # Quibdó
    "Córdoba": {"lat": 8.7479, "lon": -75.8814},          # Montería
    "Cundinamarca": {"lat": 4.7110, "lon": -74.0721},     # Bogotá
    "Guainía": {"lat": 3.8653, "lon": -67.9239},          # Inírida
    "Guaviare": {"lat": 2.5729, "lon": -72.6459},         # San José del Guaviare
    "Huila": {"lat": 2.9386, "lon": -75.2819},            # Neiva
    "La Guajira": {"lat": 11.5444, "lon": -72.9072},      # Riohacha
    "Magdalena": {"lat": 11.2408, "lon": -74.1990},       # Santa Marta
    "Meta": {"lat": 4.1420, "lon": -73.6266},             # Villavicencio
    "Nariño": {"lat": 1.2136, "lon": -77.2811},           # Pasto
    "Norte de Santander": {"lat": 7.8939, "lon": -72.5078},# Cúcuta
    "Putumayo": {"lat": 0.5051, "lon": -76.4957},         # Mocoa
    "Quindío": {"lat": 4.5350, "lon": -75.6757},          # Armenia
    "Risaralda": {"lat": 4.8087, "lon": -75.6906},        # Pereira
    "San Andrés y Providencia": {"lat": 12.5847, "lon": -81.7006},
    "Santander": {"lat": 7.1193, "lon": -73.1227},        # Bucaramanga
    "Sucre": {"lat": 9.3047, "lon": -75.3978},            # Sincelejo
    "Tolima": {"lat": 4.4389, "lon": -75.2322},           # Ibagué
    "Valle del Cauca": {"lat": 3.4516, "lon": -76.5320},  # Cali
    "Vaupés": {"lat": 1.2537, "lon": -70.2339},           # Mitú
    "Vichada": {"lat": 6.1850, "lon": -67.4932},          # Puerto Carreño
    "Bogotá D.C.": {"lat": 4.7110, "lon": -74.0721}
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

for departamento, coord in departamentos.items():
    clima = obtener_clima_actual(coord["lat"], coord["lon"])
    
    if clima:
        resultados.append({
            "Departamento": departamento,
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
            f"{row['Departamento']} | "
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
        html.H1("Clima Actual en Departamentos de Colombia"),
        html.Div(f"Última actualización: {fecha_hora_actual}",
                 style={'marginBottom': '20px', 'fontSize': 16}),
        
        html.H2("Tabla de clima actual por departamento"),
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
            center=(4.5, -74.0),
            zoom=6,
            style={'width': '100%', 'height': '600px'}
        )
    ]
)

# Main de ejecucion
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1234, debug=True)
