import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.title("⚙ Group Manager")

def connect_to_gsheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    spreadsheet = client.open("Lecture_Tracker_DB")
    group_sheet = spreadsheet.worksheet("Groups")

    return group_sheet


group_sheet = connect_to_gsheet()

records = group_sheet.get_all_records()

if records:
    df = pd.DataFrame(records)
    df.columns = df.columns.str.strip()
else:
    df = pd.DataFrame(columns=["Group ID"])

# ==============================
# Add New Group
# ==============================
st.subheader("Add New Group")

new_group = st.text_input("Enter Group ID")

if st.button("Add Group"):
    if new_group.strip() == "":
        st.error("Group ID cannot be empty")
    elif new_group in df["Group ID"].tolist():
        st.warning("Group already exists")
    else:
        group_sheet.append_row([new_group])
        st.success("Group Added Successfully")
        st.rerun()

# ==============================
# Show Existing Groups
# ==============================
st.divider()
st.subheader("Existing Groups")

if not df.empty:
    st.dataframe(df)
else:
    st.info("No groups added yet.")
