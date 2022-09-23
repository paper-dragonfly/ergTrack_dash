from dash import Dash, dash_table, dcc, html, register_page, callback
from dash.dependencies import Input, Output, State
import pandas as pd
import requests
from typing import List
from constants import ROOT_URL
from dash_fns import flask_requests_get, flask_requests_post
from dash_fns import get_name, seconds_to_duration
import dash_bootstrap_components as dbc
import plotly.express as px
from dash.exceptions import PreventUpdate
import pdb
import json

register_page(__name__,path_template='/log_table/<user_id>')


def layout(user_id=1):
    flash_workouts:List[List] = requests.get(ROOT_URL+f'/workoutlog?user_id={user_id}').json()['message']
    workouts = {
        'id' : [],
        'Date':[],
        'Time': [],
        'Distance':[],
        'Split':[],
        'Stroke Rate': [],
        'Heart Rate': [],
        'Intervals':[],
        'Comment':[]
        }
    for i in range(len(flash_workouts)):
        workouts['id'].append(flash_workouts[i][0]),
        workouts['Date'].append(flash_workouts[i][2]),
        workouts['Time'].append(seconds_to_duration(float(flash_workouts[i][3]))),
        workouts['Distance'].append(str(flash_workouts[i][4])),
        workouts['Split'].append(seconds_to_duration(float(flash_workouts[i][5]))),
        workouts['Stroke Rate'].append(str(flash_workouts[i][6])),
        workouts['Heart Rate'].append(str(flash_workouts[i][7])),
        workouts['Intervals'].append(str(flash_workouts[i][8])),
        workouts['Comment'].append(flash_workouts[i][9])

    df = pd.DataFrame(workouts)
    df.set_index('id', inplace=True, drop=False)

    return dbc.Container([
        dcc.Markdown('## Workout Log'),
        dcc.Markdown('Guest', id='user_label'),
        dcc.Store(id='invisible_id', data=user_id),
        dcc.Store(id='df_data', data=df.to_json()),
        dash_table.DataTable(
            id='table',
            columns=[{"name": k, "id": k, "deletable": False, "selectable": True} for k in df if k !='id'],
            data=df.to_dict('records'),
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            # column_selectable="single",
            row_selectable="multi",
            # row_deletable=True,
            # selected_columns=[],
            # selected_rows=[],
            selected_row_ids=[],
            page_action="native",
            page_current= 0,
            page_size= 10
            ),
        dbc.Button('Select Row', id='btn_view_details', n_clicks=0,color='secondary', href=None),
        dbc.Button('Compare', id='btn_compare', style={'display':'none'}, n_clicks=0),
        html.Div(id='graph_area')
    ])

@callback(
    Output('user_label', 'children'),
    Input('invisible_id','data')
    )
def display_username(user_id):
    return get_name(user_id).capitalize()

@callback(
    Output('btn_view_details', 'children'),
    Output('btn_view_details', 'color'),
    Output('btn_view_details','href'),
    Input('table', 'selected_row_ids')
)
def activate_view_details(selected_id):
    if len(selected_id) != 1:
        return 'Select Row', 'secondary', None
    return 'View Workout Details', 'warning', f'/details/{selected_id[0]}' 

@callback(
    Output('btn_compare', 'style'),
    Input('table', 'selected_row_ids')
)
def show_compare_btn(selected_rows):
    if len(selected_rows) > 1:
        return {'display':'block'}
    else:
        return {'display':'none'}

@callback(
    Output('graph_area', 'children'),
    Input('btn_compare', 'n_clicks'),
    State('table', 'selected_row_ids'),
    State('df_data', 'data')
)
def make_graph(n_clicks, row_ids, df):
    if n_clicks == 0:
        raise PreventUpdate
    df = json.loads(df)
    pd_df = pd.DataFrame(df)
    df_rows = pd_df.loc[pd_df['id'].isin(row_ids)]
    fig = px.bar(df_rows, x='Date', y='Split')
    return dcc.Graph(id='comp_graph',figure=fig)

