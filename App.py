import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time

# --- CONFIGURATION ---
ADMIN_PASSWORD = "admin123"
APPS = [
    "Music Player", "YouTube Music", "YouTube Video", 
    "Sim Voice calling", "Messenger Voice calling", 
    "Whatsapp Voice calling", "IMO Voice calling"
]
CRIT_NAMES = []
for name in APPS:
    CRIT_NAMES.extend([f"{name} (Max Vol)", f"{name} (Min Vol)"])

st.set_page_config(page_title="Acoustic Insights", layout="wide")

# --- CUSTOM CSS (Matching your dark theme) ---
st.markdown("""
    <style>
    .main { background-color: #121212; color: white; }
    div[data-testid="stExpander"] { background-color: #1e1e1e; border: 1px solid #f1c40f; border-radius: 10px; }
    .stButton button { background-color: #27ae60; color: white; width: 100%; border-radius: 5px; }
    .admin-btn button { background-color: #f1c40f !important; color: black !important; }
    .metric-card { background: #1e1e1e; padding: 20px; border-radius: 10px; border: 1px solid #333; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- SESSION STATE ---
if "view" not in st.session_state: st.session_state.view = "home"
if "logged_in" not in st.session_state: st.session_state.logged_in = False

# --- NAVIGATION ---
if st.session_state.view != "home":
    if st.sidebar.button("← Back to Home"):
        st.session_state.view = "home"
        st.rerun()

# --- HOME VIEW ---
if st.session_state.view == "home":
    st.markdown("<h1 style='text-align: center; color: #f1c40f;'>Acoustic Insights</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Audio Performance Analytics</h3>", unsafe_allow_html=True)
    
    st.write("##")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.write("### Admin Panel")
        st.write("View results and manage database.")
        if st.button("Enter Admin Dashboard", key="admin_btn"):
            pw = st.text_input("Enter Admin Key", type="password")
            if pw == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.session_state.view = "admin"
                st.rerun()
            elif pw: st.error("Invalid Key")
        st.markdown("</div>", unsafe_allow_html=True)
            
    with col2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.write("### User Panel")
        st.write("Submit your audio performance ratings.")
        if st.button("Start New Rating Session"):
            st.session_state.view = "user"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("##")
    with st.expander("📖 How to Rate? (Instructions)"):
        st.markdown("""
        - Select the **Model** you are testing.
        - Enter your **Name** and **Employee ID** to enable submission.
        - **Star Meaning:** 1 Star (Poor) to 5 Stars (Excellent).
        - Click **Submit** once all 14 criteria are filled.
        """)

# --- USER VIEW ---
elif st.session_state.view == "user":
    st.header("User Rating Panel")
    
    # Load Models
    try:
        models_df = conn.read(worksheet="Models", ttl=0)
        model_list = models_df["Model Name"].tolist() if not models_df.empty else []
    except:
        model_list = []
        st.error("Sheet 'Models' not found.")
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        u_name = c1.text_input("Full Name")
        u_id = c2.text_input("Employee ID")
        selected_model = st.selectbox("Select Model for Testing", [""] + model_list)
    
    if u_name and u_id and selected_model:
        st.divider()
        scores = []
        
        # Grid for rating inputs
        for i in range(0, len(CRIT_NAMES), 2):
            col_l, col_r = st.columns(2)
            with col_l:
                s_val = st.feedback("stars", key=f"user_s_{i}")
                final_s = (s_val + 1) if s_val is not None else 0
                scores.append(final_s)
                st.caption(f"**{CRIT_NAMES[i]}**: {final_s} ★")
            with col_r:
                s_val2 = st.feedback("stars", key=f"user_s_{i+1}")
                final_s2 = (s_val2 + 1) if s_val2 is not None else 0
                scores.append(final_s2)
                st.caption(f"**{CRIT_NAMES[i+1]}**: {final_s2} ★")
        
        if st.button("Submit All Ratings", type="primary"):
            if 0 in scores:
                st.warning("Please rate all 14 items before submitting.")
            else:
                new_row = pd.DataFrame([{
                    "User Name": u_name,
                    "Employee ID": u_id,
                    "Model": selected_model,
                    **dict(zip(CRIT_NAMES, scores))
                }])
                existing = conn.read(worksheet="Ratings", ttl=0)
                updated = pd.concat([existing, new_row], ignore_index=True)
                conn.update(worksheet="Ratings", data=updated)
                
                st.success(f"Submitted! Your Average: {round(sum(scores)/14, 2)} ★")
                st.balloons()
                time.sleep(3)
                st.session_state.view = "home"
                st.rerun()

# --- ADMIN VIEW ---
elif st.session_state.view == "admin":
    st.header("Admin Control Center")
    if not st.session_state.logged_in:
        st.session_state.view = "home"
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["📊 Analytics", "⚖️ Version Comparison", "⚙️ Manage Models"])
    
    # Load Ratings
    ratings_df = conn.read(worksheet="Ratings", ttl=0)
    
    with tab1:
        if not ratings_df.empty:
            target = st.selectbox("Filter by Model", ["All"] + ratings_df["Model"].unique().tolist())
            filtered = ratings_df if target == "All" else ratings_df[ratings_df["Model"] == target]
            
            st.metric("Total Submissions", len(filtered))
            st.write("### Average Score per Category")
            st.bar_chart(filtered[CRIT_NAMES].mean())
            st.write("### Raw Data")
            st.dataframe(filtered)
        else:
            st.info("No data available.")

    with tab2:
        if not ratings_df.empty and len(ratings_df["Model"].unique()) >= 2:
            col_a, col_b = st.columns(2)
            m_a = col_a.selectbox("Model A (Baseline)", ratings_df["Model"].unique(), key="ma")
            m_b = col_b.selectbox("Model B (New)", ratings_df["Model"].unique(), key="mb")
            
            avg_a = ratings_df[ratings_df["Model"] == m_a][CRIT_NAMES].mean()
            avg_b = ratings_df[ratings_df["Model"] == m_b][CRIT_NAMES].mean()
            
            diff = pd.DataFrame({
                "Criteria": CRIT_NAMES,
                m_a: avg_a.values,
                m_b: avg_b.values,
                "Delta": (avg_b - avg_a).values
            })
            st.table(diff.style.background_gradient(subset=['Delta'], cmap='RdYlGn'))
        else:
            st.warning("Need at least two models with data to compare.")

    with tab3:
        st.subheader("Register New Model")
        m_name = st.text_input("Device Name")
        m_ver = st.text_input("SW Version")
        if st.button("Add to Database"):
            if m_name and m_ver:
                m_df = conn.read(worksheet="Models", ttl=0)
                new_m = pd.DataFrame([{"Model Name": f"{m_name} (SW: {m_ver})"}])
                updated_m = pd.concat([m_df, new_m], ignore_index=True)
                conn.update(worksheet="Models", data=updated_m)
                st.success("Model Registered!")
                st.rerun()
