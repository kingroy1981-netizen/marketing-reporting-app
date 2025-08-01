import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials

# ====== CONFIGURATION ======
SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SHEET_URL = "https://docs.google.com/spreadsheets/d/1usWA6IeJ_XVh4y9aZ4gKEzAF2l8DdUreH8mIKCc-uwQ/edit#gid=0"  # <-- Դրա մեջ դնում ես քո Sheets-ի հղումը
SHEET_NAME = "RED Strimlit"  # կամ իրական sheet-ի անունը, եթե փոխել ես
# ====== END CONFIG ======

st.set_page_config(page_title="Marketing Reporting Tool", layout="wide")
st.title("Marketing Reporting Dashboard")

# ---- Upload credentials file ----
uploaded_file = st.file_uploader("Upload your Google Service Account JSON key", type="json")
if not uploaded_file:
    st.warning("Please upload your service account .json key to continue.")
    st.stop()

# ---- Connect to Google Sheets ----
creds = Credentials.from_service_account_info(
    json.load(uploaded_file),
    scopes=SCOPES
)
gc = gspread.authorize(creds)
spreadsheet = gc.open_by_url(SHEET_URL)
worksheet = spreadsheet.worksheet(SHEET_NAME)

# ---- Fetch Data ----
@st.cache_data(ttl=60)
def get_data():
    df = pd.DataFrame(worksheet.get_all_records())
    return df

data = get_data()

# ---- Calculations ----
def safe_div(a, b):
    try:
        return round(a / b, 2) if b else None
    except:
        return None

data["CPL"] = data.apply(lambda x: safe_div(x["Actual Spend"], x["Leads"]), axis=1)
data["CPA"] = data.apply(lambda x: safe_div(x["Actual Spend"], x["Meetings"]), axis=1)
data["Conversion Rate (%)"] = data.apply(lambda x: safe_div(x["Bookings"], x["Leads"])*100 if x["Leads"] else None, axis=1)

st.subheader("Data Table with KPIs")
st.dataframe(data)

st.markdown("---")

# ---- Add New Entry ----
st.subheader("Add New Record")

with st.form("add_form"):
    col1, col2, col3, col4 = st.columns(4)
    start_date = col1.date_input("Start Date")
    end_date = col2.date_input("End Date")
    project = col3.text_input("Project")
    channels = worksheet.col_values(data.columns.get_loc("Channel")+1)[1:]  # existing channels
    channel = col4.selectbox("Channel", sorted(set(channels + ["Add new..."])))
    if channel == "Add new...":
        channel = col4.text_input("New Channel")
    budget = st.number_input("Budget", min_value=0.0, value=0.0)
    actual_spend = st.number_input("Actual Spend", min_value=0.0, value=0.0)
    leads = st.number_input("Leads", min_value=0, value=0)
    meetings = st.number_input("Meetings", min_value=0, value=0)
    bookings = st.number_input("Bookings", min_value=0, value=0)
    submit = st.form_submit_button("Add Record")
    if submit:
        worksheet.append_row([
            str(start_date), str(end_date), project, channel,
            budget, actual_spend, leads, meetings, bookings
        ])
        st.success("Record added! Refresh page to see updated table.")

st.markdown("---")

if st.button("Reload Data"):
    st.cache_data.clear()
    st.experimental_rerun()
