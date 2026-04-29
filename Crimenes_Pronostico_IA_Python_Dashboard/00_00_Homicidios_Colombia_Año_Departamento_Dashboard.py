# Dashboard con informacion de homicidios en colombia por departamento del pais, con IA
# Se solicita la informacion a una API web con los datos de los homicidios en colombia y e crea
# Una tabla, una grafica y un pronostico del siguiente numero, por departamento y año
# pip install flask pandas requests
# pip 25.3.1
# Python 3.13.1
import requests
import pandas as pd
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
from datetime import datetime

# Con los siguiente lineas de codigo se importa el json desde la API
URL = "https://www.datos.gov.co/resource/m8fd-ahd9.json"
params = {"$limit": 10000000}

response = requests.get(URL, params=params)
response.raise_for_status()

data = response.json()
df = pd.DataFrame(data)

# Se indican las columnas del json y sus nombres en variables
print("Las columnas disponibles son:")
print(df.columns.tolist())

# Detectar columna fecha
posibles_fechas = ["fecha_hecho", "fecha", "fecha_del_hecho"]
col_fecha = None

for c in posibles_fechas:
    if c in df.columns:
        col_fecha = c
        break

if col_fecha is None:
    raise Exception("(-) No se encontraron columnas en la informacion")

# Renombrar a estándar
df.rename(columns={col_fecha: "fecha_hecho"}, inplace=True)

# Se procese a limpiar datos y organizar informacion de las fechas
df["fecha_hecho"] = pd.to_datetime(df["fecha_hecho"], errors="coerce")

# Extraer año desde la fecha
df["anio"] = df["fecha_hecho"].dt.year

# Normalizar departamento
df["departamento"] = df["departamento"].str.upper()

# Eliminar registros invalidos
df = df.dropna(subset=["anio", "departamento"])

# Convertir año a entero
df["anio"] = df["anio"].astype(int)

# Años disponibles
anios_disponibles = sorted(df["anio"].unique())

# Con las siguiente lineas de codigo se crea el dashboard
app = dash.Dash(__name__)

app.layout = html.Div(
    style={"width": "95%", "margin": "auto", "backgroundColor": "black", "color": "red", "minHeight": "100vh", "padding": "20px"},
    children=[
        html.H1(
            "Homicidios en Colombia (filtrado por año de fecha_hecho)",
            style={"textAlign": "center"}
        ),
        html.H4(
            f"Fecha de hoy: {datetime.now().strftime('%d-%m-%Y')}",
            style={"textAlign": "center", "color": "red"}
        ),

        html.Label("Seleccione el año (fecha_hecho):", style={"color": "red"}),
        dcc.Dropdown(
            id="select-anio",
            options=[{"label": str(a), "value": a} for a in anios_disponibles],
            value=anios_disponibles[0],
            clearable=False,
            style={"color": "black"}  # Dropdown con letras negras
        ),

        html.Hr(style={"borderColor": "red"}),

        html.H3("Tabla de homicidios del año seleccionado", style={"color": "red"}),
        dash_table.DataTable(
            id="tabla-homicidios",
            page_size=10,
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": "red",
                "color": "black",
                "fontWeight": "bold",
                "textAlign": "center"
            },
            style_cell={
                "textAlign": "left",
                "fontFamily": "Arial",
                "fontSize": "12px",
                "backgroundColor": "gray",  # Fondo gris para datos
                "color": "black"            # Letras negras
            }
        ),

        html.Hr(style={"borderColor": "red"}),

        html.H3("Homicidios por departamento", style={"color": "red"}),
        dcc.Graph(id="grafica-barras")
    ]
)

# Con las siguientes lineas de codigo se crea los callback de respuesta
@app.callback(
    [
        Output("tabla-homicidios", "data"),
        Output("tabla-homicidios", "columns"),
        Output("grafica-barras", "figure")
    ],
    Input("select-anio", "value")
)
def actualizar_dashboard(anio_seleccionado):

    # Filtrar por año
    df_anio = df[df["anio"] == anio_seleccionado]

    # Se actualiza la tabla
    columnas = [{"name": c, "id": c} for c in df_anio.columns]
    data_tabla = df_anio.to_dict("records")

    # Con este fragmento de codigo se crea la grafica
    conteo_departamento = (
        df_anio.groupby("departamento")
        .size()
        .reset_index(name="cantidad_homicidios")
        .sort_values("cantidad_homicidios", ascending=False)
    )

    fig = px.bar(
        conteo_departamento,
        x="departamento",
        y="cantidad_homicidios",
        title=f"Homicidios por departamento en {anio_seleccionado}",
        labels={
            "departamento": "Departamento",
            "cantidad_homicidios": "Cantidad de homicidios"
        },
        color="departamento"  # Cada barra con color diferente
    )

    fig.update_layout(
        template="plotly_dark",
        xaxis_tickangle=-45,
        font_color="red",
        plot_bgcolor="black",
        paper_bgcolor="black"
    )

    return data_tabla, columnas, fig

# La siguiente linea de codigo ejecuta el programa
if __name__ == "__main__":
    app.run(debug=True)
