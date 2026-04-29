# Dashboard con informacion de equipo de futbol america de cali, colombia con IA
# Se solicita la informacion a una API web con todos los datos del equipo y con eso se crea
# Una tabla, una grafica y un  pronostico del siguiente numero
# pip install flask pandas requests lxml beautifulsoup4
# pip 25.3.1
# Python 3.13.1

from flask import Flask, render_template_string
import pandas as pd
import requests

app = Flask(__name__)

# URL de Wikipedia del América de Cali
URL = "https://es.wikipedia.org/wiki/Am%C3%A9rica_de_Cali"

# Template HTML
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Dashboard América de Cali</title>
<style>
body { font-family: Arial, sans-serif; margin: 20px; }
h1 { color: #b71c1c; }
table { border-collapse: collapse; width: 100%; margin-bottom: 30px; }
th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
th { background-color: #f2f2f2; }
div.table-wrapper { overflow-x: auto; }
</style>
</head>
<body>
<h1>Dashboard: América de Cali - Tablas de Wikipedia</h1>
<p>Total de tablas encontradas: {{ tablas|length }}</p>

{% for tabla_html in tablas %}
<h2>Tabla {{ loop.index0 }}</h2>
<div class="table-wrapper">{{ tabla_html | safe }}</div>
{% endfor %}

</body>
</html>
"""

def obtener_tablas():
    # Descargar la página con User-Agent para evitar 403
    headers = {
        "User-Agent": "ProyectoEducativo/1.0 (contacto@email.com)"
    }
    response = requests.get(URL, headers=headers)
    response.raise_for_status()

    # Leer todas las tablas HTML
    tablas_df = pd.read_html(response.text)

    # Convertir cada DataFrame a HTML
    tablas_html = [df.to_html(index=False, escape=False) for df in tablas_df]
    return tablas_html

@app.route("/")
def dashboard():
    tablas_html = obtener_tablas()
    return render_template_string(HTML_TEMPLATE, tablas=tablas_html)

if __name__ == "__main__":
    # Arranca el dashboard en localhost:5000
    app.run(debug=True)
