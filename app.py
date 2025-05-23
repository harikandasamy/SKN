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

# Email Configuration
EMAIL_HOST = 'p3nwvpweb1002.shr.prod.phx3.secureserver.net'
EMAIL_USERNAME = 'database@sknfinancial.com'
EMAIL_PASSWORD = 'sknskn'
EMAIL_PORT = 587

# Initialize session state
def init_session_state():
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
    if 'selected_user' not in st.session_state:
        st.session_state.selected_user = None
    if 'selected_payment' not in st.session_state:
        st.session_state.selected_payment = None
    if 'selected_payment_no' not in st.session_state:
        st.session_state.selected_payment_no = None

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
        if result and result[0].get("status", 1) == 0:
            st.session_state.userdata = result
            st.session_state.populateusers = 1
            result_div.success("Users populated successfully")
        else:
            result_div.error(f"Error: {result[0].get('msg', 'Unknown error')}")

with col2:
    if st.button("Update Users", key="btnSaveUsers"):
        if st.session_state.populateusers == 1 and st.session_state.updateusers == 0:
            if st.session_state.selected_user:
                st.session_state.updateusers = 1
                result_div.success(f"User {st.session_state.selected_user} selected for update")
            else:
                result_div.error("Please select a user first")
        elif st.session_state.updateusers == 1:
            st.session_state.updateusers = 2
            result_div.warning(f"Confirm update for {st.session_state.selected_user}")
        elif st.session_state.updateusers == 2:
            # Get current datetime in Eastern time
            eastern = pytz.timezone('America/New_York')
            current_dt = datetime.now(eastern).strftime('%Y-%m-%d %H:%M:%S')
            
            # Here you would collect the updated values from the user table
            # For demonstration, using placeholder values
            params = (
                100,  # Amountgramperiod
                50,   # Amountpergram
                5000,  # AssessedValue
                10000, # MaxAllowed
                3.5,   # Three_Mth_Rate
                200,   # Mortgagegram
                12,    # Mortgagemonths
                current_dt,
                st.session_state.selected_user_id
            )
            
            result = process_request(3, params)
            if result and result[0].get("status", 1) == 0:
                result_div.success(f"User {st.session_state.selected_user} updated successfully")
                st.session_state.updateusers = 0
                st.session_state.selected_user = None
            else:
                result_div.error(f"Error: {result[0].get('msg', 'Unknown error')}")

with col3:
    if st.button("Revert Users", key="btnRevertUpdateUsers"):
        st.session_state.userdata = None
        st.session_state.populateusers = 0
        st.session_state.updateusers = 0
        st.session_state.updateusrname = ""
        st.session_state.selected_user = None
        result_div.info("User data cleared")

# Users Dropdown
if st.session_state.populateusers == 1 and st.session_state.userdata:
    user_options = [user['UserName'] for user in st.session_state.userdata]
    selected_user = st.selectbox("Select User", options=user_options, key="ddlUsers")
    st.session_state.selected_user = selected_user
    st.session_state.selected_user_id = next(
        user['UserID'] for user in st.session_state.userdata 
        if user['UserName'] == selected_user
    )

# User Table
if st.session_state.populateusers == 1 and st.session_state.userdata and st.session_state.selected_user:
    user_data = next(
        user for user in st.session_state.userdata 
        if user['UserName'] == st.session_state.selected_user
    )
    
    # Create editable dataframe
    editable_fields = ['Amountgramperiod', 'Amountpergram', 'MaxAllowed', 
                      'AssessedValue', 'Three_Mth_Rate', 'Mortgagegram', 'Mortgagemonths']
    user_df = pd.DataFrame([{k: user_data.get(k, '') for k in editable_fields}])
    
    edited_df = st.data_editor(
        user_df,
        hide_index=True,
        use_container_width=True,
        key="user_table_editor"
    )
    
    # Store edited values in session state
    for field in editable_fields:
        st.session_state[field] = edited_df[field].iloc[0]

# Receipt Section
st.markdown("---")
st.header("Receipt Management")

searchreceipt = st.text_input("ReceiptNo", key="searchreceipt")

col4, col5, col6 = st.columns(3)
with col4:
    if st.button("Search PaymentNo", key="btnSearchReceipt"):
        if not st.session_state.searchreceipt:
            result_div.error("Please enter a Receipt no to search")
        else:
            result = process_request(4)
            if result and result[0].get("status", 1) == 0:
                st.session_state.payment_numbers = result[0].get("paymentnos", "").split(';')
                st.session_state.receiptrevert = 1
                result_div.success("Payment numbers populated")
            else:
                result_div.error(f"Error: {result[0].get('msg', 'Unknown error')}")

with col5:
    if st.session_state.get('payment_numbers'):
        selected_payment_no = st.selectbox(
            "PaymentNo", 
            options=st.session_state.payment_numbers, 
            key="ddlPaymentNo"
        )
        st.session_state.selected_payment_no = selected_payment_no

with col6:
    if st.button("Revert", key="btnRevertReceipt"):
        st.session_state.receiptrevert = 0
        st.session_state.recipt = 0
        st.session_state.searchreceipt = ""
        st.session_state.payment_numbers = None
        st.session_state.selected_payment_no = None
        result_div.info("Receipt data cleared")

# Penalty/NSF Section
st.markdown("---")
st.header("Penalty/NSF Management")

col7, col8, col9, col10 = st.columns(4)
with col7:
    if st.button("Add Penalty", key="btnAddPenalty"):
        if not st.session_state.searchreceipt:
            result_div.error("Please enter a Receipt no first")
        elif not st.session_state.selected_payment_no:
            result_div.error("Please select a Payment No first")
        else:
            result = process_request(5, 1)  # 1 for Penalty
            if result and result[0].get("status", 1) == 0:
                result_div.success("Penalty added successfully")
            else:
                result_div.error(f"Error: {result[0].get('msg', 'Unknown error')}")

with col8:
    if st.button("Add NSF", key="btnAddNSF"):
        if not st.session_state.searchreceipt:
            result_div.error("Please enter a Receipt no first")
        elif not st.session_state.selected_payment_no:
            result_div.error("Please select a Payment No first")
        else:
            result = process_request(5, 2)  # 2 for NSF
            if result and result[0].get("status", 1) == 0:
                result_div.success("NSF added successfully")
            else:
                result_div.error(f"Error: {result[0].get('msg', 'Unknown error')}")

with col9:
    if st.button("Remove Penalty", key="btnRemovePenalty"):
        if not st.session_state.searchreceipt:
            result_div.error("Please enter a Receipt no first")
        elif not st.session_state.selected_payment_no:
            result_div.error("Please select a Payment No first")
        else:
            result = process_request(6, "Penalty")
            if result and result[0].get("status", 1) == 0:
                result_div.success("Penalty removed successfully")
            else:
                result_div.error(f"Error: {result[0].get('msg', 'Unknown error')}")

with col10:
    if st.button("Remove NSF", key="btnRemoveNSF"):
        if not st.session_state.searchreceipt:
            result_div.error("Please enter a Receipt no first")
        elif not st.session_state.selected_payment_no:
            result_div.error("Please select a Payment No first")
        else:
            result = process_request(6, "NSF")
            if result and result[0].get("status", 1) == 0:
                result_div.success("NSF removed successfully")
            else:
                result_div.error(f"Error: {result[0].get('msg', 'Unknown error')}")

# Payments Section
st.markdown("---")
st.header("Payments Management")

col11, col12, col13 = st.columns(3)
with col11:
    if st.button("List Payments", key="btnListPayments"):
        if not st.session_state.searchreceipt:
            result_div.error("Please enter a Receipt no first")
        else:
            result = process_request(7)
            if result and result[0].get("status", 1) == 0:
                st.session_state.paymentdata = result
                st.session_state.paymentstable = 1
                result_div.success("Payments listed successfully")
            else:
                result_div.error(f"Error: {result[0].get('msg', 'Unknown error')}")

with col12:
    if st.button("Remove Payments", key="btnRemovePayments"):
        if st.session_state.paymentstable == 0:
            result_div.error("Payments are not populated")
        elif not st.session_state.selected_payment:
            result_div.error("Please select a Payment first")
        elif st.session_state.paymentstable == 1:
            st.session_state.paymentstable = 2
            result_div.warning(f"Confirm removal of payment {st.session_state.selected_payment}")
        elif st.session_state.paymentstable == 2:
            result = process_request(8)
            if result and result[0].get("status", 1) == 0:
                result_div.success("Payment removed successfully")
                st.session_state.paymentstable = 0
                st.session_state.paymentdata = None
                st.session_state.selected_payment = None
            else:
                result_div.error(f"Error: {result[0].get('msg', 'Unknown error')}")

with col13:
    if st.button("Revert", key="btnRevertPayments"):
        st.session_state.receiptrevert = 0
        st.session_state.recipt = 0
        st.session_state.paymentstable = 0
        st.session_state.searchreceipt = ""
        st.session_state.paymentdata = None
        st.session_state.selected_payment = None
        result_div.info("Payments data cleared")

# Payments Dropdown and Table
if st.session_state.paymentstable == 1 and st.session_state.paymentdata:
    payment_options = [
        f"{payment['PaymentDt']} {payment['Source']} {payment['TotalPaid']}" 
        for payment in st.session_state.paymentdata
    ]
    selected_payment = st.selectbox(
        "Payments", 
        options=payment_options, 
        key="ddlPayments"
    )
    st.session_state.selected_payment = next(
        payment['PaymentID'] for payment in st.session_state.paymentdata 
        if f"{payment['PaymentDt']} {payment['Source']} {payment['TotalPaid']}" == selected_payment
    )
    
    # Display payments table
    st.dataframe(
        pd.DataFrame(st.session_state.paymentdata),
        use_container_width=True,
        hide_index=True
    )
