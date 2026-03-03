import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Lecture Tracker", layout="centered")

st.title("📚 Lecture Logger")

# ==============================
# Connect To Google Sheet
# ==============================
def connect_to_gsheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    sheet = client.open("Lecture_Tracker_DB").sheet1
    return sheet


sheet = connect_to_gsheet()

# ==============================
# Ensure Header Exists
# ==============================
expected_columns = [
    "Date",
    "Group ID",
    "Lecture Type",
    "Arrived",
    "Lecture Started",
    "Break Started",
    "Break Ended",
]

existing_data = sheet.get_all_values()

if not existing_data:
    sheet.append_row(expected_columns)
    st.stop()

# Clean headers (strip spaces)
headers = [h.strip() for h in existing_data[0]]

if headers != expected_columns:
    sheet.delete_rows(1)
    sheet.insert_row(expected_columns, 1)

# ==============================
# Load Data
# ==============================
records = sheet.get_all_records()

if records:
    df = pd.DataFrame(records)
    df.columns = df.columns.str.strip()
else:
    df = pd.DataFrame(columns=expected_columns)

# ==============================
# UI Form
# ==============================
with st.form("lecture_form"):

    group_id = st.text_input("Group ID")

    lecture_type = st.selectbox(
        "Lecture Type",
        ["Online", "Offline"]
    )

    action = st.radio(
        "Select Action",
        ["Arrived", "Lecture Started", "Break Started", "Break Ended"]
    )

    time_mode = st.radio(
        "Time Entry Mode",
        ["Use Current Date & Time", "Enter Manually"]
    )

    if time_mode == "Enter Manually":
        manual_date = st.date_input("Select Date")
        manual_time = st.time_input("Select Time")

    submitted = st.form_submit_button("Save")

# ==============================
# Save Logic
# ==============================
if submitted:

    # Handle datetime
    if time_mode == "Use Current Date & Time":
        now_dt = datetime.now()
    else:
        now_dt = datetime.combine(manual_date, manual_time)

    today = now_dt.strftime("%d/%m/%Y")
    now = now_dt.strftime("%d/%m/%Y %H:%M:%S")

    # Reload fresh data before writing
    records = sheet.get_all_records()

    if records:
        df = pd.DataFrame(records)
        df.columns = df.columns.str.strip()
    else:
        df = pd.DataFrame(columns=expected_columns)

    # Check match Date + Group ID
    mask = (df["Date"] == today) & (df["Group ID"] == group_id)

    if mask.any():
        row_index = mask.idxmax() + 2  # +2 because header row
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
        ]
        sheet.append_row(new_row)
        st.success(f"✅ Created new record at {now}")
