import requests
from constants import ROOT_URL
from typing import List, Tuple
import dash_bootstrap_components as dbc
from dash import dcc, html, register_page, Input, Output, callback, State
import pdb
import json
from dash.exceptions import PreventUpdate
from dash_fns import find_team_id, get_name, post_new_team, post_new_workout, duration_to_seconds, check_duration, check_date, post_newuser, flask_requests_get as rget, flask_requests_post as rpost


register_page(__name__, path='/newuser')

# NewUser Traits
# user_name
# dob
# sex
# team

# TODO add new user page team element not working

def layout():
    return dbc.Container([
        dbc.Row(children=dcc.Markdown(id = 'title_newuser', children = '### Add New User')),
        dcc.Store('new_user_id', data=None),
        dbc.Row([
            dbc.Col(children=dbc.Label(children='User Name', html_for='ui_name'), width=3),
            dbc.Col(children=dcc.Input(id='ui_name', value=""), width=9)]),
        dbc.Row([
            dbc.Col(children=dbc.Label(children='Date of Birth', html_for='ui_dob'), width=3),
            dbc.Col(children= dcc.Input(placeholder="yyyy-mm-dd", id='ui_dob', minLength=10, maxLength=10), width=9)]),
        dbc.Row([
            dbc.Col(children=dbc.Label(children='Sex', html_for='ri_sex'), width=3),
            dbc.Col(dcc.RadioItems(['Female', 'Male'], 'Female', inline=True, id="ri_sex"), width=9)
            ]),
        dbc.Row([
            dbc.Col(children=dbc.Label(children='Team',html_for='dd_team'), width=3),
            dbc.Col(children= dcc.Dropdown(options=['None'], id='dd_team', placeholder='select team'), width=3),
            dbc.Col(children= dcc.Input(placeholder='enter team', id='ui_team', style={"display":"none"}), width=6),
            dcc.Store(id='user_team', data=None)
            ]),
        dbc.Row(children=[dbc.Button(id='submit_user_btn',children='Submit User', n_clicks=0,color='primary'),
        dbc.Alert('Username unavailable, try something different',id='alert_username_taken', style={'display':'none'})]),
    ])

@callback(
    Output('dd_team', 'options'),
    Input('dd_team', 'options')
)
def populate_team_dropdown(init_option,get=rget, get_args={}):
    print('ran populate_team_db')
    team_info = get(ROOT_URL+'/teams',**get_args)['body']
    team_names =[]
    for i in range(len(team_info)):
        team_names.append(team_info[i][1])
    team_names.append(init_option[0]) #'None'
    team_names.append('Other')
    return team_names

@callback(
    Output('ui_team', 'style'),
    Input('dd_team', 'value')
)
def display_team_input(team_selection):
    if team_selection == 'Other':
        return {'display':'block'}
    else:
        raise PreventUpdate

@callback(
    Output('user_team', 'data'),
    Input('dd_team', 'value'),
    Input('ui_team', 'value')
)
def set_user_team(dd, ui):
    if dd == 'Other':
        return ui
    return dd

@callback(
    Output('submit_user_btn', 'children'),
    Output("submit_user_btn", 'color'),
    Output('alert_username_taken', 'style'),
    Output('new_user_id', 'data'),
    Input('submit_user_btn', 'n_clicks'),
    State('ui_name', 'value'),
    State('ui_dob', 'value'),
    State('ri_sex', 'value'),
    State('user_team','data')
)
def submit_user(n_clicks, name, dob, sex, team_name, get=rget, get_args={}, post=rpost, post_args={}):
    if n_clicks == 0:
        raise PreventUpdate
    newuser_post_dict = {'user_name':None, 'dob':None, 'sex':None, 'team_id':None}
    team_id = find_team_id(team_name, get, get_args, post, post_args)
    # generate newuser dict
    newuser_post_dict['user_name'] = name.lower()
    newuser_post_dict['dob'] = dob
    newuser_post_dict['sex'] = sex
    newuser_post_dict['team_id'] = team_id
    user_id = post_newuser(newuser_post_dict,post,post_args)['body']
    if user_id == 0:
        return 'Submit User','primary', {'display':'block'},user_id
    return 'User Added', 'success', {'display':'none'}, user_id

# TODO: for some reason user is not posting.  