import streamlit as st
import pyodbc
from datetime import datetime
import pytz

# Database Configuration
SERVER = "P3NWPLSK12SQL-v06.shr.prod.phx3.secureserver.net"
DATABASE = "SKNFSPROD"
USERNAME = "SKNFSPROD"
PASSWORD = "Password2011@"

# ---------- Initialize Session State ----------
def init_session_state():
    defaults = {
        "search_term": "",
        "twofactor": 0,
        "userdata": "",
        "populateusers": 0,
        "updateusers": 0,
        "updateusrname": "",
        "recipt": 0,
        "receiptrevert": 0,
        "paymentdata": "",
        "paymentstable": 0,
        "selected_user": "",
        "selected_payment": "",
        "selected_payment_no": "",
        "status": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ---------- DB Connection ----------
def open_connection():
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};"
        )
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        return None

# ---------- User Validation ----------
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
            return (1, "No data returned", 0)
        return (result[0], result[1], result[2])
    except Exception as e:
        return (1, f"Validation error: {str(e)}", 0)
    finally:
        conn.close()

# ---------- Stored Procedure Calls ----------
def execute_stored_procedure(callno, params=None):
    conn = open_connection()
    if not conn:
        return [{"status": 1, "msg": "Database connection failed"}]
    try:
        cursor = conn.cursor()
        if callno == 2:
            cursor.execute("{CALL P_GetAllowedAmtPerGrams}")
        # Add other callno conditions here if needed
        conn.commit()
        if callno in [2]:
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            return [{"status": 0, "msg": "Success"}]
    except Exception as e:
        return [{"status": 1, "msg": f"DB error: {str(e)}"}]
    finally:
        conn.close()

# ---------- Streamlit UI ----------
st.set_page_config(page_title="SKN Admin", layout="wide")
st.title("Show SKN Data")

# ---------- Input Section ----------
st.markdown("### Enter Credentials")
st.text_input("Search Term", key="search_term")
st.number_input("Two Factor Code", min_value=0, max_value=999999, step=1, key="twofactor")

result_div = st.empty()

# ---------- Button Handler ----------
st.markdown("---")
st.header("Users Management")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Populate Users", key="btn_populate_users"):
        user_id = 19
        search_term_val = st.session_state.search_term
        twofactor_val = st.session_state.twofactor

        result_div.success(f"Search Term: {search_term_val}")
        result_div.success(f"Two Factor: {twofactor_val}")

        message, status_code, code = validate_user(user_id, search_term_val, twofactor_val)
        result_div.info(f"Validation Result: {message}")

        if status_code <= 2:
            result = execute_stored_procedure(2)
            if result and isinstance(result, list):
                df = pd.DataFrame(result)
                st.dataframe(df)
            else:
                st.warning("No data found.")
