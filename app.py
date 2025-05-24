import streamlit as st
import pyodbc
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from datetime import datetime
import pytz
import pandas as pd

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
    if 'updateusers' not in st.session_state:
        st.session_state.updateusers = 0
    if 'updateusrname' not in st.session_state:
        st.session_state.updateusrname = ""
    if 'recipt' not in st.session_state:
        st.session_state.recipt = 0
    if 'receiptrevert' not in st.session_state:
        st.session_state.receiptrevert = 0
    if 'paymentdata' not in st.session_state:
        st.session_state.paymentdata = ""
    if 'paymentstable' not in st.session_state:
        st.session_state.paymentstable = 0
    if 'selected_user' not in st.session_state:
        st.session_state.selected_user = ""
    if 'selected_payment' not in st.session_state:
        st.session_state.selected_payment = ""
    if 'selected_payment_no' not in st.session_state:
        st.session_state.selected_payment_no = ""
    if 'two_factor' not in st.session_state:
        st.session_state.two_factor = -1
    if 'status' not in st.session_state:
        st.session_state.status = 0

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
        


        cursor.execute(
        """DECLARE @status INT, @msg VARCHAR(100), @code INT;
        EXEC P_ValidateWebUser ?, ?, ?, @status OUTPUT, @msg OUTPUT, @code OUTPUT;
        SELECT  @msg AS msg, @status AS status, @code AS code""",
        (user_id, username, factor_code)
        )
        result = cursor.fetchone()
        if result:
            st.session_state.status = result.status
            st.session_state.two_factor = result.code
            return True    

        result_div.success(st.session_state.two_factor)
        
        if result:
            return (result.status, result.msg, result.code)
        else:
            return (1, "No data returned from validation", 0)
    except Exception as e:
        return (1, f"Validation error: {str(e)}", 0)
        result_div.success("Why am I here?")
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
            conn.commit()  # Explicit commit   
        elif callno == 3:
            cursor.execute(
                "{CALL P_UpdateAllowedAmtPerGrams (?, ?, ?, ?, ?, ?, ?, ?, ?)}",
                params
            )
            conn.commit()  # Explicit commit   
        elif callno == 4:
            cursor.execute(
                "{CALL P_GetRcptDetailsforWebsite (?, ?)}",
                params
            )
            conn.commit()  # Explicit commit   
        elif callno == 5:
            cursor.execute(
                "{CALL P_AddPenalty (?, ?, ?, ?, ?, ?)}",
                params
            )
            conn.commit()  # Explicit commit   
        elif callno == 6:
            cursor.execute(
                "{CALL P_GetUpdatePenaltyRemoval (?, ?, ?, ?, ?, ?)}",
                params
            )
            conn.commit()  # Explicit commit   
        elif callno == 7:
            cursor.execute(
                "{CALL P_GetMortgagePaymentsHistory (?, ?, ?)}",
                params
            )
            conn.commit()  # Explicit commit   
        elif callno == 8:
            cursor.execute(
                "{CALL P_MortgageRevert (?, ?, ?, ?, ?)}",
                params
            )
            conn.commit()  # Explicit commit   
        
        if callno in [2, 4, 7]:
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results
        else:
            return [{"status": 0, "msg": "Operation completed successfully"}]
            
    except Exception as e:
        return [{"status": 1, "msg": f"Database error: {str(e)}"}]
    finally:
        conn.close()

# Streamlit UI Setup
st.set_page_config(
    page_title="Show SKN Data",
    layout="wide"
)


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

# Credentials Form
with st.form("credentials_form"):
    search_term = st.text_input("Enter credentials", key="search_term")
    twofactor = st.text_input("Two Factor", key="twofactor")
    submitted = st.form_submit_button("Submit")
    status, msg, code = validate_user(19, "", -1)


result_div = st.empty()

# Main Processing Function
def process_request(callno, types=None):
       
    # Validate user
    user_id = 19  # Hardcoded as in PHP code
    search_term_val = st.session_state.get("search_term", "")
    twofactor_val = st.session_state.get("twofactor", -1)
   
    status, msg, code = validate_user(user_id, "webadmin", -1)

    result_div.success(code)
    
    if status <= 2:
        if status == 1:
            return [{"status": status, "code": code, "msg": msg}]
        else:
            return [{"status": status, "code": code, "msg": msg}]
    
    # Get current datetime in Eastern time
    eastern = pytz.timezone('America/New_York')
    current_dt = datetime.now(eastern).strftime('%Y-%m-%d %H:%M:%S')

    #allow calling only if status code >= 3

    if  st.session_state.status >= 3:
    
        # Prepare parameters based on callno
        params = None
        if callno == 3:
            params = (
                st.session_state.get("Amountgramperiod", 0),
                st.session_state.get("Amountpergram", 0),
                st.session_state.get("AssessedValue", 0),
                st.session_state.get("MaxAllowed", 0),
                st.session_state.get("Three_Mth_Rate", 0),
                st.session_state.get("Mortgagegram", 0),
                st.session_state.get("Mortgagemonths", 0),
                current_dt,
                st.session_state.get("UserID", 0)
            )
        elif callno == 4:
            params = (
                st.session_state.get("searchreceipt", ""),
                user_id
            )
        elif callno == 5:
            params = (
                types,
                st.session_state.get("searchreceipt", ""),
                st.session_state.get("selected_payment_no", ""),
                user_id,
                0,  # storeid
                current_dt
            )
        elif callno == 6:
            params = (
                user_id,
                0,  # storeid
                st.session_state.get("searchreceipt", ""),
                st.session_state.get("selected_payment_no", ""),
                current_dt,
                types
            )
        elif callno == 7:
            params = (
                user_id,
                0,  # storeid
                st.session_state.get("searchreceipt", "")
            )
        elif callno == 8:
            params = (
                user_id,
                0,  # storeid
                st.session_state.get("searchreceipt", ""),
                current_dt,
                st.session_state.get("selected_payment", 0)
            )
        
        return execute_stored_procedure(callno, params)

# Users Section
st.markdown("---")
st.header("Users Management")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Populate Users", key="btnUsers"):
        result = process_request(2)
    
       
