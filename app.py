import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Leitura dos dados
df = pd.read_csv('Summer_olympic_Medals.csv')
df['Country_Name'] = df['Country_Name'].replace('United States', 'United States of America')
df = df[(df['Year'] >= 1992) & (df['Year'] <= 2020)]

# Criação do app
app = dash.Dash(__name__)
server = app.server  # <- necessário para deploy com gunicorn/Render

# Anos disponíveis
years = sorted(df['Year'].unique())

# Layout
app.layout = html.Div([
    html.H1("Dashboard de Medalhas Olímpicas (1992–2020)", style={'textAlign': 'center'}),

    html.Div([
        html.Label("Tipo de medalha:"),
        dcc.RadioItems(
            id='medal-type',
            options=[
                {'label': 'Total', 'value': 'Total'},
                {'label': 'Ouro', 'value': 'Gold'},
                {'label': 'Prata', 'value': 'Silver'},
                {'label': 'Bronze', 'value': 'Bronze'},
            ],
            value='Total',
            labelStyle={'display': 'inline-block', 'margin-right': '10px'}
        )
    ], style={'textAlign': 'center', 'padding': '10px'}),

    html.Div([
        html.Label("Ano Olímpico:"),
        dcc.Dropdown(
            id='year-dropdown',
            options=[{'label': str(y), 'value': y} for y in years],
            value=2020,
            style={'width': '200px', 'margin': 'auto'}
        )
    ], style={'textAlign': 'center', 'padding': '10px'}),

    html.Div([
        html.Label("País Selecionado:"),
        dcc.Dropdown(
            id='country-dropdown',
            options=[{'label': country, 'value': country} for country in df['Country_Name'].unique()],
            value='United States of America',
            style={'width': '200px', 'margin': 'auto'}
        )
    ], style={'textAlign': 'center', 'padding': '10px'}),

    dcc.Graph(id='map-graph', style={'height': '60vh'}),

    html.Div([
        dcc.Graph(id='area-graph'),
        dcc.Graph(id='bar-graph'),
        dcc.Graph(id='pie-graph')
    ], style={'display': 'flex', 'flexWrap': 'wrap'})
])

# Callback
@app.callback(
    [Output('map-graph', 'figure'),
     Output('area-graph', 'figure'),
     Output('bar-graph', 'figure'),
     Output('pie-graph', 'figure')],
    [Input('medal-type', 'value'),
     Input('year-dropdown', 'value'),
     Input('country-dropdown', 'value')]
)
def update_graphs(medal_type, selected_year, selected_country):
    df_filtered = df.copy()

    if medal_type == 'Total':
        df_filtered['Value'] = df_filtered['Gold'] + df_filtered['Silver'] + df_filtered['Bronze']
        title_suffix = 'Total de Medalhas'
    else:
        df_filtered['Value'] = df_filtered[medal_type]
        title_suffix = f'Medalhas de {medal_type}'

    # Mapa
    df_map = df_filtered.groupby('Country_Name')['Value'].sum().reset_index()
    map_fig = px.choropleth(df_map,
                            locations='Country_Name',
                            locationmode='country names',
                            color='Value',
                            hover_name='Country_Name',
                            color_continuous_scale=px.colors.sequential.YlOrRd,
                            title=f'{title_suffix} por País (1992–2020)')

    # Gráfico de área (top 10 países)
    top_countries = df_map.sort_values('Value', ascending=False).head(10)['Country_Name']
    df_area = df_filtered[df_filtered['Country_Name'].isin(top_countries)]
    df_area = df_area.groupby(['Country_Name', 'Year'])['Value'].sum().reset_index()
    area_fig = px.area(df_area, x='Year', y='Value', color='Country_Name',
                       title=f'{title_suffix} - Top 10 Países (1992–2020)')

    # Gráfico de barras (ano selecionado)
    df_year = df_filtered[df_filtered['Year'] == selected_year]
    df_bar = df_year.groupby('Country_Name')['Value'].sum().nlargest(10).reset_index()
    bar_fig = px.bar(df_bar, x='Country_Name', y='Value', color='Country_Name',
                     title=f'{title_suffix} em {selected_year}',
                     color_discrete_sequence=px.colors.qualitative.Set3)
    
    # Gráfico de pizza (distribuição de medalhas do país selecionado)
    df_country = df[df['Country_Name'] == selected_country]
    medals = df_country[['Gold', 'Silver', 'Bronze']].sum()
    pie_fig = px.pie(names=medals.index, values=medals.values,
                     title=f'Distribuição de Medalhas de {selected_country} (1992–2020)',
                     color_discrete_map={'Gold': 'gold', 'Silver': 'silver', 'Bronze': '#cd7f32'})

    return map_fig, area_fig, bar_fig, pie_fig

# Execução
if __name__ == '__main__':
    app.run(debug=False)
