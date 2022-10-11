from dash import Dash, dcc, html, page_registry, page_container
import dash_bootstrap_components as dbc
from dash.dependencies import Output, Input, State
from constants import ROOT_URL
import requests
import dash_fns as dfx
import pdb
import os 
from dotenv import load_dotenv

load_dotenv()

app = Dash(__name__,external_stylesheets=[dbc.themes.SANDSTONE], use_pages=True)
server = app.server


user_names = dfx.get_usernames()
if len(user_names) == 0:
    user_names = ['None']

# Layout
app.layout = dbc.Container([
    dbc.NavbarSimple([
        dcc.Store(id='user_names', data=['None']),
        dcc.Dropdown(options=user_names, value="None", id='user_dropdown'),
        dbc.DropdownMenu(
            children=None,
            id='page_menu',
            nav=True,
            label= 'Menu')
        ]),
    page_container 
])

#Callback 

@app.callback(
    Output('user_names', 'data'),
    Input('user_dropdown', 'value')
)
def reload_names(user='None'):
    user_names = dfx.get_usernames()
    if len(user_names) == 0:
        return ['None']
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

ENV = os.getenv('ENVIRONMENT')

if __name__ == '__main__' and ENV != 'production':
    if ENV == 'dev_docker':
        app.run('0.0.0.0', 5001)
    else: 
        app.run('localhost', 5001, debug=True )