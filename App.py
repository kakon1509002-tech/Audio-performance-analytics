import streamlit as st
import json
import os
import pandas as pd

# --- CONFIGURATION ---
DB_FILE = 'database.json'
ADMIN_PASSWORD = "admin123"
APPS = ["Music Player", "YouTube Music", "YouTube Video", "Sim Voice", "Messenger", "Whatsapp", "IMO"]
CRIT_NAMES = []
for name in APPS:
    CRIT_NAMES.extend([f"{name} (Max)", f"{name} (Min)"])

# --- DATABASE LOGIC ---
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {"products": [], "user_data": {}}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- SESSION STATE ---
if "view" not in st.session_state: st.session_state.view = "home"
if "logged_in" not in st.session_state: st.session_state.logged_in = False

# --- UI STYLING ---
st.markdown("""
    <style>
    .main { background-color: #121212; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #27ae60; color: white; }
    .instruction-box { background-color: #1e1e1e; padding: 20px; border: 1px solid #f1c40f; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVIGATION ---
if st.session_state.view != "home":
    if st.button("← Back to Home"):
        st.session_state.view = "home"
        st.rerun()

# --- HOME VIEW ---
if st.session_state.view == "home":
    st.title("Acoustic Insights 🎧")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Admin Panel"):
            pw = st.text_input("Enter Admin Key", type="password")
            if pw == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.session_state.view = "admin"
                st.rerun()
            elif pw: st.error("Invalid Key")
            
    with col2:
        if st.button("User Panel"):
            st.session_state.view = "user"
            st.rerun()

    with st.expander("📖 How to Rate? (Instructions)"):
        st.markdown("""
        * Select the **Model** you are testing.
        * Enter your **Name** and **ID**.
        * More stars = Better performance.
        * Submit once all 14 ratings are done.
        """)

# --- USER VIEW ---
elif st.session_state.view == "user":
    st.header("User Rating Panel")
    db = load_db()
    
    col_name, col_id = st.columns(2)
    u_name = col_name.text_input("Full Name")
    u_id = col_id.text_input("Employee ID")
    product = st.selectbox("Select Model", [""] + db["products"])
    
    if u_name and u_id and product != "":
        scores = []
        for crit in CRIT_NAMES:
            val = st.feedback("stars", key=crit) # Streamlit's built-in star rating
            if val is None: val = 0 
            else: val += 1 # feedback starts at 0
            scores.append(val)
            st.write(f"Rating for {crit}: {val}")

        if st.button("Submit All Ratings"):
            if 0 in scores:
                st.warning("Please provide a rating for all 14 criteria.")
            else:
                db["user_data"].setdefault(product, {})[u_id] = {"name": u_name, "scores": scores}
                save_db(db)
                st.success(f"Submitted! Your Avg: {round(sum(scores)/14, 2)}")
                st.balloons()
    else:
        st.info("Enter your Name, ID, and Select a Model to start rating.")

# --- ADMIN VIEW ---
elif st.session_state.view == "admin":
    st.header("Admin Control Center")
    db = load_db()

    tab1, tab2 = st.tabs(["Dashboard", "Manage Models"])
    
    with tab1:
        target = st.selectbox("View Results for:", [""] + db["products"])
        if target and target in db["user_data"]:
            users = db["user_data"][target]
            # Calculate Averages
            rows = []
            for uid, info in users.items():
                rows.append([info["name"]] + info["scores"])
            
            df = pd.DataFrame(rows, columns=["User"] + CRIT_NAMES)
            st.write("### Raw Data")
            st.dataframe(df)
            
            st.write("### Category Averages")
            avg_series = df.drop(columns="User").mean()
            st.bar_chart(avg_series)
            
    with tab2:
        new_m = st.text_input("Model Name")
        new_v = st.text_input("SW Version")
        if st.button("Add Model"):
            entry = f"{new_m} (SW: {new_v})"
            if entry not in db["products"]:
                db["products"].append(entry)
                save_db(db)
                st.rerun()