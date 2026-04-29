# Dashboard con radar de la ubicacion de paredes cercanas
# Usando el sonido se emite y se captura el tiempo de robote 
# para validar donde estan las paredes
# pip install dash plotly sounddevice pandas pdfkit
# pip 25.3.1
# Python 3.13.1

import sounddevice as sd
import numpy as np
import time
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Output, Input, State
import plotly.graph_objects as go
from threading import Thread
import pandas as pd
import io
import pdfkit 

# Configuracion de caracteristicas del sonido
SPEED_OF_SOUND = 343.0
fs = 44100
duration = 0.05
frequency = 20000
grab_time = 0.3
direcciones = ["Norte", "Sur", "Este", "Oeste"]
distancias_actuales = {dir: 0 for dir in direcciones}

# Generador de pulso de sonido en una direccion
def generar_pulso():
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    return 0.5 * np.sin(2 * np.pi * frequency * t)

pulso = generar_pulso()

# Emisor del sonido señal
def emitir_sonido(wave):
    sd.play(wave, fs)
    sd.wait()

# Grabar el sonido de vuelta para calcular distancia
def grabar_echo():
    recording = sd.rec(int(grab_time * fs), samplerate=fs, channels=1)
    sd.wait()
    return recording.flatten()

# Funcion que calcula las distancias
def calcular_distancia(emision, grabacion):
    corr = np.correlate(grabacion, emision, mode='full')
    delay_samples = np.argmax(corr) - len(emision) + 1
    delay_seconds = delay_samples / fs
    distance = (delay_seconds * SPEED_OF_SOUND) / 2
    return max(distance, 0)

# Medicion
def medir_distancias():
    global distancias_actuales
    while True:
        for dir in direcciones:
            emitir_sonido(pulso)
            grabacion = grabar_echo()
            distancias_actuales[dir] = calcular_distancia(pulso, grabacion)
        time.sleep(10)

Thread(target=medir_distancias, daemon=True).start()

# CREACION DE DASHBOARD
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Radar acústico de habitación", style={'color':'white', 'textAlign':'center'}),
    html.Div(id='reloj', style={'color':'red', 'textAlign':'center', 'fontSize':'20px', 'marginBottom':'20px'}),
    
    html.Div([
        html.Button("Exportar PDF", id="btn-pdf", n_clicks=0, style={'marginRight':'20px'}),
        html.Button("Exportar Excel", id="btn-excel", n_clicks=0)
    ], style={'textAlign':'center', 'marginBottom':'20px'}),
    
    dash_table.DataTable(
        id='tabla-distancias',
        columns=[{"name": "Dirección", "id": "direccion"},
                 {"name": "Distancia (m)", "id": "distancia"}],
        style_header={'backgroundColor':'red','color':'white','fontWeight':'bold','textAlign':'center'},
        style_cell={'backgroundColor':'gray','color':'white','textAlign':'center'},
        style_table={'width':'50%', 'margin':'auto'}
    ),
    
    dcc.Graph(id='grafica-habitacion', style={'height':'600px'}),
    dcc.Interval(id='intervalo-actualizacion', interval=1000, n_intervals=0),
    
    dcc.Download(id="download-pdf"),
    dcc.Download(id="download-excel")
], style={'backgroundColor':'black', 'height':'100vh', 'padding':'20px'})

# Callback de el dashboard
@app.callback(
    Output('tabla-distancias', 'data'),
    Output('grafica-habitacion', 'figure'),
    Output('reloj', 'children'),
    Input('intervalo-actualizacion', 'n_intervals')
)
def actualizar_dashboard(n):
    hora_actual = time.strftime("%Y-%m-%d %H:%M:%S")
    tabla = [{"direccion": dir, "distancia": round(distancias_actuales[dir], 2)} for dir in direcciones]

    norte = distancias_actuales["Norte"]
    sur = -distancias_actuales["Sur"]
    este = distancias_actuales["Este"]
    oeste = -distancias_actuales["Oeste"]

    x_coords = [oeste, este, este, oeste, oeste]
    y_coords = [norte, norte, sur, sur, norte]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_coords, y=y_coords, mode='lines', line=dict(color='blue', width=3), name='Paredes'))
    fig.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker=dict(color='red', size=10), name='PC'))
    fig.update_layout(
        plot_bgcolor='black', paper_bgcolor='black', font=dict(color='white'),
        xaxis_title="X (m)", yaxis_title="Y (m)", title="Plano aproximado de la habitación",
        xaxis=dict(scaleanchor="y", scaleratio=1),
        yaxis=dict(scaleanchor="x", scaleratio=1),
        showlegend=True
    )

    return tabla, fig, hora_actual

# Callback para la descarga del pdf-
@app.callback(
    Output("download-pdf", "data"),
    Input("btn-pdf", "n_clicks"),
    State('tabla-distancias', 'data'),
    prevent_initial_call=True
)
def exportar_pdf(n_clicks, tabla_data):
    # Cambia esta ruta a donde está wkhtmltopdf en tu PC
    wkhtmltopdf_path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

    html_content = "<html><body style='background-color:black;color:white;text-align:center;'>"
    html_content += "<h1>Radar acústico de habitación</h1>"
    html_content += f"<h3 style='color:red;'>{time.strftime('%Y-%m-%d %H:%M:%S')}</h3>"
    html_content += "<table border='1' style='margin:auto; background-color:gray; color:white;'>"
    html_content += "<tr><th>Dirección</th><th>Distancia (m)</th></tr>"
    for row in tabla_data:
        html_content += f"<tr><td>{row['direccion']}</td><td>{row['distancia']}</td></tr>"
    html_content += "</table></body></html>"

    pdf_bytes = pdfkit.from_string(html_content, False, configuration=config, options={"enable-local-file-access": ""})
    return dcc.send_bytes(pdf_bytes, "Radar_Acoustico.pdf")

# Callback para la creacion del excel
@app.callback(
    Output("download-excel", "data"),
    Input("btn-excel", "n_clicks"),
    State('tabla-distancias', 'data'),
    prevent_initial_call=True
)
def exportar_excel(n_clicks, tabla_data):
    df = pd.DataFrame(tabla_data)
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    return dcc.send_bytes(buffer.read(), "Radar_Acoustico.xlsx")

if __name__ == "__main__":
    app.run(debug=True)
