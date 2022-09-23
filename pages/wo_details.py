import pdb
from dash import dcc, register_page, Output, Input, State, callback, html
import pandas as pd 
import dash_bootstrap_components as dbc
import requests
import pdb
from typing import List
from constants import ROOT_URL
from dash_fns import calc_av_rest, flask_requests_get, flask_requests_post, get_wo_details, wo_details_df
from dash_fns import get_name, seconds_to_duration

register_page(__name__, path_template='/details/<wo_id>')

###########
def layout(wo_id=False):
    df = []
    date = ''
    wo_name = ''
    if wo_id:
        df, date, wo_name = wo_details_df(wo_id)
    return dbc.Container([
        dcc.Store(id='wo_id', data=wo_id),
        dcc.Markdown('## Workout Details'),
        dcc.Markdown(f'##### {wo_name}', id='wo_label'),
        dcc.Markdown(f'{date}', id= 'wo_date'),
        dbc.Row([
            dbc.Col(width=1),
            dbc.Col(dbc.Table.from_dataframe(pd.DataFrame(df), striped=True, bordered=True), id="wo_table", align='center'),
            dbc.Col(width=1)
        ])
    ])


