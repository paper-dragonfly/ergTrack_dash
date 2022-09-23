from dash import dcc, html, register_page

register_page(__name__, path='/sandbox')

def layout():
    return html.Div([
        dcc.Link('to home', href='/'),
        dcc.Link('to guest workout_log', href='/workout_log/1')
    ])