import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import date, datetime, timedelta
import time
import plotly.express as px
import plotly.graph_objects as go

# ---------- 1. CONFIGURATION (First Streamlit Command) ----------
st.set_page_config(page_title="Corporate Portal", layout="wide", page_icon="🏢")

# ---------- 2. DATABASE INIT & DEMO DATA ----------
DB_FILE = "portal_data_v15_fixed.db"

def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    """Initialize tables and seed demo data if empty."""
    conn = get_connection()
    c = conn.cursor()
    
    # --- TABLE CREATION ---
    
    # 1. Users
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, role TEXT,
        fullname TEXT, emp_id TEXT, tid TEXT, img_url TEXT
    )''')
    
    # 2. App Config
    c.execute('''CREATE TABLE IF NOT EXISTS app_config (
        key TEXT PRIMARY KEY, value TEXT
    )''')
    
    # 3. KPI Tasks
    c.execute('''CREATE TABLE IF NOT EXISTS tasks_v2 (
        id TEXT PRIMARY KEY, name_activity_pilot TEXT, task_name TEXT, date_of_receipt TEXT,
        actual_delivery_date TEXT, commitment_date_to_customer TEXT, status TEXT,
        ftr_customer TEXT, reference_part_number TEXT, ftr_internal TEXT, otd_internal TEXT,
        description_of_activity TEXT, activity_type TEXT, ftr_quality_gate_internal TEXT,
        date_of_clarity_in_input TEXT, start_date TEXT, otd_customer TEXT, customer_remarks TEXT,
        name_quality_gate_referent TEXT, project_lead TEXT, customer_manager_name TEXT
    )''')
    
    # 4. Training Repo
    c.execute('''CREATE TABLE IF NOT EXISTS training_repo (
        id TEXT PRIMARY KEY, title TEXT, description TEXT, link TEXT, 
        role_target TEXT, mandatory INTEGER, created_by TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS training_progress (
        user_name TEXT, training_id TEXT, status TEXT, 
        last_updated TEXT, PRIMARY KEY (user_name, training_id)
    )''')
    
    # 5. Resource Tracker (Onboarding)
    c.execute('''CREATE TABLE IF NOT EXISTS onboarding_details (
        username TEXT PRIMARY KEY, fullname TEXT, emp_id TEXT, tid TEXT,
        location TEXT, work_mode TEXT, hr_policy_briefing INTEGER,
        it_system_setup INTEGER, tid_active INTEGER, team_centre_training INTEGER,
        agt_access INTEGER, ext_mail_id INTEGER, rdp_access INTEGER,
        avd_access INTEGER, teamcenter_access INTEGER, blocking_point TEXT,
        ticket_raised TEXT
    )''')

    # --- SEED DATA (Only if tables empty) ---

    # 1. Users
    c.execute("SELECT count(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", ('admin', 'admin123', 'Super Admin', 'System Administrator', 'ADM-001', 'TID-000', ''))
        c.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", ('leader', '123', 'Team Leader', 'Sarah Jenkins', 'LDR-001', 'TID-999', ''))
        c.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", ('member', '123', 'Team Member', 'David Chen', 'MEM-001', 'TID-100', ''))

    # 2. Config
    defaults = {'primary_color': '#3b82f6', 'app_title': 'Corporate Portal', 'module_kpi': '1', 'module_training': '1', 'module_resource': '1', 'module_radar': '1'}
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO app_config VALUES (?,?)", (k, v))

    # 3. Demo Training (10 Items)
    c.execute("SELECT count(*) FROM training_repo")
    if c.fetchone()[0] == 0:
        trainings = [
            ("TR-01", "Python Basics", "Intro to Syntax", "https://python.org", "All", 1, "System"),
            ("TR-02", "Advanced Pandas", "Data Manipulation", "https://pandas.pydata.org", "Team Member", 0, "System"),
            ("TR-03", "Streamlit UI", "Building Dashboards", "https://streamlit.io", "All", 1, "System"),
            ("TR-04", "Workplace Safety", "Fire & Health", "https://osha.gov", "All", 1, "System"),
            ("TR-05", "Leadership 101", "Managing Teams", "https://hbr.org", "Team Leader", 1, "System"),
            ("TR-06", "Agile Scrum", "Sprints & Standups", "https://scrum.org", "All", 0, "System"),
            ("TR-07", "Git Version Control", "Branching Strategies", "https://github.com", "Team Member", 1, "System"),
            ("TR-08", "Cyber Security", "Phishing Awareness", "https://security.com", "All", 1, "System"),
            ("TR-09", "Conflict Resolution", "HR Guidelines", "https://hr.com", "Team Leader", 0, "System"),
            ("TR-10", "Cloud Computing", "AWS Fundamentals", "https://aws.amazon.com", "Team Member", 0, "System")
        ]
        c.executemany("INSERT INTO training_repo VALUES (?,?,?,?,?,?,?)", trainings)

    # 4. Demo Resources (10 Items)
    c.execute("SELECT count(*) FROM onboarding_details")
    if c.fetchone()[0] == 0:
        resources = [
            ("res1", "Alice Johnson", "EMP-201", "TID-201", "Chennai", "Office", 1, 1, 1, 1, 0, 1, 0, 0, 1, "", ""),
            ("res2", "Bob Smith", "EMP-202", "TID-202", "Pune", "Remote", 1, 1, 0, 0, 1, 0, 1, 1, 0, "VPN Issue", "TKT-1029"),
            ("res3", "Charlie Brown", "EMP-203", "TID-203", "Bangalore", "Office", 1, 1, 1, 1, 0, 1, 0, 0, 1, "", ""),
            ("res4", "Diana Prince", "EMP-204", "TID-204", "Chennai", "Remote", 0, 0, 0, 0, 0, 0, 0, 0, 0, "", ""),
            ("res5", "Evan Wright", "EMP-205", "TID-205", "Pune", "Office", 1, 1, 1, 0, 0, 1, 0, 0, 0, "Laptop Delay", "TKT-3321"),
            ("res6", "Fiona Gallagher", "EMP-206", "TID-206", "Client Site", "Office", 1, 1, 1, 1, 0, 1, 0, 0, 1, "", ""),
            ("res7", "George Martin", "EMP-207", "TID-207", "Bangalore", "Remote", 1, 0, 0, 0, 1, 0, 1, 0, 0, "", ""),
            ("res8", "Hannah Baker", "EMP-208", "TID-208", "Chennai", "Office", 1, 1, 1, 1, 0, 1, 0, 0, 1, "", ""),
            ("res9", "Ian Somerhalder", "EMP-209", "TID-209", "Pune", "Remote", 1, 1, 1, 1, 1, 1, 1, 1, 1, "", ""),
            ("res10", "Jack Daniels", "EMP-210", "TID-210", "Chennai", "Office", 0, 1, 0, 0, 0, 0, 0, 0, 0, "No ID Card", "")
        ]
        c.executemany("INSERT INTO onboarding_details VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", resources)

    conn.commit()
    conn.close()

# Run Init immediately to prevent "Table not found" errors
init_db()

# ---------- 3. LOAD CONFIG (Now Safe) ----------
def load_config():
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT * FROM app_config", conn)
        return dict(zip(df.key, df.value))
    except:
        return {}
    finally:
        conn.close()

config = load_config()
primary_color = config.get('primary_color', '#3b82f6')

# ---------- 4. STYLES ----------
st.markdown(f"""
    <style>
    .stApp {{ background-color: #f8f9fa; }}
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: white; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }}
    div.stButton > button {{
        width: 100%; border-radius: 6px; font-weight: 600;
        border-color: {primary_color}; color: {primary_color};
    }}
    div.stButton > button:hover {{
        background-color: {primary_color}; color: white;
    }}
    .profile-img {{
        width: 120px; height: 120px; border-radius: 50%; object-fit: cover;
        border: 4px solid {primary_color}; display: block; margin: 0 auto 15px auto;
    }}
    /* Status Badges */
    .status-ok {{ color: #10b981; font-weight: bold; }}
    .status-pending {{ color: #f59e0b; font-weight: bold; }}
    </style>
""", unsafe_allow_html=True)

# ---------- 5. ADMIN FUNCTIONS ----------
def get_db_schema(table_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [info[1] for info in cursor.fetchall()]
    conn.close()
    return columns

def add_column_to_table(table, col_name, col_type="TEXT"):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
        conn.commit()
        return True, "Column added successfully"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def manage_users(action, data=None):
    conn = get_connection()
    c = conn.cursor()
    if action == "add":
        try:
            c.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                      (data['u'], data['p'], data['r'], data['fn'], data['eid'], data['tid'], data['img']))
            conn.commit()
            return True, "User Added"
        except: return False, "Username exists"
    elif action == "delete":
        c.execute("DELETE FROM users WHERE username=?", (data,))
        conn.commit()
        return True, "User Deleted"
    conn.close()

def update_config(key, value):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO app_config VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()

# ---------- 6. AUTH LOGIC ----------
def authenticate(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    if user:
        return {
            'username': user[0], 'role': user[2], 'name': user[3],
            'emp_id': user[4], 'tid': user[5], 'img': user[6]
        }
    return None

def login_page():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        with st.container(border=True):
            st.markdown(f"<h2 style='text-align:center;'>{config.get('app_title', 'Portal')}</h2>", unsafe_allow_html=True)
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Login", type="primary"):
                user = authenticate(u, p)
                if user:
                    st.session_state.update({'logged_in': True, 'current_app': 'HOME', **user})
                    st.rerun()
                else:
                    st.error("Invalid Credentials")

# ---------- 7. SHARED HELPERS ----------
def get_table_data(table):
    conn = get_connection()
    try: df = pd.read_sql(f"SELECT * FROM {table}", conn)
    except: df = pd.DataFrame()
    conn.close()
    return df

def save_dynamic_data(table, data, pk_col, pk_val, is_new=False):
    conn = get_connection()
    c = conn.cursor()
    valid_cols = get_db_schema(table)
    clean_data = {k: v for k, v in data.items() if k in valid_cols}
    columns = ', '.join(clean_data.keys())
    placeholders = ', '.join(['?'] * len(clean_data))
    updates = ', '.join([f"{k}=?" for k in clean_data.keys()])
    values = list(clean_data.values())
    
    if is_new:
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        c.execute(sql, values)
    else:
        sql = f"UPDATE {table} SET {updates} WHERE {pk_col}=?"
        c.execute(sql, values + [pk_val])
    conn.commit()
    conn.close()

# ---------- 8. APP MODULES ----------

def app_admin():
    c1, c2 = st.columns([1, 6])
    with c1:
        if st.button("⬅ Home"): st.session_state['current_app'] = 'HOME'; st.rerun()
    with c2: st.markdown("### 🛠️ Super Admin")
    
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Users", "🎨 Config", "🗄️ Schema", "⚙️ Export"])
    
    with tab1: # Users
        with st.expander("➕ Add User"):
            with st.form("add_u"):
                c1, c2 = st.columns(2)
                nu = c1.text_input("Username")
                np = c2.text_input("Password", type="password")
                nr = c1.selectbox("Role", ["Team Member", "Team Leader", "Super Admin"])
                nf = c2.text_input("Full Name")
                ne = c1.text_input("Emp ID")
                nt = c2.text_input("TID")
                if st.form_submit_button("Create"):
                    ok, msg = manage_users("add", {'u':nu, 'p':np, 'r':nr, 'fn':nf, 'eid':ne, 'tid':nt, 'img':''})
                    if ok: st.success(msg); st.rerun()
                    else: st.error(msg)
        
        users_df = get_table_data("users")
        st.dataframe(users_df[['username','role','fullname','emp_id']], use_container_width=True)

    with tab2: # Config
        with st.form("conf"):
            t = st.text_input("Title", value=config.get('app_title'))
            c = st.color_picker("Color", value=config.get('primary_color'))
            if st.form_submit_button("Save"):
                update_config('app_title', t)
                update_config('primary_color', c)
                st.rerun()

    with tab3: # Schema
        st.info("Add columns to tables")
        t_map = {"KPI": "tasks_v2", "Resources": "onboarding_details", "Training": "training_repo"}
        sel = st.selectbox("Table", list(t_map.keys()))
        col = st.text_input("Column Name")
        if st.button("Add"):
            ok, msg = add_column_to_table(t_map[sel], col.replace(" ","_").lower())
            if ok: st.success(msg)
            else: st.error(msg)

    with tab4: # Export
        for t in ["users", "tasks_v2", "training_repo", "onboarding_details"]:
            df = get_table_data(t)
            st.download_button(f"Download {t}", df.to_csv(index=False).encode('utf-8'), f"{t}.csv", "text/csv")

def app_home():
    st.markdown(f"## Welcome, {st.session_state['name']}")
    st.write("---")
    c1, c2, c3, c4 = st.columns(4)
    if config.get('module_kpi','1')=='1':
        with c1:
            with st.container(border=True):
                st.markdown("### 📊 **KPI**")
                if st.button("Launch KPI", use_container_width=True, type="primary"): st.session_state['current_app']='KPI'; st.rerun()
    if config.get('module_training','1')=='1':
        with c2:
            with st.container(border=True):
                st.markdown("### 🎓 **Train**")
                if st.button("Launch Training", use_container_width=True, type="primary"): st.session_state['current_app']='TRAINING'; st.rerun()
    if config.get('module_resource','1')=='1':
        with c3:
            with st.container(border=True):
                st.markdown("### 🚀 **Tracker**")
                if st.button("Launch Tracker", use_container_width=True, type="primary"): st.session_state['current_app']='RESOURCE'; st.rerun()
    if config.get('module_radar','1')=='1':
        with c4:
            with st.container(border=True):
                st.markdown("### 🕸️ **Radar**")
                if st.button("View Radar", use_container_width=True): st.toast("🚧 Under Construction!", icon="👷")

def app_kpi():
    c1, c2 = st.columns([1, 6])
    with c1:
        if st.button("⬅ Home"): st.session_state['current_app']='HOME'; st.rerun()
    with c2: st.markdown("### 📊 KPI System")
    st.markdown("---")
    
    df = get_table_data("tasks_v2")
    if st.session_state['role'] in ["Team Leader", "Super Admin"]:
        if 'kpi_edit' not in st.session_state: st.session_state['kpi_edit'] = None
        if st.session_state['kpi_edit']:
            with st.container(border=True):
                is_new = st.session_state['kpi_edit'] == "NEW"
                st.subheader("Edit Task")
                cols = get_db_schema("tasks_v2")
                row_data = {}
                if not is_new:
                    row_data = df[df['id'] == st.session_state['kpi_edit']].iloc[0].to_dict()
                
                with st.form("dyn_kpi"):
                    form_data = {}
                    # Standard Fields
                    c1, c2 = st.columns(2)
                    tn = c1.text_input("Task Name", value=row_data.get('task_name',''))
                    stt = c2.selectbox("Status", ["Inprogress", "Completed"], index=0)
                    
                    # Dynamic
                    for c in [x for x in cols if x not in ['id','task_name','status']]:
                        form_data[c] = st.text_input(c.title(), value=str(row_data.get(c,'')))
                    
                    if st.form_submit_button("Save"):
                        pk = str(uuid.uuid4())[:8] if is_new else st.session_state['kpi_edit']
                        if is_new: form_data['id'] = pk
                        form_data['task_name'] = tn
                        form_data['status'] = stt
                        save_dynamic_data("tasks_v2", form_data, "id", pk, is_new)
                        st.success("Saved"); st.session_state['kpi_edit']=None; st.rerun()
                if st.button("Cancel"): st.session_state['kpi_edit']=None; st.rerun()
        
        if not st.session_state['kpi_edit']:
            if st.button("➕ New Task"): st.session_state['kpi_edit']="NEW"; st.rerun()
            st.dataframe(df, use_container_width=True)
            for _, r in df.iterrows():
                if st.button(f"Edit {r.get('task_name','Task')}", key=f"ke_{r['id']}"):
                    st.session_state['kpi_edit'] = r['id']; st.rerun()
    else:
        st.dataframe(df)

def app_resource():
    c1, c2 = st.columns([1, 6])
    with c1:
        if st.button("⬅ Home"): st.session_state['current_app']='HOME'; st.rerun()
    with c2: st.markdown("### 🚀 Resource Tracker")
    st.markdown("---")
    
    df = get_table_data("onboarding_details")
    if st.session_state['role'] in ["Team Leader", "Super Admin"]:
        c1, c2 = st.columns([4, 1])
        with c2: 
            if st.button("➕ Add"): st.session_state['res_mode']='NEW'; st.rerun()
        
        if st.session_state.get('res_mode'):
            with st.container(border=True):
                st.subheader("Resource Details")
                cols = get_db_schema("onboarding_details")
                with st.form("res_dyn"):
                    fd = {}
                    for c in cols: fd[c] = st.text_input(c.title(), value="")
                    if st.form_submit_button("Save"):
                        save_dynamic_data("onboarding_details", fd, "username", fd['username'], True)
                        st.success("Saved"); st.session_state['res_mode']=None; st.rerun()
                if st.button("Close"): st.session_state['res_mode']=None; st.rerun()
        
        for idx, row in df.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.write(f"**{row['fullname']}** | {row['location']}")
                c1.caption(f"{row['emp_id']} - {row['tid']}")
                # Render all extra columns dynamically
                extras = [c for c in df.columns if c not in ['username','fullname','emp_id','tid','location']]
                if extras: c1.caption(", ".join([f"{c}: {row[c]}" for c in extras[:3]]))

    else:
        st.info("Member Checklist View (Simplified)")

def app_training():
    c1, c2 = st.columns([1, 6])
    with c1:
        if st.button("⬅ Home"): st.session_state['current_app']='HOME'; st.rerun()
    with c2: st.markdown("### 🎓 Training Hub")
    st.markdown("---")
    df = get_table_data("training_repo")
    st.dataframe(df, use_container_width=True)

# ---------- 9. MAIN ROUTER ----------
def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['current_app'] = 'HOME'

    if st.session_state['logged_in']:
        with st.sidebar:
            img = st.session_state.get('img')
            if img: st.markdown(f"<img src='{img}' class='profile-img'>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align:center;'>{st.session_state['name']}</h3>", unsafe_allow_html=True)
            if st.session_state['role'] == 'Super Admin':
                st.markdown("---")
                if st.button("🛠️ Admin Panel"): st.session_state['current_app'] = 'ADMIN'; st.rerun()
            st.markdown("---")
            if st.button("Sign Out"): st.session_state.clear(); st.rerun()

    if not st.session_state['logged_in']:
        login_page()
    else:
        app = st.session_state.get('current_app', 'HOME')
        if app == 'HOME': app_home()
        elif app == 'KPI': app_kpi()
        elif app == 'TRAINING': app_training()
        elif app == 'RESOURCE': app_resource()
        elif app == 'ADMIN': app_admin()

if __name__ == "__main__":
    main()
