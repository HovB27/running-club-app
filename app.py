from datetime import datetime, timedelta
import streamlit as st
import extra_streamlit_components as stx
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import cloudinary
import cloudinary.uploader
import requests

# 1. SETUP
st.set_page_config(page_title="Run Club", page_icon="🏃", layout="wide")
cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_NAME"],
    api_key = st.secrets["CLOUDINARY_KEY"],
    api_secret = st.secrets["CLOUDINARY_SECRET"]
)
cookie_manager = stx.CookieManager()
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. IDENTITY
saved_name = cookie_manager.get(cookie="run_club_user")
if "user_name" not in st.session_state:
    st.session_state.user_name = saved_name if saved_name else None

if not st.session_state.user_name:
    st.title("🏃 Club Entrance")
    pwd = st.text_input("Club Password", type="password")
    name = st.text_input("Your Name")
    if st.button("Enter"):
        if pwd == "RunYerevan2026" and name:
            st.session_state.user_name = name
            cookie_manager.set("run_club_user", name, expires_at=3650)
            st.rerun()
    st.stop()

# 3. DATA LOAD
# (No URL needed here because it's in your Secrets!)
sched_df = conn.read(worksheet="Schedule")
rsvp_df = conn.read(worksheet="RSVPs")
comm_df = conn.read(worksheet="Comments")
photo_df = conn.read(worksheet="Photos")

st.title(f"👟 Welcome, {st.session_state.user_name}!")

# 4. APP LOGIC
for _, run in sched_df.iterrows():
    run_id = run['Run_ID']
    with st.expander(f"📅 {run['Date']} - {run['Run_Name']}"):
        t1, t2, t3 = st.tabs(["RSVP", "Chat", "Photos"])
        
        with t1:
            st.write(f"📍 {run['Location']} | ⏰ {run['Time']}")
            people = rsvp_df[rsvp_df['Run_ID'] == run_id]['Member_Name'].tolist()
            st.write(f"**Joiners:** {', '.join(people) if people else 'Be the first!'}")
            if st.session_state.user_name not in people:
                if st.button("I'm Coming!", key=f"r_{run_id}"):
                    new = pd.DataFrame([{"Run_ID": run_id, "Member_Name": st.session_state.user_name}])
                    conn.update(worksheet="RSVPs", data=pd.concat([rsvp_df, new]))
                    st.rerun()

        with t2:
            run_c = comm_df[comm_df['Run_ID'] == run_id]
            for _, c in run_c.iterrows(): st.write(f"**{c['Member_Name']}**: {c['Message']}")
            msg = st.text_input("Message", key=f"m_{run_id}")
            if st.button("Send", key=f"b_{run_id}"):
                new_c = pd.DataFrame([{"Run_ID": run_id, "Member_Name": st.session_state.user_name, "Message": msg}])
                conn.update(worksheet="Comments", data=pd.concat([comm_df, new_c]))
                st.rerun()

        with t3:
            run_p = photo_df[photo_df['Run_ID'] == run_id]
            if not run_p.empty:
                for _, p in run_p.iterrows():
                    st.image(p['Image_URL'])
                    st.download_button("📥 Download", requests.get(p['Image_URL']).content, f"run_{run_id}.jpg", key=f"d_{p['Image_URL']}")
            
            img = st.file_uploader("Post Photo", type=['jpg','png'], key=f"i_{run_id}")
            if img and st.button("Upload", key=f"u_{run_id}"):
                res = cloudinary.uploader.upload(img)
                new_p = pd.DataFrame([{"Run_ID": run_id, "Member_Name": st.session_state.user_name, "Image_URL": res['secure_url']}])
                conn.update(worksheet="Photos", data=pd.concat([photo_df, new_p]))
                st.rerun()
