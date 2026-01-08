import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURATION ---
ADMIN_PASSWORD = "admin123"
APPS = ["Music Player", "YouTube Music", "YouTube Video", "Sim Voice", "Messenger", "Whatsapp", "IMO"]
CRIT_NAMES = []
for name in APPS:
    CRIT_NAMES.extend([f"{name} (Max)", f"{name} (Min)"])

st.set_page_config(page_title="Acoustic Insights", layout="wide")

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- NAVIGATION ---
if "view" not in st.session_state: st.session_state.view = "home"
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if st.session_state.view != "home":
    if st.sidebar.button("← Back to Home"):
        st.session_state.view = "home"
        st.rerun()

# --- HOME VIEW ---
if st.session_state.view == "home":
    st.title("Acoustic Insights 🎧")
    st.write("Professional Audio Performance Analytics")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Admin Panel", use_container_width=True):
            pw = st.text_input("Enter Admin Key", type="password")
            if pw == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.session_state.view = "admin"
                st.rerun()
            elif pw: st.error("Invalid Key")
            
    with col2:
        if st.button("User Panel", use_container_width=True):
            st.session_state.view = "user"
            st.rerun()

# --- USER VIEW ---
elif st.session_state.view == "user":
    st.header("User Rating Panel")
    
    # Load Models from "Models" sheet
    models_df = conn.read(worksheet="Models", ttl=0)
    model_list = models_df["Model Name"].tolist() if not models_df.empty else []
    
    with st.expander("Step 1: Identity", expanded=True):
        u_name = st.text_input("Full Name")
        u_id = st.text_input("Employee ID")
        selected_model = st.selectbox("Select Model for Testing", [""] + model_list)
    
    if u_name and u_id and selected_model:
        st.write("### Step 2: Rate Performance (1-5 Stars)")
        scores = []
        for crit in CRIT_NAMES:
            score = st.feedback("stars", key=crit)
            val = (score + 1) if score is not None else 0
            scores.append(val)
        
        if st.button("Submit All Ratings", type="primary"):
            if 0 in scores:
                st.warning("Please provide a rating for all 14 criteria.")
            else:
                # Prepare data to append
                new_data = pd.DataFrame([{
                    "User Name": u_name,
                    "Employee ID": u_id,
                    "Model": selected_model,
                    **dict(zip(CRIT_NAMES, scores))
                }])
                
                # Update "Ratings" sheet
                existing_ratings = conn.read(worksheet="Ratings", ttl=0)
                updated_ratings = pd.concat([existing_ratings, new_data], ignore_index=True)
                conn.update(worksheet="Ratings", data=updated_ratings)
                
                st.success(f"Successfully submitted! Average Score: {round(sum(scores)/14, 2)}")
                st.balloons()

# --- ADMIN VIEW ---
elif st.session_state.view == "admin":
    st.header("Admin Control Center")
    tab1, tab2 = st.tabs(["📊 Analytics", "⚙️ Manage Models"])
    
    with tab1:
        ratings_df = conn.read(worksheet="Ratings", ttl=0)
        if not ratings_df.empty:
            st.write("### All User Submissions")
            st.dataframe(ratings_df)
            
            target = st.selectbox("Filter by Model", ["All"] + ratings_df["Model"].unique().tolist())
            filtered = ratings_df if target == "All" else ratings_df[ratings_df["Model"] == target]
            
            if not filtered.empty:
                st.write(f"### Average Ratings for {target}")
                avgs = filtered[CRIT_NAMES].mean()
                st.bar_chart(avgs)
        else:
            st.info("No ratings found in the database yet.")

    with tab2:
        st.write("### Add New Device")
        new_m = st.text_input("Model Name (e.g., S24)")
        new_v = st.text_input("SW Version (e.g., v1.0)")
        if st.button("Register Model"):
            if new_m and new_v:
                models_df = conn.read(worksheet="Models", ttl=0)
                new_entry = pd.DataFrame([{"Model Name": f"{new_m} (SW: {new_v})"}])
                updated_models = pd.concat([models_df, new_entry], ignore_index=True)
                conn.update(worksheet="Models", data=updated_models)
                st.success("Model Registered!")
                st.rerun()