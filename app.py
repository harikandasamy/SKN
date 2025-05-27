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
    defaults = {
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
        'twofactor': "",
        'status': 0,
        'search_term': ""
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

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
        while cursor.nextset():
            pass
        conn.commit()
        if result is None:
            return (1, "No data returned from validation", 0)
        return (result[0], result[1], result[2])
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
        conn.commit()

        if callno in [2, 4, 7]:
            columns = [column[0] for column in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return results
        else:
            return [{"status": 0, "msg": "Operation completed successfully"}]
    except Exception as e:
        return [{"status": 1, "msg": f"Database error: {str(e)}"}]
    finally:
        conn.close()

# Streamlit UI Setup
st.set_page_config(page_title="Show SKN Data", layout="wide")
st.markdown("""
<style>
.stButton>button {
    background-color: blue;
    border: 1px solid blue;
    color: white;
    padding: 10px 24px;
    cursor: pointer;
    width: 100%;
    margin: 5px 0;
}
.stButton>button:hover {
    background-color: #3e8e41;
}
.stTextInput>div>div>input {
    padding: 10px;
}
.stSelectbox>div>div>select {
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("Show SKN Data")

# Inputs outside any form
st.text_input("Enter credentials", key="search_term")
st.text_input("Two Factor", key="twofactor")

result_div = st.empty()

# Main Processing Function
def process_request(callno, types=None):
    user_id = 19
    search_term_val = st.session_state.get("search_term", "")
    try:
        twofactor_val = st.session_state.get("twofactor", "0")
    except ValueError:
        twofactor_val = "0"   
    
    result_div.success(twofactor_val)

    #msg, status_code, code = validate_user(user_id, search_term_val, twofactor_val)

    if status_code <= 2:
        return msg, status_code, code

    return execute_stored_procedure(callno, types)

# Users Section
st.markdown("---")
st.header("Users Management")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Populate Users", key="btnUsers"):
        result = process_request(2)
        st.write(result)
