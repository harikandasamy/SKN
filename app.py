import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="SKN Data Portal", layout="wide")
st.title("📋 SKN Data Portal – User and Payment Management")

# Setup default API URL
api_url = st.secrets.get("api_url", "https://yourserver/GetSKNData.php")

# Session state
if "userdata" not in st.session_state: st.session_state.userdata = []
if "paymentdata" not in st.session_state: st.session_state.paymentdata = []
if "update_mode" not in st.session_state: st.session_state.update_mode = 0
if "paymentstable" not in st.session_state: st.session_state.paymentstable = 0

# --- Search Section ---
with st.form("search_form"):
    st.subheader("🔍 Search Inputs")
    search_term = st.text_input("Enter Credentials", "")
    twofactor = st.text_input("Two Factor", "-1")
    submitted = st.form_submit_button("Search (Simulated)")
    if submitted:
        st.info("Simulated search executed.")

# --- Users Section ---
st.subheader("👥 User Operations")
if st.button("Populate Users"):
    payload = {
        "search": "search",
        "search_term": search_term,
        "twofactor": twofactor,
        "callno": 2
    }
    try:
        res = requests.post(api_url, data=payload)
        res.raise_for_status()
        st.session_state.userdata = res.json()
        st.success("✅ Users populated")
    except Exception as e:
        st.error(f"❌ Failed to fetch users: {e}")

# Display user dropdown
if st.session_state.userdata:
    usernames = [u["UserName"] for u in st.session_state.userdata]
    selected = st.selectbox("Select User", usernames)
    selected_user = next(u for u in st.session_state.userdata if u["UserName"] == selected)
    df_user = pd.DataFrame([selected_user])
    edited = st.data_editor(df_user, num_rows="fixed", use_container_width=True)

    if st.button("Update Selected User"):
        row = edited.iloc[0]
        payload = {
            "search": "search",
            "search_term": search_term,
            "twofactor": twofactor,
            "callno": 3,
            "UserID": row["UserID"],
            "Amountgramperiod": row["Amountgramperiod"],
            "Amountpergram": row["Amountpergram"],
            "MaxAllowed": row["MaxAllowed"],
            "AssessedValue": row["AssessedValue"],
            "Three_Mth_Rate": row["Three_Mth_Rate"],
            "Mortgagegram": row["Mortgagegram"],
            "Mortgagemonths": row["Mortgagemonths"]
        }
        try:
            update_res = requests.post(api_url, data=payload)
            st.success(f"✅ Updated {row['UserName']}")
        except Exception as e:
            st.error(f"❌ Update failed: {e}")

# --- Payment Section ---
st.subheader("💳 Payment Management")
receipt_no = st.text_input("Receipt No", "")

cols = st.columns(3)
with cols[0]:
    if st.button("Search Payment No"):
        payload = {
            "search": "search",
            "search_term": search_term,
            "twofactor": twofactor,
            "callno": 4,
            "receiptno": receipt_no
        }
        try:
            res = requests.post(api_url, data=payload)
            st.session_state.paymentdata = res.json()
            st.success("Payment numbers retrieved.")
        except Exception as e:
            st.error(f"Failed to retrieve payment numbers: {e}")

with cols[1]:
    if st.button("Add Penalty"):
        st.warning("Add Penalty feature not implemented here.")

with cols[2]:
    if st.button("Remove Penalty"):
        st.warning("Remove Penalty feature not implemented here.")

# --- Payments Table ---
if st.session_state.paymentdata:
    st.markdown("### 🧾 Payments Table")
    df_payments = pd.DataFrame(st.session_state.paymentdata)
    st.dataframe(df_payments)

    if st.button("Revert Payment"):
        selected_id = st.selectbox("Select Payment to Revert", df_payments["PaymentID"])
        payload = {
            "search": "search",
            "search_term": search_term,
            "twofactor": twofactor,
            "callno": 8,
            "receiptno": receipt_no,
            "idrevert": selected_id
        }
        try:
            revert_res = requests.post(api_url, data=payload)
            st.success(f"Payment reverted: {selected_id}")
        except Exception as e:
            st.error(f"Failed to revert payment: {e}")
