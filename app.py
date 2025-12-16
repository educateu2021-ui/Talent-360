import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import date, datetime, timedelta
import random
import plotly.express as px
import plotly.graph_objects as go

# ---------- CONFIG ----------
st.set_page_config(page_title="Corporate Portal", layout="wide", page_icon="🏢")

# ---------- STYLES ----------
st.markdown(
    """
    <style>
    .stApp { background-color: #f8f9fa; }
    
    /* Profile Image */
    .profile-img {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        object-fit: cover;
        border: 4px solid #dfe6e9;
        display: block;
        margin: 0 auto 15px auto;
    }
    
    /* Clean Container Styling */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Button Tweak */
    div.stButton > button {
        width: 100%;
        border-radius: 6px;
        font-weight: 600;
    }
    
    /* Plotly Transparent Background */
    .js-plotly-plot .plotly .main-svg {
        background-color: rgba(0,0,0,0) !important;
    }
    
    /* Status Badges */
    .status-active { color: #10b981; font-weight: bold; }
    .status-inactive { color: #ef4444; font-weight: bold; }
    .status-yet { color: #f59e0b; font-weight: bold; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- DATABASE ----------
# Changed version to v16 to ensure new schema and data load correctly
DB_FILE = "portal_data_final_v16_demo.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. KPI Table
    c.execute('''CREATE TABLE IF NOT EXISTS tasks_v2 (
        id TEXT PRIMARY KEY, name_activity_pilot TEXT, task_name TEXT, date_of_receipt TEXT,
        actual_delivery_date TEXT, commitment_date_to_customer TEXT, status TEXT,
        ftr_customer TEXT, reference_part_number TEXT, ftr_internal TEXT, otd_internal TEXT,
        description_of_activity TEXT, activity_type TEXT, ftr_quality_gate_internal TEXT,
        date_of_clarity_in_input TEXT, start_date TEXT, otd_customer TEXT, customer_remarks TEXT,
        name_quality_gate_referent TEXT, project_lead TEXT, customer_manager_name TEXT
    )''')
    
    # 2. Training Tables
    c.execute('''CREATE TABLE IF NOT EXISTS training_repo (
        id TEXT PRIMARY KEY, title TEXT, description TEXT, link TEXT, 
        role_target TEXT, mandatory INTEGER, created_by TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS training_progress (
        user_name TEXT, training_id TEXT, status TEXT, 
        last_updated TEXT, PRIMARY KEY (user_name, training_id)
    )''')
    
    # 3. RESOURCE TRACKER TABLE (Updated with Cost Columns)
    c.execute('''CREATE TABLE IF NOT EXISTS resource_tracker_v2 (
        id TEXT PRIMARY KEY,
        employee_name TEXT,
        employee_id TEXT,
        dev_code TEXT,
        department TEXT,
        location TEXT,
        reporting_manager TEXT,
        onboarding_date TEXT,
        experience_level TEXT,
        status TEXT,
        po_details TEXT,
        remarks TEXT,
        effective_exit_date TEXT,
        backfill_status TEXT,
        reason_for_leaving TEXT,
        hourly_rate TEXT,
        hardware_daily_cost TEXT
    )''')
    
    # --- DEMO DATA INJECTION ---
    
    # Training Demo Data
    c.execute("SELECT count(*) FROM training_repo")
    if c.fetchone()[0] == 0:
        trainings = [
            ("TR-01", "Python Basics", "Introduction to Python syntax", "https://python.org", "All", 1, "System"),
            ("TR-02", "Advanced Pandas", "Data manipulation mastery", "https://pandas.pydata.org", "Team Member", 0, "System"),
            ("TR-03", "Streamlit UI", "Building interactive dashboards", "https://streamlit.io", "All", 1, "System"),
            ("TR-04", "Workplace Safety", "Fire & Health safety protocols", "https://osha.gov", "All", 1, "System"),
            ("TR-05", "Leadership 101", "Managing high-performance teams", "https://hbr.org", "Team Leader", 1, "System")
        ]
        c.executemany("INSERT INTO training_repo VALUES (?,?,?,?,?,?,?)", trainings)

    # NEW Resource Tracker Demo Data
    c.execute("SELECT count(*) FROM resource_tracker_v2")
    if c.fetchone()[0] == 0:
        # Format: ID, Name, EmpID, Dev, Dept, Loc, Mgr, Date, Exp, Status, PO, Rem, ExitDate, Backfill, Reason, HourlyRate, HardwareCost
        resources = [
            (str(uuid.uuid4())[:8], "Alice Johnson", "EMP001", "001", "Engineering", "Chennai", "Sarah Jenkins", "2024-01-10", "SENIOR", "Active", "PO-998877", "Key Resource", "", "", "", "25", "5"),
            (str(uuid.uuid4())[:8], "Bob Smith", "EMP002", "016", "Quality", "Bangalore", "Sarah Jenkins", "2024-02-15", "MID", "Active", "PO-112233", "", "", "", "", "18", "2"),
            (str(uuid.uuid4())[:8], "Charlie Davis", "EMP003", "089", "Manufacturing", "Remote", "Sarah Jenkins", "2023-11-01", "EXPERT", "Inactive", "PO-445566", "Resigned", "2024-12-01", "Yes", "Higher Salary", "40", "0"),
            (str(uuid.uuid4())[:8], "Diana Prince", "EMP004", "002", "Engineering", "Chennai", "Sarah Jenkins", "2024-03-01", "JUNIOR", "Yet to start", "PO-778899", "Waiting for laptop", "", "", "", "12", "5"),
            (str(uuid.uuid4())[:8], "Evan Wright", "EMP005", "012", "Quality", "Pune", "Sarah Jenkins", "2024-01-20", "ADVANCED", "Active", "PO-334455", "", "", "", "", "30", "5"),
            (str(uuid.uuid4())[:8], "Fiona Green", "EMP006", "005", "Engineering", "Chennai", "Sarah Jenkins", "2023-12-10", "MID", "Inactive", "PO-223344", "Personal", "2024-11-15", "No", "Relocation", "20", "5"),
            (str(uuid.uuid4())[:8], "George Hall", "EMP007", "001", "Manufacturing", "Remote", "Sarah Jenkins", "2024-05-01", "SENIOR", "Active", "PO-556677", "", "", "", "", "28", "0"),
            (str(uuid.uuid4())[:8], "Hannah Lee", "EMP008", "089", "Engineering", "Bangalore", "Sarah Jenkins", "2024-06-15", "JUNIOR", "Active", "PO-889900", "Fresher", "", "", "", "15", "2"),
            (str(uuid.uuid4())[:8], "Ian Scott", "EMP009", "016", "Quality", "Chennai", "Sarah Jenkins", "2024-04-10", "EXPERT", "Yet to start", "PO-110022", "Notice period", "", "", "", "45", "5"),
            (str(uuid.uuid4())[:8], "Jack Wilson", "EMP010", "003", "Engineering", "Pune", "Sarah Jenkins", "2024-02-28", "MID", "Active", "PO-443322", "", "", "", "", "22", "5")
        ]
        c.executemany("INSERT INTO resource_tracker_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", resources)

    # KPI 20 TASKS DEMO DATA
    c.execute("SELECT count(*) FROM tasks_v2")
    if c.fetchone()[0] == 0:
        tasks = []
        pilots = ["David Chen", "Emily Davis"]
        statuses = ["Completed", "Inprogress", "Hold", "Cancelled"]
        
        for i in range(1, 21):
            tid = str(uuid.uuid4())[:8]
            name = f"Project Task {i:02d}"
            pilot = random.choice(pilots)
            status = random.choice(statuses)
            
            # Dates
            start = date.today() - timedelta(days=random.randint(10, 60))
            due = start + timedelta(days=random.randint(5, 15))
            
            actual = None
            otd = "N/A"
            if status == "Completed":
                # Mix of Late and On Time
                delay = random.choice([-2, -1, 0, 0, 1, 5, 10]) # Negative is early/ontime, Positive is late
                actual = due + timedelta(days=delay)
                otd = "OK" if actual <= due else "NOT OK"
            else:
                actual = None
            
            ftr = "Yes" if random.random() > 0.3 else "No"
            if status == "Cancelled": ftr = "N/A"; otd="N/A"

            tasks.append((
                tid, pilot, name, str(start), str(actual) if actual else None, str(due),
                status, ftr, f"REF-{i*100}", "Yes", otd, f"Description for task {i}",
                "Standard", "Yes", str(start), otd, "None", "QA-Ref", "Lead-X", "Mgr-Y"
            ))
            
        c.executemany("INSERT INTO tasks_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", tasks)

    conn.commit()
    conn.close()

# ---------- UTILS & HELPERS ----------

# --- KPI HELPERS ---
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
        ad = data.get("actual_delivery_date")
        cd = data.get("commitment_date_to_customer")
        if ad and cd and ad != 'None' and cd != 'None':
            a_dt = pd.to_datetime(ad, dayfirst=True, errors='coerce')
            c_dt = pd.to_datetime(cd, dayfirst=True, errors='coerce')
            if not pd.isna(a_dt) and not pd.isna(c_dt):
                otd_val = "OK" if a_dt <= c_dt else "NOT OK"
    except: pass

    cols = ['name_activity_pilot', 'task_name', 'date_of_receipt', 'actual_delivery_date', 
            'commitment_date_to_customer', 'status', 'ftr_customer', 'reference_part_number', 
            'ftr_internal', 'otd_internal', 'description_of_activity', 'activity_type', 
            'ftr_quality_gate_internal', 'date_of_clarity_in_input', 'start_date', 'otd_customer', 
            'customer_remarks', 'name_quality_gate_referent', 'project_lead', 'customer_manager_name']
    
    data['otd_internal'] = otd_val; data['otd_customer'] = otd_val
    vals = [str(data.get(k, '')) if data.get(k) is not None else '' for k in cols]

    if task_id:
        set_clause = ", ".join([f"{col}=?" for col in cols])
        c.execute(f"UPDATE tasks_v2 SET {set_clause} WHERE id=?", (*vals, task_id))
    else:
        new_id = str(uuid.uuid4())[:8]
        placeholders = ",".join(["?"] * (len(cols) + 1))
        c.execute(f"INSERT INTO tasks_v2 VALUES ({placeholders})", (new_id, *vals))
    conn.commit(); conn.close()

def import_kpi_csv(file):
    try:
        df = pd.read_csv(file)
        if 'id' not in df.columns: df['id'] = [str(uuid.uuid4())[:8] for _ in range(len(df))]
        
        required_cols = ["name_activity_pilot", "task_name", "date_of_receipt", "actual_delivery_date",
            "commitment_date_to_customer", "status", "ftr_customer", "reference_part_number",
            "ftr_internal", "otd_internal", "description_of_activity", "activity_type",
            "ftr_quality_gate_internal", "date_of_clarity_in_input", "start_date", "otd_customer",
            "customer_remarks", "name_quality_gate_referent", "project_lead", "customer_manager_name"]
            
        for col in required_cols: 
            if col not in df.columns: df[col] = None
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        cols_to_keep = ['id'] + required_cols
        df = df[cols_to_keep]
        for index, row in df.iterrows():
            placeholders = ','.join(['?'] * len(row))
            sql = f"INSERT OR REPLACE INTO tasks_v2 VALUES ({placeholders})"
            c.execute(sql, tuple(row))
        conn.commit(); conn.close()
        return True
    except: return False

# --- TRAINING HELPERS ---
def add_training(title, desc, link, role, mandatory, creator):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    tid = str(uuid.uuid4())[:8]
    c.execute("INSERT INTO training_repo VALUES (?,?,?,?,?,?,?)", 
              (tid, title, desc, link, role, 1 if mandatory else 0, creator))
    conn.commit(); conn.close()

def get_trainings(user_name=None):
    conn = sqlite3.connect(DB_FILE)
    repo = pd.read_sql_query("SELECT * FROM training_repo", conn)
    if user_name:
        prog = pd.read_sql_query("SELECT * FROM training_progress WHERE user_name=?", conn, params=(user_name,))
        if not repo.empty:
            merged = pd.merge(repo, prog, left_on='id', right_on='training_id', how='left')
            merged['status'] = merged['status'].fillna('Not Started')
            conn.close(); return merged
    conn.close(); return repo

def update_training_status(user_name, training_id, status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO training_progress VALUES (?,?,?,?)", 
              (user_name, training_id, status, str(date.today())))
    conn.commit(); conn.close()

def import_training_csv(file):
    try:
        df = pd.read_csv(file)
        if 'title' not in df.columns: return False
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        for _, row in df.iterrows():
            tid = str(uuid.uuid4())[:8]
            c.execute("INSERT INTO training_repo VALUES (?,?,?,?,?,?,?)", 
                      (tid, row['title'], row.get('description',''), row.get('link',''), 
                       row.get('role_target','All'), int(row.get('mandatory',0)), st.session_state['name']))
        conn.commit(); conn.close()
        return True
    except: return False

# --- RESOURCE TRACKER (NEW) HELPERS ---
def get_resource_list():
    conn = sqlite3.connect(DB_FILE)
    try: df = pd.read_sql_query("SELECT * FROM resource_tracker_v2", conn)
    except: df = pd.DataFrame()
    conn.close()
    return df

def save_resource_entry(data, res_id=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    cols = ['employee_name', 'employee_id', 'dev_code', 'department', 'location', 
            'reporting_manager', 'onboarding_date', 'experience_level', 'status', 
            'po_details', 'remarks', 'effective_exit_date', 'backfill_status', 
            'reason_for_leaving', 'hourly_rate', 'hardware_daily_cost']
            
    vals = [str(data.get(k, '')) for k in cols]
    
    if res_id:
        set_clause = ", ".join([f"{col}=?" for col in cols])
        c.execute(f"UPDATE resource_tracker_v2 SET {set_clause} WHERE id=?", (*vals, res_id))
    else:
        new_id = str(uuid.uuid4())[:8]
        placeholders = ",".join(["?"] * (len(cols) + 1))
        c.execute(f"INSERT INTO resource_tracker_v2 VALUES ({placeholders})", (new_id, *vals))
    conn.commit(); conn.close()

# --- PLOTLY HELPERS ---
def get_analytics_chart(df):
    if df.empty: return go.Figure()
    df_local = df.copy()
    status_counts = df_local['status'].value_counts()
    fig = px.bar(x=status_counts.index, y=status_counts.values, color=status_counts.index,
                 color_discrete_map={"Completed":"#10b981","Inprogress":"#3b82f6","Hold":"#f59e0b","Cancelled":"#ef4444"})
    fig.update_layout(xaxis_title="Status", yaxis_title="Count", height=300, showlegend=False, margin=dict(l=0,r=0,t=10,b=0))
    return fig

def get_donut(df):
    if df.empty: return go.Figure()
    # FTR Donut
    ftr_yes = len(df[df['ftr_internal']=='Yes'])
    total = len(df)
    pct = int((ftr_yes/total)*100) if total>0 else 0
    fig = go.Figure(data=[go.Pie(labels=['FTR OK','FTR NOT OK'], values=[ftr_yes, total-ftr_yes], hole=.7, textinfo='none', marker_colors=['#10b981', '#ef4444'])])
    fig.update_layout(height=240, margin=dict(l=0,r=0,t=0,b=0), 
                      annotations=[dict(text=f"FTR {pct}%", x=0.5, y=0.5, showarrow=False, font=dict(size=16))])
    return fig

# ---------- AUTH ----------
USERS = {
    "leader": {"password": "123", "role": "Team Leader", "name": "Sarah Jenkins", "emp_id": "LDR-001", "tid": "TID-999", "img": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&q=80&w=200&h=200"},
    "member1": {"password": "123", "role": "Team Member", "name": "David Chen", "emp_id": "EMP-101", "tid": "TID-101", "img": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&q=80&w=200&h=200"},
    "member2": {"password": "123", "role": "Team Member", "name": "Emily Davis", "emp_id": "EMP-102", "tid": "TID-102", "img": "https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&q=80&w=200&h=200"}
}

def login_page():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        with st.container(border=True):
            st.markdown("<h2 style='text-align:center; color:#1f2937;'>Portal Sign In</h2>", unsafe_allow_html=True)
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Secure Login", use_container_width=True, type="primary"):
                if u in USERS and USERS[u]["password"] == p:
                    st.session_state.update({
                        'logged_in': True, 'user': u, 'role': USERS[u]['role'], 
                        'name': USERS[u]['name'], 'emp_id': USERS[u].get('emp_id'),
                        'tid': USERS[u].get('tid'), 'img': USERS[u]['img'], 'current_app': 'HOME'
                    })
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

# ---------- APP SECTIONS ----------
def app_home():
    st.markdown(f"## Welcome, {st.session_state['name']}")
    st.caption(f"ID: {st.session_state.get('emp_id')} | TID: {st.session_state.get('tid')}")
    st.write("---")
    
    # 1 LINE OF 4 CARDS (RESTORED TO DESKTOP DEFAULT)
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        with st.container(border=True):
            st.markdown("### 📊 **KPI System**"); st.caption("Manage OTD & FTR")
            if st.button("Launch KPI", use_container_width=True, type="primary"): st.session_state['current_app']='KPI'; st.rerun()
    with c2:
        with st.container(border=True):
            st.markdown("### 🎓 **Training**"); st.caption("Track Progress")
            if st.button("Launch Training", use_container_width=True, type="primary"): st.session_state['current_app']='TRAINING'; st.rerun()
    with c3:
        with st.container(border=True):
            st.markdown("### 🚀 **Resource Tracker**"); st.caption("Team Mgmt Only")
            if st.button("Launch Tracker", use_container_width=True, type="primary"): st.session_state['current_app']='RESOURCE'; st.rerun()
    with c4:
        with st.container(border=True):
            st.markdown("### 🕸️ **Skill Radar**"); st.caption("Team Matrix")
            if st.button("View Radar", use_container_width=True): st.toast("🚧 Under Construction!", icon="👷")

def parse_date(d):
    if not d or d == 'None' or d == '': return None
    try: return pd.to_datetime(d).date()
    except: return None

# --- FULL KPI APP ---
def app_kpi():
    c1, c2 = st.columns([1, 6])
    with c1:
        if st.button("⬅ Home", use_container_width=True): st.session_state['current_app']='HOME'; st.rerun()
    with c2: st.markdown("### 📊 KPI Management System")
    st.markdown("---")
    
    # TEAM LEADER
    if st.session_state['role'] == "Team Leader":
        df = get_kpi_data()
        
        # 1. Editor
        if 'edit_kpi_id' not in st.session_state: st.session_state['edit_kpi_id'] = None
        if st.session_state['edit_kpi_id']:
            with st.container(border=True):
                is_new = st.session_state['edit_kpi_id'] == 'NEW'
                st.subheader("Create/Edit Task")
                default_data = {}
                if not is_new:
                    task_row = df[df['id'] == st.session_state['edit_kpi_id']]
                    if not task_row.empty: default_data = task_row.iloc[0].to_dict()

                with st.form("kpi_editor_form"):
                    c1, c2, c3 = st.columns(3)
                    pilots = [u['name'] for k,u in USERS.items() if u['role']=="Team Member"]
                    with c1:
                        tname = st.text_input("Task Name", value=default_data.get("task_name", ""))
                        pilot_val = default_data.get("name_activity_pilot")
                        p_idx = pilots.index(pilot_val) if pilot_val in pilots else 0
                        pilot = st.selectbox("Assign To", pilots, index=p_idx)
                        # OTD Display (Read only)
                        st.text_input("OTD Status (Computed)", value=default_data.get("otd_customer", "N/A"), disabled=True)
                    with c2:
                        statuses = ["Hold", "Inprogress", "Completed", "Cancelled"]
                        stat_val = default_data.get("status", "Inprogress")
                        s_idx = statuses.index(stat_val) if stat_val in statuses else 1
                        status = st.selectbox("Status", statuses, index=s_idx)
                        start_d = st.date_input("Start Date", value=parse_date(default_data.get("start_date")) or date.today())
                    with c3:
                        comm_d = st.date_input("Commitment Date", value=parse_date(default_data.get("commitment_date_to_customer")) or date.today()+timedelta(days=7))
                        act_d = st.date_input("Actual Delivery", value=parse_date(default_data.get("actual_delivery_date")) or date.today())
                    st.divider()
                    c4, c5 = st.columns(2)
                    with c4:
                        desc = st.text_area("Description", value=default_data.get("description_of_activity", ""))
                        ref_part = st.text_input("Ref Part #", value=default_data.get("reference_part_number", ""))
                    with c5:
                        ftr_opts = ["Yes", "No", "Awaited"]
                        ftr_val = default_data.get("ftr_internal", "Yes")
                        ftr = st.selectbox("FTR Internal", ftr_opts, index=ftr_opts.index(ftr_val) if ftr_val in ftr_opts else 0)
                        rem = st.text_area("Remarks", value=default_data.get("customer_remarks", ""))
                    
                    if st.form_submit_button("💾 Save Task", type="primary", use_container_width=True):
                        payload = {
                            "task_name": tname, "name_activity_pilot": pilot, "status": status,
                            "start_date": str(start_d), "commitment_date_to_customer": str(comm_d),
                            "actual_delivery_date": str(act_d), "description_of_activity": desc,
                            "reference_part_number": ref_part, "ftr_internal": ftr, "customer_remarks": rem,
                            "date_of_receipt": str(date.today()), "activity_type": "Standard"
                        }
                        save_kpi_task(payload, None if is_new else st.session_state['edit_kpi_id'])
                        st.success("Saved successfully!")
                        st.session_state['edit_kpi_id'] = None
                        st.rerun()
                if st.button("Cancel", use_container_width=True):
                    st.session_state['edit_kpi_id'] = None; st.rerun()
            st.markdown("---")

        # 2. Dashboard
        if not st.session_state['edit_kpi_id']:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Tasks", len(df))
            m2.metric("In Progress", len(df[df['status']=='Inprogress']) if not df.empty else 0)
            m3.metric("On Hold", len(df[df['status']=='Hold']) if not df.empty else 0)
            m4.metric("Completed", len(df[df['status']=='Completed']) if not df.empty else 0)
            
            tb1, tb2 = st.columns([3, 1])
            with tb1:
                with st.expander("📂 CSV Import/Export"):
                    up = st.file_uploader("Import CSV", type=['csv'])
                    if up: 
                        if import_kpi_csv(up): st.success("Imported!"); st.rerun()
                    if not df.empty:
                        st.download_button("Export CSV", data=df.to_csv(index=False).encode('utf-8'), file_name="kpi.csv", mime="text/csv")
            with tb2:
                if st.button("➕ New Task", type="primary", use_container_width=True):
                    st.session_state['edit_kpi_id'] = "NEW"; st.rerun()

            c_chart, c_donut = st.columns([2, 1])
            if not df.empty:
                with c_chart: st.plotly_chart(get_analytics_chart(df), use_container_width=True)
                with c_donut: st.plotly_chart(get_donut(df), use_container_width=True)
            
            st.markdown("#### Active Tasks")
            if not df.empty:
                # Paginate slightly for performance
                for idx, row in df.iterrows():
                    with st.container(border=True):
                        c_main, c_meta, c_btn = st.columns([4, 2, 1])
                        with c_main:
                            st.markdown(f"**{row['task_name']}**")
                            st.caption(row.get('description_of_activity',''))
                        with c_meta:
                            st.caption(f"👤 {row.get('name_activity_pilot','-')}")
                            st.caption(f"📅 Due: {row.get('commitment_date_to_customer','-')}")
                            # Status Badge
                            st_color = "black"
                            if row['status'] == "Completed": st_color = "#10b981"
                            elif row['status'] == "Cancelled": st_color = "#ef4444"
                            elif row['status'] == "Hold": st_color = "#f59e0b"
                            else: st_color = "#3b82f6"
                            st.markdown(f"<span style='color:{st_color}; font-weight:bold;'>{row['status']}</span> | OTD: {row.get('otd_customer','-')}", unsafe_allow_html=True)
                        with c_btn:
                            if st.button("Edit", key=f"kpi_edit_{row['id']}", use_container_width=True):
                                st.session_state['edit_kpi_id'] = row['id']; st.rerun()
            else: st.info("No tasks found.")

    # MEMBER
    else:
        df = get_kpi_data()
        my_tasks = df[df['name_activity_pilot'] == st.session_state['name']]
        st.metric("My Pending Tasks", len(my_tasks[my_tasks['status']!='Completed']) if not my_tasks.empty else 0)
        if not my_tasks.empty:
            for idx, row in my_tasks.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{row['task_name']}**")
                    st.write(f"Due: {row.get('commitment_date_to_customer','-')}")
                    with st.form(key=f"my_task_{row['id']}"):
                        c1, c2 = st.columns(2)
                        curr_stat = row.get('status', 'Inprogress')
                        idx_stat = ["Inprogress", "Completed", "Hold"].index(curr_stat) if curr_stat in ["Inprogress", "Completed", "Hold"] else 0
                        ns = c1.selectbox("Status", ["Inprogress", "Completed", "Hold"], index=idx_stat)
                        ad = c2.date_input("Actual Delivery", value=parse_date(row.get('actual_delivery_date')) or date.today())
                        if st.form_submit_button("Update", type="primary"):
                            conn = sqlite3.connect(DB_FILE)
                            conn.execute("UPDATE tasks_v2 SET status=?, actual_delivery_date=? WHERE id=?", (ns, str(ad), row['id']))
                            conn.commit(); conn.close()
                            st.success("Updated!"); st.rerun()

# --- TRAINING APP ---
def app_training():
    c1, c2 = st.columns([1, 6])
    with c1:
        if st.button("⬅ Home", use_container_width=True): st.session_state['current_app']='HOME'; st.rerun()
    with c2: st.markdown("### 🎓 Training Hub")
    st.markdown("---")

    if st.session_state['role'] == "Team Leader":
        t1, t2 = st.tabs(["Repository", "Add New"])
        with t1:
            df = get_trainings()
            with st.expander("📂 Import / Export"):
                col_imp, col_exp = st.columns(2)
                with col_imp:
                    up_train = st.file_uploader("Upload CSV", type=['csv'])
                    if up_train:
                        if import_training_csv(up_train): st.rerun()
                with col_exp:
                    if not df.empty:
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button("Download CSV", data=csv, file_name="training_repo.csv", mime="text/csv")
            if not df.empty: st.dataframe(df, use_container_width=True)
            else: st.info("Repository empty.")
        with t2:
            with st.form("add_training_form"):
                tt = st.text_input("Title")
                td = st.text_area("Desc")
                tl = st.text_input("Link")
                tm = st.checkbox("Mandatory")
                if st.form_submit_button("Publish", type="primary", use_container_width=True):
                    add_training(tt, td, tl, "All", tm, st.session_state['name'])
                    st.success("Published."); st.rerun()
    else:
        df = get_trainings(user_name=st.session_state['name'])
        if not df.empty:
            comp = len(df[df['status']=='Completed'])
            st.progress(comp/len(df), text=f"Progress: {int((comp/len(df))*100)}%")
        st.markdown("#### Modules")
        if df.empty: st.info("No training found.")
        else:
            for idx, row in df.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"**{row['title']}**")
                        st.caption(row['description'])
                        st.markdown(f"[{row['link']}]({row['link']})")
                    with c2:
                        c_stat = row['status']
                        n_stat = st.selectbox("Status", ["Not Started", "In Progress", "Completed"], 
                                                index=["Not Started", "In Progress", "Completed"].index(c_stat), 
                                                key=f"tr_stat_{row['id']}", label_visibility="collapsed")
                        if n_stat != c_stat:
                            update_training_status(st.session_state['name'], row['id'], n_stat); st.rerun()

# --- RESOURCE TRACKER APP (UPDATED) ---
def app_resource():
    c1, c2 = st.columns([1, 6])
    with c1:
        if st.button("⬅ Home", use_container_width=True): st.session_state['current_app']='HOME'; st.rerun()
    with c2: st.markdown("### 🚀 Resource Tracker")
    st.markdown("---")

    # 🛑 ACCESS RESTRICTION: TEAM LEADERS ONLY 🛑
    if st.session_state['role'] != "Team Leader":
        st.error("🚫 ACCESS RESTRICTED")
        st.warning(f"Hello {st.session_state['name']}, this module is restricted to Team Leaders and above.")
        return

    # --- STATE MANAGEMENT ---
    if 'res_edit_id' not in st.session_state: st.session_state['res_edit_id'] = None
    if 'res_view_mode' not in st.session_state: st.session_state['res_view_mode'] = 'LIST' 

    # --- LIST VIEW WITH FILTERS ---
    if st.session_state['res_view_mode'] == 'LIST':
        
        # 1. SEARCH & FILTERS SECTION (Collapsible)
        with st.expander("🔎 Search & Filters", expanded=False):
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                search_query = st.text_input("Search Name/ID/Dev", placeholder="Type to search...")
            with fc2:
                dept_filter = st.multiselect("Filter Department", ["Engineering", "Quality", "Manufacturing"])
            with fc3:
                stat_filter = st.multiselect("Filter Status", ["Active", "Inactive", "Yet to start"])

        # 2. DATA TABLE & ACTIONS
        col_act, col_add = st.columns([5, 1])
        with col_act:
            st.markdown("#### Resource List")
        with col_add:
            if st.button("➕ Add New", type="primary", use_container_width=True):
                st.session_state['res_edit_id'] = None
                st.session_state['res_view_mode'] = 'FORM'
                st.rerun()
        
        df = get_resource_list()
        
        if not df.empty:
            # Apply Filters
            if search_query:
                df = df[df.apply(lambda row: search_query.lower() in str(row.values).lower(), axis=1)]
            if dept_filter:
                df = df[df['department'].isin(dept_filter)]
            if stat_filter:
                df = df[df['status'].isin(stat_filter)]
            
            # --- CUSTOMIZE DATAFRAME FOR DISPLAY ---
            # Calculate derived costs for display
            df['hourly_rate'] = pd.to_numeric(df['hourly_rate'], errors='coerce').fillna(0)
            df['hardware_daily_cost'] = pd.to_numeric(df['hardware_daily_cost'], errors='coerce').fillna(0)
            df['Daily_Labor_Cost_$'] = df['hourly_rate'] * 8
            df['Total_Daily_Bill_$'] = df['Daily_Labor_Cost_$'] + df['hardware_daily_cost']
            
            display_cols = ['employee_name', 'employee_id', 'department', 'status', 'location', 
                            'hourly_rate', 'Daily_Labor_Cost_$', 'Total_Daily_Bill_$']
            
            st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
            
            st.markdown("##### Manage Entry")
            if len(df) > 0:
                sel_res = st.selectbox("Select Resource to Edit/View", df['employee_name'] + " (" + df['employee_id'] + ")")
                if st.button("Edit Selected", use_container_width=True):
                    # Find ID
                    sel_id = df[df['employee_name'] + " (" + df['employee_id'] + ")" == sel_res].iloc[0]['id']
                    st.session_state['res_edit_id'] = sel_id
                    st.session_state['res_view_mode'] = 'FORM'
                    st.rerun()
            else:
                st.info("No records match your filters.")
        else:
            st.info("No resources found in database.")

    # --- FORM VIEW (ADD/EDIT) ---
    elif st.session_state['res_view_mode'] == 'FORM':
        res_id = st.session_state['res_edit_id']
        is_edit = res_id is not None
        
        st.subheader("Edit Resource" if is_edit else "New Resource Onboarding")
        
        # Load Data if Edit
        d = {}
        if is_edit:
            df = get_resource_list()
            row = df[df['id'] == res_id]
            if not row.empty: d = row.iloc[0].to_dict()

        # We do NOT use st.form here to allow dynamic UI updates
        with st.container(border=True):
            col1, col2 = st.columns(2)
            
            with col1:
                emp_name = st.text_input("Employee Name", value=d.get('employee_name', ''))
                dev_opts = ["001", "002", "003", "005", "012", "016", "089"]
                dev_val = d.get('dev_code', '001')
                dev_code = st.selectbox("DEV", dev_opts, index=dev_opts.index(dev_val) if dev_val in dev_opts else 0)
                loc_opts = ["Chennai", "Bangalore", "Pune", "Remote"]
                loc_val = d.get('location', 'Chennai')
                location = st.selectbox("Location", loc_opts, index=loc_opts.index(loc_val) if loc_val in loc_opts else 0)
                o_date = st.date_input("Onboarding Start Date", value=parse_date(d.get('onboarding_date')) or date.today())
                stat_opts = ["Yet to start", "Active", "Inactive"]
                stat_val = d.get('status', 'Yet to start')
                status = st.selectbox("Status", stat_opts, index=stat_opts.index(stat_val) if stat_val in stat_opts else 0)

            with col2:
                emp_id = st.text_input("Employee ID", value=d.get('employee_id', ''))
                dept_opts = ["Engineering", "Quality", "Manufacturing"]
                dept_val = d.get('department', 'Engineering')
                department = st.selectbox("Department", dept_opts, index=dept_opts.index(dept_val) if dept_val in dept_opts else 0)
                rep_man = st.selectbox("Reporting Manager", ["Sarah Jenkins", "Mike Ross", "Harvey Specter"], index=0)
                exp_opts = ["JUNIOR", "MID", "ADVANCED", "SENIOR", "EXPERT"]
                exp_val = d.get('experience_level', 'JUNIOR')
                exp_lvl = st.selectbox("Experience Level", exp_opts, index=exp_opts.index(exp_val) if exp_val in exp_opts else 0)
                po_det = st.text_input("PO Details", value=d.get('po_details', ''), placeholder="PO number")

            # --- FINANCIALS (NEW SECTION) ---
            st.markdown("##### 💲 Financials (USD)")
            fin1, fin2, fin3, fin4 = st.columns(4)
            with fin1:
                # User inputs Hourly Rate
                hr_rate = st.number_input("Hourly Rate ($)", min_value=0.0, value=float(d.get('hourly_rate', 0.0)))
            with fin2:
                # User inputs Hardware Cost
                hw_cost = st.number_input("Hardware Cost (Daily $)", min_value=0.0, value=float(d.get('hardware_daily_cost', 0.0)))
            with fin3:
                # Auto Calculate Labor Daily
                lab_daily = hr_rate * 8
                st.metric("Labor Daily (8h)", f"${lab_daily:,.2f}")
            with fin4:
                # Auto Calculate Total Daily
                tot_daily = lab_daily + hw_cost
                st.metric("Total Daily Bill", f"${tot_daily:,.2f}")

            # Remarks
            remarks = st.text_area("Remarks if any", value=d.get('remarks', ''))

            # --- CONDITIONAL BRANCHING FOR INACTIVE ---
            exit_date = None
            backfill = "No"
            reason = ""
            
            if status == "Inactive":
                st.markdown("---")
                st.warning("⚠️ Resource Inactive - Exit Details Required")
                ec1, ec2, ec3 = st.columns(3)
                with ec1:
                    exit_date = st.date_input("Effective Exit Date", value=parse_date(d.get('effective_exit_date')) or date.today())
                with ec2:
                    bf_val = d.get('backfill_status', 'No')
                    backfill = st.selectbox("Backfill Status", ["Yes", "No"], index=["Yes", "No"].index(bf_val) if bf_val in ["Yes", "No"] else 1)
                with ec3:
                    reason = st.text_input("Reason for Leaving", value=d.get('reason_for_leaving', ''))

            st.markdown("<br>", unsafe_allow_html=True)
            
            # ACTIONS
            b1, b2 = st.columns([1, 1])
            with b1:
                if st.button("Cancel", use_container_width=True):
                    st.session_state['res_view_mode'] = 'LIST'
                    st.session_state['res_edit_id'] = None
                    st.rerun()
            with b2:
                if st.button("💾 Save Record", type="primary", use_container_width=True):
                    # Validation
                    if not emp_name or not emp_id:
                        st.error("Name and Employee ID are required.")
                    elif status == "Inactive" and not reason:
                        st.error("Reason for Leaving is mandatory for Inactive status.")
                    else:
                        payload = {
                            "employee_name": emp_name, "employee_id": emp_id, "dev_code": dev_code,
                            "department": department, "location": location, "reporting_manager": rep_man,
                            "onboarding_date": str(o_date), "experience_level": exp_lvl, "status": status,
                            "po_details": po_det, "remarks": remarks,
                            "effective_exit_date": str(exit_date) if exit_date else "",
                            "backfill_status": backfill if status == "Inactive" else "",
                            "reason_for_leaving": reason if status == "Inactive" else "",
                            "hourly_rate": str(hr_rate),
                            "hardware_daily_cost": str(hw_cost)
                        }
                        save_resource_entry(payload, res_id)
                        st.success("Resource Saved Successfully!")
                        st.session_state['res_view_mode'] = 'LIST'
                        st.session_state['res_edit_id'] = None
                        st.rerun()

# ---------- MAIN CONTROLLER ----------
def main():
    init_db()
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['current_app'] = 'HOME'

    if st.session_state['logged_in']:
        with st.sidebar:
            img_url = st.session_state.get('img', '')
            if img_url: st.markdown(f"<img src='{img_url}' class='profile-img'>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align:center;'>{st.session_state.get('name','')}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center; color:gray;'>{st.session_state.get('role','')}</p>", unsafe_allow_html=True)
            st.markdown("---")
            if st.button("Sign Out", use_container_width=True): st.session_state.clear(); st.rerun()

    if not st.session_state['logged_in']:
        login_page()
    else:
        app = st.session_state.get('current_app', 'HOME')
        if app == 'HOME': app_home()
        elif app == 'KPI': app_kpi()
        elif app == 'TRAINING': app_training()
        elif app == 'RESOURCE': app_resource()

if __name__ == "__main__":
    main()
