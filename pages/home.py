from dash import dcc, html, register_page, Output, Input, State, callback
import dash_bootstrap_components as dbc
from PIL import Image

register_page(__name__, path='/')

pil_image = Image.open("erg_cartoon.png")


def layout():
    return dbc.Container([
        dcc.Markdown('# Welcome to ErgTracker'),
        html.Img(src=pil_image, width='100%'),
        dbc.Button('View Instructions', id='btn_info', n_clicks=0),
        html.Div([
            dcc.Markdown('### App Info')

        ], id='div_info')
            
    ])


