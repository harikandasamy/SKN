from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
import pyodbc
import smtplib
import json
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Allow Streamlit frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to your Streamlit domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connection helper
def get_db_connection():
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=tcp:sknfsprodazure.database.windows.net,1433;"
        "DATABASE=sknfsprodazure_final;"
        "UID=sknfsprodazure;"
        "PWD=Password2025@;"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str)

# Email function
def send_email():
    try:
        smtp = smtplib.SMTP("p3nwvpweb1002.shr.prod.phx3.secureserver.net", 587)
        smtp.starttls()
        smtp.login("database@sknfinancial.com", "sknskn")
        from_addr = "database@sknfinancial.com"
        to_addr = "database@sknfinancial.com"
        message = "Subject: Enquiry for tour and travels package\n\nThis is a test email."
        smtp.sendmail(from_addr, to_addr, message)
        smtp.quit()
        return "Message sent!"
    except Exception as e:
        return str(e)

# Endpoint to handle form requests
@app.post("/GetSKNData")
def get_skn_data(
    search: str = Form(...),
    search_term: str = Form(...),
    twofactor: str = Form(...),
    callno: int = Form(...),
    receiptno: Optional[str] = Form(None),
    paymentno: Optional[str] = Form(None),
    type: Optional[str] = Form(None),
    idrevert: Optional[str] = Form(None),
    UserID: Optional[str] = Form(None),
    Amountgramperiod: Optional[str] = Form(None),
    Amountpergram: Optional[str] = Form(None),
    MaxAllowed: Optional[str] = Form(None),
    AssessedValue: Optional[str] = Form(None),
    Three_Mth_Rate: Optional[str] = Form(None),
    Mortgagegram: Optional[str] = Form(None),
    Mortgagemonths: Optional[str] = Form(None)
):
    send_email()  # Optional email notification
    
    conn = get_db_connection()
    cursor = conn.cursor()

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Validate user
    cursor.execute("EXEC P_ValidateWebUser @userID=?, @username=?, @factorcode=?", 19, search_term, twofactor)
    result = cursor.fetchall()
    if not result:
        return [{"status": 1, "msg": "User validation failed"}]

    status, msg, code = result[0]

    if status <= 2:
        return [{"status": status, "msg": code if status == 1 else msg}]

    # Handle logic by callno
    try:
        if callno == 2:
            cursor.execute("EXEC P_GetAllowedAmtPerGrams")

        elif callno == 3:
            cursor.execute("""
                EXEC P_UpdateAllowedAmtPerGrams 
                @l_Amountgramperiod=?, @l_Amountpergram=?, @l_AssessedValue=?, 
                @l_MaxAllowed=?, @l_Three_Mth_Rate=?, @l_Mortgagegram=?, 
                @l_Mortgagemonths=?, @l_effectdate=?, @l_userID=?
            """, Amountgramperiod, Amountpergram, AssessedValue, MaxAllowed,
                Three_Mth_Rate, Mortgagegram, Mortgagemonths, now, UserID)

        elif callno == 4:
            cursor.execute("EXEC P_GetRcptDetailsforWebsite @s_search=?, @l_userID=?", receiptno, 19)

        elif callno == 5:
            cursor.execute("EXEC P_AddPenalty @type=?, @rcptno=?, @paymentno=?, @userid=?, @storeid=?, @dt=?",
                           type, receiptno, paymentno, 19, 0, now)

        elif callno == 6:
            cursor.execute("EXEC P_GetUpdatePenaltyRemoval @l_userID=?, @l_storeID=?, @l_RcptNo=?, @paymentno=?, @dt=?, @type=?",
                           19, 0, receiptno, paymentno, now, type)

        elif callno == 7:
            cursor.execute("EXEC P_GetMortgagePaymentsHistory @UserId=?, @storeID=?, @RcptNo=?",
                           19, 0, receiptno)

        elif callno == 8:
            cursor.execute("EXEC P_MortgageRevert @UserId=?, @storeID=?,@RcptNo=?,@l_dt=?,@idrevert=?",
                           19, 0, receiptno, now, idrevert)

        else:
            return [{"status": "error", "msg": "Invalid callno"}]

        # Fetch results
        columns = [column[0] for column in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return data

    except Exception as e:
        return [{"status": "error", "msg": str(e)}]
