import streamlit as st
import pyodbc
from datetime import datetime
import pytz
import uuid

# Database Configuration
SERVER = "P3NWPLSK12SQL-v06.shr.prod.phx3.secureserver.net"
DATABASE = "SKNFSPROD"
USERNAME = "SKNFSPROD"
PASSWORD = "Password2011@"

# Initialize session state with unique keys
def init_session_state():
    session_keys = {
        'userdata': "",
        'populateusers': 0,
        'updateusers': 0,
        'updateusrname': "",
        'recipt': 0,
        'receiptrevert': 0,
        'paymentdata': "",
        'paymentstable': 0,
        'selected_user': "",
        'selected_payment': "",
        'selected_payment_no': "",
        'twofactor': "-1",
        'search_term': "",
        'form_submitted': False,
        'debug_mode': False
    }
    
    for key, default in session_keys.items():
        if key not in st.session_state:
            st.session_state[key] = default

init_session_state()

# Database Connection
def open_connection():
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={SERVER};"
            f"DATABASE={DATABASE};"
            f"UID={USERNAME};"
            f"PWD={PASSWORD};"
        )
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        return None

# User Validation
def validate_user(user_id, username, factor_code):
    conn = open_connection()
    if not conn:
        return (1, "Database connection error", 0)
    
    try:
        cursor = conn.cursor()
        cursor.execute("{CALL P_ValidateWebUser (?, ?, ?)}", (user_id, username, factor_code))
        result = cursor.fetchone()
        return (result.status, result.msg, result.code) if result else (1, "No data returned", 0)
    except Exception as e:
        return (1, f"Validation error: {str(e)}", 0)
    finally:
        conn.close()

# Database Operations
def execute_stored_procedure(callno, params=None):
    conn = open_connection()
    if not conn:
        return [{"status": 1, "msg": "Database connection failed"}]
    
    try:
        cursor = conn.cursor()
        
        if callno == 2:
            cursor.execute("{CALL P_GetAllowedAmtPerGrams}")
        elif callno == 3:
            cursor.execute("{CALL P_UpdateAllowedAmtPerGrams (?, ?, ?, ?, ?, ?, ?, ?, ?)}", params)
        elif callno == 4:
            cursor.execute("{CALL P_GetRcptDetailsforWebsite (?, ?)}", params)
        elif callno == 5:
            cursor.execute("{CALL P_AddPenalty (?, ?, ?, ?, ?, ?)}", params)
        elif callno == 6:
            cursor.execute("{CALL P_GetUpdatePenaltyRemoval (?, ?, ?, ?, ?, ?)}", params)
        elif callno == 7:
            cursor.execute("{CALL P_GetMortgagePaymentsHistory (?, ?, ?)}", params)
        elif callno == 8:
            cursor.execute("{CALL P_MortgageRevert (?, ?, ?, ?, ?)}", params)
        
        if callno in [2, 4, 7]:
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            return [{"status": 0, "msg": "Operation completed successfully"}]
    except Exception as e:
        return [{"status": 1, "msg": f"Database error: {str(e)}"}]
    finally:
        conn.close()

# Main Processing Function
def process_request(callno, types=None):
    user_id = 19
    search_term_val = st.session_state.search_term
    twofactor_val = st.session_state.twofactor

    if not twofactor_val or twofactor_val == "-1":
        return [{"status": 1, "msg": "Two-factor code is required"}]
    
    status, msg, code = validate_user(user_id, search_term_val, twofactor_val)
    if status <= 2:
        return [{"status": status, "msg": msg}]
    
    eastern = pytz.timezone('America/New_York')
    current_dt = datetime.now(eastern).strftime('%Y-%m-%d %H:%M:%S')
    
    params_map = {
        3: (
            st.session_state.get("Amountgramperiod", 0),
            st.session_state.get("Amountpergram", 0),
            st.session_state.get("AssessedValue", 0),
            st.session_state.get("MaxAllowed", 0),
            st.session_state.get("Three_Mth_Rate", 0),
            st.session_state.get("Mortgagegram", 0),
            st.session_state.get("Mortgagemonths", 0),
            current_dt,
            st.session_state.get("UserID", 0)
        ),
        4: (st.session_state.get("searchreceipt", ""), user_id),
        5: (types, st.session_state.get("searchreceipt", ""), 
            st.session_state.get("selected_payment_no", ""), user_id, 0, current_dt),
        6: (user_id, 0, st.session_state.get("searchreceipt", ""),
            st.session_state.get("selected_payment_no", ""), current_dt, types),
        7: (user_id, 0, st.session_state.get("searchreceipt", "")),
        8: (user_id, 0, st.session_state.get("searchreceipt", ""), current_dt,
            st.session_state.get("selected_payment", 0))
    }
    
    return execute_stored_procedure(callno, params_map.get(callno))

# Streamlit UI Setup
st.set_page_config(page_title="Show SKN Data", layout="wide")

# Main container
main_container = st.container()
with main_container:
    st.title("Show SKN Data")
    
    # Credentials Form
    with st.form(key=f"cred_form_{uuid.uuid4()}"):
        st.text_input("Enter credentials", key=f"cred_input_{uuid.uuid4()}")
        twofactor = st.number_input(
            "Two Factor Code",
            key=f"twofactor_{uuid.uuid4()}",
            min_value=0,
            step=1,
            format="%d"
        )
        submit = st.form_submit_button("Submit", key=f"submit_{uuid.uuid4()}")
        
        if submit:
            st.session_state.search_term = st.session_state[f"cred_input_{list(st.session_state.keys())[-3]}"]
            st.session_state.twofactor = str(twofactor)
            st.session_state.form_submitted = True
            st.success("Credentials submitted!")

    # Users Management
    st.markdown("---")
    st.header("Users Management")

    cols = st.columns(3)
    with cols[0]:
        if st.button("Populate Users", key=f"populate_{uuid.uuid4()}"):
            if not st.session_state.form_submitted:
                st.error("Please submit credentials first")
            else:
                result = process_request(2)
                if result and result[0].get("status", 1) == 0:
                    st.session_state.userdata = result
                    st.session_state.populateusers = 1
                    st.success("Users populated successfully")
                else:
                    error_msg = result[0].get('msg', 'Unknown error') if result else "No result returned"
                    st.error(f"Error: {error_msg}")

    # Debug Section
    st.sidebar.checkbox("Debug Mode", key="debug_mode")
    if st.session_state.debug_mode:
        with st.expander("Debug Information"):
            st.write("Session State:", st.session_state)
            st.write("Database Connection:", "Active" if open_connection() else "Inactive")
