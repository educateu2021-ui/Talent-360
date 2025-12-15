import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import date, datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import time

# ---------- CONFIG ----------
st.set_page_config(page_title="Corporate Portal", layout="wide", page_icon="🏢")

# ---------- STYLES ----------
st.markdown(
    """
    <style>
    /* Global Background */
    .stApp { background-color: #f8f9fa; }
    
    /* TRANSFORM BUTTONS INTO CARDS 
       This CSS targets the buttons inside the columns to look like cards 
    */
    div.stButton > button {
        height: 220px;              /* Fixed height for uniformity */
        width: 100%;                /* Full width of the column */
        border-radius: 15px;
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        color: #1f2937;             /* Dark text */
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
        
        /* Flexbox for centering content vertically */
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        
        /* Typography overrides for the button label */
        font-size: 16px;
        white-space: pre-wrap;      /* Allows new lines (\n) in button text */
        line-height: 1.5;
    }

    /* Hover Effect */
    div.stButton > button:hover {
        transform: translateY(-7px);
        box-shadow: 0 12px 25px rgba(0,0,0,0.1);
        border-color: #3b82f6;      /* Blue border on hover */
        color: #3b82f6;             /* Blue text on hover */
        background-color: #ffffff;
    }

    /* Active (Click) Effect */
    div.stButton > button:active {
        background-color: #f3f4f6;
        transform: translateY(-2px);
    }
    
    /* Sidebar Profile Image Styling */
    .profile-container {
        display: flex;
        justify-content: center;
        margin-bottom: 15px;
    }
    .profile-img {
        width: 100px; 
        height: 100px; 
        object-fit: cover; 
        border-radius: 50%; 
        border: 3px solid #e5e7eb;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- DATABASE & UTILS (Logic Unchanged) ----------
DB_FILE = "portal_data_v3.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks_v2 (
        id TEXT PRIMARY KEY, name_activity_pilot TEXT, task_name TEXT, date_of_receipt TEXT,
        actual_delivery_date TEXT, commitment_date_to_customer TEXT, status TEXT,
        ftr_customer TEXT, reference_part_number TEXT, ftr_internal TEXT, otd_internal TEXT,
        description_of_activity TEXT, activity_type TEXT, ftr_quality_gate_internal TEXT,
        date_of_clarity_in_input TEXT, start_date TEXT, otd_customer TEXT, customer_remarks TEXT,
        name_quality_gate_referent TEXT, project_lead TEXT, customer_manager_name TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS training_repo (
        id TEXT PRIMARY KEY, title TEXT, description TEXT, link TEXT, 
        role_target TEXT, mandatory INTEGER, created_by TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS training_progress (
        user_name TEXT, training_id TEXT, status TEXT, 
        last_updated TEXT, PRIMARY KEY (user_name, training_id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS onboarding_tasks (
        id TEXT PRIMARY KEY, task_name TEXT, description TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS onboarding_progress (
        user_name TEXT, task_id TEXT, is_completed INTEGER,
        PRIMARY KEY (user_name, task_id)
    )''')
    conn.commit()
    conn.close()

# --- Helpers ---
def get_kpi_data():
    conn = sqlite3.connect(DB_FILE)
    try: df = pd.read_sql_query("SELECT * FROM tasks_v2", conn)
    except: df = pd.DataFrame()
    conn.close()
    return df

def save_kpi_task(data, task_id=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    otd_val = "N/A"
    try:
        if data.get("actual_delivery_date") and data.get("commitment_date_to_customer"):
            a = pd.to_datetime(str(data["actual_delivery_date"]))
            cm = pd.to_datetime(str(data["commitment_date_to_customer"]))
            otd_val = "OK" if a <= cm else "NOT OK"
    except: pass
    cols = ['name_activity_pilot', 'task_name', 'date_of_receipt', 'actual_delivery_date', 
            'commitment_date_to_customer', 'status', 'ftr_customer', 'reference_part_number', 
            'ftr_internal', 'otd_internal', 'description_of_activity', 'activity_type', 
            'ftr_quality_gate_internal', 'date_of_clarity_in_input', 'start_date', 'otd_customer', 
            'customer_remarks', 'name_quality_gate_referent', 'project_lead', 'customer_manager_name']
    vals = [data.get(k) for k in cols]
    vals[9] = otd_val; vals[15] = otd_val
    if task_id:
        set_clause = ", ".join([f"{col}=?" for col in cols])
        c.execute(f"UPDATE tasks_v2 SET {set_clause} WHERE id=?", (*vals, task_id))
    else:
        new_id = str(uuid.uuid4())[:8]
        placeholders = ",".join(["?"] * (len(cols) + 1))
        c.execute(f"INSERT INTO tasks_v2 VALUES ({placeholders})", (new_id, *vals))
    conn.commit()
    conn.close()

def add_training(title, desc, link, role, mandatory, creator):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    tid = str(uuid.uuid4())[:8]
    c.execute("INSERT INTO training_repo VALUES (?,?,?,?,?,?,?)", 
              (tid, title, desc, link, role, 1 if mandatory else 0, creator))
    conn.commit()
    conn.close()

def get_trainings(user_role=None, user_name=None):
    conn = sqlite3.connect(DB_FILE)
    repo = pd.read_sql_query("SELECT * FROM training_repo", conn)
    if user_name:
        prog = pd.read_sql_query("SELECT * FROM training_progress WHERE user_name=?", conn, params=(user_name,))
        if not repo.empty:
            merged = pd.merge(repo, prog, left_on='id', right_on='training_id', how='left')
            merged['status'] = merged['status'].fillna('Not Started')
            conn.close()
            return merged
    conn.close()
    return repo

def update_training_status(user_name, training_id, status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO training_progress VALUES (?,?,?,?)", 
              (user_name, training_id, status, str(date.today())))
    conn.commit()
    conn.close()

def add_onboarding_task(name, desc):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    tid = str(uuid.uuid4())[:8]
    c.execute("INSERT INTO onboarding_tasks VALUES (?,?,?)", (tid, name, desc))
    conn.commit()
    conn.close()

def get_onboarding_status(user_name):
    conn = sqlite3.connect(DB_FILE)
    tasks = pd.read_sql_query("SELECT * FROM onboarding_tasks", conn)
    prog = pd.read_sql_query("SELECT * FROM onboarding_progress WHERE user_name=?", conn, params=(user_name,))
    if tasks.empty:
        conn.close(); return pd.DataFrame()
    merged = pd.merge(tasks, prog, left_on='id', right_on='task_id', how='left')
    merged['is_completed'] = merged['is_completed'].fillna(0)
    conn.close()
    return merged

def toggle_onboarding(user_name, task_id, checked):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    val = 1 if checked else 0
    c.execute("INSERT OR REPLACE INTO onboarding_progress VALUES (?,?,?)", (user_name, task_id, val))
    conn.commit()
    conn.close()

# ---------- AUTH & SESSION ----------
USERS = {
    "leader": {
        "password": "123", 
        "role": "Team Leader", 
        "name": "Sarah Jenkins", 
        "img": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&q=80&w=200&h=200"
    },
    "member1": {
        "password": "123", 
        "role": "Team Member", 
        "name": "David Chen", 
        "img": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&q=80&w=200&h=200"
    },
    "member2": {
        "password": "123", 
        "role": "Team Member", 
        "name": "Emily Davis", 
        "img": "https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&q=80&w=200&h=200"
    }
}

def login_page():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("""
        <div style='background:white; padding:30px; border-radius:15px; box-shadow:0 4px 15px rgba(0,0,0,0.05); text-align:center;'>
            <h2 style='color:#111827;'>Portal Sign In</h2>
            <p style='color:#6b7280; font-size:0.9rem;'>Enter your corporate credentials</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Secure Login", use_container_width=True, type="primary"):
            if u in USERS and USERS[u]["password"] == p:
                st.session_state.update({
                    'logged_in': True, 'user': u, 
                    'role': USERS[u]['role'], 'name': USERS[u]['name'],
                    'img': USERS[u]['img'],
                    'current_app': 'HOME'
                })
                st.rerun()
            else:
                st.error("Invalid credentials.")

# ---------- APP: HOME DASHBOARD ----------
def app_home():
    st.markdown(f"## Hello, {st.session_state['name']}")
    st.markdown("Access your operational modules below.")
    st.write("")
    
    # 4 Columns Layout
    c1, c2, c3, c4 = st.columns(4)
    
    # NOTE: The "\n" in the button labels are handled by the 'white-space: pre-wrap' CSS above.
    # This makes the button serve as the entire card.
    
    with c1:
        # Module 1: KPI
        # We use a large emoji/icon and text inside the button label
        if st.button("📊\n\nKPI System\n\nTrack Projects & OTD", use_container_width=True, key="btn_kpi"):
            st.session_state['current_app'] = 'KPI'
            st.rerun()

    with c2:
        # Module 2: Training
        if st.button("🎓\n\nTraining Hub\n\nUpskill & Learn", use_container_width=True, key="btn_train"):
            st.session_state['current_app'] = 'TRAINING'
            st.rerun()

    with c3:
        # Module 3: Onboarding
        if st.button("🚀\n\nOnboarding\n\nNew Hire Setup", use_container_width=True, key="btn_onb"):
            st.session_state['current_app'] = 'ONBOARDING'
            st.rerun()

    with c4:
        # Module 4: Skill Radar (Under Construction)
        if st.button("🕸️\n\nSkill Radar\n\nCompetency Matrix", use_container_width=True, key="btn_radar"):
            st.toast("🚧 Skill Radar is currently under construction!", icon="👷")
            time.sleep(1) # Small delay for visual feedback

# ---------- APP: KPI SYSTEM ----------
def app_kpi():
    st.markdown("### 📊 KPI Management System")
    if st.button("← Back to Dashboard"):
        st.session_state['current_app'] = 'HOME'
        st.rerun()
    st.markdown("---")
    
    if st.session_state['role'] == "Team Leader":
        df = get_kpi_data()
        m1, m2, m3 = st.columns(3)
        m1.metric("Active Projects", len(df))
        m2.metric("Delivered", len(df[df['status']=='Completed']) if not df.empty else 0)
        m3.metric("Pending", len(df[df['status']!='Completed']) if not df.empty else 0)
        
        with st.expander("➕ Create New Task"):
            with st.form("new_task"):
                c1, c2 = st.columns(2)
                tname = c1.text_input("Task Name")
                pilot = c2.selectbox("Assignee", [u['name'] for k,u in USERS.items() if u['role']=="Team Member"])
                comm_date = c1.date_input("Deadline", min_value=date.today())
                if st.form_submit_button("Assign Task"):
                    save_kpi_task({'task_name':tname, 'name_activity_pilot':pilot, 'commitment_date_to_customer':str(comm_date), 'status':'Inprogress', 'start_date':str(date.today())})
                    st.success("Task Assigned successfully.")
                    st.rerun()
        
        if not df.empty:
            st.dataframe(df[['task_name', 'name_activity_pilot', 'status', 'commitment_date_to_customer', 'otd_internal']], use_container_width=True)
        else:
            st.info("No active tasks.")
    else:
        df = get_kpi_data()
        my_tasks = df[df['name_activity_pilot'] == st.session_state['name']]
        st.markdown("#### My Tasks")
        if not my_tasks.empty:
            for _, row in my_tasks.iterrows():
                with st.expander(f"{row['task_name']} ({row['status']})"):
                    st.write(f"**Due Date:** {row['commitment_date_to_customer']}")
                    with st.form(f"upd_{row['id']}"):
                        ns = st.selectbox("Update Status", ["Inprogress", "Completed", "Hold"])
                        ad = st.date_input("Completion Date", value=date.today())
                        if st.form_submit_button("Update Progress"):
                            conn = sqlite3.connect(DB_FILE)
                            conn.execute("UPDATE tasks_v2 SET status=?, actual_delivery_date=? WHERE id=?", (ns, str(ad), row['id']))
                            conn.commit(); conn.close()
                            st.success("Status Updated"); st.rerun()
        else:
            st.info("No tasks assigned.")

# ---------- APP: TRAINING TRACKER ----------
def app_training():
    st.markdown("### 🎓 Training Tracker")
    if st.button("← Back to Dashboard"):
        st.session_state['current_app'] = 'HOME'
        st.rerun()
    st.markdown("---")

    if st.session_state['role'] == "Team Leader":
        tabs = st.tabs(["Repository", "Add Module"])
        with tabs[0]:
            df = get_trainings()
            if not df.empty: st.dataframe(df, use_container_width=True)
            else: st.info("Repository empty.")
        with tabs[1]:
            with st.form("add_training"):
                tt = st.text_input("Module Title")
                td = st.text_area("Short Description")
                tl = st.text_input("Content Link")
                tm = st.checkbox("Mark as Mandatory")
                if st.form_submit_button("Publish Module"):
                    add_training(tt, td, tl, "All", tm, st.session_state['name'])
                    st.success("Published."); st.rerun()
    else:
        df = get_trainings(user_name=st.session_state['name'])
        if not df.empty:
            comp = len(df[df['status']=='Completed'])
            st.progress(comp/len(df), text=f"Learning Progress: {int((comp/len(df))*100)}%")
        
        st.markdown("#### Assigned Modules")
        if df.empty: st.info("No training modules found.")
        else:
            cols = st.columns(3)
            for idx, row in df.iterrows():
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div style='background:white; padding:15px; border-radius:10px; border:1px solid #e5e7eb; height:100%; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>
                        <div style='font-weight:bold; color:#1f2937;'>{row['title']}</div>
                        <div style='font-size:0.8rem; color:#6b7280; margin-bottom:10px;'>{row['description']}</div>
                        <a href='{row['link']}' target='_blank' style='color:#3b82f6; text-decoration:none; font-size:0.9rem;'>▶ Access Content</a>
                    </div>
                    """, unsafe_allow_html=True)
                    st.write("")
                    c_stat = row['status']
                    n_stat = st.selectbox("Status", ["Not Started", "In Progress", "Completed"], 
                                          index=["Not Started", "In Progress", "Completed"].index(c_stat), 
                                          key=f"tr_{row['id']}", label_visibility="collapsed")
                    if n_stat != c_stat:
                        update_training_status(st.session_state['name'], row['id'], n_stat)
                        st.rerun()
                    st.markdown("---")

# ---------- APP: ONBOARDING ----------
def app_onboarding():
    st.markdown("### 🚀 Onboarding Hub")
    if st.button("← Back to Dashboard"):
        st.session_state['current_app'] = 'HOME'
        st.rerun()
    st.markdown("---")

    if st.session_state['role'] == "Team Leader":
        st.markdown("#### Checklist Configuration")
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.form("add_ob"):
                t = st.text_input("Task Name"); d = st.text_input("Details")
                if st.form_submit_button("Add Item"):
                    add_onboarding_task(t, d); st.success("Added"); st.rerun()
        with c2:
            conn = sqlite3.connect(DB_FILE)
            tasks = pd.read_sql_query("SELECT * FROM onboarding_tasks", conn)
            conn.close()
            if not tasks.empty: st.dataframe(tasks, use_container_width=True)
    else:
        st.markdown(f"#### Onboarding Checklist")
        df = get_onboarding_status(st.session_state['name'])
        if df.empty: st.info("No checklist available.")
        else:
            comp = df['is_completed'].sum(); total = len(df)
            st.progress(comp/total, text=f"{int(comp)}/{total} Steps Completed")
            st.markdown("<div style='background:white; padding:20px; border-radius:10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
            for _, row in df.iterrows():
                is_done = bool(row['is_completed'])
                c1, c2 = st.columns([0.05, 0.95])
                with c1:
                    checked = st.checkbox("", value=is_done, key=f"ob_{row['id']}")
                with c2:
                    st.markdown(f"<div style='margin-top:5px; {'text-decoration:line-through; color:gray;' if is_done else 'font-weight:bold;'}'>{row['task_name']}</div>", unsafe_allow_html=True)
                    if not is_done: st.caption(row['description'])
                if checked != is_done:
                    toggle_onboarding(st.session_state['name'], row['id'], checked)
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# ---------- MAIN CONTROLLER ----------
def main():
    init_db()
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['current_app'] = 'HOME'

    if st.session_state['logged_in']:
        with st.sidebar:
            # Professional Profile Image (Rounded)
            img_url = st.session_state.get('img', '')
            if img_url:
                st.markdown(f"""
                <div class="profile-container">
                    <img src='{img_url}' class="profile-img">
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"<h3 style='text-align:center; margin:0;'>{st.session_state.get('name','')}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center; color:gray; font-size:0.9rem;'>{st.session_state.get('role','')}</p>", unsafe_allow_html=True)
            st.markdown("---")
            if st.button("Sign Out", use_container_width=True):
                st.session_state.clear()
                st.rerun()

    if not st.session_state['logged_in']:
        login_page()
    else:
        app = st.session_state.get('current_app', 'HOME')
        if app == 'HOME': app_home()
        elif app == 'KPI': app_kpi()
        elif app == 'TRAINING': app_training()
        elif app == 'ONBOARDING': app_onboarding()

if __name__ == "__main__":
    main()
