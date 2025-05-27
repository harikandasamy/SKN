import streamlit as st
import pyodbc

# Database Configuration
SERVER = "P3NWPLSK12SQL-v06.shr.prod.phx3.secureserver.net"
DATABASE = "SKNFSPROD"
USERNAME = "SKNFSPROD"
PASSWORD = "Password2011@"

# Initialize session state defaults
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

def validate_user(user_id, username, factor_code):
    conn = open_connection()
    if not conn:
        return (1, "Database connection error", 0)
    try:
        cursor = conn.cursor()
        cursor.execute("{CALL P_ValidateWebUser (?, ?, ?)}", (user_id, username, factor_code))

        # Advance through result sets until data row found
        result = None
        while True:
            row = cursor.fetchone()
            if row:
                result = row
                break
            if not cursor.nextset():
                break

        conn.commit()

        if result is None:
            return (1, "No data returned from validation", 0)

        return (result[0], result[1], result[2])  # msg, status, code
    except Exception as e:
        return (1, f"Validation error: {str(e)}", 0)
    finally:
        conn.close()

def execute_stored_procedure(callno, params=None):
    conn = open_connection()
    if not conn:
        return [{"status": 1, "msg": "Database connection failed"}]
    try:
        cursor = conn.cursor()
        if callno == 2:
            cursor.execute("SET NOCOUNT ON; EXEC P_GetAllowedAmtPerGrams")
        elif callno == 3:
            cursor.execute("""
                SET NOCOUNT ON; EXEC P_UpdateAllowedAmtPerGrams ?, ?, ?, ?, ?, ?, ?, ?, ?
            """, (
                form_data["Amountgramperiod"],
                form_data["Amountpergram"],
                form_data["AssessedValue"],
                form_data["MaxAllowed"],
                form_data["Three_Mth_Rate"],
                form_data["Mortgagegram"],
                form_data["Mortgagemonths"],
                get_est_time(),
                form_data["UserID"]
            ))
        elif callno == 4:
            cursor.execute("SET NOCOUNT ON; EXEC P_GetRcptDetailsforWebsite ?, ?", (form_data["receiptno"], 19))
        elif callno == 5:
            cursor.execute("SET NOCOUNT ON; EXEC P_AddPenalty ?, ?, ?, ?, ?, ?", (
                form_data["type"],
                form_data["receiptno"],
                form_data["paymentno"],
                19,
                0,
                get_est_time()
            ))
        elif callno == 6:
            cursor.execute("SET NOCOUNT ON; EXEC P_GetUpdatePenaltyRemoval ?, ?, ?, ?, ?, ?", (
                19,
                0,
                form_data["receiptno"],
                form_data["paymentno"],
                get_est_time(),
                form_data["type"]
            ))
        elif callno == 7:
            cursor.execute("SET NOCOUNT ON; EXEC P_GetMortgagePaymentsHistory ?, ?, ?", (
                19,
                0,
                form_data["receiptno"]
            ))
        elif callno == 8:
            cursor.execute("SET NOCOUNT ON; EXEC P_MortgageRevert ?, ?, ?, ?, ?", (
                19,
                0,
                form_data["receiptno"],
                get_est_time(),
                form_data["idrevert"]
            ))
        else:
            return [{"status": 1, "msg": "Invalid callno"}]

        # Try fetching results
        results = []
        columns = [col[0] for col in cursor.description] if cursor.description else []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        return results if results else [{"status": 0, "msg": "Operation completed successfully"}]

    except Exception as e:
        return [{"status": 1, "msg": f"DB error: {str(e)}"}]
    finally:
        conn.close()
        
st.set_page_config(page_title="Show SKN Data", layout="wide")
st.title("Show SKN Data")

st.text_input("Enter credentials", key="search_term")
st.text_input("Two Factor", key="twofactor")

result_div = st.empty()

def process_request(callno, types=None):
    user_id = 19
    search_term_val = st.session_state.get("search_term", "")
    twofactor_val = st.session_state.get("twofactor", "").strip() or "0"

    msg, status_code, code = validate_user(user_id, search_term_val, twofactor_val)
    result_div.success(f"Status: {status_code} | Message: {msg} | Code: {code}")

    if status_code <= 2:
        return {"msg": msg, "status": status_code, "code": code}

    # Proceed to your other stored procedures if validation passed
    return execute_stored_procedure(callno, types)

st.markdown("---")
st.header("Users Management")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Populate Users", key="btnUsers"):
        result = process_request(2)
        st.write(result)
    if st.button("Update Users", key="btnUpdateUsers"):
        result = process_request(2)
        st.write(result)
    if st.button("Update Users", key="btnRevertUsers"):
        result = process_request(2)
        st.write(result)
