import streamlit as st
import pyodbc
from datetime import datetime
import pytz

# Database Configuration
SERVER = "P3NWPLSK12SQL-v06.shr.prod.phx3.secureserver.net"
DATABASE = "SKNFSPROD"
USERNAME = "SKNFSPROD"
PASSWORD = "Password2011@"

# Initialize session state
def init_session_state():
    if 'userdata' not in st.session_state:
        st.session_state.userdata = ""
    if 'populateusers' not in st.session_state:
        st.session_state.populateusers = 0
    if 'twofactor' not in st.session_state:
        st.session_state.twofactor = "-1"
    if 'search_term' not in st.session_state:
        st.session_state.search_term = ""
    if 'form_submitted' not in st.session_state:
        st.session_state.form_submitted = False

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
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            # Add other procedure calls as needed
            return [{"status": 0, "msg": "Operation completed successfully"}]
    except Exception as e:
        return [{"status": 1, "msg": f"Database error: {str(e)}"}]
    finally:
        conn.close()

# Streamlit UI
st.set_page_config(page_title="Show SKN Data", layout="wide")

# Main container
with st.container():
    st.title("Show SKN Data")
    
    # Credentials Form with proper submit button
    with st.form(key="credentials_form"):
        search_term = st.text_input("Enter credentials", key="search_term_input")
        twofactor_input = st.number_input(
            "Two Factor Code",
            min_value=0,
            step=1,
            format="%d",
            key="twofactor_input"
        )
        
        # Proper form submit button
        submitted = st.form_submit_button("Submit Credentials")
        
        if submitted:
            st.session_state.search_term = search_term
            st.session_state.twofactor = str(twofactor_input)
            st.session_state.form_submitted = True
            st.success("Credentials submitted successfully!")

    # Users Management Section
    st.markdown("---")
    st.header("Users Management")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Populate Users", key="populate_users_btn"):
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
    
    return execute_stored_procedure(callno)

# Debug section
if st.checkbox("Show Debug Information"):
    st.write("Session State:", st.session_state)
