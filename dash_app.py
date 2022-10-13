from dash import Dash, dcc, html, page_registry, page_container
import dash_bootstrap_components as dbc
from dash.dependencies import Output, Input, State
# from constants import ROOT_URL
import requests
import dash_fns as dfx
import pdb
import os 


app = Dash(__name__,external_stylesheets=[dbc.themes.SANDSTONE], use_pages=True)
server = app.server


# def get_usernames():
#     # user_names = dfx.get_usernames()
#     # if len(user_names) == 0:
#     #     user_names = ['None']
#     user_names = ['jaja']
#     return user_names
# user_names=get_usernames()   

# Layout
app.layout = dbc.Container([
    dbc.NavbarSimple([
        # dcc.Store(id='user_names', data=['None']),
        dcc.Dropdown(
            options=['None'], 
            value="None", 
            id='user_dropdown'),
        dbc.Button(
            children='⟳', 
            id='btn_ref',
            color='light',
            size='sm', 
            n_clicks=0),
        dbc.DropdownMenu(
            children=None,
            id='page_menu',
            nav=True,
            label= 'Menu',
            in_navbar=True)
        ]),
    page_container 
])

# Callbacks 

@app.callback(
    Output('user_dropdown', 'options'),
    Input('btn_ref', 'n_clicks')
)
def reload_names(n_clicks):
    print('ran reload_names')     
    user_names = dfx.get_usernames()
    print('user_names:', user_names)
    return user_names


@app.callback(
    Output('page_menu', 'children'),
    Input('user_dropdown','value')
)
def choose_page(username='None'):
    if username == 'None':
        id = 0
        pages = [  
            dbc.DropdownMenuItem('Home', href=f'/'),
            dbc.DropdownMenuItem('Add New User', href='/newuser')
            ]
    else:
        id = dfx.get_id(username.lower())
        pages = [  
            dbc.DropdownMenuItem('Home', href=f'/'),
            dbc.DropdownMenuItem('Workout Log', href=f'/log_table/{id}'),
            dbc.DropdownMenuItem('Add Workout', href=f'/upload_image/{id}'),
            # dbc.DropdownMenuItem('Add Workout Manual', href=f'/addworkout/{id}'),
            # dbc.DropdownMenuItem('sandbox', href='/sandbox'),
            dbc.DropdownMenuItem('Add New User', href='/newuser'),
        ]
    return pages

ENV = os.getenv('ENV')

if __name__ == '__main__' and ENV != 'production':
    if ENV == 'dev_docker':
        app.run('0.0.0.0', 5001)
    else: 
        app.run('localhost', 5001, debug=True )