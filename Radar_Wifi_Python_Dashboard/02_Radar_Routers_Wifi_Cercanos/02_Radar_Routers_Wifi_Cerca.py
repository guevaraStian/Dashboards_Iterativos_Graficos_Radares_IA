# Dashboard con radar en python con la ubicacion 
# De dispositivos conectados a la red local
# Se muestra un mapa con la ubicacion probable de cada dispositivo
# pip install dash plotly pywifi pandas kaleido reportlab
# pip 25.3.1
# Python 3.13.1

import time
import math
import random
import numpy as np
import pandas as pd
from datetime import datetime
import plotly.graph_objs as go
from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output, State
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Intentar importar pywifi
try:
    import pywifi
    from pywifi import const
    WIFI_AVAILABLE = True
except Exception as e:
    print(" (-) pywifi no disponible:", e)
    WIFI_AVAILABLE = False




# El siguiente codigo ayuda a crear el escaneo
def Escaneo_Routers_Cerca():
    if not WIFI_AVAILABLE:
        return Simular_Router_Wifi()

    try:
        wifi = pywifi.PyWiFi()
        interfaces = wifi.interfaces()

        if not interfaces:
            return Simular_Router_Wifi()

        iface = interfaces[0]
        iface.scan()
        time.sleep(2)

        results = iface.scan_results()
        Red_wifi = []

        for Red_W in results:
            Red_wifi.append({
                "ssid": Red_W.ssid if Red_W.ssid else "Hidden",
                "bssid": Red_W.bssid,
                "rssi": Red_W.signal
            })

        if not Red_wifi:
            return Simular_Router_Wifi()

        return Red_wifi

    except Exception as e:
        print("(-) Error escaneando WiFi:", e)
        return Simular_Router_Wifi()


# A continuacion s
def Simular_Router_Wifi():
    Simulacion_Red_wifi = []

    for i in range(random.randint(5, 10)):
        Simulacion_Red_wifi.append({
            "ssid": f"WiFi_{i}",
            "bssid": f"AA:BB:CC:DD:EE:{i:02X}",
            "rssi": random.randint(-90, -30)
        })

    return Simulacion_Red_wifi


# La siguiente funcion calcula la distancia del router por medio de rssi
def Distancia_Estimada(rssi, tx_power=-50, n=2.5):
    return round(10 ** ((tx_power - rssi) / (10 * n)), 2)


# A continuacion se muestra el codigo que limpia los datos
def Preparar_Informacion():
    data = Escaneo_Routers_Cerca()

    for d in data:
        d["distance"] = Distancia_Estimada(d["rssi"])

    df = pd.DataFrame(data)

    if df.empty:
        return pd.DataFrame(columns=["ssid", "bssid", "rssi", "distance"])

    df = df.sort_values(by="distance")
    return df


# La funcion siguiente crea el radar y sus caracteristicas
def Crear_Radar(df):
    if df.empty:
        return go.Figure()

    angles = np.linspace(0, 360, len(df), endpoint=False)

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=df["distance"],
        theta=angles,
        mode='markers+text',
        text=df["ssid"],
        hovertext=df["ssid"] +
                  "<br>BSSID: " + df["bssid"] +
                  "<br>RSSI: " + df["rssi"].astype(str),
        hoverinfo="text",
        textposition="top center",
        marker=dict(
            size=12,
            color=df["rssi"],
            colorscale="Viridis",
            showscale=True
        )
    ))

    fig.update_layout(
        title="Radar de routers de WiFi cerca",
        paper_bgcolor="black",
        font=dict(color="red"),
        polar=dict(
            bgcolor="black",
            radialaxis=dict(
                visible=True,
                color="red",
                gridcolor="gray"
            )
        ),
        showlegend=False
    )

    return fig


# El siguiente codigo muestra la creacion del dashboard
app = Dash(__name__)

app.layout = html.Div(
    style={"backgroundColor": "black", "color": "red", "padding": "20px"},
    children=[

        html.H1(" WiFi Radar Dashboard", style={"textAlign": "center"}),

        # En la etiqueta h3 queda referenciado la fecha y hora actual
        html.H3(id="datetime-display", style={"textAlign": "center"}),

        html.H3("(+) Routers detectados"),

        dash_table.DataTable(
            id="table",
            columns=[
                {"name": "SSID (Nombre de Red)", "id": "ssid"},
                {"name": "BSSID (MAC)", "id": "bssid"},
                {"name": "RSSI", "id": "rssi"},
                {"name": "Distancia (m)", "id": "distance"},
            ],
            style_table={"overflowX": "auto"},
            style_cell={
                "textAlign": "center",
                "backgroundColor": "#D3D3D3",
                "color": "black"
            },
            style_header={
                "backgroundColor": "red",
                "color": "black",
                "fontWeight": "bold"
            },
            sort_action="native"
        ),

        dcc.Graph(id="radar"),

        html.Br(),

        html.Button("Boton para exportar PDF", id="btn_pdf"),

        dcc.Download(id="download_pdf"),

        dcc.Interval(id="interval", interval=5000, n_intervals=0)
    ]
)


# El siguiente callback se encarga de actualizar la pagina cuando sea necesario
@app.callback(
    [Output("radar", "figure"),
     Output("table", "data")],
    Input("interval", "n_intervals")
)
def update(n):
    df = Preparar_Informacion()
    return Crear_Radar(df), df.to_dict("records")


# Este callback actualiza la fecha y hora automaticamente
@app.callback(
    Output("datetime-display", "children"),
    Input("interval", "n_intervals")
)
def update_time(n):
    now = datetime.now().strftime("Fehcha y hora:  %d/%m/%Y  %H:%M:%S")
    return now


# Con este callback, se da la opcion de descargar el dashboard en pdf
@app.callback(
    Output("download_pdf", "data"),
    Input("btn_pdf", "n_clicks"),
    State("table", "data"),
    prevent_initial_call=True
)
def Exportar_PDF(n, data):
    df = pd.DataFrame(data)
    fig = Crear_Radar(df)

    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    img_bytes = fig.to_image(format="png")

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Caracteristicas del titulo
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 760, " WiFi Radar Reporte")

    # Caracteristicas de la fecha
    c.setFont("Helvetica", 10)
    c.drawString(50, 745, f"Generado: {timestamp}")

    # Radar
    with open("temp_radar.png", "wb") as f:
        f.write(img_bytes)

    c.drawImage("temp_radar.png", 50, 400, width=500, height=300)

    # Creacion de la tabla
    y = 380
    c.setFont("Helvetica", 8)

    for _, row in df.iterrows():
        text = f"{row['ssid']} | {row['bssid']} | {row['distance']} m"
        c.drawString(50, y, text)
        y -= 12

        if y < 50:
            c.showPage()
            y = 750

    c.save()
    buffer.seek(0)

    return dcc.send_bytes(buffer.getvalue(), "wifi_report.pdf")


# Este if pone a funcionar el dashboard e imprime en consola cuando se inicia
if __name__ == "__main__":
    print("Iniciando WiFi Radar Dashboard...")
    print("http://127.0.0.1:8050")
    app.run(debug=True)