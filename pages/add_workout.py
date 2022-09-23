import requests
import pandas as pd
import pdb
from constants import ROOT_URL
import dash_bootstrap_components as dbc
from dash import dcc, html, register_page, callback, Input, Output, State 
from dash_fns import format_and_post_intervals, format_time, duration_to_seconds, post_new_workout, check_date, check_duration, generate_post_wo_dict, format_and_post_intervals
from dash.exceptions import PreventUpdate
import json 


register_page(__name__,path_template='/addworkout/<user_id>')
print('ADD_WORKOUT LOADED')

empty_single_table = {'Date':[],'Time':[],'Distance':[],'Split':[],'s/m':[],'HR':[],'Comment':[]}
empty_post_wo_dict = {'user_id':None, 'workout_date':None,'time_sec':None,'distance':None,'split':None,'sr':None,'hr':None,'intervals':1, 'comment':None}
empty_intrvl_table = {'Date':[],'Time':[],'Distance':[],'Split':[],'s/m':[],'HR':[],'Rest':[],'Comment':[]}
empty_post_intrvl_dict = {'workout_id':None,'time_sec':None,'distance':None,'split':None,'sr':None,'hr':None,'rest':None,'comment':None}

def layout(user_id='1'):
    return dbc.Container([
        #Radio Select
        html.Div([
            dcc.Store(id='user_id', data=user_id),
            dcc.Markdown('## Add Workout - Single', id='head_wotype'),
            dcc.RadioItems(options=['Single Time/Distance','Intervals'], value='Single Time/Distance', id='radio_select'),
        # user_input both
            dbc.Row([
                dbc.Col(dbc.Label('Date',html_for='ui_date'), width=2),
                dbc.Col(dcc.Input(placeholder='yyyy-mm-dd',id="ui_date", size='10',minLength=10, maxLength=10 ), width=4)
                ]),
            dbc.Row([
                dbc.Col(dbc.Label('Time',html_for='ui_hours'), width=2),
                dbc.Col(dcc.Input(placeholder='hours', id='ui_hours', size='10', maxLength=2), width=2),
                dbc.Col(dcc.Input(placeholder='minutes',id='ui_min',size='10', maxLength=2), width=2),
                dbc.Col(dcc.Input(placeholder='seconds',id='ui_sec',size='10', maxLength=2), width=2),
                dbc.Col(dcc.Input(placeholder='tenths',id='ui_ten',size='10', maxLength=1), width=2)
                ]),
            dbc.Row([
                dbc.Col(dbc.Label('Distance',html_for='ui_dist'), width=2),
                dbc.Col(dcc.Input(placeholder='meters',id="ui_dist", size='10', type="number"), width=4)
                ]),
            dbc.Row([
                dbc.Col(dbc.Label('Split',html_for='ui_split'), width=2),
                dbc.Col(dcc.Input(placeholder='m:ss.d',id="ui_split", size='10',minLength=4, maxLength=6), width=4)
                ]),
            dbc.Row([
                dbc.Col(dbc.Label('Stroke Rate',html_for='ui_sr'), width=2),
                dbc.Col(dcc.Input(placeholder='s/m',id="ui_sr", size='10', type="number",maxLength=2), width=4)
                ]),
            dbc.Row([
                dbc.Col(dbc.Label('Heart Rate',html_for='ui_hr'), width=2),
                dbc.Col(dcc.Input(placeholder='BPM',id="ui_hr", size='10', type="number"), width=4)
                ]),
            dbc.Row([
                dbc.Col(dbc.Label('Comment',html_for='ui_com'), width=2),
                dbc.Col(dcc.Input('',id="ui_com", size='20'), width=8)
                ]),
                # pg1 - single specific
            html.Div([
                dbc.Row([
                    dbc.Button('Submit Workout', id='single_submit_btn', n_clicks=0, color='primary'),
                    dbc.Alert(id='sing_alert', style={'display':'none'},color='warning')
                ]),
                dcc.Store(id='single_df_dict', data=empty_single_table),
                dcc.Store(id='single_post_dict', data=empty_post_wo_dict),
                dbc.Row(children=None, id='single_table')
                # dcc.Markdown(id='single_json')
                ], id='sing_pg', style={'display':'block'}),
            # pg2 - interval specific
            html.Div([
                dbc.Row([
                    dbc.Col(dbc.Label('Rest',html_for='ui_rest'), width=2),
                    dbc.Col(dcc.Input(placeholder='seconds',id="ui_rest", size='10'), width=4)
                    ]),
                dbc.Button('Submit Interval', id='interval_submit', n_clicks=0, color='primary'),
                dbc.Alert(id='intrvl_alert', style={'display':'none'},color='warning'),
                dcc.Store(id='int_dict', data=empty_intrvl_table),
                dcc.Store(id='intrvl_formatting_approved', data=False),
                dbc.Row(
                    [dbc.Table.from_dataframe(pd.DataFrame(empty_intrvl_table),striped=True,bordered=True)], 
                    id='interval_table'),
                dbc.Button('Submit workout', id='intwo_submit', n_clicks=0, color='primary'),
                ], id='int_pg', style={'display':'none'}), 
            dcc.Markdown('',id='data_json')],
            id='pg_box')
    ])      


# Respond to radio selection
@callback(
    Output('sing_pg', 'style'),
    Output('int_pg', 'style'),
    Input('radio_select', 'value')
)
def choose_page_to_display(choice):
    if choice == 'Single Time/Distance':
        return {'display':'block'}, {'display':'none'}
    return {'display':'none'}, {'display':'block'}

#SINGLE WORKOUT
# create workout summary table
@callback(
    Output('single_table','children'),
    Output('single_df_dict', 'data'),
    Input('single_submit_btn','n_clicks'),
    State('ui_date','value'),
    State('ui_hours', 'value'),
    State('ui_min', 'value'),
    State('ui_sec', 'value'),
    State('ui_ten', 'value'),
    State('ui_dist', 'value'),
    State('ui_split', 'value'),
    State('ui_sr', 'value'),
    State('ui_hr', 'value'),
    State('ui_com', 'value'),
    State('single_df_dict', 'data')
)
def create_summary_table(n_clicks, date, hours, min, sec,ten,dist,split,sr,hr,com, df):
    if n_clicks == 0:
        raise PreventUpdate 
    time = format_time(hours, min, sec, ten)
    #populate table df
    df['Date'].append(date)
    df['Time'].append(time)
    df['Distance'].append(dist)
    df['Split'].append(split)
    df['s/m'].append(sr)
    df['HR'].append(hr)
    df['Comment'].append(com)
    return dbc.Table.from_dataframe(pd.DataFrame(df), striped=True, bordered=True), df

#Generate post_dict and post workout to db
@callback(
    Output('single_post_dict','data'),
    Output('single_submit_btn', 'children'),
    Output('single_submit_btn', 'color'),
    Output('sing_alert','children'),
    Output('sing_alert', 'style'),
    Input('single_submit_btn','n_clicks'),
    State('user_id','data'),
    State('ui_date','value'),
    State('ui_hours', 'value'),
    State('ui_min', 'value'),
    State('ui_sec', 'value'),
    State('ui_ten', 'value'),
    State('ui_dist', 'value'),
    State('ui_split', 'value'),
    State('ui_sr', 'value'),
    State('ui_hr', 'value'),
    State('ui_com', 'value'),
    State('single_post_dict', 'data')
)
def create_data_dict(n_clicks, user_id, date, hours, min, sec,ten,dist,split,sr,hr,com, pdict):
    if n_clicks == 0:
        raise PreventUpdate
    # check inputs format
    valid_date:dict = check_date(date)
    if not valid_date['accept']:
        alert_message = 'Date formatting wrong: '+valid_date['message']
        return pdict, 'Submit Workout', 'primary', alert_message, {'display':'block'}
    time:str = format_time(hours, min, sec, ten) #hh:mm:ss.d
    valid_time = check_duration(time)
    if not valid_time['accept']:
        alert_message = 'Time formatting wrong: '+valid_time['message']
        return pdict, 'Submit Workout', 'primary', alert_message, {'display':'block'}
    time_sec:int = duration_to_seconds(time)
    wsplit = '00:0'+split 
    valid_split = check_duration(wsplit)
    if not valid_split['accept']:
        alert_message = 'Split formatting wrong: '+valid_split['message']
        return pdict, 'Submit Workout', 'primary', alert_message, {'display':'block'}
    split_sec:int = duration_to_seconds(wsplit)
    #populate post dict
    pdict['user_id'] = int(user_id) 
    pdict['workout_date']=date
    pdict['time_sec']=int(time_sec)
    pdict['distance']=int(dist)
    pdict['split']=int(split_sec)
    pdict['sr']=int(sr)
    pdict['hr']=int(hr)
    pdict['comment']= com
    print(pdict)
    flask_workout_id = post_new_workout(pdict)['workout_id']
    print('WO ID', flask_workout_id)
    return pdict, 'Workout Submitted!', 'success', None, {"display":'none'}


# INTERVAL

# Add intervals to inverval table
@callback(
    Output('interval_table','children'), #table
    Output('int_dict','data'), #table contents
    Output('intrvl_alert','children'), #alert message
    Output('intrvl_alert', 'style'), #alert visibility
    Output('intrvl_formatting_approved','data'), #formatting approval 
    Input('interval_submit', 'n_clicks'),
    State('ui_date','value'),
    State('ui_hours', 'value'),
    State('ui_min', 'value'),
    State('ui_sec', 'value'),
    State('ui_ten', 'value'),
    State('ui_dist', 'value'),
    State('ui_split', 'value'),
    State('ui_sr', 'value'),
    State('ui_hr', 'value'),
    State('ui_rest', 'value'),
    State('ui_com', 'value'),
    State('int_dict', 'data')
)
def add_interval(n_clicks, date, hours, min, sec, ten, dist, split, sr, hr, rest, com, df):
    if n_clicks == 0:
        raise PreventUpdate
    blank_table=dbc.Table.from_dataframe(pd.DataFrame(df), striped=True, bordered=True)
    # check inputs format
    valid_date:dict = check_date(date)
    if not valid_date['accept']:
        alert_message = 'Date formatting wrong: '+valid_date['message']
        return blank_table, df, alert_message, {'display':'block'}, False
    time:str = format_time(hours, min, sec, ten) #hh:mm:ss.d
    valid_time = check_duration(time)
    if not valid_time['accept']:
        alert_message = 'Time formatting wrong: '+valid_time['message']
        return blank_table, df, alert_message, {'display':'block'}, False
    wsplit = '00:0'+split 
    valid_split = check_duration(wsplit)
    if not valid_split['accept']:
        alert_message = 'Split formatting wrong: '+valid_split['message']
        return blank_table, df, alert_message, {'display':'block'}, False
    time = format_time(hours, min, sec, ten)
    df['Date'].append(date)
    df['Time'].append(time)
    df['Distance'].append(dist)
    df['Split'].append(split)
    df['s/m'].append(sr)
    df['HR'].append(hr)
    df['Rest'].append(rest)
    df['Comment'].append(com)
    return dbc.Table.from_dataframe(pd.DataFrame(df), striped=True, bordered=True), df, None, {'display':'none'}, True

#Create workout summary post_dict and post wo to db 
@callback(
    Output('intwo_submit', 'children'),
    Output('intwo_submit', 'color'),
    Input('intwo_submit','n_clicks'),
    State('intrvl_formatting_approved', 'data'),
    State('int_dict', 'data'),
    State('user_id', 'data'),
)
def post_wo_summary(n_clicks, formatting_approved, int_dict, user_id):
    if n_clicks==0 or not formatting_approved:
        raise PreventUpdate
    wo_dict = generate_post_wo_dict(int_dict, user_id, empty_post_wo_dict)
    wo_id = post_new_workout(wo_dict)['workout_id']
    format_and_post_intervals(wo_id, int_dict)
    return 'Interval Workout Submitted!', 'success'




# empty_post_wo_dict = {'user_id':None, 'workout_date':None,'time_sec':None,'distance':None,'split':None,'sr':None,'hr':None,'intervals':1, 'comment':None}

# empty_intrvl_table = {'Date':[],'Time':[],'Distance':[],'Split':[],'s/m':[],'HR':[],'Rest':[],'Comment':[]}

# empty_post_intrvl_dict = {'workout_id':None,'time_sec':None,'distance':None,'split':None,'sr':None,'hr':None,'rest':None,'comment':None}