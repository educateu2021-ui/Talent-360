import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import date, datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# ---------- CONFIG ----------
st.set_page_config(page_title="Corporate Portal", layout="wide", page_icon="🏢")

# ---------- STYLES ----------
st.markdown(
    """
    <style>
    .stApp { background-color: #f6f7fb; }
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    
    /* Card Styles */
    .card {
        background: #ffffff;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e5e7eb;
        padding: 20px;
        margin-bottom: 16px;
        transition: transform 0.2s;
    }
    .card:hover { transform: translateY(-2px); box-shadow: 0 10px 15px rgba(0,0,0,0.05); }
    
    /* Home Page Cards */
    .app-card {
        text-align: center;
        padding: 30px;
        cursor: pointer;
        border-top: 5px solid #3b82f6;
    }
    .app-title { font-size: 1.2rem; font-weight: 700; color: #1f2937; margin-top: 10px; }
    .app-desc { font-size: 0.9rem; color: #6b7280; margin-bottom: 20px; }
    
    /* Badges */
    .badge { padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
    .badge-success { background: #d1fae5; color: #065f46; }
    .badge-warning { background: #fef3c7; color: #92400e; }
    .badge-danger { background: #fee2e2; color: #991b1b; }
    
    /* Global Text */
    h1, h2, h3 { color: #111827; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- DATABASE & UTILS ----------
DB_FILE = "portal_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. KPI TABLE
    c.execute('''CREATE TABLE IF NOT EXISTS tasks_v2 (
        id TEXT PRIMARY KEY, name_activity_pilot TEXT, task_name TEXT, date_of_receipt TEXT,
        actual_delivery_date TEXT, commitment_date_to_customer TEXT, status TEXT,
        ftr_customer TEXT, reference_part_number TEXT, ftr_internal TEXT, otd_internal TEXT,
        description_of_activity TEXT, activity_type TEXT, ftr_quality_gate_internal TEXT,
        date_of_clarity_in_input TEXT, start_date TEXT, otd_customer TEXT, customer_remarks TEXT,
        name_quality_gate_referent TEXT, project_lead TEXT, customer_manager_name TEXT
    )''')

    # 2. TRAINING REPO
    c.execute('''CREATE TABLE IF NOT EXISTS training_repo (
        id TEXT PRIMARY KEY, title TEXT, description TEXT, link TEXT, 
        role_target TEXT, mandatory INTEGER, created_by TEXT
    )''')

    # 3. TRAINING PROGRESS
    c.execute('''CREATE TABLE IF NOT EXISTS training_progress (
        user_name TEXT, training_id TEXT, status TEXT, 
        last_updated TEXT, PRIMARY KEY (user_name, training_id)
    )''')

    # 4. ONBOARDING TASKS
    c.execute('''CREATE TABLE IF NOT EXISTS onboarding_tasks (
        id TEXT PRIMARY KEY, task_name TEXT, description TEXT
    )''')

    # 5. ONBOARDING PROGRESS
    c.execute('''CREATE TABLE IF NOT EXISTS onboarding_progress (
        user_name TEXT, task_id TEXT, is_completed INTEGER,
        PRIMARY KEY (user_name, task_id)
    )''')
    
    conn.commit()
    conn.close()

# --- KPI Helpers --- (Kept from original)
def get_kpi_data():
    conn = sqlite3.connect(DB_FILE)
    try:
        df = pd.read_sql_query("SELECT * FROM tasks_v2", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

def save_kpi_task(data, task_id=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # OTD Logic
    otd_val = "N/A"
    try:
        if data.get("actual_delivery_date") and data.get("commitment_date_to_customer"):
            a = pd.to_datetime(str(data["actual_delivery_date"]))
            cm = pd.to_datetime(str(data["commitment_date_to_customer"]))
            otd_val = "OK" if a <= cm else "NOT OK"
    except: pass

    # Insert/Update logic simplified for brevity but functional
    cols = ['name_activity_pilot', 'task_name', 'date_of_receipt', 'actual_delivery_date', 
            'commitment_date_to_customer', 'status', 'ftr_customer', 'reference_part_number', 
            'ftr_internal', 'otd_internal', 'description_of_activity', 'activity_type', 
            'ftr_quality_gate_internal', 'date_of_clarity_in_input', 'start_date', 'otd_customer', 
            'customer_remarks', 'name_quality_gate_referent', 'project_lead', 'customer_manager_name']
    
    vals = [data.get(k) for k in cols]
    vals[9] = otd_val # force otd_internal
    vals[15] = otd_val # force otd_customer

    if task_id:
        set_clause = ", ".join([f"{col}=?" for col in cols])
        c.execute(f"UPDATE tasks_v2 SET {set_clause} WHERE id=?", (*vals, task_id))
    else:
        new_id = str(uuid.uuid4())[:8]
        placeholders = ",".join(["?"] * (len(cols) + 1))
        c.execute(f"INSERT INTO tasks_v2 VALUES ({placeholders})", (new_id, *vals))
    
    conn.commit()
    conn.close()

# --- Training Helpers ---
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
    # Get all repo items
    repo = pd.read_sql_query("SELECT * FROM training_repo", conn)
    
    if user_name:
        # Get progress
        prog = pd.read_sql_query("SELECT * FROM training_progress WHERE user_name=?", conn, params=(user_name,))
        if not repo.empty:
            # Merge
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

# --- Onboarding Helpers ---
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
        conn.close()
        return pd.DataFrame()
        
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
    "leader": {"password": "123", "role": "Team Leader", "name": "Alice (Lead)"},
    "member1": {"password": "123", "role": "Team Member", "name": "Bob (Member)"},
    "member2": {"password": "123", "role": "Team Member", "name": "Charlie (Member)"}
}

def login_page():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center;'>Portal Login</h2>", unsafe_allow_html=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Sign In", use_container_width=True, type="primary"):
            if u in USERS and USERS[u]["password"] == p:
                st.session_state.update({
                    'logged_in': True, 'user': u, 
                    'role': USERS[u]['role'], 'name': USERS[u]['name'],
                    'current_app': 'HOME'
                })
                st.rerun()
            else:
                st.error("Invalid credentials.")
        st.markdown("</div>", unsafe_allow_html=True)

# ---------- APP: HOME DASHBOARD ----------
def app_home():
    st.markdown(f"## Welcome back, {st.session_state['name']}!")
    st.markdown("Select a module to continue:")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("""
        <div class='card app-card'>
            <div style='font-size:3rem;'>📊</div>
            <div class='app-title'>KPI System</div>
            <div class='app-desc'>Manage tasks, OTD, and FTR metrics.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open KPI System", use_container_width=True):
            st.session_state['current_app'] = 'KPI'
            st.rerun()

    with c2:
        st.markdown("""
        <div class='card app-card'>
            <div style='font-size:3rem;'>🎓</div>
            <div class='app-title'>Training Tracker</div>
            <div class='app-desc'>Access training repository and track progress.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Training", use_container_width=True):
            st.session_state['current_app'] = 'TRAINING'
            st.rerun()

    with c3:
        st.markdown("""
        <div class='card app-card'>
            <div style='font-size:3rem;'>🚀</div>
            <div class='app-title'>Onboarding</div>
            <div class='app-desc'>New hire checklist and documentation.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Onboarding", use_container_width=True):
            st.session_state['current_app'] = 'ONBOARDING'
            st.rerun()

# ---------- APP: KPI SYSTEM (Condensed Original) ----------
def app_kpi():
    st.markdown("### 📊 KPI Management System")
    if st.button("← Back to Home"):
        st.session_state['current_app'] = 'HOME'
        st.rerun()
    
    # Leader View (Simplified for integration)
    if st.session_state['role'] == "Team Leader":
        df = get_kpi_data()
        
        # Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Tasks", len(df))
        m2.metric("Completed", len(df[df['status']=='Completed']) if not df.empty else 0)
        pending = len(df[df['status']!='Completed']) if not df.empty else 0
        m3.metric("Pending", pending)
        
        # Add Task
        with st.expander("➕ Add New Task"):
            with st.form("new_task"):
                c1, c2 = st.columns(2)
                tname = c1.text_input("Task Name")
                pilot = c2.selectbox("Assign Pilot", [u['name'] for k,u in USERS.items() if u['role']=="Team Member"])
                comm_date = c1.date_input("Commitment Date", min_value=date.today())
                if st.form_submit_button("Create Task"):
                    save_kpi_task({'task_name':tname, 'name_activity_pilot':pilot, 'commitment_date_to_customer':str(comm_date), 'status':'Inprogress', 'start_date':str(date.today())})
                    st.success("Task Created")
                    st.rerun()
        
        # Data Table
        if not df.empty:
            st.dataframe(df[['task_name', 'name_activity_pilot', 'status', 'commitment_date_to_customer', 'otd_internal']], use_container_width=True)
        else:
            st.info("No tasks found.")

    # Member View
    else:
        df = get_kpi_data()
        my_tasks = df[df['name_activity_pilot'] == st.session_state['name']]
        
        st.markdown("#### My Assigned Tasks")
        if not my_tasks.empty:
            for _, row in my_tasks.iterrows():
                with st.expander(f"{row['task_name']} ({row['status']})"):
                    st.write(f"Due: {row['commitment_date_to_customer']}")
                    with st.form(f"upd_{row['id']}"):
                        ns = st.selectbox("Update Status", ["Inprogress", "Completed", "Hold"])
                        ad = st.date_input("Actual Date", value=date.today())
                        if st.form_submit_button("Update"):
                            # Direct update for simplicity
                            conn = sqlite3.connect(DB_FILE)
                            conn.execute("UPDATE tasks_v2 SET status=?, actual_delivery_date=? WHERE id=?", (ns, str(ad), row['id']))
                            conn.commit()
                            conn.close()
                            st.success("Updated")
                            st.rerun()
        else:
            st.info("You have no pending tasks.")

# ---------- APP: TRAINING TRACKER ----------
def app_training():
    st.markdown("### 🎓 Training Tracker")
    if st.button("← Back to Home"):
        st.session_state['current_app'] = 'HOME'
        st.rerun()

    # LEADER: Repository Management
    if st.session_state['role'] == "Team Leader":
        tabs = st.tabs(["Training Repository", "Add New Training"])
        
        with tabs[0]:
            df = get_trainings()
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Repository is empty.")
                
        with tabs[1]:
            with st.form("add_training"):
                st.write("Add new training module for the team.")
                tt = st.text_input("Training Title")
                td = st.text_area("Description")
                tl = st.text_input("Resource Link (Video/Doc)")
                tm = st.checkbox("Mandatory?")
                if st.form_submit_button("Add to Repository"):
                    add_training(tt, td, tl, "All", tm, st.session_state['name'])
                    st.success("Training added.")
                    st.rerun()

    # MEMBER: My Trainings
    else:
        df = get_trainings(user_name=st.session_state['name'])
        
        # Progress Bar
        if not df.empty:
            total = len(df)
            comp = len(df[df['status']=='Completed'])
            prog_val = comp / total
            st.progress(prog_val, text=f"Overall Progress: {int(prog_val*100)}%")
        
        st.markdown("#### Mandatory Trainings")
        
        if df.empty:
            st.info("No trainings assigned yet.")
        else:
            # Grid Layout for cards
            cols = st.columns(3)
            for idx, row in df.iterrows():
                col = cols[idx % 3]
                with col:
                    st.markdown(f"""
                    <div class='card'>
                        <div style='font-weight:bold; font-size:1.1rem'>{row['title']}</div>
                        <p style='font-size:0.9rem; color:#666'>{row['description']}</p>
                        <a href='{row['link']}' target='_blank' style='display:block; margin-bottom:10px;'>🔗 Open Resource</a>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Status Updater
                    current_status = row['status']
                    new_status = st.selectbox(
                        "Status", 
                        ["Not Started", "In Progress", "Completed"], 
                        index=["Not Started", "In Progress", "Completed"].index(current_status),
                        key=f"tr_{row['id']}"
                    )
                    
                    if new_status != current_status:
                        update_training_status(st.session_state['name'], row['id'], new_status)
                        st.rerun()
                    st.markdown("---")

# ---------- APP: ONBOARDING ----------
def app_onboarding():
    st.markdown("### 🚀 Onboarding Hub")
    if st.button("← Back to Home"):
        st.session_state['current_app'] = 'HOME'
        st.rerun()

    # LEADER: Setup Checklist
    if st.session_state['role'] == "Team Leader":
        st.markdown("#### Manage Onboarding Checklist")
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.form("add_ob"):
                t = st.text_input("Task Name")
                d = st.text_input("Description")
                if st.form_submit_button("Add Item"):
                    add_onboarding_task(t, d)
                    st.success("Item added")
                    st.rerun()
        with c2:
            conn = sqlite3.connect(DB_FILE)
            tasks = pd.read_sql_query("SELECT * FROM onboarding_tasks", conn)
            conn.close()
            if not tasks.empty:
                st.dataframe(tasks, use_container_width=True)
            else:
                st.info("No items in checklist yet.")

    # MEMBER: My Checklist
    else:
        st.markdown(f"#### Onboarding Checklist for {st.session_state['name']}")
        df = get_onboarding_status(st.session_state['name'])
        
        if df.empty:
            st.info("No onboarding tasks defined.")
        else:
            completed_count = df['is_completed'].sum()
            total_count = len(df)
            st.progress(completed_count/total_count, text=f"{int(completed_count)}/{total_count} Completed")
            
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            for _, row in df.iterrows():
                is_done = bool(row['is_completed'])
                col1, col2 = st.columns([0.1, 0.9])
                with col1:
                    # Checkbox triggers reruns
                    checked = st.checkbox("", value=is_done, key=f"ob_{row['id']}")
                with col2:
                    st.markdown(f"**{row['task_name']}**")
                    st.caption(row['description'])
                
                # Logic to update DB if changed
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

    # 1. Sidebar (Persistent Info)
    if st.session_state['logged_in']:
        with st.sidebar:
            st.image("https://api.dicebear.com/7.x/avataaars/svg?seed=" + st.session_state.get('name', 'User'), width=80)
            st.markdown(f"**{st.session_state.get('name','')}**")
            st.caption(f"{st.session_state.get('role','')}")
            st.markdown("---")
            if st.button("Logout", type="primary"):
                st.session_state.clear()
                st.rerun()

    # 2. Router
    if not st.session_state['logged_in']:
        login_page()
    else:
        app = st.session_state.get('current_app', 'HOME')
        
        if app == 'HOME':
            app_home()
        elif app == 'KPI':
            app_kpi()
        elif app == 'TRAINING':
            app_training()
        elif app == 'ONBOARDING':
            app_onboarding()

if __name__ == "__main__":
    main()
