
import streamlit as st
import json
import os

st.title("⚙ Group Manager")

GROUP_FILE = "groups.json"

if not os.path.exists(GROUP_FILE):
    with open(GROUP_FILE, "w") as f:
        json.dump([], f)

with open(GROUP_FILE, "r") as f:
    groups = json.load(f)

# -----------------------
# Add Group
# -----------------------
st.subheader("Add New Group")

new_group = st.text_input("Enter Group ID")

if st.button("Add Group"):
    if new_group and new_group not in groups:
        groups.append(new_group)
        with open(GROUP_FILE, "w") as f:
            json.dump(groups, f)
        st.success("Group Added Successfully!")
        st.rerun()
    else:
        st.warning("Group already exists or empty.")

# -----------------------
# Show Groups
# -----------------------
st.divider()
st.subheader("Existing Groups")

if groups:
    st.write(groups)
else:
    st.info("No groups added yet.")
