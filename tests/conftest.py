import pytest
from ergTrack_api.src.api_ergTrack.app import create_app
from ergTrack_api.src.api_ergTrack.logic import db_connect 
# from ergTrack_api.tests.test_logic import db_connect
import pdb

app = create_app('testing')

@pytest.fixture
def client():
    return app.test_client()

def delete_entry(table,id_col,id):
    try:
        conn, cur = db_connect('testing', True)
        cur.execute(f"DELETE FROM {table} * WHERE {id_col}='{id}' ")
    finally:
        conn.close()
        cur.close()

def clear_test_db():
    try: 
        conn, cur = db_connect('testing', True)
        cur.execute("DELETE FROM interval_log *")
        cur.execute("DELETE FROM workout_log *")
        cur.execute("DELETE FROM users *")
        cur.execute("DELETE FROM team *")
    finally:
        cur.close()
        conn.close()
        
   
def clear_erg_db(cur): 
    try:
        conn, cur = db_connect('testing', True)
        cur.execute("DELETE FROM interval_log *")
        cur.execute("DELETE FROM workout_log *")
        cur.execute("DELETE FROM users *")
        cur.execute("DELETE FROM team *")
    finally:
        cur.close()
        conn.close() 


def delete_test_db():
    conn, cur = db_connect('testing',True)
    cur.execute("""DROP DATABASE "erg_test" """)
    cur.close()
    conn.close()
