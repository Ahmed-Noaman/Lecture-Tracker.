%%writefile app.py

import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo  # built-in in Python 3.9+
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Lecture Tracker", layout="centered")
st.title("📚 Lecture Logger")

# ----------------------------
# Google Sheets connection
# ----------------------------
def connect_to_gsheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open("Lecture_Tracker_DB")
    data_sheet = spreadsheet.worksheet("Sheet1")
    group_sheet = spreadsheet.worksheet("Groups")

    return sheet, group_sheet

sheet, group_sheet = connect_to_gsheet()


# ==============================
# Load Groups
# ==============================
group_records = group_sheet.get_all_records()

if group_records:
    group_df = pd.DataFrame(group_records)
    group_df.columns = group_df.columns.str.strip()
    groups = group_df["Group ID"].dropna().tolist()
else:
    groups = []

if not groups:
    st.warning("⚠ No groups found. Please add groups from Group Manager page.")
    st.stop()
# ----------------------------
# Expected Columns
# ----------------------------
expected_columns = [
    "Date",
    "Group ID",
    "Lecture Type",
    "Arrived",
    "Lecture Started",
    "Break Started",
    "Break Ended",
    "Lecture Ended",
]


# ----------------------------
# Read Data and Ensure Columns
# ----------------------------
data = sheet.get_all_values()

if not data:
    # Sheet empty → insert header row
    sheet.append_row(expected_columns)
    st.stop()

# First row is header
header = [h.strip() for h in data[0]]

# Fix header if not matching expected
if header != expected_columns:
    sheet.delete_rows(1)
    sheet.insert_row(expected_columns, 1)
    header = expected_columns

# Load sheet data into DataFrame
records = sheet.get_all_records()
if records:
    df = pd.DataFrame(records)
    df = df.reindex(columns=expected_columns)
else:
    # Empty sheet after header
    df = pd.DataFrame(columns=expected_columns)

# ----------------------------
# Form UI
# ----------------------------
with st.form("lecture_form"):

    group_id = st.text_input("Group ID")
    lecture_type = st.selectbox("Lecture Type", ["Online", "Offline"])
    action = st.radio(
        "Select Action", ["Arrived", "Lecture Started", "Break Started", "Break Ended","Lecture Ended"]
    )

    time_mode = st.radio("Time Entry Mode", ["Use Current Date & Time", "Enter Manually"])
    if time_mode == "Enter Manually":
        manual_date = st.date_input("Select Date")
        manual_time = st.time_input("Select Time")

    submitted = st.form_submit_button("Save")

# ----------------------------
# Save Logic
# ----------------------------
if submitted:

    if not group_id.strip():
        st.error("⚠ Group ID cannot be empty")
        st.stop()

    # Determine timestamp
    if time_mode == "Use Current Date & Time":
        now_dt = datetime.now(ZoneInfo("Africa/Cairo"))
    else:
        now_dt = datetime.combine(manual_date, manual_time)

    today = now_dt.strftime("%d/%m/%Y")
    now = now_dt.strftime("%d/%m/%Y %H:%M:%S")

    # Reload fresh data
    records = sheet.get_all_records()
    if records:
        df = pd.DataFrame(records)
        df = df.reindex(columns=expected_columns)
    else:
        df = pd.DataFrame(columns=expected_columns)

    # ----------------------------
    # Find row with same Date + Group
    # ----------------------------
    if not df.empty:
        mask = (df["Date"] == today) & (df["Group ID"] == group_id)
    else:
        mask = pd.Series(dtype=bool)

    if mask.any():
        row_index = mask.idxmax() + 2  # +2 because sheet index starts at 1 and header
        col_index = df.columns.get_loc(action) + 1
        sheet.update_cell(row_index, col_index, now)
        st.success(f"✅ Updated {action} at {now}")
    else:
        new_row = [
            today,
            group_id,
            lecture_type,
            now if action == "Arrived" else "",
            now if action == "Lecture Started" else "",
            now if action == "Break Started" else "",
            now if action == "Break Ended" else "",
            now if action == "Lecture Ended" else "",
        ]
        sheet.append_row(new_row)
        st.success(f"✅ Created new record at {now}")
        
