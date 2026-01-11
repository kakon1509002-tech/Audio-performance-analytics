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
    st.title("Acoustic Insights 🎧")
    st.write("Professional Audio Performance Analytics & Reporting")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("### Admin Portal")
        pw = st.text_input("Enter Admin Key", type="password")
        if st.button("Login as Admin", use_container_width=True):
            if pw == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.session_state.view = "admin"
                st.rerun()
            else:
                st.error("Invalid Key")
            
    with col2:
        st.success("### User Portal")
        st.write("Submit new audio ratings for a device.")
        if st.button("Start Rating Session", use_container_width=True):
            st.session_state.view = "user"
            st.rerun()

    with st.expander("📖 How to Rate? (Instructions)"):
        st.markdown("""
        1. Select the **Model** you are currently testing.
        2. Enter your **Name** and **Employee ID**.
        3. **Star Meaning:** More stars represent better performance.
        4. Click **Submit Ratings** once all 14 categories are filled.
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
        st.error("Error: 'Models' sheet not found in Google Sheets.")
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        u_name = c1.text_input("Full Name")
        u_id = c2.text_input("Employee ID")
        selected_model = st.selectbox("Select Model", [""] + model_list)
    
    if u_name and u_id and selected_model:
        st.write("### Audio Performance Criteria")
        scores = []
        
        # Grid layout for stars
        for i in range(0, len(CRIT_NAMES), 2):
            col_left, col_right = st.columns(2)
            with col_left:
                s1 = st.feedback("stars", key=f"s_{i}")
                val1 = (s1 + 1) if s1 is not None else 0
                scores.append(val1)
                st.caption(f"**{CRIT_NAMES[i]}**: {val1} ★")
            with col_right:
                s2 = st.feedback("stars", key=f"s_{i+1}")
                val2 = (s2 + 1) if s2 is not None else 0
                scores.append(val2)
                st.caption(f"**{CRIT_NAMES[i+1]}**: {val2} ★")
        
        if st.button("Submit All Ratings", type="primary", use_container_width=True):
            if 0 in scores:
                st.warning("Please provide a rating for all 14 criteria.")
            else:
                new_data = pd.DataFrame([{
                    "User Name": u_name,
                    "Employee ID": u_id,
                    "Model": selected_model,
                    **dict(zip(CRIT_NAMES, scores))
                }])
                
                existing = conn.read(worksheet="Ratings", ttl=0)
                updated = pd.concat([existing, new_data], ignore_index=True)
                conn.update(worksheet="Ratings", data=updated)
                
                st.success(f"Submitted! Your Avg: {round(sum(scores)/14, 2)} ★")
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

    tab1, tab2, tab3 = st.tabs(["📊 Analytics", "⚖️ Comparison", "⚙️ Manage"])
    
    ratings_df = conn.read(worksheet="Ratings", ttl=0)
    
    with tab1:
        if not ratings_df.empty:
            target = st.selectbox("View Model", ["All"] + ratings_df["Model"].unique().tolist())
            filtered = ratings_df if target == "All" else ratings_df[ratings_df["Model"] == target]
            
            st.metric("Submissions", len(filtered))
            avgs = filtered[CRIT_NAMES].mean()
            st.bar_chart(avgs)
            st.dataframe(filtered)
        else:
            st.info("No data yet.")

    with tab2:
        if not ratings_df.empty and len(ratings_df["Model"].unique()) >= 2:
            m_a = st.selectbox("Model A", ratings_df["Model"].unique(), key="ma")
            m_b = st.selectbox("Model B", ratings_df["Model"].unique(), key="mb")
            
            avg_a = ratings_df[ratings_df["Model"] == m_a][CRIT_NAMES].mean()
            avg_b = ratings_df[ratings_df["Model"] == m_b][CRIT_NAMES].mean()
            
            diff = pd.DataFrame({
                "Criteria": CRIT_NAMES,
                m_a: avg_a.values,
                m_b: avg_b.values,
                "Delta": (avg_b - avg_a).values
            })
            
            st.write(f"#### Comparison: {m_a} vs {m_b}")
            st.dataframe(diff.style.background_gradient(subset=['Delta'], cmap='RdYlGn'))
            st.bar_chart(diff.set_index("Criteria")[[m_a, m_b]])
        else:
            st.warning("Need ratings for at least two different models to compare.")

    with tab3:
        st.subheader("Database Management")
        nm = st.text_input("New Model Name")
        nv = st.text_input("SW Version")
        if st.button("Add Model"):
            if nm and nv:
                m_df = conn.read(worksheet="Models", ttl=0)
                updated_m = pd.concat([m_df, pd.DataFrame([{"Model Name": f"{nm} (SW: {nv})"}])], ignore_index=True)
                conn.update(worksheet="Models", data=updated_m)
                st.success("Model Added!")
                st.rerun()