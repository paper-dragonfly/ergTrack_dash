from sys import stderr
import pandas as pd
import pdb
from dash import dcc, html, register_page, callback, Input, Output, State 
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash_fns import choose_title, format_and_post_intervals, generate_post_wo_dict2, post_new_workout, format_and_post_intervals, validate_form_inputs
from dash.exceptions import PreventUpdate
import cv2
import datetime
import base64
import numpy as np
from matplotlib import pyplot as plt
from ocr_pipeline import clean_ocr 

register_page(__name__,path_template='/upload_image/<user_id>')

## PLAN 
# upload image
# crop (skip for now)
# convert to binary/json
    # uploaded as base64 encoded str, need to convert to
    # cv2.imread - what is it reading? what format? 
# send data to img processing pipeline
# send back results dict
# populate form with data - make form editable for corrections
# submit workout


### Empty forms 
EMPTY_SINGLE_TABLE = {'Date':[],'Time':[],'Distance':[],'Split':[],'s/m':[],'HR':[],'Comment':[]}
EMPTY_POST_WO_DICT = {'user_id':None, 'workout_date':None,'time_sec':None,'distance':None,'split':None,'sr':None,'hr':None,'intervals':1, 'comment':None}
EMPTY_INTERVAL_TABLE = {'Date':[],'Time':[],'Distance':[],'Split':[],'s/m':[],'HR':[],'Rest':[],'Comment':[]}
EMPTY_POST_INTERVAL_DICT = {'workout_id':None,'time_sec':None,'distance':None,'split':None,'sr':None,'hr':None,'rest':None,'comment':None}


def layout(user_id=1):
    return dbc.Container([
        dcc.Store(id='user_id', data=user_id),
        dcc.Markdown('# Add Workout'),
        dbc.Row([
            # LEFT SCREEN
            dbc.Col([
                # Radio Select: input type
                dcc.RadioItems(
                    ['Manually', 'From Image'], 
                    'Manually', 
                    labelStyle={'display': 'block'},
                    id='radio_input_type'),
                html.Br(),
                # Radio Select: workout type
                dcc.Markdown('#### Workout Type'),
                dcc.RadioItems(
                    options=['Single Distance', 'Single Time', 'Interval Distance', 'Interval Time'],
                    value = 'Single Distance',
                    labelStyle={'display':'block'},
                    id = 'radio_wotype'), 
                html.Br(), 
                
                # Visible when INPUT = MANUAL 
                html.Div([
                    # Single Distance Choices
                    html.Div([
                        dcc.Markdown('#### Single Distance (m)'),
                        dcc.RadioItems(
                            ['2000', '5000', '10000', 'other'],
                            labelStyle={'display':'block'},
                            id='radio_sdist_ops'),
                        dcc.Input(placeholder='custom distance (m)', id='ui_sdist_ops')
                    ], style={'display':'none'}, id='div_man_sdist'),
                    # Single Time Choices
                    html.Div([
                        dcc.Markdown('#### Single Time'),
                        dcc.RadioItems(
                            ['15:00', '30:00', '45:00', 'other'],
                            labelStyle={'display':'block'},
                            id='radio_stime_ops'),
                        dcc.Input(placeholder='custom time (hh:mm:ss)', id='ui_stime_ops')
                    ], style={'display':'none'}, id='div_man_stime'),
                    # Interval Distance Choices
                    html.Div([
                        dcc.Markdown('#### Interval Distance'),
                        dcc.RadioItems(
                            ['500', '1000', '2000', 'other'],
                            labelStyle={'display':'block'},
                            id='radio_idist_ops'),
                        dcc.Input(placeholder='custom distance (m)', id='ui_idist_ops')
                    ], style={'display':'none'}, id='div_man_idist'),
                     # Interval Distance Choices
                    html.Div([
                        dcc.Markdown('#### Interval Time'),
                        dcc.RadioItems(
                            ['1:00', '15:00', '30:00', 'other'],
                            labelStyle={'display':'block'},
                            id='radio_itime_ops'),
                        dcc.Input(placeholder='custom time (hh:mm:ss)', id='ui_itime_ops')
                    ], style={'display':'none'}, id='div_man_itime'),
                    html.Br(),
                    dbc.Button('Fill Form',id='btn_fill_form', n_clicks=0),
                    dcc.Store('quick_pick_val', data=None)
                ], style={'display':'block'}, id='div_manually'),  

                
                # Visible when INPUT = Image | Upload + Display image 
                html.Div([
                    dcc.Upload(
                        id='upload-image',
                        children=html.Button('Upload Image', id="upload_image")),
                    dcc.Store(id='base64_img', data=None),
                    dcc.Store(id='np_array_img', data=None),
                    dcc.Store(id='raw_ocr', data=None),
                    html.Div(id='output_upload')
                ], style={'display':'none'}, id='div_from_image')
            ]),

        #RIGHT SCREEN - BOTH        
        # data form feilds
            dbc.Col([
                dcc.Store(id='ocr_dict', data=None),
                dcc.Markdown('## Workout Summary', id='h2_input_form'),
                dbc.Row([
                    dbc.Col(dbc.Label('Date',html_for='ui_date2'), width=2),
                    dbc.Col(dcc.Input(placeholder='Jan 01 2000',id="ui_date2", size='20' ), width=4)
                    ]),
                dbc.Row([
                    dbc.Col(dbc.Label('Time',html_for='ui_time2'), width=2),
                    dbc.Col(dcc.Input(placeholder='hh:mm:ss.t', id='ui_time2', size='15', maxLength=12), width=4)
                    ]),
                dbc.Row([
                    dbc.Col(dbc.Label('Distance',html_for='ui_dist2'), width=2),
                    dbc.Col(dcc.Input(placeholder='meters',id="ui_dist2", size='10'), width=4)
                    ]),
                dbc.Row([
                    dbc.Col(dbc.Label('Split',html_for='ui_split2'), width=2),
                    dbc.Col(dcc.Input(placeholder='m:ss.d',id="ui_split2", size='10'), width=4)
                    ]),
                dbc.Row([
                    dbc.Col(dbc.Label('Stroke Rate',html_for='ui_sr2'), width=2),
                    dbc.Col(dcc.Input(placeholder='s/m',id="ui_sr2", size='10'), width=4)
                    ]),
                dbc.Row([
                    dbc.Col(dbc.Label('Heart Rate',html_for='ui_hr2'), width=2),
                    dbc.Col(dcc.Input(placeholder='BPM',id="ui_hr2", size='10'), width=4)
                    ]),
                dbc.Row([
                    dbc.Col(dbc.Label('Comment',html_for='ui_com2'), width=2),
                    dbc.Col(dcc.Input('',id="ui_com2", size='20'), width=8)
                    ]),
                dbc.Row([
                    dbc.Col(dbc.Label('Rest',html_for='ui_rest2'), width=2),
                    dbc.Col(dcc.Input(placeholder='seconds',id="ui_rest2", size='10'), width=4)
                    ]),
                # End of form
                dbc.Button('Submit Interval', id='interval_submit2', n_clicks=0, color='primary'),
                dbc.Alert(id='intrvl_alert2', style={'display':'none'},color='warning'),
                dbc.Alert(id='all_added_alert', children='Full Workout Staged', color='info', style={'display':'none'}),
                dcc.Store(id='intrvl_count', data=None),
                dcc.Store(id='int_dict2', data=EMPTY_INTERVAL_TABLE),
                dcc.Store(id='intrvl_formatting_approved2', data=False),
                dbc.Row(
                    [dbc.Table.from_dataframe(pd.DataFrame(EMPTY_INTERVAL_TABLE),striped=True,bordered=True)], 
                    id='interval_table2'),
                dbc.Button('Submit workout', id='btn_submit_workout2', n_clicks=0, color='primary')
                ], style={'display':'block'}, id='form_col')
        ])])

#display manual vs upload_image options
@callback(
    Output('div_manually', 'style'),
    Output('div_from_image', 'style'),
    Input('radio_input_type','value')
)
def show_div(input_type):
    display = {'display':'block'}
    hide = {'display': 'none'}
    if input_type == 'Manually':
        return display, hide 
    return hide, display 

# manual input > quick pick dist/time
@callback(
    Output('div_man_sdist', 'style'),
    Output('div_man_stime', 'style'),
    Output('div_man_idist', 'style'),
    Output('div_man_itime', 'style'),
    Input('radio_input_type','value'),
    Input('radio_wotype', 'value')
)
def display_quick_select_values(input_type, wo_type):
    if input_type == 'From Image':
        raise PreventUpdate
    display = {'display':'block'}
    hide = {'display': 'none'}
    if wo_type == 'Single Distance':
        return display, hide, hide, hide 
    elif wo_type == 'Single Time':
        return hide, display, hide, hide
    elif wo_type == 'Interval Distance':
        return hide, hide, display, hide
    else:
        return hide, hide, hide, display 

#store quick_pick val
@callback(
    Output('quick_pick_val', 'data'),
    Input('btn_fill_form', 'n_clicks'),
    State('radio_wotype', 'value'),
    State('radio_sdist_ops', 'value'),
    State('radio_stime_ops', 'value'),
    State('radio_idist_ops', 'value'),
    State('radio_itime_ops', 'value'),
    State('ui_sdist_ops', 'value'),
    State('ui_stime_ops', 'value'),
    State('ui_idist_ops', 'value'),
    State('ui_itime_ops', 'value'),
    State('quick_pick_val', 'data')
)
def store_quick_pick(n_clicks,wo_type,rsdist,rstime,ridist,ritime,ui_sdist, ui_stime, ui_idist, ui_itime, quick_pick_val):
    if n_clicks == 0:
        raise PreventUpdate
    print(n_clicks)
    print('QUICK PICK VAL: ', quick_pick_val)
    pdb.set_trace() 

    if wo_type =='Single Distance':
        if rsdist == 'other' or ui_sdist != "":
            val= ui_sdist
        else:
            val= rsdist
    elif wo_type == 'Single Interval' or ui_sdist != "": 
        if rstime == 'other':
            val= ui_stime
        else:
            val= rstime
    elif wo_type =='Interval Distance' or ui_sdist != "":
        if ridist == 'other':
            val= ui_idist
        else:
            val= ridist
    elif wo_type == 'Single Interval' or ui_sdist != "": 
        if ritime == 'other':
            val= ui_itime
        else:
            val= ritime
    print('VAL ', val)
    return val 


# Show form     
# @callback(
#     Output('form_col','style'),
#     Input('btn_fill_form','n_clicks'),
#     Input('raw_ocr', 'data'),
#     prevent_initial_call=True
# )
# def show_form(manual_n_clicks, image_uploaded):
#     if image_uploaded:
#         return {'display':'block'}

# FROM IMAGE
#upload pic
@callback(
    Output('output_upload', 'children'),
    Output('base64_img', 'data'),
    Input('upload-image', 'contents'), 
    State('upload-image', 'filename'),
    State('upload-image', 'last_modified'),
    prevent_initial_call=True)
def upload_img(contents, filename, date):
    if contents is not None:
        base64_img = contents[23:]
        print('b64: ', type(base64_img))
        children = dbc.Container([
            html.H5(filename),
            html.H6(datetime.datetime.fromtimestamp(date)),
            # HTML images accept base64 encoded strings in the same format
            # that is supplied by the upload
            html.Img(src=contents,id='erg_pic',style={'width':'70%'}),
            html.Hr() #horizontal line
            ])
        return children, base64_img


@callback(
    Output('np_array_img', 'data'),
    Input('base64_img', 'data')
)
def convert_to_cv2_compatible(b64):
    if b64 is not None:
        print('run convert to cv2 compatible')
        b64_bytes = b64.encode('ascii')
        im_bytes = base64.b64decode(b64_bytes)
        im_arr = np.frombuffer(im_bytes, dtype=np.uint8) # im_arr is one-dim np array
        img = cv2.imdecode(im_arr, flags=cv2.IMREAD_COLOR)
        return img


@callback(
    Output('raw_ocr', 'data'),
    Input('np_array_img', 'data')
)
def extract_ocr(image):
    if image is not None: 
        image = np.array(image, dtype='uint8')
        raw_ocr = clean_ocr(image)
        print(raw_ocr, file=stderr)
        return raw_ocr 

#FORM
@callback(
    Output('ui_date2', 'value'),
    Output('ui_time2', 'value'),
    Output('ui_dist2', 'value'),
    Output('ui_split2', 'value'),
    Output('ui_sr2', 'value'),
    Output('ui_hr2', 'value'),
    Output('ui_rest2','value'),
    Output('intrvl_count', 'data'),
    Input('btn_fill_form', 'n_clicks'),
    Input('raw_ocr', 'data'),
    Input('interval_submit2', 'n_clicks'),
    Input('intrvl_formatting_approved2','data'),
    State('radio_input_type','value'),
    State('radio_wotype','value'),
    State('quick_pick_val', 'data'),
    State('ui_date2', 'value'),
    State('int_dict2', 'data'),
    prevent_initial_call = True
)
def fill_form(n_clicks_manual_fill_form, raw_ocr, n_clicks_intsubmit, formatted, radio_it, radio_wot, quick_pick_val, date, df):
    if radio_it == 'Manually':
        print('form fill quick val: ', quick_pick_val)
        date = date 
        split = '2:00'
        sr = '20'
        hr = 'n/a'
        rest = 'n/a'
        if radio_wot == 'Interval Time' or radio_wot== 'Interval Distance':
            rest = '60'
        if radio_wot == 'Single Distance' or radio_wot == 'Interval Distance':
            return date, None, quick_pick_val, split, sr,hr,rest,None 
        elif radio_wot == 'Single Time' or radio_wot=='Interval Time':  
            return date, quick_pick_val, None, split, sr,hr,rest, None
    elif radio_it == 'From Image':
        if not raw_ocr:
            raise PreventUpdate #TODO: change this to allow manual input
        num_ints = len(raw_ocr['time'])
        print('num ints', num_ints, file=stderr)
        hr = 'n/a'
        rest = 'n/a'
        if radio_wot == 'Intervals':
            rest = None  
        if n_clicks_intsubmit == 0: 
            if len(raw_ocr['summary']) == 5: #HR is present in image
                hr = raw_ocr['summary'][4] 
            #.strip() removes leading and trailing white spaces
            return raw_ocr['date'].strip(), raw_ocr['summary'][0].strip(), raw_ocr['summary'][1].strip(), raw_ocr['summary'][2].strip(), raw_ocr['summary'][3].strip(), hr, rest, num_ints
        if not formatted:
            print('blocked formatted  == False', file=stderr)
            raise PreventUpdate 
        else:
            i = len(df['Time'])-1
            if i < num_ints: 
                return date, raw_ocr['time'][i], raw_ocr['dist'][i], raw_ocr['split'][i], raw_ocr['sr'][i], hr, rest, num_ints
            else: 
                return date, None, None, None, None, None, None, num_ints 
    


# Add intervals to inverval table
@callback(
    Output('h2_input_form', 'children'), #form title
    Output('interval_table2','children'), #table
    Output('int_dict2','data'), #table contents
    Output('intrvl_alert2','children'), #alert message
    Output('intrvl_alert2', 'style'), #alert visibility
    Output('intrvl_formatting_approved2','data'), #formatting approval
    Output('all_added_alert', 'style'), 
    Input('interval_submit2', 'n_clicks'),
    State('ui_date2','value'),
    State('ui_time2', 'value'),
    State('ui_dist2', 'value'),
    State('ui_split2', 'value'),
    State('ui_sr2', 'value'),
    State('ui_hr2', 'value'),
    State('ui_rest2', 'value'),
    State('ui_com2', 'value'),
    State('int_dict2', 'data'),
    State('h2_input_form', 'children'),
    State('radio_wotype', 'value'),
    State('intrvl_count', 'data')
)
def stage_interval(n_clicks, date, time, dist, split, sr, hr, rest, com, df,head, radio, num_intrvls):
    if n_clicks == 0:
        raise PreventUpdate
    display = {'display':'block'}
    dont_display = {'display':'none'}
    blank_table=dbc.Table.from_dataframe(pd.DataFrame(df), striped=True, bordered=True)
    # check format of inputs
    print('INPUTS: ', date, time, dist, split, sr, hr, rest, file=stderr)
    error_messages = validate_form_inputs(date, time, dist, split, sr, hr, rest)
    if error_messages:
        return head, blank_table, df, error_messages, display, False, dont_display
    # formatting good - populate df   
    df['Date'].append(date)
    df['Time'].append(time)
    df['Distance'].append(dist)
    df['Split'].append(split)
    df['s/m'].append(sr)
    df['HR'].append(hr)
    df['Rest'].append(rest)
    df['Comment'].append(com)
    # df = pd.DataFrame(df)
    num_rows = len(df['Date'])
    complete_alert = display if (num_rows == num_intrvls + 1) else dont_display
    head = choose_title(radio, num_rows)
    return head, dbc.Table.from_dataframe(pd.DataFrame(df), striped=True, bordered=True), df, None, dont_display, True, complete_alert


#Post wo to db 
@callback(
    Output('btn_submit_workout2', 'children'),
    Output('btn_submit_workout2', 'color'),
    Input('btn_submit_workout2', 'n_clicks'),
    State('intrvl_formatting_approved2', 'data'),
    State('int_dict2', 'data'),
    State('user_id', 'data'),
    State('radio_wotype', 'value')
)
def post_wo_to_db(n_clicks, formatting_approved, int_dict, user_id, radio):
    if n_clicks==0 or not formatting_approved:
        raise PreventUpdate
    interval = False
    if radio == 'Intervals':
        interval = True
    wo_dict = generate_post_wo_dict2(int_dict, user_id, EMPTY_POST_WO_DICT, interval)
    print(wo_dict)
    wo_id = post_new_workout(wo_dict)['workout_id']
    idict = format_and_post_intervals(wo_id, int_dict, interval)
    return 'Workout Submitted!', 'success'