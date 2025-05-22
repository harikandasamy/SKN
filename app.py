import streamlit as st
import pyodbc  # For SQL Server connection
import pandas as pd
from datetime import datetime
import json
import smtplib
from email.mime.text import MIMEText
import urllib
from urllib.parse import quote_plus  # Import the specific function needed
import sqlalchemy
from sqlalchemy import create_engine  # Alternative method

# Page configuration
st.set_page_config(page_title="SKN Data Management", layout="wide")

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'two_factor' not in st.session_state:
    st.session_state.two_factor = ""
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'payment_data' not in st.session_state:
    st.session_state.payment_data = None

# Database connection function
def open_connection():
    try:        
        server = 'tcp:sknfsprodazure.database.windows.net,1433'
        database = 'sknfsprodazure_final'
        username = 'sknfsprodazure'
        password = 'Password2025@'
        
        params = urllib.parse.quote_plus(
            f"DRIVER=ODBC Driver 17 for SQL Server;"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=30;"
        )
        
        engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
        return engine.connect()

        
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return None

# Authentication function
def validate_user(credentials, two_factor):
    conn = open_connection()
    if not conn:
        return (1, "Database connection error", "")
    
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC P_ValidateWebUser @userID=?, @username=?, @factorcode=?", 
                       (19, credentials, two_factor))
        
        result = cursor.fetchone()
        if result:
            return (result.status, result.msg, result.code)
        else:
            return (1, "Authentication failed", "")
    except Exception as e:
        return (1, f"Authentication error: {str(e)}", "")
    finally:
        conn.close()

# Data retrieval functions
def get_allowed_amt_per_grams():
    conn = open_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC P_GetAllowedAmtPerGrams")
        columns = [column[0] for column in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return data
    except Exception as e:
        st.error(f"Error retrieving user data: {str(e)}")
        return None
    finally:
        conn.close()

def get_rcpt_details(receipt_no):
    conn = open_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC P_GetRcptDetailsforWebsite @s_search=?, @l_userID=?", 
                      (receipt_no, 19))
        columns = [column[0] for column in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return data
    except Exception as e:
        st.error(f"Error retrieving receipt details: {str(e)}")
        return None
    finally:
        conn.close()

# Update functions
def update_allowed_amt(user_id, amount_data):
    conn = open_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "EXEC P_UpdateAllowedAmtPerGrams @l_Amountgramperiod=?, @l_Amountpergram=?, "
            "@l_AssessedValue=?, @l_MaxAllowed=?, @l_Three_Mth_Rate=?, @l_Mortgagegram=?, "
            "@l_Mortgagemonths=?, @l_effectdate=?, @l_userID=?",
            (
                amount_data['Amountgramperiod'],
                amount_data['Amountpergram'],
                amount_data['AssessedValue'],
                amount_data['MaxAllowed'],
                amount_data['Three_Mth_Rate'],
                amount_data['Mortgagegram'],
                amount_data['Mortgagemonths'],
                datetime.now(),
                user_id
            )
        )
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Update error: {str(e)}")
        return False
    finally:
        conn.close()

# Email function
def send_email():
    try:
        msg = MIMEText("Enquiry for tour and travels package")
        msg['Subject'] = "SKN Data Update Notification"
        msg['From'] = "database@sknfinancial.com"
        msg['To'] = "database@sknfinancial.com"
        
        with smtplib.SMTP('p3nwvpweb1002.shr.prod.phx3.secureserver.net', 587) as server:
            server.starttls()
            server.login('database@sknfinancial.com', 'sknskn')
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Email error: {str(e)}")
        return False

# Main App UI
st.title("SKN Data Management System")

# Authentication Section
if not st.session_state.authenticated:
    with st.form("auth_form"):
        credentials = st.text_input("Enter credentials", key="credentials")
        two_factor = st.text_input("Two Factor Code", key="two_factor")
        
        if st.form_submit_button("Authenticate"):
            status, msg, code = validate_user(credentials, two_factor)
            
            if status <= 2:
                st.error(msg)
                if status == 1:
                    send_email()
                    st.info(f"Verification code sent: {code}")
            else:
                st.session_state.authenticated = True
                st.session_state.credentials = credentials
                st.session_state.two_factor = two_factor
                st.rerun()
else:
    st.success("Authenticated successfully")
    
    # User Management Section
    st.header("User Management")
    
    if st.button("Populate Users"):
        user_data = get_allowed_amt_per_grams()
        if user_data:
            st.session_state.user_data = user_data
            st.success("Users populated successfully")
    
    if st.session_state.user_data:
        df_users = pd.DataFrame(st.session_state.user_data)
        selected_user = st.selectbox("Select User", df_users['UserName'].unique())
        
        if selected_user:
            user_df = df_users[df_users['UserName'] == selected_user]
            st.write(f"Editing user: {selected_user}")
            
            # Display editable table
            edited_df = st.data_editor(
                user_df[['Amountgramperiod', 'Amountpergram', 'MaxAllowed', 
                        'AssessedValue', 'Three_Mth_Rate', 'Mortgagegram', 'Mortgagemonths']],
                key="user_editor"
            )
            
            if st.button("Update User"):
                if update_allowed_amt(
                    int(user_df['UserID'].iloc[0]),
                    edited_df.iloc[0].to_dict()
                ):
                    st.success("User updated successfully")
                else:
                    st.error("Failed to update user")
    
    # Receipt Management Section
    st.header("Receipt Management")
    receipt_no = st.text_input("Receipt Number", key="receipt_no")
    
    if st.button("Search Receipt"):
        if receipt_no:
            receipt_data = get_rcpt_details(receipt_no)
            if receipt_data:
                st.session_state.payment_data = receipt_data
                st.success("Receipt details loaded")
            else:
                st.error("No data found for this receipt")
        else:
            st.warning("Please enter a receipt number")
    
    if st.session_state.payment_data:
        df_payments = pd.DataFrame(st.session_state.payment_data)
        st.dataframe(df_payments)
        
        # Payment actions
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("Add Penalty"):
                st.warning("Penalty addition would go here")
        with col2:
            if st.button("Add NSF"):
                st.warning("NSF addition would go here")
        with col3:
            if st.button("Remove Penalty"):
                st.warning("Penalty removal would go here")
        with col4:
            if st.button("Remove NSF"):
                st.warning("NSF removal would go here")
    
    # Logout button
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()
