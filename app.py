import streamlit as st
import pyodbc  # For SQL Server connection
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from datetime import datetime
import pytz

# Database Configuration
SERVER = "sknfsprodazure.database.windows.net"
DATABASE = "sknfsprodazure"
USERNAME = "sknfsprodazure"
PASSWORD = "Password2025@"

# Email Configuration
EMAIL_HOST = 'p3nwvpweb1002.shr.prod.phx3.secureserver.net'
EMAIL_USERNAME = 'database@sknfinancial.com'
EMAIL_PASSWORD = 'sknskn'
EMAIL_PORT = 587

# State variables
if 'userdata' not in st.session_state:
    st.session_state.userdata = None
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
    st.session_state.paymentdata = None
if 'paymentstable' not in st.session_state:
    st.session_state.paymentstable = 0

# Database Connection
def open_connection():
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={SERVER};"
            f"DATABASE={DATABASE};"
            f"UID={USERNAME};"
            f"PWD={PASSWORD};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=30;"
        )
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        return None

# Email Function
def send_email():
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USERNAME
        msg['Subject'] = "Enquiry for tour and travels package"
        msg['Cc'] = EMAIL_USERNAME
        
        # Add message body if needed
        # msg.attach(MIMEText("Your message here", 'plain'))
        
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(msg)
        
        return "Message sent!"
    except Exception as e:
        return f"Error sending email: {str(e)}"

# User Validation
def validate_user(user_id, username, factor_code):
    conn = open_connection()
    if not conn:
        return (1, "Database connection error", 0)
    
    try:
        cursor = conn.cursor()
        cursor.execute("{CALL P_ValidateWebUser (?, ?, ?)}", (user_id, username, factor_code))
        
        result = cursor.fetchone()
        if result:
            return (result.status, result.msg, result.code)
        else:
            return (1, "No data returned from validation", 0)
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
            cursor.execute(
                "{CALL P_UpdateAllowedAmtPerGrams (?, ?, ?, ?, ?, ?, ?, ?, ?)}",
                params
            )
        elif callno == 4:
            cursor.execute(
                "{CALL P_GetRcptDetailsforWebsite (?, ?)}",
                params
            )
        elif callno == 5:
            cursor.execute(
                "{CALL P_AddPenalty (?, ?, ?, ?, ?, ?)}",
                params
            )
        elif callno == 6:
            cursor.execute(
                "{CALL P_GetUpdatePenaltyRemoval (?, ?, ?, ?, ?, ?)}",
                params
            )
        elif callno == 7:
            cursor.execute(
                "{CALL P_GetMortgagePaymentsHistory (?, ?, ?)}",
                params
            )
        elif callno == 8:
            cursor.execute(
                "{CALL P_MortgageRevert (?, ?, ?, ?, ?)}",
                params
            )
        
        # Fetch all rows if it's a SELECT procedure
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
    width: 10%;
}
.stButton>button:hover {
    background-color: #3e8e41;
}
</style>
""", unsafe_allow_html=True)

st.title("Show SKN Data")

# Credentials Form
with st.form("credentials_form"):
    search_term = st.text_input("Enter credentials", key="search_term")
    twofactor = st.text_input("Two Factor", key="twofactor")
    submitted = st.form_submit_button("Submit")

result_div = st.empty()

# Main Processing Function
def process_request(callno, types=None):
    # First send email notification
    email_result = send_email()
    if "error" in email_result.lower():
        return [{"status": 1, "msg": email_result}]
    
    # Validate user
    user_id = 19  # Hardcoded as in PHP code
    search_term_val = st.session_state.get("search_term", "")
    twofactor_val = st.session_state.get("twofactor", -1)
    
    status, msg, code = validate_user(user_id, search_term_val, twofactor_val)
    
    if status <= 2:
        if status == 1:
            return [{"status": status, "msg": code}]
        else:
            return [{"status": status, "msg": msg}]
    
    # Get current datetime in Eastern time
    eastern = pytz.timezone('America/New_York')
    current_dt = datetime.now(eastern).strftime('%Y-%m-%d %H:%M:%S')
    
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
            st.session_state.get("receiptno", ""),
            user_id
        )
    elif callno == 5:
        params = (
            types,
            st.session_state.get("receiptno", ""),
            st.session_state.get("paymentno", ""),
            user_id,
            0,  # storeid
            current_dt
        )
    elif callno == 6:
        params = (
            user_id,
            0,  # storeid
            st.session_state.get("receiptno", ""),
            st.session_state.get("paymentno", ""),
            current_dt,
            st.session_state.get("type", "")
        )
    elif callno == 7:
        params = (
            user_id,
            0,  # storeid
            st.session_state.get("receiptno", "")
        )
    elif callno == 8:
        params = (
            user_id,
            0,  # storeid
            st.session_state.get("receiptno", ""),
            current_dt,
            st.session_state.get("idrevert", 0)
        )
    
    # Execute the stored procedure
    return execute_stored_procedure(callno, params)

# UI Components and Event Handlers
if submitted:
    result = process_request(2)  # Default call for validation
    result_div.json(result)

# Add other UI components and handlers from the previous conversion
# (Users section, Receipt section, Payments section, etc.)
# These would be the same as in the previous conversion

# Example of how to handle a button click:
if st.button("Populate Users"):
    result = process_request(2)
    if result and result[0].get("status", 1) == 0:
        st.session_state.userdata = result  # Store the user data
        st.session_state.populateusers = 1
        result_div.success("Users populated successfully")
    else:
        result_div.error(f"Error: {result[0].get('msg', 'Unknown error')}")

# Note: You would need to add similar handlers for all the other buttons
# and functionality from your original HTML/JavaScript code
