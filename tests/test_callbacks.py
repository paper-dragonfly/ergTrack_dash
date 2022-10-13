from tests.conftest import app
from dash_app import app as dash_app
from pages.workout_log import activate_view_details
import cv2
from pages.add_image import extract_ocr, fill_form, EMPTY_INTERVAL_TABLE, post_wo_to_db, stage_interval
from pytest import raises
from dash_fns import flask_client_get as client_get, flask_client_post as client_post, reformat_date
from api_ergTrack.logic import db_connect
import tests.conftest as c
import pdb
from pages.new_user import populate_team_dropdown, display_team_input, set_user_team, submit_user
from dash.exceptions import PreventUpdate

# KEY
# 00 : Not connected to app fn
# 01 : dash_front.py
# 02 : new_user.py
# 03 : add_image.py
# 04 : workout_log.py
# 05 : wo_details.py


def test_00_populate_test_db():
    """
    NOTE: not testing a function
    Add entries to the test db to be used to test all GET functions 
    """
    try:
        conn, cur= db_connect('testing', True)
        cur.execute("INSERT INTO team(team_id,team_name) VALUES (%s,%s),(%s,%s) ON CONFLICT DO NOTHING", (1,'utah crew', 2, 'tumbleweed'))
        cur.execute("INSERT INTO users(user_id, user_name, dob, sex, team) VALUES(%s,%s,%s,%s,%s),(%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING", (1,'kaja','1994-12-20','Female',1,2,'moonshine','1991-01-01','Male',2))
    finally:
        cur.close()
        conn.close()


# new_user.py
def test_021_populate_team_dropdown(client):
    team_list = populate_team_dropdown(['None'], client_get, {'client':client})
    assert team_list == ['utah crew', 'tumbleweed', 'None', 'Other']


def test_022_display_team_input():
    assert display_team_input('Other') == {'display':'block'}
    with raises(PreventUpdate):
        display_team_input('fish')

#post
def test_023_submit_user(client):
    with raises(PreventUpdate):
        submit_user(0,'name','dob','sex','t','p','pa')
    #new user, existing team
  
    output = submit_user(1,'jam','2000-01-01','Female','tumbleweed',client_get, {'client':client}, client_post, {'client':client})
    assert output[0] == 'User Added'
    assert output[3] != 0 #user_id
    # existing user
    output2 = submit_user(1,'jam','2000-01-01','Female','tumbleweed',client_get, {'client':client},client_post, {'client':client})
    assert output2[0] == 'Submit User'
    assert output2[2] == {'display':'block'} #alert - user_name taken
    assert output2[3] == 0 #user_id
    # new user, new team 
    output3 = submit_user(1,'falcon','2000-01-01','Female','newteam',client_get, {'client':client},client_post, {'client':client})
    assert output3[0] == 'User Added'
    assert output3[3] != 0 


## PAGE: add_image.py 

def test_031_upload_image():
    pass #not sure how to write a test for this


def test_032_convert_to_cv2_compatible():
    pass # not sure how to start with b64 img

def test_033_extract_ocr():
    """
    GIVEN a cv2 compatible image
    ASSERT fn returns dict
    """
    filepath = '/Users/katcha/NiCode_Academy/ErgApp/apps/web/tests/test_erg01.jpg'
    img = cv2.imread(filepath)
    ocr_output = extract_ocr(img)
    assert type(ocr_output) == dict

OCR_RESULT_ERG01 = {'wo': ['4'], 'date': 'soy 19 2021', 'summary': ['h00.0', '1048', '1545', '21'], 'time': ['L000', '2:00.0', 'B00.0', '4.00.0'], 'dist': ['263', '263', '258', '26u'], 'split': ['1:51.5', '1:54.0', '1:56.2', '1:55.3'], 'sr': ['31', '30', '31']}

def test_034_fill_form_wo_summary():
    """
    GIVEN a raw_ocr dict
    CONFIRM error is raised if no raw_ocr
    ASSERT form is filled with summary data as expected when img initially uploaded
    CONFIRM PreventUpdate raised (form not populated with next interval) if formatting is incorrect
    GIVEN a 'submit interval' click AND properly formatted form
    ASSERT form filled with next interval
    """
    raw_ocr = OCR_RESULT_ERG01
    with raises(PreventUpdate):
        fill_form(None, 0, 'f', 'r', 'd','df')
    output = fill_form(raw_ocr, 0, False, 'Single Time/Distance', None, EMPTY_INTERVAL_TABLE ) 
    assert output == (raw_ocr['date'], raw_ocr['summary'][0], raw_ocr['summary'][1], raw_ocr['summary'][2], raw_ocr['summary'][3], 'n/a', 'n/a', 4)
    with raises(PreventUpdate):
        fill_form(raw_ocr, 1, False, 'r', 'd','df')
    output = fill_form(raw_ocr, 1, True, 'r','2000-01-01',{'Time':[1]})
    assert output == ('2000-01-01', 'L000', '263', '1:51.5', '31', 'n/a', 'n/a', 4)


def test_035_stage_interval():
    """
    GIVEN 'Submit Interval' btn is clicked 
    IF form formatting correct 
    ASSERT df is as expected AND alert not displayed
    IF formatting incorrect
    ASSERT returns error messages
    """
    output = stage_interval(1, 'Jan 01 2000', '4:00.0', '1048', '1:54.5', '22','n/a','n/a','4min',EMPTY_INTERVAL_TABLE, 'Title', 'single',4)
    assert output[2] == {'Date':['Jan 01 2000'], 'Time':['4:00.0'],'Distance':['1048'], 'Split': ['1:54.5'], 's/m':['22'],'HR':['n/a'],'Rest':['n/a'], 'Comment':['4min']}
    assert output[3] == None #alert message
    assert output[5] == True # Formatting correct
    # Formatting incorrect 
    output=stage_interval(1, 'fire 01 2000', '4:000', '1048d', '1:54.45', '22','n/a','n/a','4min',EMPTY_INTERVAL_TABLE, 'Title', 'single',4)
    assert output[5] == False 
    assert output[3] == ['Date formatting error: date length incorrect','Time formatting error: must use hh:mm:ss.d formatting','Distance formatting error','Split formatting error: must use m:ss.d formatting']


def test_036_post_wo_to_db(mocker):
    """
    GIVEN 'Submit Workout' btn is clicked 
    IF formatting approved 
    ASSERT returns expected
    IF btn not yet clicked OR formatting wrong
    CONFIRM raises error 
    """
    mocker.patch('pages.add_image.generate_post_wo_dict2', return_value={})
    mocker.patch('pages.add_image.post_new_workout', return_value={'workout_id':0})
    mocker.patch('pages.add_image.format_and_post_intervals', return_value=None)
    assert post_wo_to_db(1,True,{}, 0, 'Intervals') == ('Workout Submitted!', 'success')
    with raises(PreventUpdate):
        assert post_wo_to_db(0,True,{},0,'Intervals')
        assert post_wo_to_db(1,False,{},0,'Intervals')
    
def test_041_display_username():
    """
    WHEN user_id passed to fn
    ASSERT returns capitalized user_names"""
    pass #skip - simple

def test_042_activate_view_details():
    """
    WHEN user selects a single row
    ASSERT btn changes to become link to view detials of that wo
    WHEN user selects no rows or >1 rows 
    ASSERT btn remains in original form 
    """
    assert activate_view_details([1])[1]=='warning'
    assert activate_view_details([])[1] == 'secondary'
    assert activate_view_details([1,2])[1] == 'secondary'
     

def test_043_show_compare_btn():
    """
    GIVEN a number of selected rows
    IF num_selected >= 2 
    ASSERT compare_workouts btn visible 
    IF num_selected < 2
    ASSERT compare_workouts btn invisible"""
    pass # skip - simple

def test_044_make_graph():
    pass # skip - need to work on graph

def test_clear_testdb():
    c.clear_test_db()

        
