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


# User management section
with st.expander("User Management"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Populate Users"):
            conn = open_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("{CALL P_GetAllowedAmtPerGrams}")
                    rows = cursor.fetchall()
                    
                    if rows:
                        st.session_state.userdata = rows
                        st.session_state.populateusers = 1
                        st.success("Users populated successfully")
                    else:
                        st.error("No user data found")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                finally:
                    conn.close()
    
    with col2:
        if st.button("Update Users"):
            if st.session_state.populateusers == 1 and st.session_state.updateusers == 0:
                st.session_state.updateusers = 1
                st.info("Select a user to update")
            elif st.session_state.updateusers == 1:
                st.session_state.updateusers = 2
                st.warning("Confirm that you are updating user values")
            elif st.session_state.updateusers == 2:
                st.session_state.updateusers = 0
                st.success("User values updated")
            else:
                st.error("Users are not populated")
    
    with col3:
        if st.button("Revert Users"):
            st.session_state.populateusers = 0
            st.session_state.updateusers = 0
            st.session_state.updateusrname = ""
            st.session_state.userdata = None
            st.success("User data cleared")
    
    if st.session_state.populateusers == 1 and st.session_state.userdata:
        user_options = [f"{row.UserName} (ID: {row.UserID})" for row in st.session_state.userdata]
        selected_user = st.selectbox("Select User", options=user_options)
        
        if st.session_state.updateusers >= 1:
            user_df = pd.DataFrame.from_records(
                [row.__dict__ for row in st.session_state.userdata],
                columns=st.session_state.userdata[0].__dict__.keys()
            )
            editable_df = st.data_editor(user_df)

# Receipt management section
with st.expander("Receipt Management"):
    receipt_no = st.text_input("Receipt No", key="searchreceipt")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Search Payment No"):
            if receipt_no:
                conn = open_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        cursor.execute("{CALL P_GetRcptDetailsforWebsite (?, ?)}", receipt_no, 19)
                        rows = cursor.fetchall()
                        
                        if rows:
                            st.session_state.paymentdata = rows
                            st.session_state.receiptrevert = 1
                            st.session_state.recipt = receipt_no
                            st.success("Payment data loaded")
                        else:
                            st.error("No payment data found")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                    finally:
                        conn.close()
            else:
                st.error("Please enter a Receipt No")
    
    with col2:
        if st.button("Revert Receipt"):
            st.session_state.receiptrevert = 0
            st.session_state.recipt = 0
            st.session_state.paymentdata = None
            st.success("Receipt data cleared")
    
    if st.session_state.receiptrevert == 1 and st.session_state.paymentdata:
        payment_options = [f"Payment {idx+1}" for idx in range(len(st.session_state.paymentdata))]
        selected_payment = st.selectbox("Select Payment", options=payment_options)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("Add Penalty"):
                st.warning("Add penalty functionality would go here")
        
        with col2:
            if st.button("Add NSF"):
                st.warning("Add NSF functionality would go here")
        
        with col3:
            if st.button("Remove Penalty"):
                st.warning("Remove penalty functionality would go here")
        
        with col4:
            if st.button("Remove NSF"):
                st.warning("Remove NSF functionality would go here")

# Payments section
with st.expander("Payments"):
    if st.button("List Payments"):
        if st.session_state.recipt:
            if st.session_state.paymentstable == 0:
                conn = open_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        cursor.execute("{CALL P_GetMortgagePaymentsHistory (?, ?, ?)}", 19, 0, st.session_state.recipt)
                        rows = cursor.fetchall()
                        
                        if rows:
                            st.session_state.paymentdata = rows
                            st.session_state.paymentstable = 1
                            st.success("Payments listed successfully")
                        else:
                            st.error("No payment data found")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                    finally:
                        conn.close()
            else:
                st.info("Payments are already populated")
        else:
            st.error("Please search for a receipt first")
    
    if st.button("Remove Payments"):
        if st.session_state.paymentstable == 1:
            st.session_state.paymentstable = 2
            st.warning("Confirm payment removal")
        elif st.session_state.paymentstable == 2:
            st.session_state.paymentstable = 0
            st.success("Payment removed successfully")
        else:
            st.error("Payments are not populated")
    
    if st.button("Revert Payments"):
        st.session_state.receiptrevert = 0
        st.session_state.recipt = 0
        st.session_state.paymentstable = 0
        st.session_state.paymentdata = None
        st.success("Payment data cleared")
    
    if st.session_state.paymentstable >= 1 and st.session_state.paymentdata:
        payment_df = pd.DataFrame.from_records(
            [row.__dict__ for row in st.session_state.paymentdata],
            columns=st.session_state.paymentdata[0].__dict__.keys()
        )
        st.dataframe(payment_df)
