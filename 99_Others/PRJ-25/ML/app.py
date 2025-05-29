import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.graph_objects as go

# === CONFIG ===
df_path = "df_temp_1_corrected"  # <- use corrected CSVs

# Load data
df = pd.read_csv(df_path + ".csv")

# Get sensor columns (temperature only)
t_sensor_cols = [col for col in df.columns if col.startswith("T_")]

# Initialize first sensor to display
default_sensor = t_sensor_cols[0]

# === Dash App ===
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H3(f"Interactive Editor for Sensors in {df_path}"),
    dcc.Dropdown(
        id='sensor-selector',
        options=[{'label': col, 'value': col} for col in t_sensor_cols],
        value=default_sensor
    ),
    dcc.Graph(id='editable-graph'),
    html.Div("Click on a point to edit its value."),
    html.Div([
        html.Label(id='current-y-label', children="New Y value:"),
        dcc.Input(id='new-y', type='number', step=0.01),
        html.Button("Apply Edit", id='edit-btn')
    ], style={'margin-top': '10px'}),
    html.Button("Save All Changes", id="save-btn"),
    html.Div(id='save-output')
])

# Store selected index and column
selected_index_store = {'index': None, 'sensor': default_sensor}

# Generate figure dynamically


def create_figure(sensor_col, selected_index=None):
    fig = go.Figure(data=[go.Scatter(
        x=df['Time'], y=df[sensor_col],
        mode='markers+lines', name=sensor_col,
        marker=dict(size=6, color='blue')
    )])

    if selected_index is not None:
        fig.add_trace(go.Scatter(
            x=[df['Time'][selected_index]],
            y=[df[sensor_col][selected_index]],
            mode='markers',
            marker=dict(color='red', size=10),
            name='Selected Point'
        ))

    fig.update_layout(
        title=f"Edit {sensor_col} by selecting a point",
        xaxis_title='Time',
        yaxis_title='Temperature (C)',
        template='plotly_white',
    )
    return fig

# Callbacks


@app.callback(
    Output('editable-graph', 'figure'),
    Input('sensor-selector', 'value')
)
def update_graph(sensor_col):
    selected_index_store['sensor'] = sensor_col
    return create_figure(sensor_col)


@app.callback(
    Output('current-y-label', 'children'),
    Input('editable-graph', 'clickData')
)
def update_label(clickData):
    if clickData and 'points' in clickData:
        point = clickData['points'][0]
        idx = point['pointIndex']
        selected_index_store['index'] = idx
        sensor = selected_index_store['sensor']
        val = df.at[idx, sensor]
        return f"New Y value (current: {val}):"
    return "New Y value:"


@app.callback(
    Output('save-output', 'children'),
    Input('edit-btn', 'n_clicks'),
    State('new-y', 'value')
)
def apply_edit(n_clicks, new_y):
    if n_clicks and new_y is not None:
        idx = selected_index_store['index']
        sensor = selected_index_store['sensor']
        if idx is not None and sensor is not None:
            df.at[idx, sensor] = new_y
            return f"Updated {sensor} at index {idx} to value {new_y}"
    return "No edit applied."


@app.callback(
    Output('save-output', 'children', allow_duplicate=True),
    Input('save-btn', 'n_clicks'),
    prevent_initial_call=True
)
def save_changes(n_clicks):
    df.to_csv(df_path + ".csv", index=False)
    return f"Changes saved to {df_path}.csv"


if __name__ == '__main__':
    app.run(debug=True)
