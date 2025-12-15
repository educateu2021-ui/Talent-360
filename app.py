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
    
    /* Card Container Polish */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Button Polish */
    div.stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Chart Container Background */
    .js-plotly-plot .plotly .main-svg {
        background-color: rgba(0,0,0,0) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- DATABASE & UTILS ----------
DB_FILE = "portal_data_v8.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # KPI Table (Full Schema)
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
        if data.get("actual_delivery_date") and data.get("commitment_date_to_customer"):
            a = pd.to_datetime(str(data["actual_delivery_date"]), dayfirst=True, errors='coerce')
            cm = pd.to_datetime(str(data["commitment_date_to_customer"]), dayfirst=True, errors='coerce')
            if not pd.isna(a) and not pd.isna(cm):
                otd_val = "OK" if a <= cm else "NOT OK"
    except: pass
    
    cols = ['name_activity_pilot', 'task_name', 'date_of_receipt', 'actual_delivery_date', 
            'commitment_date_to_customer', 'status', 'ftr_customer', 'reference_part_number', 
            'ftr_internal', 'otd_internal', 'description_of_activity', 'activity_type', 
            'ftr_quality_gate_internal', 'date_of_clarity_in_input', 'start_date', 'otd_customer', 
            'customer_remarks', 'name_quality_gate_referent', 'project_lead', 'customer_manager_name']
    
    # Update OTD fields in data dict
    data['otd_internal'] = otd_val
    data['otd_customer'] = otd_val
    
    vals = [data.get(k) for k in cols]
    
    if task_id:
        set_clause = ", ".join([f"{col}=?" for col in cols])
        c.execute(f"UPDATE tasks_v2 SET {set_clause} WHERE id=?", (*vals, task_id))
    else:
        new_id = str(uuid.uuid4())[:8]
        placeholders = ",".join(["?"] * (len(cols) + 1))
        c.execute(f"INSERT INTO tasks_v2 VALUES ({placeholders})", (new_id, *vals))
    conn.commit()
    conn.close()

def update_task_status_simple(task_id, new_status, new_actual_date=None):
    # Logic to update just status/date for members
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Calculate OTD if date provided
    otd_val = "N/A"
    if new_actual_date:
        c.execute("SELECT commitment_date_to_customer FROM tasks_v2 WHERE id=?", (task_id,))
        res = c.fetchone()
        if res and res[0]:
            try:
                cm = pd.to_datetime(res[0], dayfirst=True, errors='coerce')
                ad = pd.to_datetime(str(new_actual_date), dayfirst=True, errors='coerce')
                otd_val = "OK" if ad <= cm else "NOT OK"
            except: pass
            
    if new_actual_date:
        c.execute("UPDATE tasks_v2 SET status=?, actual_delivery_date=?, otd_internal=?, otd_customer=? WHERE id=?", 
                  (new_status, str(new_actual_date), otd_val, otd_val, task_id))
    else:
        c.execute("UPDATE tasks_v2 SET status=? WHERE id=?", (new_status, task_id))
    conn.commit()
    conn.close()

def import_data_from_csv(file):
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
        
        # Ensure cols exist
        for col in required_cols:
            if col not in df.columns: df[col] = None
            
        # Select and save
        cols_to_keep = ['id'] + required_cols
        df = df[cols_to_keep]
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
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

# --- PLOTLY HELPERS ---
def get_analytics_chart(df):
    if df.empty: return go.Figure()
    df_local = df.copy()
    df_local['start_date'] = pd.to_datetime(df_local['start_date'], dayfirst=True, errors='coerce')
    df_local = df_local.dropna(subset=['start_date'])
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

# --- TRAINING/ONBOARDING HELPERS ---
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
        "password": "123", "role": "Team Leader", "name": "Sarah Jenkins", 
        "img": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&q=80&w=200&h=200"
    },
    "member1": {
        "password": "123", "role": "Team Member", "name": "David Chen", 
        "img": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&q=80&w=200&h=200"
    },
    "member2": {
        "password": "123", "role": "Team Member", "name": "Emily Davis", 
        "img": "https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&q=80&w=200&h=200"
    }
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
                        'logged_in': True, 'user': u, 
                        'role': USERS[u]['role'], 'name': USERS[u]['name'],
                        'img': USERS[u]['img'],
                        'current_app': 'HOME'
                    })
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

# ---------- APP: HOME DASHBOARD (2x2 GRID RESPONSIVE) ----------
def app_home():
    st.markdown(f"## Welcome, {st.session_state['name']}")
    st.caption("Select a module to continue")
    st.write("---")
    
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        with st.container(border=True):
            st.markdown("### 📊")
            st.markdown("**KPI System**")
            st.caption("Projects & OTD")
            if st.button("Launch KPI", use_container_width=True, type="primary"):
                st.session_state['current_app'] = 'KPI'
                st.rerun()

    with r1c2:
        with st.container(border=True):
            st.markdown("### 🎓")
            st.markdown("**Training Hub**")
            st.caption("Track Progress")
            if st.button("Launch Training", use_container_width=True, type="primary"):
                st.session_state['current_app'] = 'TRAINING'
                st.rerun()
    
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        with st.container(border=True):
            st.markdown("### 🚀")
            st.markdown("**Onboarding**")
            st.caption("Checklists")
            if st.button("Launch Setup", use_container_width=True, type="primary"):
                st.session_state['current_app'] = 'ONBOARDING'
                st.rerun()

    with r2c2:
        with st.container(border=True):
            st.markdown("### 🕸️")
            st.markdown("**Skill Radar**")
            st.caption("Team Matrix")
            if st.button("View Radar", use_container_width=True):
                st.toast("🚧 Under Construction!", icon="👷")

# ---------- APP: KPI SYSTEM (INTEGRATED) ----------
def parse_date_like(d):
    if d is None: return None
    if isinstance(d, date): return d
    try: return pd.to_datetime(d, dayfirst=True, errors='coerce').date()
    except: return None

def kpi_task_form(task_id=None, default_data=None):
    if default_data is None: default_data = {}
    title = "Edit Task" if task_id else "Create New Task"
    
    def safe_val(k, fallback=""):
        v = default_data.get(k)
        return v if v is not None else fallback

    with st.container(border=True):
        st.subheader(title)
        with st.form(key=f"kpi_form_{task_id or 'new'}"):
            c1, c2, c3 = st.columns(3)
            pilots = [u['name'] for k,u in USERS.items() if u['role']=="Team Member"]
            
            with c1:
                tname = st.text_input("Task Name", value=safe_val("task_name"))
                p_idx = pilots.index(safe_val("name_activity_pilot")) if safe_val("name_activity_pilot") in pilots else 0
                pilot = st.selectbox("Assign To", pilots, index=p_idx)
                act_type = st.selectbox("Activity Type", ["3d development","2d drawing","Release"], index=0)
            
            with c2:
                statuses = ["Hold","Inprogress","Completed","Cancelled"]
                s_idx = statuses.index(safe_val("status")) if safe_val("status") in statuses else 1
                status = st.selectbox("Status", statuses, index=s_idx)
                start_d = st.date_input("Start Date", value=parse_date_like(safe_val("start_date")) or date.today())
                rec_d = st.date_input("Receipt Date", value=parse_date_like(safe_val("date_of_receipt")) or date.today())
            
            with c3:
                comm_d = st.date_input("Commitment Date", value=parse_date_like(safe_val("commitment_date_to_customer")) or (date.today()+timedelta(days=7)))
                act_d = st.date_input("Actual Delivery", value=parse_date_like(safe_val("actual_delivery_date")) or date.today())
                ref_part = st.text_input("Ref Part #", value=safe_val("reference_part_number"))

            st.markdown("---")
            c4, c5 = st.columns(2)
            with c4:
                ftr = st.selectbox("FTR Internal", ["Yes", "No"], index=0)
                desc = st.text_area("Description", value=safe_val("description_of_activity"))
            with c5:
                rem = st.text_area("Remarks", value=safe_val("customer_remarks"))
                plead = st.text_input("Project Lead", value=safe_val("project_lead", st.session_state['name']))

            if st.form_submit_button("Save Task", type="primary"):
                payload = {
                    "task_name": tname, "name_activity_pilot": pilot, "activity_type": act_type,
                    "status": status, "start_date": str(start_d), "date_of_receipt": str(rec_d),
                    "commitment_date_to_customer": str(comm_d), "actual_delivery_date": str(act_d),
                    "reference_part_number": ref_part, "ftr_internal": ftr, 
                    "description_of_activity": desc, "customer_remarks": rem, "project_lead": plead,
                    "date_of_clarity_in_input": str(rec_d) # Defaulting for simplicity
                }
                save_kpi_task(payload, task_id)
                st.success("Task Saved!")
                st.session_state['edit_kpi_id'] = None # Close form
                st.rerun()

def app_kpi():
    # Header
    c1, c2 = st.columns([1, 6])
    with c1:
        if st.button("⬅ Home", use_container_width=True):
            st.session_state['current_app'] = 'HOME'
            st.rerun()
    with c2:
        st.markdown("### 📊 KPI Management System")
    st.markdown("---")
    
    # --- TEAM LEADER VIEW ---
    if st.session_state['role'] == "Team Leader":
        df = get_kpi_data()
        
        # 1. Top Metrics (Native Streamlit)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Jobs", len(df))
        m2.metric("In Progress", len(df[df['status']=='Inprogress']) if not df.empty else 0)
        m3.metric("On Hold", len(df[df['status']=='Hold']) if not df.empty else 0)
        m4.metric("Completed", len(df[df['status']=='Completed']) if not df.empty else 0)
        
        st.write("")
        
        # 2. Action Bar (Import / Export / New)
        ac1, ac2, ac3 = st.columns([2, 1, 1])
        with ac1:
            with st.expander("📂 Import / Export"):
                up = st.file_uploader("Import CSV", type=['csv'])
                if up:
                    if import_data_from_csv(up): st.success("Data Imported!")
                
                csv_data = df.to_csv(index=False).encode('utf-8') if not df.empty else ""
                st.download_button("Download CSV", data=csv_data, file_name="kpi_data.csv", mime="text/csv")
        
        with ac3:
            if st.button("➕ New Task", type="primary", use_container_width=True):
                st.session_state['edit_kpi_id'] = "NEW"

        # 3. Form Logic (Conditional Render)
        if st.session_state.get('edit_kpi_id'):
            if st.session_state['edit_kpi_id'] == "NEW":
                kpi_task_form()
            else:
                # Find task data
                task_row = df[df['id'] == st.session_state['edit_kpi_id']].iloc[0].to_dict()
                # Clean up None values for form
                clean_row = {k: (v if v is not None else "") for k,v in task_row.items()}
                kpi_task_form(st.session_state['edit_kpi_id'], clean_row)
            
            if st.button("Cancel Form"):
                st.session_state['edit_kpi_id'] = None
                st.rerun()

        st.write("---")

        # 4. Analytics Row
        c_chart, c_donut = st.columns([2, 1])
        with c_chart:
            with st.container(border=True):
                st.markdown("**Monthly Activity**")
                st.plotly_chart(get_analytics_chart(df), use_container_width=True)
        with c_donut:
            with st.container(border=True):
                st.markdown("**Completion Rate**")
                st.plotly_chart(get_donut(df), use_container_width=True)

        # 5. Task List with Edit Buttons
        st.markdown("#### Active Tasks")
        if not df.empty:
            # Filter Logic
            fc1, fc2 = st.columns([2, 2])
            with fc1:
                search = st.text_input("Search Task")
            
            df_display = df.copy()
            if search:
                df_display = df_display[df_display['task_name'].str.contains(search, case=False, na=False)]
            
            # Custom List View using Containers (Responsive)
            for idx, row in df_display.iterrows():
                with st.container(border=True):
                    ic1, ic2, ic3, ic4 = st.columns([3, 2, 2, 1])
                    with ic1:
                        st.markdown(f"**{row['task_name']}**")
                        st.caption(row.get('description_of_activity', ''))
                    with ic2:
                        st.caption("Pilot")
                        st.write(f"👤 {row.get('name_activity_pilot', '-')}")
                    with ic3:
                        st.caption("Deadline")
                        st.write(f"📅 {row.get('commitment_date_to_customer', '-')}")
                    with ic4:
                        st.caption("Status")
                        st.write(f"**{row['status']}**")
                        if st.button("Edit", key=f"btn_edit_{row['id']}"):
                            st.session_state['edit_kpi_id'] = row['id']
                            st.rerun()
        else:
            st.info("No tasks found.")
            
        # 6. Team Perf & FTR/OTD
        st.write("---")
        pc1, pc2 = st.columns(2)
        with pc1:
            with st.container(border=True):
                st.markdown("**OTD & FTR Trends**")
                st.plotly_chart(get_ftr_otd_chart(df), use_container_width=True)
        with pc2:
            with st.container(border=True):
                st.markdown("**Team Performance**")
                if not df.empty:
                    members = df['name_activity_pilot'].unique()
                    for m in members:
                        if m:
                            mt = df[df['name_activity_pilot']==m]
                            comp = len(mt[mt['status']=='Completed'])
                            st.markdown(f"**{m}**: {len(mt)} Tasks ({int((comp/len(mt))*100)}% Done)")
                            st.progress(comp/len(mt) if len(mt)>0 else 0)

    # --- TEAM MEMBER VIEW ---
    else:
        df = get_kpi_data()
        my_tasks = df[df['name_activity_pilot'] == st.session_state['name']]
        
        # Stats
        m1, m2 = st.columns(2)
        m1.metric("My Pending Tasks", len(my_tasks[my_tasks['status']!='Completed']))
        m2.metric("My Completed", len(my_tasks[my_tasks['status']=='Completed']))
        
        st.markdown("#### My Assigned Tasks")
        if not my_tasks.empty:
            for _, row in my_tasks.iterrows():
                with st.expander(f"{row['task_name']} ({row['status']})"):
                    st.write(f"**Due Date:** {row['commitment_date_to_customer']}")
                    st.write(f"**Description:** {row['description_of_activity']}")
                    
                    with st.form(f"upd_{row['id']}"):
                        c_a, c_b = st.columns(2)
                        ns = c_a.selectbox("Status", ["Inprogress", "Completed", "Hold"], 
                                           index=["Inprogress", "Completed", "Hold"].index(row['status']) if row['status'] in ["Inprogress", "Completed", "Hold"] else 0)
                        ad = c_b.date_input("Actual Delivery Date", value=parse_date_like(row['actual_delivery_date']) or date.today())
                        
                        if st.form_submit_button("Update Progress", type="primary", use_container_width=True):
                            update_task_status_simple(row['id'], ns, ad)
                            st.success("Status Updated")
                            st.rerun()
        else:
            st.info("You have no tasks assigned.")

# ---------- APP: TRAINING TRACKER ----------
def app_training():
    c1, c2 = st.columns([1, 5])
    with c1:
        if st.button("⬅ Home", use_container_width=True):
            st.session_state['current_app'] = 'HOME'
            st.rerun()
    with c2:
        st.markdown("### 🎓 Training Hub")
    st.markdown("---")

    if st.session_state['role'] == "Team Leader":
        tabs = st.tabs(["Repo", "Add New"])
        with tabs[0]:
            df = get_trainings()
            if not df.empty: st.dataframe(df, use_container_width=True)
            else: st.info("Repository empty.")
        with tabs[1]:
            with st.form("add_training"):
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
                    st.markdown(f"**{row['title']}**")
                    st.caption(row['description'])
                    st.markdown(f"[{row['link']}]({row['link']})")
                    c_stat = row['status']
                    n_stat = st.selectbox("Status", ["Not Started", "In Progress", "Completed"], 
                                          index=["Not Started", "In Progress", "Completed"].index(c_stat), 
                                          key=f"tr_{row['id']}", label_visibility="collapsed")
                    if n_stat != c_stat:
                        update_training_status(st.session_state['name'], row['id'], n_stat)
                        st.rerun()

# ---------- APP: ONBOARDING ----------
def app_onboarding():
    c1, c2 = st.columns([1, 5])
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
            with st.form("add_ob"):
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
