# Dashboard con informacion de los ultimos delitos informaticos cometidos en colombia
# Se solicita la informacion a una API web con los datos de los delitos informaticos documentados
# Una tabla, un json, con datos de cada registro
# pip install flask pandas requests dash
# pip 26.1.1
# Python 3.13.9
# apt update
# apt install python3-venv -y
# python3 -m venv venv
# source venv/bin/activate
# pip install --upgrade pip
# pip install streamlit pandas requests plotly

from datetime import datetime
import json
import time
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# Se guarda el titulo de la pagina y el tipo de letra del dashboard
st.set_page_config(page_title="Delitos Informáticos Colombia", layout="wide")

# Las siguientes lineas de codigo tiene las propiedades del CSS de los diferentes selectores 
st.markdown(
    """
    <style>
    /* Fondo principal y de la barra lateral */
    .stApp, [data-testid="stSidebar"] {
        background-color: #000000 !important;
    }
    /* Forzar color rojo (#FF0000) en textos, títulos y etiquetas */
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, .stSelectbox, .stButton, div {
        color: #FF0000 !important;
    }
    /* Estilo específico para los inputs y botones */
    div[data-baseweb="input"], div[data-baseweb="select"], button {
        background-color: #111111 !important;
        border: 1px solid #FF0000 !important;
    }
    /* Color de datos dentro de la tabla */
    .stDataFrame div {
        color: #FF0000 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Se guardan en variables lo relacionado a la pagina web
st.title("Delitos informáticos colombia")

# A continuacion, mostrar fecha y hora actual en formato legible
ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.write(f"**Fecha y hora actual:** {ahora}")

# Posteriormente, filtro de las columnas de la tabla de los datos (Año y Mes)
col1, col2, col3 = st.columns([1, 1.5, 1.5])

with col2:
    # Codigo que recibe la informacion del año a seleccionar
    anios_disponibles = [str(a) for a in range(2010, datetime.now().year + 1)]
    # aparece en pantalla el año actual por defecto
    anio_seleccionado = st.selectbox("Seleccione el Año", anios_disponibles, index=len(anios_disponibles)-1)

with col3:
    # Se continua a guardar la fecha
    meses = {
        "Enero": "01", "Febrero": "02", "Marzo": "03", "Abril": "04",
        "Mayo": "05", "Junio": "06", "Julio": "07", "Agosto": "08",
        "Septiembre": "09", "Octubre": "10", "Noviembre": "11", "Diciembre": "12"
    }
    mes_nombre = st.selectbox("Seleccione el Mes", list(meses.keys()), index=datetime.now().month - 1)
    mes_codigo = meses[mes_nombre]

with col1:
    # En las siguiente lineas de codigo esta el botón para ejecutar la consulta
    st.write("##")  # Espaciador para alinear con los selectores
    consultar_btn = st.button("Consultar Mes")


# La siguiente funcion indica los datos de la consulta a la API de datos colombia por rango de mes
def consultar_datos_mes(anio, mes):
    DATASET_ID = "4v6r-wu98"
    BASE_URL = f"https://www.datos.gov.co/resource/{DATASET_ID}.json"
    DATE_FIELD = "fecha_hecho"

    LIMIT = 50000
    OFFSET = 0
    registros = []

    # Se carga streamlit
    status_text = st.empty()
    
    # Calcular rangos de fecha del mes
    fecha_inicio = f"{anio}-{mes}-01T00:00:00"
    # Se procesan los datos
    siguiente_mes = int(mes) + 1
    siguiente_anio = int(anio)
    if siguiente_mes > 12:
        siguiente_mes = 1
        siguiente_anio += 1
    fecha_fin = f"{siguiente_anio}-{str(siguiente_mes).zfill(2)}-01T00:00:00"

    while True:
        # Posteriormente se crean los datos de filtrar por todo el rango del mes seleccionado
        params = {
            "$where": f"{DATE_FIELD} >= '{fecha_inicio}' AND {DATE_FIELD} < '{fecha_fin}'",
            "$limit": LIMIT,
            "$offset": OFFSET,
        }

        status_text.text(f"Descargando registros desde el offset {OFFSET}...")

        try:
            r = requests.get(BASE_URL, params=params, timeout=60)
            r.raise_for_status()
            datos = r.json()
        except Exception as e:
            st.error(f"Error al conectarse a la API: {e}")
            break

        if not datos:
            break

        registros.extend(datos)
        OFFSET += LIMIT
        time.sleep(0.1)

    status_text.empty()  # con este codigo se limpia el texto de estado
    return registros


# El siguiente codigo indica la renderizacion de la pagina
if consultar_btn:
    st.write(f"### Resultados para el periodo: {mes_nombre} de {anio_seleccionado}")

    # Obtener registros de la API
    datos_crudos = consultar_datos_mes(anio_seleccionado, mes_codigo)

    if datos_crudos:
        # Guardar en archivo local JSON
        with open("delitos_informaticos_mes.json", "w", encoding="utf-8") as f:
            json.dump(datos_crudos, f, ensure_ascii=False, indent=2)

        # Convertir a DataFrame de Pandas
        df = pd.DataFrame(datos_crudos)

        # Identificar dinámicamente las columnas clave de la API de la Policía (Socrata usa minúsculas)
        col_depto = "departamento" if "departamento" in df.columns else (df.columns[0] if len(df.columns) > 0 else "departamento")
        col_muni = "municipio" if "municipio" in df.columns else "municipio"
        col_arma = "arma_empleada" if "arma_empleada" in df.columns else ("medio_utilizado" if "medio_utilizado" in df.columns else None)
        col_genero = "genero" if "genero" in df.columns else "sexo"

        # En los siguientes codigos se crea la tabla y la grafica con los datos
        st.write("#### Resumen de Delitos por Departamento e Indicadores Clave")
        
        # Agrupación avanzada para exprimir la mayor cantidad de datos posibles
        agrupacion_dict = {col_depto: 'count'} # Primera métrica obligatoria: Total Delitos
        
        # Añadir métricas extras dinámicamente si las columnas existen en la respuesta de la API
        if col_muni in df.columns:
            agrupacion_dict[col_muni] = 'nunique' # Cuántos municipios únicos se vieron afectados
        if col_arma and col_arma in df.columns:
            agrupacion_dict[col_arma] = lambda x: x.mode().iloc[0] if not x.mode().empty else "N/A" # El medio más común usado
        if col_genero in df.columns:
            agrupacion_dict[col_genero] = lambda x: x.mode().iloc[0] if not x.mode().empty else "N/A" # Género de víctima más recurrente

        # Construcción de la tabla maestra agrupada
        df_resumen = df.groupby(col_depto).agg(agrupacion_dict)
        
        # Se procede a renombrar de forma limpia y amigable
        columnas_nuevas = ["Total Delitos en el Mes"]
        if col_muni in df.columns: columnas_nuevas.append("Municipios Afectados")
        if col_arma and col_arma in df.columns: columnas_nuevas.append("Medio Más Frecuente")
        if col_genero in df.columns: columnas_nuevas.append("Género de Víctima Común")
        
        df_resumen.columns = columnas_nuevas
        df_resumen = df_resumen.sort_values(by="Total Delitos en el Mes", ascending=False)
        
        # luego renderizamos la tabla principal modificada
        st.dataframe(df_resumen, use_container_width=True)

        # -------------------------------------------------------------------------
        # ANEXO: Mapa político de Colombia con círculos proporcionales rojos
        # -------------------------------------------------------------------------
        st.write("#### Mapa Político - Distribución de Delitos Informáticos en Colombia")
        
        # Diccionario de coordenadas aproximadas (centroides) de los departamentos de Colombia
        coordenadas_colombia = {
            'AMAZONAS': {'lat': -1.4419, 'lon': -71.5724}, 'ANTIOQUIA': {'lat': 6.2442, 'lon': -75.5812},
            'ARAUCA': {'lat': 7.0847, 'lon': -70.7454}, 'ATLANTICO': {'lat': 10.9639, 'lon': -74.7964},
            'BOLIVAR': {'lat': 9.2422, 'lon': -75.1364}, 'BOYACA': {'lat': 5.5353, 'lon': -73.3678},
            'CALDAS': {'lat': 5.0689, 'lon': -75.5174}, 'CAQUETA': {'lat': 1.6144, 'lon': -75.6062},
            'CASANARE': {'lat': 5.3378, 'lon': -72.3959}, 'CAUCA': {'lat': 2.4419, 'lon': -76.6064},
            'CESAR': {'lat': 10.0333, 'lon': -73.2500}, 'CHOCO': {'lat': 6.0000, 'lon': -77.0000},
            'CORDOBA': {'lat': 8.7479, 'lon': -75.8814}, 'CUNDINAMARCA': {'lat': 4.6097, 'lon': -74.0817},
            'GUAINIA': {'lat': 2.5000, 'lon': -68.5000}, 'GUAVIARE': {'lat': 2.5656, 'lon': -72.6428},
            'HUILA': {'lat': 2.5359, 'lon': -75.5275}, 'LA GUAJIRA': {'lat': 11.3000, 'lon': -72.5000},
            'MAGDALENA': {'lat': 10.4153, 'lon': -74.2000}, 'META': {'lat': 3.9852, 'lon': -73.0000},
            'NARIÑO': {'lat': 1.2814, 'lon': -77.2779}, 'NORTE DE SANTANDER': {'lat': 7.8939, 'lon': -72.5072},
            'PUTUMAYO': {'lat': 1.1498, 'lon': -76.6465}, 'QUINDIO': {'lat': 4.5339, 'lon': -75.6811},
            'RISARALDA': {'lat': 4.8133, 'lon': -75.6961}, 'SAN ANDRES': {'lat': 12.5847, 'lon': -81.7006},
            'SANTANDER': {'lat': 7.1254, 'lon': -73.1198}, 'SUCRE': {'lat': 9.3047, 'lon': -75.3978},
            'TOLIMA': {'lat': 4.4389, 'lon': -75.2322}, 'VALLE DEL CAUCA': {'lat': 3.4372, 'lon': -76.5225},
            'VAUPES': {'lat': 1.2500, 'lon': -70.5000}, 'VICHADA': {'lat': 4.4233, 'lon': -69.7925},
            'BOGOTA D.C.': {'lat': 4.6097, 'lon': -74.0817}
        }

        # Preparar los datos mapeando las coordenadas a cada fila limpia
        df_mapa = df_resumen.reset_index()
        df_mapa['dept_upper'] = df_mapa[col_depto].astype(str).str.upper().str.strip()
        
        # Asignar latitud y longitud por defecto si el nombre no coincide exactamente
        df_mapa['lat'] = df_mapa['dept_upper'].apply(lambda x: coordenadas_colombia.get(x, {'lat': 4.5709, 'lon': -74.2973})['lat'])
        df_mapa['lon'] = df_mapa['dept_upper'].apply(lambda x: coordenadas_colombia.get(x, {'lat': 4.5709, 'lon': -74.2973})['lon'])

        # Cargar los contornos geográficos políticos de Colombia (GeoJSON) para delimitar las fronteras
        geojson_url = "https://raw.githubusercontent.com/mendozamiguel/colombia-geojson/master/colombia.geojson"
        try:
            geojson_data = requests.get(geojson_url, timeout=10).json()
        except:
            geojson_data = None

        # Si el GeoJSON se descargó exitosamente, usamos un mapa de coropletas de fondo combinado con burbujas
        if geojson_data:
            # Creación del mapa base político (líneas de división territorial)
            fig_mapa = px.choropleth(
                df_mapa,
                geojson=geojson_data,
                locations='dept_upper',
                featureidkey="properties.DPTO",
                color_discrete_sequence=["#111111"], # Fronteras oscuras coherentes con el dashboard
                scope="south america"
            )
            
            # Anexar las burbujas rojas personalizadas de tamaño dependiente de los delitos
            fig_burbujas = px.scatter_geo(
                df_mapa,
                lat='lat',
                lon='lon',
                size='Total Delitos en el Mes',
                hover_name=col_depto,
                hover_data=['Total Delitos en el Mes'],
                size_max=45 # Tamaño máximo escalable de los círculos
            )
            
            # Forzar color rojo sólido en los marcadores del mapa
            fig_burbujas.update_traces(marker=dict(color="#FF0000", opacity=0.7, line=dict(width=1, color='#FFFFFF')))
            fig_mapa.add_traces(fig_burbujas.data)
        else:
            # Fallback en caso de fallo de red: Se genera el mapa de burbujas clásico directo
            fig_mapa = px.scatter_geo(
                df_mapa,
                lat='lat',
                lon='lon',
                size='Total Delitos en el Mes',
                hover_name=col_depto,
                hover_data=['Total Delitos en el Mes'],
                size_max=45,
                scope="south america"
            )
            fig_mapa.update_traces(marker=dict(color="#FF0000", opacity=0.7))

        # Estilizar visualmente el mapa para adaptarlo al fondo negro y límites de Colombia
        fig_mapa.update_geos(
            fitbounds="locations",
            visible=False,
            bgcolor="rgba(0,0,0,1)",
            showcountries=True,
            countrycolor="#222222"
        )
        fig_mapa.update_layout(
            paper_bgcolor="rgba(0,0,0,1)",
            plot_bgcolor="rgba(0,0,0,1)",
            margin={"r":0,"t":0,"l":0,"b":0},
            font=dict(color="#FF0000")
        )
        st.plotly_chart(fig_mapa, use_container_width=True)


        # Se crea la grafica de barras
        st.write("#### Total de crímenes por departamento")

        # Posteriormente preparamos datos para la gráfica basándose en nuestro dataframe resumido
        df_counts = df_resumen.reset_index()

        # Crear la gráfica con escala de color Azul (mínimo) a Rojo (máximo)
        fig = px.bar(
            df_counts,
            x=col_depto,
            y="Total Delitos en el Mes",
            color="Total Delitos en el Mes",
            color_continuous_scale=["#0000FF", "#FF0000"],  # Azul a Rojo
            labels={col_depto: "Departamento"},
        )

        # Estilizar la gráfica para el entorno oscuro
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,1)",
            plot_bgcolor="rgba(0,0,0,1)",
            font=dict(color="#FF0000"),
            xaxis=dict(gridcolor="#222222", tickangle=45),
            yaxis=dict(gridcolor="#222222"),
            coloraxis_showscale=True,
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning(
            f"No se encontraron registros de delitos informáticos para {mes_nombre} de {anio_seleccionado}."
        )