import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import json

with open('municipalities.geojson', 'r', encoding='utf-8') as f:
    municipalities_geojson = json.load(f)

data_file = 'data.csv'
df = pd.read_csv(data_file)

#standardize region names in CSV
df['Region'] = df['Region'].str.strip().str.lower()

#standardize GeoJSON region names
for feature in municipalities_geojson['features']:
    feature['properties']['label_dk'] = feature['properties']['label_dk'].strip().lower()

#verify region matching between CSV and GeoJSON
geojson_regions = {feature['properties']['label_dk'] for feature in municipalities_geojson['features']}
csv_regions = set(df['Region'])

print("Regions in CSV but not in GeoJSON:", csv_regions - geojson_regions)
print("Regions in GeoJSON but not in CSV:", geojson_regions - csv_regions)

#check for missing geometries
missing_geometry = [
    feature['properties']['label_dk']
    for feature in municipalities_geojson['features']
    if not feature.get('geometry') or not feature['geometry'].get('coordinates')
]
print("Regions with Missing Geometry in GeoJSON:", missing_geometry)

#agregate data by Region
agg_data = df.groupby('Region', as_index=False).agg({'value': 'sum'})

#replace missing or invalid values in 'value'
agg_data['value'] = pd.to_numeric(agg_data['value'], errors='coerce').fillna(0)


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H3("Danish Municipalities Choropleth Map", style={"textAlign": "center"}),
            dcc.Graph(id='choropleth-map')
        ], width=12)
    ])
])

@app.callback(
    Output('choropleth-map', 'figure'),
    [Input('choropleth-map', 'clickData')]
)
def update_choropleth(map_click_data):
    #debug print
    print("Plotted Regions (For Map):", agg_data['Region'].unique())

    fig = go.Figure()

    fig.add_trace(go.Choroplethmapbox(
        geojson=municipalities_geojson,
        locations=agg_data['Region'],
        z=agg_data['value'],
        featureidkey="properties.label_dk",
        colorscale="Greens",
        colorbar_title="Value",
        marker_line_width=1,  #
        marker_line_color='red', #made them red to easy spot 
        hovertemplate="<b>%{location}</b><br>Value: %{z}<extra></extra>"
    ))

    fig.add_trace(go.Choroplethmapbox(
        geojson=municipalities_geojson,
        locations=agg_data['Region'],
        z=[None] * len(agg_data['Region']),  #Transparent regions
        featureidkey="properties.label_dk",
        marker_line_width=2,
        marker_line_color='black',
        showscale=False
    ))

    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_zoom=6,
        mapbox_center={"lat": 56.0, "lon": 10.0},
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
