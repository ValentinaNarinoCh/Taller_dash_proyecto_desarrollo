"""
Dashboard de demanda energética (Austria) con Dash/Plotly.

Este módulo monta una aplicación Dash que:
- Carga una serie temporal desde ``datos_energia.csv`` (índice por columna ``time``).
- Muestra la demanda histórica y una proyección con bandas superior/inferior.
- Permite al usuario elegir una fecha/hora inicial y el horizonte de proyección.

Requisitos de datos
-------------------
Se espera un CSV con, al menos, las columnas:
- ``time``: marca de tiempo parseable por ``pandas.to_datetime``.
- ``AT_load_actual_entsoe_transparency``: demanda observada [MW].
- ``forecast``: proyección puntual [MW].
- ``Upper bound`` y ``Lower bound``: límites de banda [MW].

Ejecución
---------
Ejecute el archivo para iniciar el servidor local de Dash.

Notas
-----
- El diseño y controles están en español.
- Las excepciones por datos faltantes o formatos inválidos no se capturan aquí;
  se propagan para facilitar el depurado.
"""
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import numpy as np
import pandas as pd
import datetime as dt



app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
app.title = "Dashboard energia"

server = app.server
app.config.suppress_callback_exceptions = True


# Load data from csv
def load_data():
    """
    Carga la serie temporal desde ``datos_energia.csv`` y la prepara para graficar.

    La función:
    1) lee el CSV,
    2) convierte la columna ``time`` a ``datetime``,
    3) establece ``time`` como índice del ``DataFrame``.

    Returns
    -------
    pandas.DataFrame
        Marco con índice temporal y, al menos, las columnas
        ``AT_load_actual_entsoe_transparency``, ``forecast``,
        ``Upper bound`` y ``Lower bound``.

    Raises
    ------
    FileNotFoundError
        Si el archivo ``datos_energia.csv`` no está disponible.
    KeyError
        Si falta la columna ``time`` u otras columnas esperadas.
    ValueError
        Si alguna marca temporal no puede convertirse a ``datetime``.
    """
    # To do: Completar la función
    data3=pd.read_csv('datos_energia.csv')
    data3['time'] = pd.to_datetime(data3['time'])
    data3.set_index('time', inplace=True)
    return data3

# Cargar datos
data = load_data()

# Graficar serie
def plot_series(data, initial_date, proy):
    """
    Construye la figura de la serie de tiempo con demanda, proyección y banda.

    La serie se filtra desde ``initial_date`` hasta el penúltimo bloque, recortando
    ``120 - proy`` puntos del final para que el tramo visible coincida con el
    horizonte solicitado.

    Parameters
    ----------
    data : pandas.DataFrame
        Serie con índice de fechas y columnas:
        ``AT_load_actual_entsoe_transparency``, ``forecast``,
        ``Upper bound`` y ``Lower bound``.
    initial_date : datetime-like
        Fecha/hora inicial (inclusive) desde la que se graficará.
    proy : int
        Número de horas a proyectar (0–119). Se usa para calcular el recorte final.

    Returns
    -------
    plotly.graph_objs.Figure
        Figura con tres trazas (observado, proyección y banda de confianza).

    Raises
    ------
    KeyError
        Si faltan columnas requeridas en ``data``.
    """
    data_plot = data.loc[initial_date:]
    data_plot = data_plot[:-(120-proy)]
    fig = go.Figure([
        go.Scatter(
            name='Demanda energética',
            x=data_plot.index,
            y=data_plot['AT_load_actual_entsoe_transparency'],
            mode='lines',
            line=dict(color="#188463"),
        ),
        go.Scatter(
            name='Proyección',
            x=data_plot.index,
            y=data_plot['forecast'],
            mode='lines',
            line=dict(color="#bbffeb",),
        ),
        go.Scatter(
            name='Upper Bound',
            x=data_plot.index,
            y=data_plot['Upper bound'],
            mode='lines',
            marker=dict(color="#444"),
            line=dict(width=0),
            showlegend=False
        ),
        go.Scatter(
            name='Lower Bound',
            x=data_plot.index,
            y=data_plot['Lower bound'],
            marker=dict(color="#444"),
            line=dict(width=0),
            mode='lines',
            fillcolor="rgba(242, 255, 251, 0.3)",
            fill='tonexty',
            showlegend=False
        )
    ])

    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        yaxis_title='Demanda total [MW]',
        #title='Continuous, variable value error bars',
        hovermode="x"
    )
    #fig = px.line(data2, x='local_timestamp', y="Demanda total [MW]", markers=True, labels={"local_timestamp": "Fecha"})
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#2cfec1")
    fig.update_xaxes(showgrid=True, gridwidth=0.25, gridcolor='#7C7C7C')
    fig.update_yaxes(showgrid=True, gridwidth=0.25, gridcolor='#7C7C7C')
    #fig.update_traces(line_color='#2cfec1')

    return fig



def description_card():
    """
    Crea la tarjeta de descripción del panel.

    Returns
    -------
    dash.html.Div
        Componente con el título del panel y un texto introductorio.
    """
    return html.Div(
        id="description-card",
        children=[
            #html.H5("Proyecto 1"),
            html.H3("Pronóstico de producción energética"),
            html.Div(
                id="intro",
                children="Esta herramienta contiene información sobre la demanda energética total en Austria cada hora según lo públicado en ENTSO-E Data Portal. Adicionalmente, permite realizar pronósticos hasta 5 dias en el futuro."
            ),
        ],
    )


def generate_control_card():
    """
    Crea la tarjeta de controles (fecha/hora inicial y horizonte de proyección).

    Utiliza los límites mínimo y máximo del índice de ``data`` para configurar
    el selector de fecha, y un ``Dropdown`` para la hora (0–24).

    Returns
    -------
    dash.html.Div
        Contenedor con los componentes de entrada del usuario.
    """
    return html.Div(
        id="control-card",
        children=[

            # Fecha inicial
            html.P("Seleccionar fecha y hora inicial:"),

            html.Div(
                id="componentes-fecha-inicial",
                children=[
                    html.Div(
                        id="componente-fecha",
                        children=[
                            dcc.DatePickerSingle(
                                id='datepicker-inicial',
                                min_date_allowed=min(data.index.date),
                                max_date_allowed=max(data.index.date),
                                initial_visible_month=min(data.index.date),
                                date=max(data.index.date)-dt.timedelta(days=7)
                            )
                        ],
                        style=dict(width='30%')
                    ),
                    
                    html.P(" ",style=dict(width='5%', textAlign='center')),
                    
                    html.Div(
                        id="componente-hora",
                        children=[
                            dcc.Dropdown(
                                id="dropdown-hora-inicial-hora",
                                options=[{"label": i, "value": i} for i in np.arange(0,25)],
                                value=pd.to_datetime(max(data.index)-dt.timedelta(days=7)).hour,
                                # style=dict(width='50%', display="inline-block")
                            )
                        ],
                        style=dict(width='20%')
                    ),
                ],
                style=dict(display='flex')
            ),

            html.Br(),

            # Slider proyección
            html.Div(
                id="campo-slider",
                children=[
                    html.P("Ingrese horas a proyectar:"),
                    dcc.Slider(
                        id="slider-proyeccion",
                        min=0,
                        max=119,
                        step=1,
                        value=0,
                        marks=None,
                        tooltip={"placement": "bottom", "always_visible": True},
                    )
                ]
            )     
     
        ]
    )


app.layout = html.Div(
    id="app-container",
    children=[
        
        # Left column
        html.Div(
            id="left-column",
            className="four columns",
            children=[description_card(), generate_control_card()]
            + [
                html.Div(
                    ["initial child"], id="output-clientside", style={"display": "none"}
                )
            ],
        ),
        
        # Right column
        html.Div(
            id="right-column",
            className="eight columns",
            children=[


                # Grafica de la serie de tiempo
                html.Div(
                    id="model_graph",
                    children=[
                        html.B("Demanda energética total en Austria [MW]"),
                        html.Hr(),
                        dcc.Graph(
                            id="plot_series",  
                        )
                    ],
                ),

            
            ],
        ),
    ],
)


@app.callback(
    Output(component_id="plot_series", component_property="figure"),
    [Input(component_id="datepicker-inicial", component_property="date"),
    Input(component_id="dropdown-hora-inicial-hora", component_property="value"),
    Input(component_id="slider-proyeccion", component_property="value")]
)
def update_output_div(date, hour, proy):
    """
    Callback de Dash que actualiza la figura de la serie de tiempo.

    Convierte ``date`` (YYYY-MM-DD) y ``hour`` en un ``Timestamp`` inicial,
    y genera la figura llamando a ``plot_series``.

    Parameters
    ----------
    date : str or None
        Fecha seleccionada en formato ``YYYY-MM-DD``.
    hour : int or None
        Hora del día (0–24) seleccionada por el usuario.
    proy : int or None
        Horizonte de proyección en horas (0–119).

    Returns
    -------
    plotly.graph_objs.Figure
        La figura actualizada para el componente ``dcc.Graph``.

    Notes
    -----
    Si alguno de los parámetros es ``None``, el callback no devuelve nada
    (Dash conservará la figura anterior).
    """
    if ((date is not None) & (hour is not None) & (proy is not None)):
        hour = str(hour)
        minute = str(0)

        initial_date = date + " " + hour + ":" + minute
        initial_date = pd.to_datetime(initial_date, format="%Y-%m-%d %H:%M")

        # Graficar
        plot = plot_series(data, initial_date, int(proy))
        return plot


# Run the server
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
