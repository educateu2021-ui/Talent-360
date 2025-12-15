import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import date, datetime, timedelta
import time
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
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- DATABASE ----------
DB_FILE = "portal_data_final_v2.db"

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
    
    # --- DUMMY DATA GENERATION ---
    # Check if training repo is empty, if so, add dummy data
    c.execute("SELECT count(*) FROM training_repo")
    if c.fetchone()[0] == 0:
        dummy_trainings = [
            ("TR-001", "Python for Data Science", "Intro to Pandas & Streamlit", "https://python.org", "All", 1, "System"),
            ("TR-002", "Workplace Safety 101", "Fire safety and evacuation protocols", "https://safety.com", "All", 1, "System"),
            ("TR-003", "Advanced Leadership", "Managing high-performance teams", "https://hbr.org", "Team Leader", 0, "System"),
            ("TR-004", "Git & Version Control", "Branching strategies and PRs", "https://github.com", "Team Member", 1, "System"),
            ("TR-005", "Agile Methodologies", "Scrum vs Kanban breakdown", "https://agilealliance.org", "All", 0, "System")
        ]
        c.executemany("INSERT INTO training_repo VALUES (?,?,?,?,?,?,?)", dummy_trainings)
        print("Dummy training data added.")

    conn.commit()
    conn.close()

# ---------- UTILS & LOGIC ----------

# --- KPI Logic ---
def get_kpi_data():
    conn = sqlite3.connect(DB_FILE)
    try: df = pd.read_sql_query("SELECT * FROM tasks_v2", conn)
    except: df = pd.DataFrame()
    conn.close()
    return df

def save_kpi_task(data, task_id=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Robust OTD Calculation
    otd_val = "N/A"
    try:
        ad = data.get("actual_delivery_date")
        cd = data.get("commitment_date_to_customer")
        if ad and cd and ad != 'None' and cd != 'None':
            a_dt = pd.to_datetime(ad, dayfirst=True, errors='coerce')
            c_dt = pd.to_datetime(cd, dayfirst=True, errors='coerce')
            if not pd.isna(a_dt) and not pd.isna(c_dt):
                otd_val = "OK" if a_dt <= c_dt else "NOT OK"
    except Exception as e:
        print(f"OTD Calc Error: {e}")

    # Prepare Data
    cols = ['name_activity_pilot', 'task_name', 'date_of_receipt', 'actual_delivery_date', 
            'commitment_date_to_customer', 'status', 'ftr_customer', 'reference_part_number', 
            'ftr_internal', 'otd_internal', 'description_of_activity', 'activity_type', 
            'ftr_quality_gate_internal', 'date_of_clarity_in_input', 'start_date', 'otd_customer', 
            'customer_remarks', 'name_quality_gate_referent', 'project_lead', 'customer_manager_name']
    
    data['otd_internal'] = otd_val
    data['otd_customer'] = otd_val
    
    # Ensure all keys exist in data dict
    vals = [str(data.get(k, '')) if data.get(k) is not None else '' for k in cols]

    if task_id:
        set_clause = ", ".join([f"{col}=?" for col in cols])
        c.execute(f"UPDATE tasks_v2 SET {set_clause} WHERE id=?", (*vals, task_id))
    else:
        new_id = str(uuid.uuid4())[:8]
        placeholders = ",".join(["?"] * (len(cols) + 1))
        c.execute(f"INSERT INTO tasks_v2 VALUES ({placeholders})", (new_id, *vals))
    
    conn.commit()
    conn.close()

def import_kpi_csv(file):
    try:
        df = pd.read_csv(file)
        if 'id' not in df.columns:
            df['id'] = [str(uuid.uuid4())[:8] for _ in range(len(df))]
        
        required_cols = [
            "name_activity_pilot", "task_name", "date_of_receipt", "actual_delivery_date",
            "commitment_date_to_customer", "status", "ftr_customer", "reference_part_number",
            "ftr_internal", "otd_internal", "description_of_activity", "activity_type",
            "ftr_quality_gate_internal", "date_of_clarity_in_input", "start_date", "otd_customer",
            "customer_remarks", "name_quality_gate_referent", "project_lead", "customer_manager_name"
        ]
        
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
            
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Import Error: {e}")
        return False

# --- Training Logic with Import/Export ---
def add_training(title, desc, link, role, mandatory, creator):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    tid = str(uuid.uuid4())[:8]
    c.execute("INSERT INTO training_repo VALUES (?,?,?,?,?,?,?)", 
              (tid, title, desc, link, role, 1 if mandatory else 0, creator))
    conn.commit()
    conn.close()

def get_trainings(user_name=None):
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

def import_training_csv(file):
    try:
        df = pd.read_csv(file)
        # Required columns: title, description, link, role_target, mandatory
        req = ['title', 'description', 'link', 'role_target', 'mandatory']
        if not all(col in df.columns for col in req):
            st.error(f"CSV missing columns. Required: {req}")
            return False
            
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        count = 0
        for _, row in df.iterrows():
            tid = str(uuid.uuid4())[:8]
            c.execute("INSERT INTO training_repo VALUES (?,?,?,?,?,?,?)", 
                      (tid, row['title'], row['description'], row['link'], 
                       row['role_target'], int(row['mandatory']), st.session_state['name']))
            count += 1
            
        conn.commit()
        conn.close()
        st.success(f"Successfully imported {count} modules!")
        return True
    except Exception as e:
        st.error(f"Training Import Error: {e}")
        return False

# --- Onboarding Logic ---
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

# --- PLOTLY HELPERS ---
def get_analytics_chart(df):
    if df.empty: return go.Figure()
    df_local = df.copy()
    df_local['start_date'] = pd.to_datetime(df_local['start_date'], dayfirst=True, errors='coerce')
    df_local = df_local.dropna(subset=['start_date'])
    if df_local.empty: return go.Figure()
    
    df_local['month'] = df_local['start_date'].dt.strftime('%b')
    monthly = df_local.groupby(['month', 'status']).size().reset_index(name='count')
    fig = px.bar(monthly, x='month', y='count', color='status', barmode='group',
                 color_discrete_map={"Completed":"#10b981","Inprogress":"#3b82f6","Hold":"#ef4444","Cancelled":"#9ca3af"})
    fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=300)
    return fig

def get_donut(df):
    if df.empty: return go.Figure()
    total = len(df)
    completed = len(df[df['status']=='Completed'])
    completed_pct = int((completed/total)*100) if total>0 else 0
    fig = go.Figure(data=[go.Pie(labels=['Completed','Pending'], values=[completed_pct, 100-completed_pct], hole=.7, textinfo='none')])
    fig.update_layout(height=240, margin=dict(l=0,r=0,t=0,b=0), 
                      annotations=[dict(text=f"{completed_pct}%", x=0.5, y=0.5, showarrow=False, font=dict(size=20))])
    return fig

def get_ftr_otd_chart(df):
    if df.empty: return go.Figure()
    df_local = df.copy()
    df_local['actual_delivery_date'] = pd.to_datetime(df_local['actual_delivery_date'], dayfirst=True, errors='coerce')
    df_local = df_local.dropna(subset=['actual_delivery_date'])
    if df_local.empty: return go.Figure()
    df_local['month'] = df_local['actual_delivery_date'].dt.strftime('%b')
    monthly_stats = df_local.groupby('month').agg({
        'otd_internal': lambda x: ((x=='OK') | (x=='Yes')).mean()*100,
        'ftr_internal': lambda x: (x=='Yes').mean()*100
    }).reset_index()
    fig = go.Figure()
    fig.add_bar(x=monthly_stats['month'], y=monthly_stats['ftr_internal'], name='FTR %', marker_color='#8e44ad')
    fig.add_bar(x=monthly_stats['month'], y=monthly_stats['otd_internal'], name='OTD %', marker_color='#2980b9')
    fig.update_layout(barmode='group', height=300, margin=dict(l=0,r=0,t=10,b=0))
    return fig

# ---------- AUTH ----------
USERS = {
    "leader": {"password": "123", "role": "Team Leader", "name": "Sarah Jenkins", "img": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&q=80&w=200&h=200"},
    "member1": {"password": "123", "role": "Team Member", "name": "David Chen", "img": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&q=80&w=200&h=200"},
    "member2": {"password": "123", "role": "Team Member", "name": "Emily Davis", "img": "https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&q=80&w=200&h=200"}
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
                        'name': USERS[u]['name'], 'img': USERS[u]['img'], 'current_app': 'HOME'
                    })
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

# ---------- APP SECTIONS ----------

def app_home():
    st.markdown(f"## Welcome, {st.session_state['name']}")
    st.caption("Select a module below to begin.")
    st.write("---")
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        with st.container(border=True):
            st.markdown("### 📊")
            st.markdown("**KPI System**")
            st.caption("Manage OTD & FTR")
            if st.button("Launch KPI", use_container_width=True, type="primary"):
                st.session_state['current_app'] = 'KPI'
                st.rerun()

    with c2:
        with st.container(border=True):
            st.markdown("### 🎓")
            st.markdown("**Training Hub**")
            st.caption("Track Progress")
            if st.button("Launch Training", use_container_width=True, type="primary"):
                st.session_state['current_app'] = 'TRAINING'
                st.rerun()

    with c3:
        with st.container(border=True):
            st.markdown("### 🚀")
            st.markdown("**Onboarding**")
            st.caption("New Hire Setup")
            if st.button("Launch Setup", use_container_width=True, type="primary"):
                st.session_state['current_app'] = 'ONBOARDING'
                st.rerun()

    with c4:
        with st.container(border=True):
            st.markdown("### 🕸️")
            st.markdown("**Skill Radar**")
            st.caption("Team Matrix")
            if st.button("View Radar", use_container_width=True):
                st.toast("🚧 Under Construction!", icon="👷")

# --- KPI APP ---
def parse_date(d):
    if not d or d == 'None': return None
    try: return pd.to_datetime(d).date()
    except: return None

def app_kpi():
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
        
        # 1. State Management for Forms
        if 'edit_kpi_id' not in st.session_state:
            st.session_state['edit_kpi_id'] = None

        # 2. EDITOR SECTION
        if st.session_state['edit_kpi_id']:
            with st.container(border=True):
                is_new = st.session_state['edit_kpi_id'] == 'NEW'
                st.subheader("Create Task" if is_new else "Edit Task")
                
                default_data = {}
                if not is_new:
                    task_row = df[df['id'] == st.session_state['edit_kpi_id']]
                    if not task_row.empty:
                        default_data = task_row.iloc[0].to_dict()

                with st.form("kpi_editor_form"):
                    c1, c2, c3 = st.columns(3)
                    pilots = [u['name'] for k,u in USERS.items() if u['role']=="Team Member"]
                    
                    with c1:
                        tname = st.text_input("Task Name", value=default_data.get("task_name", ""))
                        pilot_val = default_data.get("name_activity_pilot")
                        p_idx = pilots.index(pilot_val) if pilot_val in pilots else 0
                        pilot = st.selectbox("Assign To", pilots, index=p_idx)
                        
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
                        ftr = st.selectbox("FTR Internal", ["Yes", "No"], index=0)
                        rem = st.text_area("Remarks", value=default_data.get("customer_remarks", ""))

                    col_sub, col_can = st.columns([1, 1])
                    with col_sub:
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
                    st.session_state['edit_kpi_id'] = None
                    st.rerun()
            st.markdown("---")

        # 3. DASHBOARD VIEW
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
                        if import_kpi_csv(up): st.success("Imported!")
                        st.rerun()
                    if not df.empty:
                        st.download_button("Export CSV", data=df.to_csv(index=False).encode('utf-8'), file_name="kpi.csv", mime="text/csv")
            with tb2:
                if st.button("➕ New Task", type="primary", use_container_width=True):
                    st.session_state['edit_kpi_id'] = "NEW"
                    st.rerun()

            c_chart, c_donut = st.columns([2, 1])
            if not df.empty:
                with c_chart:
                    st.plotly_chart(get_analytics_chart(df), use_container_width=True)
                with c_donut:
                    st.plotly_chart(get_donut(df), use_container_width=True)
            
            st.markdown("#### Active Tasks")
            if not df.empty:
                for idx, row in df.iterrows():
                    with st.container(border=True):
                        c_main, c_meta, c_btn = st.columns([4, 2, 1])
                        with c_main:
                            st.markdown(f"**{row['task_name']}**")
                            st.caption(row.get('description_of_activity',''))
                        with c_meta:
                            st.caption(f"👤 {row.get('name_activity_pilot','-')}")
                            st.caption(f"📅 Due: {row.get('commitment_date_to_customer','-')}")
                            st.write(f"**{row['status']}**")
                        with c_btn:
                            if st.button("Edit", key=f"kpi_edit_{row['id']}", use_container_width=True):
                                st.session_state['edit_kpi_id'] = row['id']
                                st.rerun()
            else:
                st.info("No tasks found.")

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
                            conn.commit()
                            conn.close()
                            st.success("Updated!")
                            st.rerun()

# --- TRAINING APP (Added Import/Export) ---
def app_training():
    c1, c2 = st.columns([1, 6])
    with c1:
        if st.button("⬅ Home", use_container_width=True):
            st.session_state['current_app'] = 'HOME'
            st.rerun()
    with c2:
        st.markdown("### 🎓 Training Hub")
    st.markdown("---")

    if st.session_state['role'] == "Team Leader":
        # Tabs for better organization
        t1, t2 = st.tabs(["Repository", "Add New"])
        
        with t1:
            df = get_trainings()
            
            # --- New: Export/Import for Training ---
            with st.expander("📂 Import / Export Training CSV"):
                col_imp, col_exp = st.columns(2)
                with col_imp:
                    up_train = st.file_uploader("Upload Training CSV", type=['csv'])
                    if up_train:
                        if import_training_csv(up_train): st.rerun()
                with col_exp:
                    if not df.empty:
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button("Download CSV", data=csv, file_name="training_repo.csv", mime="text/csv")

            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Repository empty.")
                
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
                            update_training_status(st.session_state['name'], row['id'], n_stat)
                            st.rerun()

def app_onboarding():
    c1, c2 = st.columns([1, 6])
    with c1:
        if st.button("⬅ Home", use_container_width=True):
            st.session_state['current_app'] = 'HOME'
            st.rerun()
    with c2:
        st.markdown("### 🚀 Onboarding")
    st.markdown("---")

    if st.session_state['role'] == "Team Leader":
        st.markdown("#### Setup")
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.form("add_ob_form"):
                t = st.text_input("Task"); d = st.text_input("Details")
                if st.form_submit_button("Add", type="primary", use_container_width=True):
                    add_onboarding_task(t, d); st.success("Added"); st.rerun()
        with c2:
            conn = sqlite3.connect(DB_FILE)
            tasks = pd.read_sql_query("SELECT * FROM onboarding_tasks", conn)
            conn.close()
            if not tasks.empty: st.dataframe(tasks, use_container_width=True)
    else:
        st.markdown(f"#### Checklist")
        df = get_onboarding_status(st.session_state['name'])
        if df.empty: st.info("No checklist.")
        else:
            comp = df['is_completed'].sum(); total = len(df)
            st.progress(comp/total, text=f"{int(comp)}/{total} Done")
            
            with st.container(border=True):
                for _, row in df.iterrows():
                    is_done = bool(row['is_completed'])
                    c1, c2 = st.columns([0.15, 0.85])
                    with c1:
                        checked = st.checkbox("", value=is_done, key=f"ob_chk_{row['id']}")
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
