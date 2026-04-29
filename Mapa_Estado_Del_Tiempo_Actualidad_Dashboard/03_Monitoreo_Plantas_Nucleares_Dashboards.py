# Monitoreo de plantas nucleares del mundo
# Ubicacion, temperatura, humedad, radiacion
# pip install dash dash-leaflet requests pandas
# pip 25.3.1
# Python 3.13.1
import requests
import pandas as pd
import dash
from dash import html, dash_table
import dash_leaflet as dl
from datetime import datetime

# UBICACIONES NUCLEARES MUNDIALES

ubicaciones = {
    "Flamanville": {"lat": 49.655, "lon": -1.615, "pais": "France", "codigo": "FR"},
    "Sizewell B": {"lat": 52.237, "lon": 1.594, "pais": "United Kingdom", "codigo": "GB"},
    "Cofrentes": {"lat": 39.022, "lon": -1.135, "pais": "Spain", "codigo": "ES"},
    "Tihange": {"lat": 50.493, "lon": 5.449, "pais": "Belgium", "codigo": "BE"},
    "Ringhals": {"lat": 57.263, "lon": 12.037, "pais": "Sweden", "codigo": "SE"},
    "Olkiluoto": {"lat": 61.233, "lon": 21.483, "pais": "Finland", "codigo": "FI"},
    "Leibstadt": {"lat": 47.530, "lon": 8.233, "pais": "Switzerland", "codigo": "CH"},
    "Paks": {"lat": 46.640, "lon": 18.875, "pais": "Hungary", "codigo": "HU"},
    "Bohunice": {"lat": 48.296, "lon": 18.382, "pais": "Slovakia", "codigo": "SK"},
    "Dukovany": {"lat": 49.983, "lon": 16.300, "pais": "Czech Republic", "codigo": "CZ"},
    "Cernavodă": {"lat": 44.320, "lon": 27.915, "pais": "Romania", "codigo": "RO"},
    "Kozloduy": {"lat": 43.616, "lon": 27.250, "pais": "Bulgaria", "codigo": "BG"},
    "Krško": {"lat": 45.933, "lon": 15.500, "pais": "Slovenia", "codigo": "SI"},
    "Borssele": {"lat": 51.450, "lon": 3.750, "pais": "Netherlands", "codigo": "NL"},
    "Zaporizhzhia": {"lat": 47.509, "lon": 34.583, "pais": "Ukraine", "codigo": "UA"},
    "Palo Verde": {"lat": 33.236, "lon": -112.865, "pais": "United States", "codigo": "US"},
    "Bruce": {"lat": 44.283, "lon": -81.483, "pais": "Canada", "codigo": "CA"},
    "Laguna Verde": {"lat": 19.533, "lon": -96.350, "pais": "Mexico", "codigo": "MX"},
    "Angra": {"lat": -22.717, "lon": -41.883, "pais": "Brazil", "codigo": "BR"},
    "Atucha": {"lat": -34.183, "lon": -59.100, "pais": "Argentina", "codigo": "AR"},
    "Daya Bay": {"lat": 22.695, "lon": 114.434, "pais": "China", "codigo": "CN"},
    "Tarapur": {"lat": 19.800, "lon": 72.731, "pais": "India", "codigo": "IN"},
    "Kashiwazaki-Kariwa": {"lat": 37.421, "lon": 138.579, "pais": "Japan", "codigo": "JP"},
    "Kori": {"lat": 35.136, "lon": 129.079, "pais": "South Korea", "codigo": "KR"},
    "KANUPP": {"lat": 24.904, "lon": 67.081, "pais": "Pakistan", "codigo": "PK"},
    "Bushehr": {"lat": 28.944, "lon": 50.834, "pais": "Iran", "codigo": "IR"},
    "Barakah": {"lat": 24.305, "lon": 52.720, "pais": "United Arab Emirates", "codigo": "AE"},
    "Kursk": {"lat": 51.730, "lon": 36.190, "pais": "Russia", "codigo": "RU"},
    "Metsamor": {"lat": 40.184, "lon": 44.405, "pais": "Armenia", "codigo": "AM"},
    "Ostrovets": {"lat": 55.500, "lon": 24.983, "pais": "Belarus", "codigo": "BY"},
    "Koeberg": {"lat": -33.607, "lon": 18.475, "pais": "South Africa", "codigo": "ZA"},
}

# FUNCIÓN CONSULTA CLIMA

def obtener_clima(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current_weather=true"
        f"&hourly=precipitation,relativehumidity_2m,shortwave_radiation"
        f"&timezone=auto"
    )
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        current = data.get("current_weather", {})
        hourly = data.get("hourly", {})
        hora = current.get("time")
        idx = hourly["time"].index(hora)
        return {
            "temp": current.get("temperature", 0),
            "prec": hourly["precipitation"][idx],
            "hum": hourly["relativehumidity_2m"][idx],
            "rad": hourly["shortwave_radiation"][idx],
        }
    except:
        return None

# CREAR MARCADORES Y DATAFRAME PARA TABLA

markers = []
data_list = []

for nombre, info in ubicaciones.items():
    clima = obtener_clima(info["lat"], info["lon"])
    if clima:
        bandera_url = f"https://flagcdn.com/w40/{info['codigo'].lower()}.png"
        popup = dl.Popup(
            html.Div([
                html.Img(src=bandera_url, style={"width": "40px"}),
                html.H4(info["pais"], style={"color": "red", "margin": "5px"}),
                html.H4(nombre, style={"color": "red", "margin": "5px"}),
                html.P(f"Temperatura: {clima['temp']} °C"),
                html.P(f"Lluvia: {clima['prec']} mm"),
                html.P(f"Humedad: {clima['hum']} %"),
                html.P(f"Radiación solar: {clima['rad']} W/m²"),
            ])
        )
        markers.append(dl.Marker(position=(info["lat"], info["lon"]), children=popup))
        
        data_list.append({
            "País": info["pais"],
            "Ciudad": nombre,
            "Temperatura (°C)": clima["temp"],
            "Lluvia (mm)": clima["prec"],
            "Humedad (%)": clima["hum"],
            "Radiación solar (W/m²)": clima["rad"]
        })

# Crear DataFrame
df = pd.DataFrame(data_list)

# CREACION DEL DASHBOARD

app = dash.Dash(__name__)
fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

app.layout = html.Div(
    style={"backgroundColor": "black", "color": "red", "padding": "20px"},
    children=[
        html.H1("Monitoreo Climático Mundial en Plantas Nucleares"),
        html.Div(f"Última actualización: {fecha}"),
        
        # MAPA
        dl.Map(
            center=[20, 0],
            zoom=2,
            children=[
                dl.TileLayer(),
                dl.LayerGroup(markers)
            ],
            style={'width': '100%', 'height': '700px', 'marginBottom': '30px'}
        ),
        
        # TABLA
        html.H2("Datos Climáticos por Ciudad"),
        dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict('records'),
            style_header={
                "backgroundColor": "red",
                "color": "black",
                "fontWeight": "bold",
                "textAlign": "center"
            },
            style_cell={
                "backgroundColor": "#d3d3d3",
                "color": "black",
                "textAlign": "center"
            },
            style_table={'overflowX': 'auto', 'marginTop': '20px'}
        )
    ]
)

if __name__ == "__main__":
    app.run(debug=True, port=1431)