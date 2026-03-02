import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

st.set_page_config(page_title="Lecture Tracker", layout="centered")

st.title("📚 Lecture Logger")

DATA_FILE = "data.csv"
GROUP_FILE = "groups.json"

# -----------------------
# Load Groups
# -----------------------
if not os.path.exists(GROUP_FILE):
    with open(GROUP_FILE, "w") as f:
        json.dump([], f)

with open(GROUP_FILE, "r") as f:
    groups = json.load(f)

if not groups:
    st.warning("⚠ Please add Group IDs first from Group Manager page.")
    st.stop()

# -----------------------
# Main Form
# -----------------------
with st.form("lecture_form"):

    group_id = st.selectbox("Select Group ID", groups)

    lecture_type = st.selectbox(
        "Lecture Type",
        ["Online", "Offline"]
    )

    action = st.radio(
        "Select Action",
        ["Arrived", "Lecture Started", "Break Started", "Break Ended","Lecture Ended"]
    )

    # ----------------------------
    # Time Entry Option
    # ----------------------------
    time_mode = st.radio(
        "Time Entry Mode",
        ["Use Current Date & Time", "Enter Manually"]
    )

    if time_mode == "Enter Manually":
        manual_date = st.date_input("Select Date")
        manual_time = st.time_input("Select Time")

    submitted = st.form_submit_button("Save Action")

# -----------------------
#Connect To Sheet
# -----------------------
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


# -----------------------
# Save Logic
# -----------------------
if submitted:

    # ----------------------------
    # Handle Date & Time
    # ----------------------------
    if time_mode == "Use Current Date & Time":
        now_dt = datetime.now()
    else:
        now_dt = datetime.combine(manual_date, manual_time)

    today = now_dt.strftime("%d/%m/%Y")
    now = now_dt.strftime("%d/%m/%Y %H:%M:%S")

    # ----------------------------
    # Ensure file exists
    # ----------------------------
    # if not os.path.exists(DATA_FILE):
    #     df = pd.DataFrame(columns=[
    #         "Date", "Group ID", "Lecture Type",
    #         "Arrived", "Lecture Started",
    #         "Break Started", "Break Ended", "Lecture Ended"
    #     ])
    #     df.to_csv(DATA_FILE, index=False)

    # df = pd.read_csv(DATA_FILE)

    # # ----------------------------
    # # Match Date + Group ID
    # # ----------------------------
    # mask = (df["Date"] == today) & (df["Group ID"] == group_id)

    # if mask.any():
    #     df.loc[mask, action] = now
    #     st.success(f"✅ Updated existing record: {action} at {now}")
    # else:
    #     new_row = {
    #         "Date": today,
    #         "Group ID": group_id,
    #         "Lecture Type": lecture_type,
    #         "Arrived": "",
    #         "Lecture Started": "",
    #         "Break Started": "",
    #         "Break Ended": "",
    #         "Lecture Ended": "",
    #     }

    #     new_row[action] = now
    #     df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    #     st.success(f"✅ Created new record with {action} at {now}")

    # df.to_csv(DATA_FILE, index=False)


sheet = connect_to_gsheet()

# Get all records
records = sheet.get_all_records()
df = pd.DataFrame(records)

mask = (df["Date"] == today) & (df["Group ID"] == group_id)

if mask.any():
    row_index = mask.idxmax() + 2  # +2 because sheet index starts at 1 and header row
    col_index = df.columns.get_loc(action) + 1
    sheet.update_cell(row_index, col_index, now)
    st.success("Updated existing record.")
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
    st.success("Created new record.")

