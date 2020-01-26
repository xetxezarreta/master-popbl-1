import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import processing
import plotly.graph_objects as go

dashboard = processing.Dashboard()

# Create app layout
app = dash.Dash(__name__)
app.layout = html.Div([
    # Title
    html.Div([
        html.H1(
            "Visual Analytic Process",
            style={"margin-bottom": "0px"},
        ),
        html.H3(
            "",
            style={"margin-bottom": "0px"},
        ),
    ],
        id="title",
        className="one-half column",
    ),

    # dashboard
    html.Div([
        # filters
        html.Div([
            html.P("Cluster algorithm: DBSCAN"),

            html.P("EPS value selector"),
            dcc.Input(
                id="eps_input_range", type="text", placeholder="input with range",
                debounce= True,
                min=0,
                value=2
            ),

            html.P("Minimum Sample number selector"),
            dcc.Input(
                id="min_samples_input_range", type="text", placeholder="input",
                debounce= True,
                min=2,
                value=14
            ),

            html.P("Filter correlation attributes"),
            dcc.Dropdown(
                id='correlation-dropdown',
                options=dashboard.get_variable_names(),
                multi=True,
            )
        ],
            id="filters",
            className="container",
        ),

        # indicators
        html.Div([
            # Precision
            html.Div([
                html.H1("Silhouette"),
                html.H3(id="silhouette_text")
            ],
                id="silhouette",
                className="mini_container indicator",
            ),

            # Recall
            html.Div([
                html.H1("N-Clusters"),
                html.H3(id="clusters_text")
            ],
                id="clusters",
                className="mini_container indicator",
            ),

            # F1-Score
            html.Div([
                html.H1("N-Noise"),
                html.H3(id="noise_text")
            ],
                id="noise",
                className="mini_container indicator",
            ),
        ],
            id="indicators",
        ),

        html.Div([
            dcc.Graph(id='correlation-graph')
        ],
            id="graphs",
        ),

        html.Div([
            dcc.Graph(id='table_g', figure=go.Figure(data=[go.Table(header=dict(values=[]),
                                                                    cells=dict(values=[]))]))
        ],
            id="table_div",

        )
    ],
        id="dashboard",
        className="flex-display",
    ),
])


@app.callback(
    [
        Output("silhouette_text", "children"),
        Output("clusters_text", "children"),
        Output("noise_text", "children"),
        Output("table_g", "figure"),
    ],
    [
        Input("min_samples_input_range", "value"),
        Input("eps_input_range", "value")
    ],
)
def algorithm_updated(ms, eps):
    dashboard.update_model('DBSCAN', int(ms), float(eps))
    accuracy, f1, rocauc = dashboard.get_indicators()
    columns, values = dashboard.get_table_data()
    figure = go.Figure(data=[go.Table(header=dict(values=columns), cells=dict(values=values))])
    return accuracy, f1, rocauc, figure


@app.callback(
    Output("correlation-graph", "figure"),
    [Input("correlation-dropdown", "value")],
)
def correlation_updated(value):
    graph = create_new_graph(value)
    return graph


def create_new_graph(value):
    graph = {}
    if value is not None and len(value) == 2:
        trace = []

        df_cluster = dashboard.get_df_cluster()
        for i in df_cluster.cluster.unique():
            temp_df = df_cluster[df_cluster["cluster"] == i]

            trace.append(dict(
                x=temp_df[value[0]],
                y=temp_df[value[1]],
                text=temp_df['cluster'],
                mode='markers',
                opacity=0.4,
                marker={
                    'size': 15,
                    'line': {'width': 0.5, 'color': 'white'}
                },
                name=i
            ))
        graph = {
            'data': trace,
            'layout': dict(
                xaxis={'title': str(value[0])},
                yaxis={'title': str(value[1])},
                legend={'x': 0, 'y': 1},
                hovermode='closest',
            )
        }
    return graph


if __name__ == '__main__':
    app.run_server(debug=True)
