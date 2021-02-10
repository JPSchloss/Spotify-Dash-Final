#### Spotify Top 200 Application ####

#### Initial Set Up ####

# Importing Libraries
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

import dash
import dash_html_components as html
import dash_core_components as dcc

import networkx as nx

from dash.dependencies import Input, Output

import base64
import warnings

# Bringing in Data
collab_data = pd.read_csv("./data/US_Spotify_Data.csv")
collab_genres = pd.read_csv("./data/US_Spotify_Genre_Data.csv")
collab_features_data = pd.read_csv("./data/US_Spotify_Audio_Features_Working_Data.csv")
network_data = pd.read_csv("./data/Genre_Network_Data.csv")

# Cleaning Up Some Columns
collab_data['Date'] = pd.to_datetime(collab_data['Date'])
collab_data['Album_release_dayweek'] = pd.Categorical(collab_data['Album_release_dayweek'],
                                                      categories=['Mon', 'Tue', 'Wed',
                                                                  'Thu', 'Fri', 'Sat', 'Sun'],
                                                      ordered=True)

# Setting Colors
colors = {
    'main_color': '#1DB954',
    'bg_color': '#1DB954',
    'alt_bg_color': '#000000',
    'plot_bg_color': '#000000',
    'txt_color1': '#FFFFFF',
    'txt_color2': '#191414',
    'genrebarcolors': ['greenyellow', 'chartreuse', 'lawngreen', '#1DB954', 'lime'],
    'collabbarcolors': ['greenyellow', 'chartreuse', 'lawngreen', '#1DB954', 'lime',
                        'greenyellow', 'chartreuse', 'lawngreen', '#1DB954', 'lime',
                        'greenyellow']
}

# Setting Up A Function For Later...
def create_edgelist(data):
    # Create dictionary of track to genres of genres of artists
    track_genre = {}
    turi_list = list(data['Track URI2'])
    g_list = list(data['Genre'])

    for i in range(len(data)):

        uri = turi_list[i]
        genre = g_list[i]

        if uri in track_genre:
            track_genre[uri].append(genre)
        else:
            track_genre[uri] = [genre]

    # Create Edgelist dataframee
    track_list = []
    genre1_list = []
    genre2_list = []

    for key, values in track_genre.items():
        for i in range(1, len(values)):
            track_list.append(key)
            genre1_list.append(values[0])
            genre2_list.append(values[i])

    edge_list = pd.DataFrame({'Track URI2': track_list,
                              'Artist Genre': genre1_list,
                              'Collaborator Genre': genre2_list})

    return edge_list

# Loading in Header Photo
image_filename = './assets/SpotifyImg.png'
encoded_image = base64.b64encode(open(image_filename, 'rb').read())

# Loading in Base Stylesheet
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

#### Declaring Application ####
app = dash.Dash(__name__, suppress_callback_exceptions=True)


#### Setting Base App Layout With Tabs ####
app.layout = html.Div(style={'backgroundColor': colors['alt_bg_color']},
                      children=[
                          html.Div(style={'backgroundColor': colors['alt_bg_color'], 'textAlign': 'center'}, children=[
                              html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()))]),

                          dcc.Tabs(
                              id="tabs-with-classes",
                              value='Overview',
                              parent_className='custom-tabs',
                              className='custom-tabs-container',
                              children=[
                                  dcc.Tab(
                                      label='Overview',
                                      value='Overview',
                                      className='custom-tab',
                                      selected_className='custom-tab--selected'
                                  ),
                                  dcc.Tab(
                                      label='Tracks',
                                      value='Tracks',
                                      className='custom-tab',
                                      selected_className='custom-tab--selected'
                                  ),
                                  dcc.Tab(
                                      label='Artists',
                                      value='Artists', className='custom-tab',
                                      selected_className='custom-tab--selected'
                                  ),
                                  dcc.Tab(
                                      label='Legacy',
                                      value='Legacy',
                                      className='custom-tab',
                                      selected_className='custom-tab--selected'
                                  ),
                                  dcc.Tab(
                                      label='Additional Info',
                                      value='Additional Info',
                                      className='custom-tab',
                                      selected_className='custom-tab--selected'
                                  ),
                              ]),
                          html.Div(id='tabs-content-classes')
                      ]
                      )


#### Setting Up Tabs and Layout ####
@app.callback(Output('tabs-content-classes', 'children'),
              Input('tabs-with-classes', 'value'))
def render_content(tab):
    if tab == 'Overview':
        return html.Div([
            html.H1(children='What Factors Correlate with “Successful” Collaborations?'),
            html.Div(className='text-header',
                     children=[
                         html.Div('''
                        This application leverages data from Spotify’s Top 200 Charts in the US between 2017 - 2020 
                        and enables users to visualize and explore various factors that correlate with the success 
                        of a successful track. While the application was originally developed to explore factors 
                        that determine the success of collaborations, it can serve as a starting point for broader 
                        analyses beyond this topic, depending on the users’ needs.
                            ''', style={'text-align': 'left', 'padding-left': '30px', 'padding-right': '30px'}),
                         html.Br(),
                         html.Div('''This page gives a broad overview of the distribution of the number of artists 
                         involved in each track, as well as the distribution of number of artists across genres. 
                         Additionally, breakdowns of how key metrics of success vary across genres are also shown. 
                         The primary metrics of success used within this application are: the position on chart, 
                         number of streams, and revenue, which varies linearly with streams at a rate of $0.00331 per stream.
                         ''', style={'text-align': 'left', 'padding-left': '30px', 'padding-right': '30px'})]),
            html.H2(children='Collaboration Metrics'),
            dcc.RadioItems(className='graph-radio-buttons',
                           id='collab_data_source',
                           options=[
                               {'label': 'Count', 'value': 'Count'},
                               {'label': 'Position', 'value': 'Position'},
                               {'label': 'Streams', 'value': 'Streams'},
                               {'label': 'Revenue', 'value': 'Revenue'}],
                           value='Count',
                           labelStyle={'display': 'inline-block'}),
            html.Div(className='graph-container',
                     children=[dcc.Graph(id='collab_bar_chart')]),
            html.Br(),
            html.H2(children='Genre Metrics'),
            html.Div(className='group-select-buttons', children=[
                html.Div(
                    dcc.Dropdown(className='selection-box',
                                 id='genre_selections',
                                 options=[{'label': i, 'value': i} for i in
                                          collab_genres['Artist Genre'].unique()],
                                 multi=True,
                                 value="None"),
                    style={'width': '60%', 'display': 'inline-block', 'vertical-align': 'left'}),
                html.Div(
                    dcc.RadioItems(className='graph-radio-buttons2',
                                   id='genre_data_source',
                                   options=[
                                       {'label': 'Count', 'value': 'Count'},
                                       {'label': 'Position', 'value': 'Position'},
                                       {'label': 'Streams', 'value': 'Streams'},
                                       {'label': 'Revenue', 'value': 'Revenue'}],
                                   value='Count',
                                   labelStyle={'display': 'inline-block'}),
                    style={'width': '40%', 'display': 'inline-block', 'vertical-align': 'right'})]),
            html.Div(className='graph-container',
                     children=[dcc.Graph(id='genre_bar_chart')]),
            html.Br(),
            html.H2(children='Chart Position Metrics'),
            html.Div(className='group-select-buttons', children=[
                html.Div([
                    dcc.RadioItems(className='graph-radio-buttons2',
                                   id='position_streams_data_source',
                                   options=[
                                       {'label': 'All Streams', 'value': 'All Streams'},
                                       {'label': 'Average Streams', 'value': 'Average Streams'}],
                                   value='All Streams',
                                   labelStyle={'display': 'inline-block'}),
                    html.Div(className='graph-container2',
                             children=[dcc.Graph(id='position_streams_bar_chart')])],
                    style={'width': '49%', 'display': 'inline-block', 'align-content': 'left', 'padding-right': '9px'}),
                html.Div([
                    dcc.RadioItems(className='graph-radio-buttons2',
                                   id='position_revenue_data_source',
                                   options=[
                                       {'label': 'All Revenues', 'value': 'All Revenues'},
                                       {'label': 'Average Revenues', 'value': 'Average Revenues'},
                                   ],
                                   value='All Revenues',
                                   labelStyle={'display': 'inline-block'}
                                   ),
                    html.Div(className='graph-container2',
                             children=[dcc.Graph(id='position_revenue_bar_chart')])],
                    style={'width': '49%', 'display': 'inline-block', 'align-content': 'right', 'padding-left': '9px'})
            ]),
            html.Div(style={'background-color': '#000000', 'padding-bottom': '70px'})
        ])
    elif tab == 'Tracks':
        return html.Div([
            html.H1(children='An Exploration of Tracks'),
            html.Div(className='text-header',
                     children=[
                         html.Div('''
                        This page gives a snapshot of some of the most successful tracks between 2017 - 2020 
                        and their performance over time. This allows for a comparison across various metrics, 
                        including position, streams, and ranking. The time horizon on the x-axis can be varied 
                        accordingly to visualize how each metric evolves over each song’s lifetime on the chart. 
                        Most tracks tend to reach their peak within the first couple of days on the chart, 
                        and gradually plateau out.
                            ''', style={'text-align': 'left', 'padding-left': '30px', 'padding-right': '30px'})]),
            html.H2(children='Tracks Highlights'),
            html.Div(className='group-text-containers', children=[
                html.Div(className='graph-container2', children=[
                    html.H3(children='Top Average Position'),
                    html.H4(children='Homicide By Logic ft. Eminem')],
                         style={'width': '48%', 'display': 'inline-block', 'align-content': 'left',
                                'padding-left': '9px'}),

                html.Div(className='graph-container2', children=[
                    html.H3(children='Top Average Streams & Revenue'),
                    html.H4(children="I Don't Fuck With You By Big Sean")],
                         style={'width': '48%', 'display': 'inline-block', 'align-content': 'right',
                                'padding-left': '9px'})]),
            html.H2(children='Track Metrics'),
            html.Div(className='group-select-buttons', children=[
                html.Div(
                    dcc.Dropdown(className='selection-box',
                                 id='track_selections',
                                 options=[{'label': i, 'value': i} for i in
                                          collab_data['Track Name'].unique()],
                                 multi=True,
                                 value="None"),
                    style={'width': '60%', 'display': 'inline-block', 'vertical-align': 'left'}),
                html.Div(
                    dcc.RadioItems(className='graph-radio-buttons2',
                                   id='track_data_source',
                                   options=[
                                       {'label': 'Count', 'value': 'Count'},
                                       {'label': 'Position', 'value': 'Position'},
                                       {'label': 'Streams', 'value': 'Streams'},
                                       {'label': 'Revenue', 'value': 'Revenue'}],
                                   value='Count',
                                   labelStyle={'display': 'inline-block'}),
                    style={'width': '40%', 'display': 'inline-block', 'vertical-align': 'right'})]),
            html.Div(className='graph-container',
                     children=[dcc.Graph(id='track_bar_chart')]),
            html.Br(),
            html.H2(children='Track Revenue Over Time'),
            html.Div(className='group-select-buttons', children=[
                html.Div(
                    dcc.Dropdown(className='selection-box',
                                 id='track_revenue_selection',
                                 options=[{'label': i, 'value': i} for i in
                                          collab_data['Track Name'].unique()],
                                 multi=True,
                                 value='None')),
            ]),
            html.Div(className='graph-container',
                     children=[dcc.Graph(id='track_revenue_over_time_plot')]),
            html.Br(),
            html.H2(children='Track Metrics Over Time'),
            html.Div(className='group-select-buttons', children=[
                html.Div(
                    dcc.Dropdown(className='selection-box',
                                 id='top_tracks_track_selection',
                                 options=[{'label': i, 'value': i} for i in
                                          collab_data['Track Name'].unique()],
                                 multi=True,
                                 value="None"),
                    style={'width': '60%', 'display': 'inline-block', 'vertical-align': 'left'}),
                html.Div(
                    dcc.RadioItems(className='graph-radio-buttons2',
                                   id='top_tracks_data_source',
                                   options=[
                                       {'label': 'Position', 'value': 'Position'},
                                       {'label': 'Streams', 'value': 'Streams'}],
                                   value='Position',
                                   labelStyle={'display': 'inline-block'}),
                    style={'width': '40%', 'display': 'inline-block', 'vertical-align': 'right'})]),
            html.Div(className='graph-container',
                     children=[dcc.Graph(id='top_tracks_over_time_plot')]),

            html.Div(style={'background-color': '#000000', 'padding-bottom': '70px'})
        ])
    elif tab == 'Artists':
        return html.Div([
            html.H1(children='An Exploration of Artists'),
            html.Div(className='text-header',
                     children=[
                         html.Div('''
                                    This page gives an overview of the most successful artists by various metrics. 
                                    Additionally, users can view the average score for each audio feature for any given 
                                    artists. The average score for each audio feature is extracted from Spotify’s API 
                                    and is calculated using each artist’s most recent 20 albums, allowing for a 
                                    quantitive comparison of musical styles across artists.
                                        ''',
                                  style={'text-align': 'left', 'padding-left': '30px', 'padding-right': '30px'})]),
            html.H2(children='Artist Metrics'),
            html.Div(className='group-select-buttons', children=[
                html.Div(
                    dcc.Dropdown(className='selection-box',
                                 id='artist_selections',
                                 options=[{'label': i, 'value': i} for i in
                                          collab_data['Artist Name'].unique()],
                                 multi=True,
                                 value="None"),
                    style={'width': '60%', 'display': 'inline-block', 'vertical-align': 'left'}),
                html.Div(
                    dcc.RadioItems(className='graph-radio-buttons2',
                                   id='artist_data_source',
                                   options=[
                                       {'label': 'Count', 'value': 'Count'},
                                       {'label': 'Position', 'value': 'Position'},
                                       {'label': 'Streams', 'value': 'Streams'},
                                       {'label': 'Revenue', 'value': 'Revenue'}],
                                   value='Count',
                                   labelStyle={'display': 'inline-block'}),
                    style={'width': '40%', 'display': 'inline-block', 'vertical-align': 'right'})]),
            html.Div(className='graph-container',
                     children=[dcc.Graph(id='artist_bar_chart')]),
            html.Br(),
            html.H2(children='Artist Highlights'),
            html.Div(className='group-text-containers', children=[
                html.Div(className='graph-container2', children=[
                    html.H3(children='Marvin Divine'),
                    html.H4(children='Top Average Position')],
                         style={'width': '30%', 'display': 'inline-block', 'align-content': 'left',
                                'padding-right': '9px'}),
                html.Div(className='graph-container2', children=[
                    html.H3(children='August Alsina'),
                    html.H4(children='Top Average Streams & Revenue')],
                         style={'width': '30%', 'display': 'inline-block', 'align-content': 'center',
                                'padding-left': '9px', 'padding-right': '9px'}),
                html.Div(className='graph-container2', children=[
                    html.H3(children='Drake'),
                    html.H4(children='Most Frequent In Dataset')],
                         style={'width': '30%', 'display': 'inline-block', 'align-content': 'right',
                                'padding-left': '9px'})]),
            html.Br(),
            html.H2(children='Artist Audio Features'),
            html.Div(className='group-select-buttons', children=[
                html.Div(
                    dcc.Dropdown(className='selection-box',
                                 id='artist_selections2',
                                 options=[{'label': i, 'value': i} for i in
                                          collab_data['Artist Name'].unique()],
                                 multi=True,
                                 value='None')),
            ]),
            html.Div(className='graph-container',
                     children=[dcc.Graph(id='artist_radar_graph')]),
            html.Div(style={'background-color': '#000000', 'padding-bottom': '70px'})
        ])
    elif tab == 'Legacy':
        return html.Div([
            html.H1(children='An Exploration Into Chart Legacy'),
            html.Div(className='text-header',
                     children=[
                         html.Div('''This page explores factors related to the length of a track’s duration on 
                         the chart. Users can examine the distribution of the number of tracks by duration on the 
                         chart, as well as observe how key metrics of success can vary as a track accumulates more 
                        days on the chart.''',
                                  style={'text-align': 'left', 'padding-left': '30px', 'padding-right': '30px'})]),

            html.H2(children='Legacy & Count Metrics'),
            dcc.RadioItems(className='graph-radio-buttons',
                           id='track_artist',
                           options=[
                               {'label': 'Tracks', 'value': 'Tracks'},
                               {'label': 'Artists', 'value': 'Artists'}],
                           value='Tracks',
                           labelStyle={'display': 'inline-block'}),
            html.Div(className='graph-container',
                     children=[dcc.Graph(id='count_time_plot')]),
            html.Br(),
            html.H2(children='Legacy & Track Metrics'),
            html.Div(className='group-select-buttons2', children=[
                html.Div(
                    dcc.RadioItems(className='graph-radio-buttons2',
                                   id='tracks_on_chart_avg_or_max',
                                   options=[
                                       {'label': 'Average', 'value': 'Average'},
                                       {'label': 'Max', 'value': 'Max'}],
                                   value='Average',
                                   labelStyle={'display': 'inline-block'}),
                    style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'left'}),
                html.Div(
                    dcc.RadioItems(className='graph-radio-buttons3',
                                   id='tracks_on_chart_data_source',
                                   options=[
                                       {'label': 'Position', 'value': 'Position'},
                                       {'label': 'Streams', 'value': 'Streams'},
                                       {'label': 'Revenue', 'value': 'Revenue'}],
                                   value='Position',
                                   labelStyle={'display': 'inline-block'}),
                    style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'right'})]),
            html.Div(className='graph-container',
                     children=[dcc.Graph(id='tracks_on_chart_plot')]),
            html.Br(),
            html.H2(children='Legacy & Artist Metrics'),
            html.Div(className='group-select-buttons2', children=[
                html.Div(
                    dcc.RadioItems(className='graph-radio-buttons2',
                                   id='artist_on_chart_avg_or_max',
                                   options=[
                                       {'label': 'Average', 'value': 'Average'},
                                       {'label': 'Max', 'value': 'Max'}],
                                   value='Average',
                                   labelStyle={'display': 'inline-block'}),
                    style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'left'}),
                html.Div(
                    dcc.RadioItems(className='graph-radio-buttons3',
                                   id='artist_on_chart_data_source',
                                   options=[
                                       {'label': 'Position', 'value': 'Position'},
                                       {'label': 'Streams', 'value': 'Streams'},
                                       {'label': 'Revenue', 'value': 'Revenue'}],
                                   value='Position',
                                   labelStyle={'display': 'inline-block'}),
                    style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'right'})]),
            html.Div(className='graph-container',
                     children=[dcc.Graph(id='artist_on_chart_plot')]),
            html.Br(),
            html.H2(children='Legacy & Collaboration Metrics'),
            html.Div(className='group-select-buttons2', children=[
                html.Div(
                    dcc.RadioItems(className='graph-radio-buttons2',
                                   id='collab_artist_on_chart_avg_or_max',
                                   options=[
                                       {'label': 'Average', 'value': 'Average'},
                                       {'label': 'Max', 'value': 'Max'}],
                                   value='Average',
                                   labelStyle={'display': 'inline-block'}),
                    style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'left'}),
                html.Div(
                    dcc.RadioItems(className='graph-radio-buttons3',
                                   id='collab_artist_on_chart_data_source',
                                   options=[
                                       {'label': 'Position', 'value': 'Position'},
                                       {'label': 'Streams', 'value': 'Streams'},
                                       {'label': 'Revenue', 'value': 'Revenue'}],
                                   value='Position',
                                   labelStyle={'display': 'inline-block'}),
                    style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'right'})]),
            html.Div(className='graph-container',
                     children=[dcc.Graph(id='collab_artist_on_chart_plot')]),
            html.Div(style={'background-color': '#000000', 'padding-bottom': '70px'})
        ])
    elif tab == 'Additional Info':
        return html.Div([
            html.H1(children='Some Additional Factors'),
            html.Div(className='text-header',
                     children=[
                         html.Div('''This page outlines how key metrics of success varies with the timing of 
                         the release of a track. Tracks released closer to Friday and Saturday tend to perform 
                         better on average than tracks released on other days of the week.''',
                                  style={'text-align': 'left', 'padding-left': '30px', 'padding-right': '30px'})]),

            html.H2(children='Key Times For Album Releases'),
            html.Div(className='group-text-containers', children=[
                html.Div(className='graph-container2', children=[
                    html.H3(children='Month'),
                    html.H4(children='Albums released in April tend to have the highest streams and revenue.')],
                         style={'width': '48%', 'display': 'inline-block', 'align-content': 'left',
                                'padding-left': '9px'}),

                html.Div(className='graph-container2', children=[
                    html.H3(children='Day Of The Week'),
                    html.H4(children='Albums released on Saturday tend to have the highest streams and revenue.')],
                         style={'width': '48%', 'display': 'inline-block', 'align-content': 'right',
                                'padding-left': '9px'})]),
            html.Br(),
            html.H2(children='Album Release Metrics'),
            html.Div(className='group-select-buttons', children=[
                html.Div(
                    dcc.RadioItems(className='graph-radio-buttons2',
                                   id='month_day_value',
                                   options=[
                                       {'label': 'Months', 'value': 'Months'},
                                       {'label': 'Days', 'value': 'Days'}],
                                   value='Months',
                                   labelStyle={'display': 'inline-block'}),
                    style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'left'}),
                html.Div(
                    dcc.RadioItems(className='graph-radio-buttons3',
                                   id='month_day_data_source',
                                   options=[
                                       {'label': 'Count', 'value': 'Count'},
                                       {'label': 'Position', 'value': 'Position'},
                                       {'label': 'Streams', 'value': 'Streams'},
                                       {'label': 'Revenue', 'value': 'Revenue'}],
                                   value='Count',
                                   labelStyle={'display': 'inline-block'}),
                    style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'right'})]),

            html.Div(className='graph-container',
                     children=[dcc.Graph(id='month_day_plot')]),
            html.H2(children='Genre Network'),
            html.Div(className='group-select-buttons', children=[
                html.Div(
                    dcc.Dropdown(className='selection-box',
                                 id='genre_network_selections',
                                 options=[{'label': i, 'value': i} for i in
                                          network_data['Genre'].unique()],
                                 multi=True,
                                 value=[]),
                    style={'width': '50%', 'display': 'inline-block', 'vertical-align': 'left'}),
                html.Div(
                    dcc.Dropdown(className='selection-box',
                                 id='year_value',
                                 options=[{'label': i, 'value': i} for i in
                                          network_data['Year'].unique()],
                                 multi=True,
                                 value=[]),
                    style={'width': '30%', 'display': 'inline-block', 'vertical-align': 'left'}),
                html.Div(
                    dcc.RadioItems(className='graph-radio-buttons2',
                                   id='network_data_source',
                                   options=[
                                       {'label': 'Count', 'value': 'Count'},
                                       {'label': 'Streams', 'value': 'Streams'}],
                                   value='Count',
                                   labelStyle={'display': 'inline-block'}),
                    style={'width': '20%', 'display': 'inline-block', 'vertical-align': 'right'})]),
            html.Div(className='graph-container',
                     children=[dcc.Graph(id='network_plot')]),
            html.Br(),
            html.Div(style={'background-color': '#000000', 'padding-bottom': '70px'})
        ])


########## GRAPH FUNCTIONS #############
#### Collaborator Box Plots ####
@app.callback(Output('collab_bar_chart', 'figure'),
              [Input('collab_data_source', 'value')])
def collab_bar_charts(data_source):
    if data_source == 'Count':
        count_collaborators = (
            collab_data.drop_duplicates("Track URI2")
                .groupby(["No. of Artists"])
                .count()
                .reset_index()
                .rename(columns={"Unnamed: 0": "Count of Tracks"})
                .sort_values(by="No. of Artists", ascending=True)
        )
        count_collaborators = px.bar(count_collaborators, x="No. of Artists", y="Count of Tracks",
                                     color_discrete_sequence=colors['collabbarcolors'],
                                     title='Count of Collaborations in Dataset')

        count_collaborators.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1']
        )

        return count_collaborators

    elif data_source == 'Position':
        position_collaborators = (
            collab_data.drop_duplicates("Track Name")
                .groupby(["No. of Artists"])["Position"]
                .mean()
                .reset_index(name="Average Position")
                .sort_values(by="No. of Artists", ascending=True)
        )
        position_collaborators = px.bar(position_collaborators, x="No. of Artists", y="Average Position",
                                        color_discrete_sequence=colors['collabbarcolors'],
                                        title='Average Position Based On Number of Collaborators'
                                        )

        position_collaborators.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1']
        )
        return position_collaborators

    elif data_source == 'Streams':
        streams_collaborators = (
            collab_data.drop_duplicates("Track Name")
                .groupby(["No. of Artists"])["Streams"]
                .mean()
                .reset_index(name="Streams")
                .sort_values(by="No. of Artists", ascending=True)
        )
        streams_collaborators = px.bar(streams_collaborators, x="No. of Artists", y="Streams",
                                       color_discrete_sequence=colors['collabbarcolors'],
                                       title='Average Streams Based On Number of Collaborators')

        streams_collaborators.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1']
        )
        return streams_collaborators

    elif data_source == 'Revenue':
        revenue_collaborators = (
            collab_data.drop_duplicates("Track Name")
                .groupby(["No. of Artists"])["Revenue"]
                .mean()
                .reset_index(name="Revenue")
                .sort_values(by="No. of Artists", ascending=True)
        )

        revenue_collaborators = px.bar(revenue_collaborators, x="No. of Artists", y="Revenue",
                                       color_discrete_sequence=colors['collabbarcolors'],
                                       title='Average Revenue Based on Number of Collaborators')

        revenue_collaborators.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1']
        )
        return revenue_collaborators


#### Genre Metric Plots ####
@app.callback(Output('genre_bar_chart', 'figure'),
              Input('genre_data_source', 'value'),
              Input('genre_selections', 'value'))
def genre_bar_charts(data_source, genres):
    if genres == 'None' or genres == []:
        select_collab_genres = collab_genres.copy()
    else:
        select_collab_genres = collab_genres[collab_genres['Artist Genre'].isin(genres)]

    if data_source == 'Count':
        count_genres = (
            select_collab_genres
                .groupby(["Artist Genre"])
                .count()
                .reset_index()
                .rename(columns={"Unnamed: 0": "Count of Artists"})
                .sort_values(by="Count of Artists", ascending=False)
        )

        if genres == 'None' or genres == []:
            count_genres = count_genres.head(5)
        else:
            pass

        count_genres = px.bar(count_genres, x="Count of Artists", y="Artist Genre", orientation='h',
                              color_discrete_sequence=colors['collabbarcolors'],
                              title='Count of Artists For Each Genre')

        count_genres.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1']
        )

        return count_genres

    elif data_source == 'Position':
        position_genres = (
            select_collab_genres
                .groupby(["Artist Genre"])["Position"]
                .mean()
                .reset_index(name="Average Position")
                .sort_values(by="Average Position", ascending=True)
        )

        if genres == 'None' or genres == []:
            position_genres = position_genres.head(5).sort_values(by="Average Position", ascending=False)
        else:
            pass

        position_genres = px.bar(position_genres, x="Average Position", y="Artist Genre", orientation='h',
                                 color_discrete_sequence=colors['collabbarcolors'],
                                 title='Average Position For Each Genre')

        position_genres.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1']
        )
        return position_genres

    elif data_source == 'Streams':
        streams_genres = (
            select_collab_genres
                .groupby(["Artist Genre"])["Streams"]
                .mean()
                .reset_index(name="Average Streams")
                .sort_values(by="Average Streams", ascending=False)
        )

        if genres == 'None' or genres == []:
            streams_genres = streams_genres.head(5)
        else:
            pass

        streams_genres = px.bar(streams_genres, x="Average Streams", y="Artist Genre", orientation='h',
                                color_discrete_sequence=colors['collabbarcolors'],
                                title='Average Streams For Each Genre')

        streams_genres.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1']
        )
        return streams_genres

    elif data_source == 'Revenue':
        revenue_genres = (
            select_collab_genres
                .groupby(["Artist Genre"])["Revenue"]
                .mean()
                .reset_index(name="Average Revenue")
                .sort_values(by="Average Revenue", ascending=False)
        )

        if genres == 'None' or genres == []:
            revenue_genres = revenue_genres.head(5)
        else:
            pass

        revenue_genres = px.bar(revenue_genres, x="Average Revenue", y="Artist Genre", orientation='h',
                                color_discrete_sequence=colors['collabbarcolors'],
                                title='Average Revenue For Each Genre')

        revenue_genres.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1']
        )
        return revenue_genres


#### Position Metrics Plots - All Streams/ Average ####
@app.callback(Output('position_streams_bar_chart', 'figure'),
              [Input('position_streams_data_source', 'value')])
def position_streams_charts(data_source):
    if data_source == 'All Streams':
        streams_position = px.scatter(collab_data, x="Position", y="Streams",
                                      color_discrete_sequence=[colors['main_color']],
                                      title='All Streams Compared to Position')

        streams_position.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1']
        )

        return streams_position

    elif data_source == 'Average Streams':
        average_streams_position = (
            collab_data.groupby(["Position"])["Streams"]
                .mean()
                .reset_index(name='Average Streams')
        )

        average_streams_position = px.scatter(average_streams_position, x="Position", y="Average Streams",
                                              color_discrete_sequence=[colors['main_color']],
                                              title='Average Streams Compared to Position')

        average_streams_position.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1']
        )

        return average_streams_position


#### Position Metrics Plots - All Revenues/ Average ####
@app.callback(Output('position_revenue_bar_chart', 'figure'),
              [Input('position_revenue_data_source', 'value')])
def position_revenue_bar_charts(data_source):
    if data_source == 'All Revenues':
        revenue_position = px.scatter(collab_data, x="Position", y="Revenue",
                                      color_discrete_sequence=[colors['main_color']],
                                      title='All Revenues Compared to Position')

        revenue_position.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1']
        )

        return revenue_position

    elif data_source == 'Average Revenues':
        average_revenue_position = (
            collab_data.groupby(["Position"])["Revenue"]
                .mean()
                .reset_index(name='Average Revenue')
        )

        average_revenue_position = px.scatter(average_revenue_position, x="Position", y="Average Revenue",
                                              color_discrete_sequence=[colors['main_color']],
                                              title='Average Revenue Compared to Position')

        average_revenue_position.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1']
        )

        return average_revenue_position


#### Track Metric Plots ####
@app.callback(Output('track_bar_chart', 'figure'),
              Input('track_data_source', 'value'),
              Input('track_selections', 'value'))
def track_bar_charts(data_source, track_names):
    if track_names == 'None' or track_names == []:
        select_collab_tracks = collab_data.copy()
    else:
        select_collab_tracks = collab_data[collab_data['Track Name'].isin(track_names)]

    if data_source == 'Count':
        count_tracks = (
            select_collab_tracks
                .groupby(["Track Name"])
                .count()
                .reset_index()
                .rename(columns={"Unnamed: 0": "Count"})
                .sort_values(by="Count", ascending=False)
        )

        if track_names == 'None' or track_names == []:
            count_tracks = count_tracks.head(5)
        else:
            pass

        count_tracks = px.bar(count_tracks, x="Count", y="Track Name", orientation='h',
                              color_discrete_sequence=colors['genrebarcolors'],
                              title='Count of Tracks In The Dataset')

        count_tracks.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1']
        )

        return count_tracks

    elif data_source == 'Position':
        position_tracks = (
            select_collab_tracks
                .groupby(["Track Name"])["Position"]
                .mean()
                .reset_index(name="Average Position")
                .sort_values(by="Average Position", ascending=True)
        )

        if track_names == 'None' or track_names == []:
            position_tracks = position_tracks.head(5).sort_values(by="Average Position", ascending=False)
        else:
            pass

        position_tracks = px.bar(position_tracks, x="Average Position", y="Track Name", orientation='h',
                                 color_discrete_sequence=colors['genrebarcolors'],
                                 title='Average Position For Each Track')

        position_tracks.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1']
        )
        return position_tracks

    elif data_source == 'Streams':
        streams_tracks = (
            select_collab_tracks
                .groupby(["Track Name"])["Streams"]
                .mean()
                .reset_index(name="Average Streams")
                .sort_values(by="Average Streams", ascending=True)
        )

        if track_names == 'None' or track_names == []:
            streams_tracks = streams_tracks.head(5).sort_values(by="Average Streams", ascending=False)
        else:
            pass

        streams_tracks = px.bar(streams_tracks, x="Average Streams", y="Track Name", orientation='h',
                                color_discrete_sequence=colors['genrebarcolors'],
                                title='Average Streams For Each Track')

        streams_tracks.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1']
        )
        return streams_tracks

    elif data_source == 'Revenue':
        revenue_tracks = (
            select_collab_tracks
                .groupby(["Track Name"])["Revenue"]
                .mean()
                .reset_index(name="Average Revenue")
                .sort_values(by="Average Revenue", ascending=True)
        )

        if track_names == 'None' or track_names == []:
            revenue_tracks = revenue_tracks.head(5).sort_values(by="Average Revenue", ascending=False)
        else:
            pass

        revenue_tracks = px.bar(revenue_tracks, x="Average Revenue", y="Track Name", orientation='h',
                                color_discrete_sequence=colors['genrebarcolors'],
                                title='Average Revenue For Each Artist')

        revenue_tracks.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1']
        )
        return revenue_tracks


#### Track Revenue Over Time ####
# Timeline selector is not necessary... should be implicitly in figure...
@app.callback(Output('track_revenue_over_time_plot', 'figure'),
              Input('track_revenue_selection', 'value'))
def track_revenue_over_time(tracks):
    if tracks == 'None' or tracks == []:
        revenue_top_tracks = (
            collab_data.groupby(['Track Name'])['Revenue']
                .mean()
                .reset_index(name='Average Revenue')
                .sort_values(by='Average Revenue', ascending=False)
                .head(15)
        )

    else:
        revenue_top_tracks = collab_data[collab_data['Track Name'].isin(tracks)]

    track_revenue_overtime = (
        collab_data[collab_data['Track Name'].isin(list(revenue_top_tracks['Track Name']))]
            .groupby(['Track Name', 'Date'])['Revenue']
            .mean()
            .reset_index(name='Average Revenue')
    )

    track_revenue_plot = px.line(track_revenue_overtime, x="Date", y="Average Revenue", color='Track Name',
                                 color_discrete_sequence=colors['collabbarcolors'],
                                 title='Top Tracks Over Time Based on Revenue')

    track_revenue_plot.update_layout(
        plot_bgcolor=colors['plot_bg_color'],
        paper_bgcolor=colors['plot_bg_color'],
        font_color=colors['txt_color1'],
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                         label="1 Month",
                         step="month",
                         stepmode="backward"),
                    dict(count=6,
                         label="6 Months",
                         step="month",
                         stepmode="backward"),
                    dict(count=1,
                         label="1 Year",
                         step="year",
                         stepmode="backward"),
                    dict(label="All",
                         step="all")
                ])
            ),
            rangeslider=dict(
                visible=True
            ),
            type="date",
        )
    )

    return track_revenue_plot


#### Top Tracks Over Time ####
@app.callback(Output('top_tracks_over_time_plot', 'figure'),
              Input('top_tracks_data_source', 'value'),
              Input('top_tracks_track_selection', 'value'))
def top_tracks_over_time(data_source, tracks):
    if data_source == 'Position':
        if tracks == 'None' or tracks == []:
            top_tracks = (
                collab_data.groupby(['Track Name'])['Position']
                    .mean()
                    .reset_index(name='Average Position')
                    .sort_values(by='Average Position', ascending=True)
                    .head(15)
            )

        else:
            top_tracks = collab_data[collab_data['Track Name'].isin(tracks)]

        track_position_overtime = (
            collab_data[collab_data['Track Name'].isin(list(top_tracks['Track Name']))]
                .groupby(['Track Name', 'Date'])['Position']
                .mean()
                .reset_index(name='Average Position')
        )

        track_position_plot = px.line(track_position_overtime, x="Date", y="Average Position",
                                      title='Top Tracks Over Time Based on Position',
                                      color_discrete_sequence=colors['collabbarcolors'], color='Track Name')

        track_position_plot.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1'],
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1,
                             label="1 Month",
                             step="month",
                             stepmode="backward"),
                        dict(count=6,
                             label="6 Months",
                             step="month",
                             stepmode="backward"),
                        dict(count=1,
                             label="1 Year",
                             step="year",
                             stepmode="backward"),
                        dict(label="All",
                             step="all")
                    ])
                ),
                rangeslider=dict(
                    visible=True
                ),
                type="date",
            )
        )

        return track_position_plot

    if data_source == 'Streams':
        if tracks == 'None' or tracks == []:
            top_tracks = (
                collab_data.groupby(['Track Name'])['Streams']
                    .mean()
                    .reset_index(name='Average Streams')
                    .sort_values(by='Average Streams', ascending=True)
                    .head(15)
            )

        else:
            top_tracks = collab_data[collab_data['Track Name'].isin(tracks)]

        track_streams_overtime = (
            collab_data[collab_data['Track Name'].isin(list(top_tracks['Track Name']))]
                .groupby(['Track Name', 'Date'])['Streams']
                .mean()
                .reset_index(name='Average Streams')
        )

        track_streams_plot = px.line(track_streams_overtime, x="Date", y="Average Streams",
                                     title='Top Tracks Over Time Based on Streams',
                                     color_discrete_sequence=colors['collabbarcolors'], color='Track Name')

        track_streams_plot.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1'],
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1,
                             label="1 Month",
                             step="month",
                             stepmode="backward"),
                        dict(count=6,
                             label="6 Months",
                             step="month",
                             stepmode="backward"),
                        dict(count=1,
                             label="1 Year",
                             step="year",
                             stepmode="backward"),
                        dict(label="All",
                             step="all")
                    ])
                ),
                rangeslider=dict(
                    visible=True
                ),
                type="date",
            )
        )

        return track_streams_plot


#### Artist Metric Plots ####
@app.callback(Output('artist_bar_chart', 'figure'),
              Input('artist_data_source', 'value'),
              Input('artist_selections', 'value'))
def artist_bar_charts(data_source, artist_names):
    if artist_names == 'None' or artist_names == []:
        select_collab_artists = collab_data.copy()
    else:
        select_collab_artists = collab_data[collab_data['Artist Name'].isin(artist_names)]

    if data_source == 'Count':
        count_artists = (
            select_collab_artists
                .groupby(["Artist Name"])
                .count()
                .reset_index()
                .rename(columns={"Unnamed: 0": "Count"})
                .sort_values(by="Count", ascending=False)
        )

        if artist_names == 'None' or artist_names == []:
            count_artists = count_artists.head(5)
        else:
            pass

        count_artists = px.bar(count_artists, x="Count", y="Artist Name", orientation='h',
                               color_discrete_sequence=colors['genrebarcolors'],
                               title='Count of Artist Occurences In The Dataset')

        count_artists.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1']
        )

        return count_artists

    elif data_source == 'Position':
        position_artists = (
            select_collab_artists
                .groupby(["Artist Name"])["Position"]
                .mean()
                .reset_index(name="Average Position")
                .sort_values(by="Average Position", ascending=True)
        )

        if artist_names == 'None' or artist_names == []:
            position_artists = position_artists.head(5).sort_values(by="Average Position", ascending=False)
        else:
            pass

        position_artists = px.bar(position_artists, x="Average Position", y="Artist Name", orientation='h',
                                  color_discrete_sequence=colors['genrebarcolors'],
                                  title='Average Position For Each Artist')

        position_artists.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1']
        )
        return position_artists

    elif data_source == 'Streams':
        streams_artists = (
            select_collab_artists
                .groupby(["Artist Name"])["Streams"]
                .mean()
                .reset_index(name="Average Streams")
                .sort_values(by="Average Streams", ascending=True)
        )

        if artist_names == 'None' or artist_names == []:
            streams_artists = streams_artists.head(5).sort_values(by="Average Streams", ascending=False)
        else:
            pass

        streams_artists = px.bar(streams_artists, x="Average Streams", y="Artist Name", orientation='h',
                                 color_discrete_sequence=colors['genrebarcolors'],
                                 title='Average Streams For Each Artist')

        streams_artists.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1']
        )
        return streams_artists

    elif data_source == 'Revenue':
        revenue_artists = (
            select_collab_artists
                .groupby(["Artist Name"])["Revenue"]
                .mean()
                .reset_index(name="Average Revenue")
                .sort_values(by="Average Revenue", ascending=True)
        )

        if artist_names == 'None' or artist_names == []:
            revenue_artists = revenue_artists.head(5).sort_values(by="Average Revenue", ascending=False)
        else:
            pass

        revenue_artists = px.bar(revenue_artists, x="Average Revenue", y="Artist Name", orientation='h',
                                 color_discrete_sequence=colors['genrebarcolors'],
                                 title='Average Revenue For Each Artist')

        revenue_artists.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1']
        )
        return revenue_artists


#### Artist Radar Graphs ####
@app.callback(Output('artist_radar_graph', 'figure'),
              Input('artist_selections2', 'value'))
def audio_radial_graph(artist_names):
    if artist_names == 'None' or artist_names == []:
        select_audio_features = collab_features_data[collab_features_data['Artist Name'].isin(
            ['Drake', 'Post Malone', 'Travis Scott', 'Khalid', 'Juice WRLD'])]
    else:
        select_audio_features = collab_features_data[collab_features_data['Artist Name'].isin(artist_names)]

    radar_graph = go.Figure()

    for i in select_audio_features['Artist Name'].unique():
        radar_graph.add_trace(go.Scatterpolar(
            r=select_audio_features[select_audio_features['Artist Name'] == i]['value'],
            theta=select_audio_features[select_audio_features['Artist Name'] == i]['variable'],
            fill='toself',
            name=i))

    radar_graph.update_layout(
        polar=dict(
            bgcolor=colors['plot_bg_color'],
            radialaxis=dict(
                visible=True,
                range=[0, 1])),
        title='Audio Features For Selected Artists',
        paper_bgcolor=colors['plot_bg_color'],
        font_color=colors['txt_color1'])

    return radar_graph


#### Count Metrics By Length Of Time ####
@app.callback(Output('count_time_plot', 'figure'),
              Input('track_artist', 'value'))
def count_days(track_artist):
    if track_artist == 'Artists':
        count_artistdays = (
            collab_data
                .groupby(['Artist_days_onchart'])
                .count()
                .reset_index()
                .rename(columns={"Artist Name": "Count"})
        )

        count_artistdays = px.scatter(count_artistdays, x="Artist_days_onchart", y="Count",
                                      color_discrete_sequence=[colors['main_color']],
                                      title='Count of Artists in the Dataset By Length of Time on The Chart'
                                      )

        count_artistdays.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1'],
            xaxis_title="Length of Time on Chart (days)"
        )

        return count_artistdays

    elif track_artist == 'Tracks':
        count_trackdays = (
            collab_data
                .groupby(['Song_days_onchart'])
                .count()
                .reset_index()
                .rename(columns={"Track URI2": "Count"})
        )

        count_trackdays = px.scatter(count_trackdays, x="Song_days_onchart", y="Count",
                                     color_discrete_sequence=[colors['main_color']],
                                     title='Count of Tracks By Length of Time on The Chart'
                                     )

        count_trackdays.update_layout(
            plot_bgcolor=colors['plot_bg_color'],
            paper_bgcolor=colors['plot_bg_color'],
            font_color=colors['txt_color1'],
            xaxis_title="Length of Time on Chart (days)"
        )

        return count_trackdays


#### Track Metrics By Length Of Time ####
@app.callback(Output('tracks_on_chart_plot', 'figure'),
              Input('tracks_on_chart_avg_or_max', 'value'),
              Input('tracks_on_chart_data_source', 'value'))
def track_on_chart(avg_or_max, data_source):
    if avg_or_max == 'Average':
        if data_source == 'Position':
            average_position_trackdays = (
                collab_data.groupby(["Song_days_onchart"])["Position"]
                    .mean()
                    .reset_index()
            )

            average_position_trackdays = px.scatter(average_position_trackdays, x="Song_days_onchart", y="Position",
                                                    color_discrete_sequence=[colors['main_color']],
                                                    title='Average Chart Position Compared to Length of Time on The Chart'
                                                    )

            average_position_trackdays.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Length of Time on Chart (days)"
            )

            return average_position_trackdays

        elif data_source == 'Streams':
            average_streams_trackdays = (
                collab_data.groupby(["Song_days_onchart"])["Streams"]
                    .mean()
                    .reset_index()
            )

            average_streams_trackdays = px.scatter(average_streams_trackdays, x="Song_days_onchart", y="Streams",
                                                   color_discrete_sequence=[colors['main_color']],
                                                   title='Average Streams Compared to Length of Time on The Chart'
                                                   )

            average_streams_trackdays.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Length of Time on Chart (days)"
            )

            return average_streams_trackdays

        elif data_source == 'Revenue':
            average_revenue_trackdays = (
                collab_data.groupby(["Song_days_onchart"])["Revenue"]
                    .mean()
                    .reset_index()
            )

            average_revenue_trackdays = px.scatter(average_revenue_trackdays, x="Song_days_onchart", y="Revenue",
                                                   color_discrete_sequence=[colors['main_color']],
                                                   title='Average Revenue Compared to Length of Time on The Chart'
                                                   )

            average_revenue_trackdays.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Length of Time on Chart (days)"
            )

            return average_revenue_trackdays

    elif avg_or_max == 'Max':
        if data_source == 'Position':
            max_position_trackdays = (
                collab_data.groupby(["Song_days_onchart"])["Position"]
                    .min()
                    .reset_index()
            )

            max_position_trackdays = px.scatter(max_position_trackdays, x="Song_days_onchart", y="Position",
                                                color_discrete_sequence=[colors['main_color']],
                                                title='Highest Chart Position Compared to Length of Time on The Chart'
                                                )

            max_position_trackdays.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Length of Time on Chart (days)"
            )

            return max_position_trackdays

        elif data_source == 'Streams':
            max_streams_trackdays = (
                collab_data.groupby(["Song_days_onchart"])["Streams"]
                    .max()
                    .reset_index()
            )

            max_streams_trackdays = px.scatter(max_streams_trackdays, x="Song_days_onchart", y="Streams",
                                               color_discrete_sequence=[colors['main_color']],
                                               title='Max Number of Streams Compared to Length of Time on The Chart'
                                               )

            max_streams_trackdays.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Length of Time on Chart (days)"
            )

            return max_streams_trackdays

        elif data_source == 'Revenue':
            max_revenue_trackdays = (
                collab_data.groupby(["Song_days_onchart"])["Revenue"]
                    .max()
                    .reset_index()
            )

            max_revenue_trackdays = px.scatter(max_revenue_trackdays, x="Song_days_onchart", y="Revenue",
                                               color_discrete_sequence=[colors['main_color']],
                                               title='Max Revenue Compared to Length of Time on The Chart'
                                               )

            max_revenue_trackdays.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Length of Time on Chart (days)"
            )

            return max_revenue_trackdays


#### Artist Metrics By Length Of Time ####
@app.callback(Output('artist_on_chart_plot', 'figure'),
              Input('artist_on_chart_avg_or_max', 'value'),
              Input('artist_on_chart_data_source', 'value'))
def artist_on_chart(avg_or_max, data_source):
    if avg_or_max == 'Average':
        if data_source == 'Position':
            average_position_artistdays = (
                collab_data.groupby(["Artist_days_onchart"])["Position"]
                    .mean()
                    .reset_index()
            )

            average_position_artistdays = px.scatter(average_position_artistdays, x="Artist_days_onchart", y="Position",
                                                     color_discrete_sequence=[colors['main_color']],
                                                     title='Average Artist Chart Position Compared to Length of Time on The Chart'
                                                     )

            average_position_artistdays.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Length of Time on Chart (days)"
            )

            return average_position_artistdays

        elif data_source == 'Streams':
            average_streams_artistdays = (
                collab_data.groupby(["Artist_days_onchart"])["Streams"]
                    .mean()
                    .reset_index()
            )

            average_streams_artistdays = px.scatter(average_streams_artistdays, x="Artist_days_onchart", y="Streams",
                                                    color_discrete_sequence=[colors['main_color']],
                                                    title='Average Artist Streams Compared to Length of Time on The Chart'
                                                    )

            average_streams_artistdays.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Length of Time on Chart (days)"
            )

            return average_streams_artistdays

        elif data_source == 'Revenue':
            average_revenue_artistdays = (
                collab_data.groupby(["Artist_days_onchart"])["Revenue"]
                    .mean()
                    .reset_index()
            )

            average_revenue_artistdays = px.scatter(average_revenue_artistdays, x="Artist_days_onchart", y="Revenue",
                                                    color_discrete_sequence=[colors['main_color']],
                                                    title='Average Artist Revenue Compared to Length of Time on The Chart'
                                                    )

            average_revenue_artistdays.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Length of Time on Chart (days)"
            )

            return average_revenue_artistdays

    elif avg_or_max == 'Max':
        if data_source == 'Position':
            max_position_artistdays = (
                collab_data.groupby(["Artist_days_onchart"])["Position"]
                    .min()
                    .reset_index()
            )

            max_position_artistdays = px.scatter(max_position_artistdays, x="Artist_days_onchart", y="Position",
                                                 color_discrete_sequence=[colors['main_color']],
                                                 title='Highest Artist Chart Position Compared to Length of Time on The Chart'
                                                 )

            max_position_artistdays.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Length of Time on Chart (days)"
            )

            return max_position_artistdays

        elif data_source == 'Streams':
            max_streams_artistdays = (
                collab_data.groupby(["Artist_days_onchart"])["Streams"]
                    .max()
                    .reset_index()
            )

            max_streams_artistdays = px.scatter(max_streams_artistdays, x="Artist_days_onchart", y="Streams",
                                                color_discrete_sequence=[colors['main_color']],
                                                title='Max Number of Streams for Artists Compared to Length of Time on The Chart'
                                                )

            max_streams_artistdays.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Length of Time on Chart (days)"
            )

            return max_streams_artistdays

        elif data_source == 'Revenue':
            max_revenue_artistdays = (
                collab_data.groupby(["Artist_days_onchart"])["Revenue"]
                    .max()
                    .reset_index()
            )

            max_revenue_artistdays = px.scatter(max_revenue_artistdays, x="Artist_days_onchart", y="Revenue",
                                                color_discrete_sequence=[colors['main_color']],
                                                title='Max Revenue for Artists Compared to Length of Time on The Chart'
                                                )

            max_revenue_artistdays.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Length of Time on Chart (days)"
            )

            return max_revenue_artistdays


#### Collab Artist Metrics By Length Of Time ####
@app.callback(Output('collab_artist_on_chart_plot', 'figure'),
              Input('collab_artist_on_chart_avg_or_max', 'value'),
              Input('collab_artist_on_chart_data_source', 'value'))
def collab_artist_on_chart(avg_or_max, data_source):
    if avg_or_max == 'Average':
        if data_source == 'Position':
            average_position_collab_artistdays = (
                collab_data.drop_duplicates('Track URI2')
                    .groupby(["Collab_avg_days_onchart"])["Position"]
                    .mean()
                    .reset_index()
            )

            average_position_collab_artistdays = px.scatter(average_position_collab_artistdays,
                                                            x="Collab_avg_days_onchart", y="Position",
                                                            color_discrete_sequence=[colors['main_color']],
                                                            title='Artist Collab Average Position Compared to Length of Time on The Chart'
                                                            )

            average_position_collab_artistdays.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Length of Time on Chart (days)"
            )

            return average_position_collab_artistdays

        elif data_source == 'Streams':
            average_streams_collab_artistdays = (
                collab_data.drop_duplicates('Track URI2')
                    .groupby(["Collab_avg_days_onchart"])["Streams"]
                    .mean()
                    .reset_index()
            )

            average_streams_collab_artistdays = px.scatter(average_streams_collab_artistdays,
                                                           x="Collab_avg_days_onchart", y="Streams",
                                                           color_discrete_sequence=[colors['main_color']],
                                                           title='Artist Collab Average Streams Compared to Length of Time on The Chart'
                                                           )

            average_streams_collab_artistdays.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Length of Time on Chart (days)"
            )

            return average_streams_collab_artistdays

        elif data_source == 'Revenue':
            average_revenue_collab_artistdays = (
                collab_data.drop_duplicates('Track URI2')
                    .groupby(["Collab_avg_days_onchart"])["Revenue"]
                    .mean()
                    .reset_index()
            )

            average_revenue_collab_artistdays = px.scatter(average_revenue_collab_artistdays,
                                                           x="Collab_avg_days_onchart", y="Revenue",
                                                           color_discrete_sequence=[colors['main_color']],
                                                           title='Artist Collab Average Revenue Compared to Length of Time on The Chart'
                                                           )

            average_revenue_collab_artistdays.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Length of Time on Chart (days)"
            )

            return average_revenue_collab_artistdays

    elif avg_or_max == 'Max':
        if data_source == 'Position':
            max_position_collab_artistdays = (
                collab_data.drop_duplicates('Track URI2')
                    .groupby(["Collab_avg_days_onchart"])["Position"]
                    .min()
                    .reset_index()
            )

            max_position_collab_artistdays = px.scatter(max_position_collab_artistdays, x="Collab_avg_days_onchart",
                                                        y="Position",
                                                        color_discrete_sequence=[colors['main_color']],
                                                        title='Artist Collab Highest Chart Position Compared to Length of Time on The Chart'
                                                        )

            max_position_collab_artistdays.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Length of Time on Chart (days)"
            )

            return max_position_collab_artistdays

        elif data_source == 'Streams':
            max_streams_collab_artistdays = (
                collab_data.drop_duplicates('Track URI2')
                    .groupby(["Collab_avg_days_onchart"])["Streams"]
                    .max()
                    .reset_index()
            )

            max_streams_collab_artistdays = px.scatter(max_streams_collab_artistdays, x="Collab_avg_days_onchart",
                                                       y="Streams",
                                                       color_discrete_sequence=[colors['main_color']],
                                                       title='Artist Collab Max Streams Compared to Length of Time on The Chart'
                                                       )

            max_streams_collab_artistdays.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Length of Time on Chart (days)"
            )

            return max_streams_collab_artistdays

        elif data_source == 'Revenue':
            max_revenue_collab_artistdays = (
                collab_data.drop_duplicates('Track URI2')
                    .groupby(["Collab_avg_days_onchart"])["Revenue"]
                    .max()
                    .reset_index()
            )

            max_revenue_collab_artistdays = px.scatter(max_revenue_collab_artistdays, x="Collab_avg_days_onchart",
                                                       y="Revenue",
                                                       color_discrete_sequence=[colors['main_color']],
                                                       title='Artist Collab Max Revenue Compared to Length of Time on The Chart'
                                                       )

            max_revenue_collab_artistdays.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Length of Time on Chart (days)"
            )

            return max_revenue_collab_artistdays


#### Month/Day of Week Bar Charts ####
@app.callback(Output('month_day_plot', 'figure'),
              Input('month_day_value', 'value'),
              Input('month_day_data_source', 'value'))
def month_week_bar_charts(month_day, data_source):
    if month_day == 'Months':
        if data_source == 'Count':
            count_month = (
                collab_data.drop_duplicates('Track Name')
                    .groupby(['Album_release_month'])
                    .count()
                    .reset_index()
                    .rename(columns={'Track URI2': 'Count'})
                    .sort_values(by='Album_release_month', ascending=True)
            )

            count_month = px.bar(count_month, x="Album_release_month", y="Count",
                                 color_discrete_sequence=colors['collabbarcolors'],
                                 title="Release Month and Count in Dataset")

            count_month.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Month",
                xaxis=dict(dtick=1)
            )

            return count_month

        elif data_source == 'Position':
            position_month = (
                collab_data.drop_duplicates('Track Name')
                    .groupby(['Album_release_month'])['Position']
                    .mean()
                    .reset_index()
                    .sort_values(by='Album_release_month', ascending=True)
            )

            position_month = px.bar(position_month, x="Album_release_month", y="Position",
                                    color_discrete_sequence=colors['collabbarcolors'],
                                    title="Release Month and Average Chart Position")

            position_month.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Month",
                xaxis=dict(dtick=1)
            )

            return position_month

        elif data_source == 'Streams':
            streams_month = (
                collab_data.drop_duplicates('Track Name')
                    .groupby(['Album_release_month'])['Streams']
                    .mean()
                    .reset_index()
                    .sort_values(by='Album_release_month', ascending=True)
            )

            streams_month = px.bar(streams_month, x="Album_release_month", y="Streams",
                                   color_discrete_sequence=colors['collabbarcolors'],
                                   title="Release Month and Average Streams")

            streams_month.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Month",
                xaxis=dict(dtick=1)
            )

            return streams_month

        elif data_source == 'Revenue':
            revenue_month = (
                collab_data.drop_duplicates('Track Name')
                    .groupby(['Album_release_month'])['Revenue']
                    .mean()
                    .reset_index()
                    .sort_values(by='Album_release_month', ascending=True)
            )

            revenue_month = px.bar(revenue_month, x="Album_release_month", y="Revenue",
                                   color_discrete_sequence=colors['collabbarcolors'],
                                   title="Release Month and Average Revenue")

            revenue_month.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Month",
                xaxis=dict(dtick=1)
            )

            return revenue_month

    elif month_day == "Days":
        if data_source == 'Count':
            count_days = (
                collab_data.drop_duplicates('Track Name')
                    .groupby(['Album_release_dayweek'])
                    .count()
                    .reset_index()
                    .rename(columns={'Track URI2': 'Count'})
                    .sort_values(by='Album_release_dayweek', ascending=True)
            )

            count_days = px.bar(count_days, x='Album_release_dayweek', y='Count',
                                color_discrete_sequence=colors['collabbarcolors'],
                                title="Release Day and Count in Dataset")

            count_days.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Day Of The Week",
                xaxis=dict(dtick=1)
            )

            return count_days

        elif data_source == 'Position':
            position_days = (
                collab_data.drop_duplicates('Track Name')
                    .groupby(['Album_release_dayweek'])['Position']
                    .mean()
                    .reset_index()
                    .sort_values(by='Album_release_dayweek', ascending=True)
            )

            position_days = px.bar(position_days, x='Album_release_dayweek', y="Position",
                                   color_discrete_sequence=colors['collabbarcolors'],
                                   title="Release Day and Average Chart Position")

            position_days.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Day Of The Week",
                xaxis=dict(dtick=1)
            )

            return position_days

        elif data_source == 'Streams':
            streams_days = (
                collab_data.drop_duplicates('Track Name')
                    .groupby(['Album_release_dayweek'])['Streams']
                    .mean()
                    .reset_index()
                    .sort_values(by='Album_release_dayweek', ascending=True)
            )

            streams_days = px.bar(streams_days, x='Album_release_dayweek', y="Streams",
                                  color_discrete_sequence=colors['collabbarcolors'],
                                  title="Release Day and Average Streams")

            streams_days.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Day Of The Week",
                xaxis=dict(dtick=1)
            )

            return streams_days

        elif data_source == 'Revenue':
            revenue_days = (
                collab_data.drop_duplicates('Track Name')
                    .groupby(['Album_release_dayweek'])['Revenue']
                    .mean()
                    .reset_index()
                    .sort_values(by='Album_release_dayweek', ascending=True)
            )

            revenue_days = px.bar(revenue_days, x='Album_release_dayweek', y="Revenue",
                                  color_discrete_sequence=colors['collabbarcolors'],
                                  title="Release Day and Average Revenue")

            revenue_days.update_layout(
                plot_bgcolor=colors['plot_bg_color'],
                paper_bgcolor=colors['plot_bg_color'],
                font_color=colors['txt_color1'],
                xaxis_title="Day Of The Week",
                xaxis=dict(dtick=1)
            )

            return revenue_days




#### Genre Network Plot
@app.callback(Output('network_plot', 'figure'),
              Input('genre_network_selections', 'value'),
              Input('year_value', 'value'),
              Input('network_data_source', 'value'))

def generate_network_plotly(genres=[], year=[], metric=[]):
    # Reduce dataframe
    if year != []:
        reduced_data = network_data[network_data['Year'].isin(year)][['Track URI2', 'Artist Name', 'Genre']].drop_duplicates(
            ignore_index=True)
    else:
        reduced_data = network_data[['Track URI2', 'Artist Name', 'Genre']].drop_duplicates(ignore_index=True)

    # Create Graph
    digraph = nx.DiGraph()

    # Create Node List
    nodes_df = reduced_data.groupby(['Genre'])[['Artist Name']].count().reset_index(drop=False).rename(
        columns={'Artist Name': 'Count'})
    nodes_df['Size'] = nodes_df['Count'].apply(lambda x: 5 * x ** (1 / 3))
    nodes_df = nodes_df[nodes_df.Genre != 'unknown']
    nodes_df = nodes_df[nodes_df.Genre != 'other'].reset_index(drop=False)

    # Add Nodes
    for i in range(len(nodes_df)):
        digraph.add_node(nodes_df.Genre[i], title=nodes_df.Genre[i], count=nodes_df.Count[i], size=nodes_df.Size[i])

    # Create Edge List
    edges_df = create_edgelist(reduced_data)

    edges_df = edges_df[edges_df['Artist Genre'] != edges_df['Collaborator Genre']]

    for g in ['unknown', 'other']:
        edges_df = edges_df[edges_df['Artist Genre'] != g]
        edges_df = edges_df[edges_df['Collaborator Genre'] != g]

    if genres != []:
        a, b = edges_df[edges_df['Artist Genre'].isin(genres)], edges_df[edges_df['Collaborator Genre'].isin(genres)]
        edges_df = pd.concat([a, b])

    if metric == 'Count':
        edge_list_reduced = edges_df.groupby(['Artist Genre', 'Collaborator Genre'])[
            ['Artist Genre', 'Collaborator Genre']].count().rename(
            columns={'Artist Genre': 'Count', 'Collaborator Genre': 'Weight'}).reset_index(drop=False)
        edge_list_reduced['Weight'] = edge_list_reduced['Count'].apply(lambda x: x / (max(edge_list_reduced['Count'])))
        edge_list_reduced['Color'] = edge_list_reduced['Weight'].apply(lambda x: plt.cm.summer(x))
        title_label = 'Genre Network Based on Counts'

    elif metric == 'Streams':
        track_streams = network_data.groupby(['Track URI2'])[['Streams']].sum().reset_index(drop=False)
        edge_list_reduced = edges_df.set_index('Track URI2').join(track_streams.set_index('Track URI2'))
        edge_list_reduced = edge_list_reduced.groupby(['Artist Genre', 'Collaborator Genre'])[
            ['Streams']].sum().reset_index(drop=False)
        edge_list_reduced['Weight'] = edge_list_reduced['Streams'].apply(
            lambda x: x / edge_list_reduced['Streams'].max())
        edge_list_reduced['Color'] = edge_list_reduced['Weight'].apply(lambda x: plt.cm.summer(x))
        title_label = 'Genre Network Based on Cumulative Streams'

    # Add Edges
    for i in range(len(edge_list_reduced)):
        u = edge_list_reduced['Artist Genre'][i]
        v = edge_list_reduced['Collaborator Genre'][i]
        color = edge_list_reduced['Color'][i]
        m = edge_list_reduced[metric][i]
        digraph.add_edge(u, v, color=color, metric=m)

    # Plot Graph

    pos = nx.circular_layout(digraph)

    for node in digraph.nodes:
        digraph.nodes[node]['pos'] = list(pos[node])

    edge_x = []
    edge_y = []
    edge_weight = []
    for edge in digraph.edges():
        x0, y0 = digraph.nodes[edge[0]]['pos']
        x1, y1 = digraph.nodes[edge[1]]['pos']
        weight = digraph.edges[edge]['metric']
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)
        edge_weight.append(weight)

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(
            width=2,
        ),
        hoverinfo='none',
        mode='lines',
        opacity=0.5
    )

    node_x = []
    node_y = []
    node_size = []
    node_label = []
    hover_label = []
    for node in digraph.nodes():
        x, y = digraph.nodes[node]['pos']
        size = digraph.nodes[node]['size']
        n_label = '<b>' + digraph.nodes[node]['title'] + '</b>'
        h_label = str(digraph.nodes[node]['count']) + ' artists'
        node_x.append(x)
        node_y.append(y)
        node_size.append(size)
        node_label.append(n_label)
        hover_label.append(h_label)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        hovertext=hover_label,
        text=node_label,
        textfont_color='#FFFFFF',
        textfont_size=12,
        marker=dict(
            showscale=False,
            color='#1DB954',
            size=node_size,
            line_width=0,
            opacity=1,
        ))

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title=title_label,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        plot_bgcolor='#000000',
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        annotations=[dict(
                            ax=(digraph.nodes[edge[0]]['pos'][0] + digraph.nodes[edge[1]]['pos'][0]) / 2,
                            ay=(digraph.nodes[edge[0]]['pos'][1] + digraph.nodes[edge[1]]['pos'][1]) / 2, axref='x',
                            ayref='y',
                            x=(digraph.nodes[edge[1]]['pos'][0] * 3 + digraph.nodes[edge[0]]['pos'][0]) / 4,
                            y=(digraph.nodes[edge[1]]['pos'][1] * 3 + digraph.nodes[edge[0]]['pos'][1]) / 4, xref='x',
                            yref='y',
                            showarrow=True,
                            arrowhead=2,
                            arrowsize=2,
                            arrowwidth=1,
                            opacity=1,
                            arrowcolor=mpl.colors.to_hex(digraph.edges[edge]['color']),
                        )
                            for edge in digraph.edges]
                    ))

    # Add custom color bar
    summer_color = [mpl.colors.to_hex(plt.cm.summer(i / 10)) for i in range(0, 12, 2)]

    try:
        mx_value = int(edge_list_reduced[metric].max())

    except ValueError:
        mx_value = 0.000000001

    if mx_value % 10 == 0:
        colorbar_max = mx_value
    else:
        colorbar_max = mx_value + (10 - mx_value % 10)

    interval = colorbar_max // 5
    tick_values = np.arange(0, colorbar_max + interval, interval)

    colorbar_trace = go.Scatter(x=[None], y=[None],
                                mode='markers',
                                marker=dict(
                                    colorscale=summer_color,
                                    showscale=True,
                                    cmin=0,
                                    cmax=colorbar_max,
                                    colorbar=dict(
                                        thickness=15,
                                        tickvals=tick_values,
                                        tickformat='0.2s',
                                        outlinewidth=0)
                                ),
                                hoverinfo='none'
                                )

    fig.add_trace(colorbar_trace)

    warnings.filterwarnings('ignore')

    fig.update_layout(
        plot_bgcolor='#000000',
        paper_bgcolor='#000000',
        font_color='#FFFFFF'
    )

    return fig




if __name__ == '__main__':
    app.run_server(debug=False, dev_tools_ui=False, dev_tools_props_check=False)
