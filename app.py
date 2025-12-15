import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import date, datetime, timedelta
import time

# ---------- CONFIG ----------
# Layout="wide" allows the 4 columns to spread out on desktop
st.set_page_config(page_title="Corporate Portal", layout="wide", page_icon="🏢")

# ---------- RESPONSIVE CSS ----------
st.markdown(
    """
    <style>
    /* 1. Global Background & Font */
    .stApp { background-color: #f8f9fa; }
    
    /* 2. Sidebar Profile Image - Responsive centering */
    .profile-img {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        object-fit: cover;
        border: 4px solid #dfe6e9;
        display: block;
        margin: 0 auto 15px auto;
    }
    
    /* 3. Mobile/Tablet Optimization */
    /* On smaller screens, add a bit more breathing room between stacked containers */
    div[data-testid="stVerticalBlock"] > div {
        margin-bottom: 0.5rem;
    }
    
    /* 4. Button Full Width & Touch Friendly */
    /* Ensures buttons inside cards are easy to tap on mobile */
    div[data-testid="stVerticalBlockBorderWrapper"] button {
        width: 100%;
        min-height: 45px;
    }
    
    /* 5. Header Spacing */
    .block-container { padding-top: 2rem; padding-bottom: 3rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- DATABASE & UTILS ----------
DB_FILE = "portal_data_v6.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # KPI Table
    c.execute('''CREATE TABLE IF NOT EXISTS tasks_v2 (
        id TEXT PRIMARY KEY, name_activity_pilot TEXT, task_name TEXT, date_of_receipt TEXT,
        actual_delivery_date TEXT, commitment_date_to_customer TEXT, status TEXT,
        ftr_customer TEXT, reference_part_number TEXT, ftr_internal TEXT, otd_internal TEXT,
        description_of_activity TEXT, activity_type TEXT, ftr_quality_gate_internal TEXT,
        date_of_clarity_in_input TEXT, start_date TEXT, otd_customer TEXT, customer_remarks TEXT,
        name_quality_gate_referent TEXT, project_lead TEXT, customer_manager_name TEXT
    )''')
    # Training Tables
    c.execute('''CREATE TABLE IF NOT EXISTS training_repo (
        id TEXT PRIMARY KEY, title TEXT, description TEXT, link TEXT, 
        role_target TEXT, mandatory INTEGER, created_by TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS training_progress (
        user_name TEXT, training_id TEXT, status TEXT, 
        last_updated TEXT, PRIMARY KEY (user_name, training_id)
    )''')
    # Onboarding Tables
    c.execute('''CREATE TABLE IF NOT EXISTS onboarding_tasks (
        id TEXT PRIMARY KEY, task_name TEXT, description TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS onboarding_progress (
        user_name TEXT, task_id TEXT, is_completed INTEGER,
        PRIMARY KEY (user_name, task_id)
    )''')
    conn.commit()
    conn.close()

# --- Logic Helpers (Robust & Bug-Free) ---
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
    # Responsive: On mobile, use full width (1 column). On desktop, center it (3 cols).
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        with st.container(border=True):
            st.markdown("<h2 style='text-align:center; color:#1f2937;'>Portal Sign In</h2>", unsafe_allow_html=True)
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

# ---------- APP: HOME DASHBOARD (RESPONSIVE) ----------
def app_home():
    st.markdown(f"## Welcome, {st.session_state['name']}")
    st.caption("Select a module to continue")
    st.write("---")
    
    # RESPONSIVE LOGIC:
    # st.columns(4) will automatically stack on mobile devices.
    # This creates "One Line" (Vertical Stack) on Mobile and "One Row" (Horizontal) on Desktop.
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        with st.container(border=True):
            st.markdown("### 📊")
            st.markdown("**KPI System**")
            st.caption("Manage OTD & FTR")
            # Actionable Full Width Button
            if st.button("Launch KPI", use_container_width=True, type="primary"):
                st.session_state['current_app'] = 'KPI'
                st.rerun()

    with c2:
        with st.container(border=True):
            st.markdown("### 🎓")
            st.markdown("**Training Hub**")
            st.caption("Track Progress")
            # Actionable Full Width Button
            if st.button("Launch Training", use_container_width=True, type="primary"):
                st.session_state['current_app'] = 'TRAINING'
                st.rerun()

    with c3:
        with st.container(border=True):
            st.markdown("### 🚀")
            st.markdown("**Onboarding**")
            st.caption("New Hire Setup")
            # Actionable Full Width Button
            if st.button("Launch Setup", use_container_width=True, type="primary"):
                st.session_state['current_app'] = 'ONBOARDING'
                st.rerun()

    with c4:
        with st.container(border=True):
            st.markdown("### 🕸️")
            st.markdown("**Skill Radar**")
            st.caption("Team Matrix")
            # Actionable Full Width Button
            if st.button("View Radar", use_container_width=True):
                st.toast("🚧 Under Construction!", icon="👷")

# ---------- APP: KPI SYSTEM ----------
def app_kpi():
    # Responsive Header
    c1, c2 = st.columns([1, 6])
    with c1:
        if st.button("⬅ Home", use_container_width=True):
            st.session_state['current_app'] = 'HOME'
            st.rerun()
    with c2:
        st.markdown("### 📊 KPI Management System")
    
    st.markdown("---")
    
    if st.session_state['role'] == "Team Leader":
        df = get_kpi_data()
        
        # Responsive Metrics: Auto-stack on mobile
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
                # Full width button for mobile touch targets
                if st.form_submit_button("Assign Task", type="primary", use_container_width=True):
                    save_kpi_task({'task_name':tname, 'name_activity_pilot':pilot, 'commitment_date_to_customer':str(comm_date), 'status':'Inprogress', 'start_date':str(date.today())})
                    st.success("Task Assigned.")
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
                # Expander works great on mobile
                with st.expander(f"{row['task_name']} ({row['status']})"):
                    st.write(f"**Due Date:** {row['commitment_date_to_customer']}")
                    with st.form(f"upd_{row['id']}"):
                        ns = st.selectbox("Update Status", ["Inprogress", "Completed", "Hold"])
                        ad = st.date_input("Completion Date", value=date.today())
                        if st.form_submit_button("Update Progress", type="primary", use_container_width=True):
                            conn = sqlite3.connect(DB_FILE)
                            conn.execute("UPDATE tasks_v2 SET status=?, actual_delivery_date=? WHERE id=?", (ns, str(ad), row['id']))
                            conn.commit(); conn.close()
                            st.success("Status Updated"); st.rerun()
        else:
            st.info("No tasks assigned.")

# ---------- APP: TRAINING TRACKER ----------
def app_training():
    c1, c2 = st.columns([1, 6])
    with c1:
        if st.button("⬅ Home", use_container_width=True):
            st.session_state['current_app'] = 'HOME'
            st.rerun()
    with c2:
        st.markdown("### 🎓 Training Tracker")
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
                if st.form_submit_button("Publish Module", type="primary", use_container_width=True):
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
            for idx, row in df.iterrows():
                with st.container(border=True):
                    # Using columns for card layout
                    c_info, c_action = st.columns([2, 1])
                    with c_info:
                        st.markdown(f"**{row['title']}**")
                        st.caption(row['description'])
                        st.markdown(f"[{row['link']}]({row['link']})")
                    with c_action:
                        c_stat = row['status']
                        n_stat = st.selectbox("Status", ["Not Started", "In Progress", "Completed"], 
                                              index=["Not Started", "In Progress", "Completed"].index(c_stat), 
                                              key=f"tr_{row['id']}", label_visibility="collapsed")
                        if n_stat != c_stat:
                            update_training_status(st.session_state['name'], row['id'], n_stat)
                            st.rerun()

# ---------- APP: ONBOARDING ----------
def app_onboarding():
    c1, c2 = st.columns([1, 6])
    with c1:
        if st.button("⬅ Home", use_container_width=True):
            st.session_state['current_app'] = 'HOME'
            st.rerun()
    with c2:
        st.markdown("### 🚀 Onboarding Hub")
    st.markdown("---")

    if st.session_state['role'] == "Team Leader":
        st.markdown("#### Checklist Configuration")
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.form("add_ob"):
                t = st.text_input("Task Name"); d = st.text_input("Details")
                if st.form_submit_button("Add Item", type="primary", use_container_width=True):
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
            
            with st.container(border=True):
                for _, row in df.iterrows():
                    is_done = bool(row['is_completed'])
                    # Touch friendly columns
                    c1, c2 = st.columns([0.15, 0.85])
                    with c1:
                        # Checkbox is native and touch friendly
                        checked = st.checkbox("", value=is_done, key=f"ob_{row['id']}")
                    with c2:
                        st.markdown(f"<div style='margin-top:5px; {'text-decoration:line-through; color:gray;' if is_done else 'font-weight:bold;'}'>{row['task_name']}</div>", unsafe_allow_html=True)
                        if not is_done: st.caption(row['description'])
                    if checked != is_done:
                        toggle_onboarding(st.session_state['name'], row['id'], checked)
                        st.rerun()

# ---------- MAIN CONTROLLER ----------
def main():
    init_db()
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['current_app'] = 'HOME'

    if st.session_state['logged_in']:
        with st.sidebar:
            # Professional Profile Image (Unsplash)
            img_url = st.session_state.get('img', '')
            if img_url:
                st.markdown(f"<img src='{img_url}' class='profile-img'>", unsafe_allow_html=True)
            
            st.markdown(f"<h3 style='text-align:center;'>{st.session_state.get('name','')}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center; color:gray;'>{st.session_state.get('role','')}</p>", unsafe_allow_html=True)
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
