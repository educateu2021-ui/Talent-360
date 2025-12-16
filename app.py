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
    .profile-img {
        width: 120px; height: 120px; border-radius: 50%; object-fit: cover;
        border: 4px solid #dfe6e9; display: block; margin: 0 auto 15px auto;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    div.stButton > button {
        width: 100%; border-radius: 6px; font-weight: 600;
    }
    /* Dynamic Badge for Custom Modules */
    .custom-module {
        border-top: 3px solid #6366f1;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- DATABASE & DYNAMIC ENGINE ----------
DB_FILE = "portal_v16_super.db"

def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Core Tables
    c.execute('''CREATE TABLE IF NOT EXISTS module_registry (
        id TEXT PRIMARY KEY, 
        module_name TEXT, 
        table_name TEXT, 
        description TEXT, 
        icon TEXT
    )''')
    
    # 2. Existing Modules (Hardcoded Tables)
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
    
    c.execute('''CREATE TABLE IF NOT EXISTS onboarding_details (
        username TEXT PRIMARY KEY, fullname TEXT, emp_id TEXT, tid TEXT,
        location TEXT, work_mode TEXT, hr_policy_briefing INTEGER,
        it_system_setup INTEGER, tid_active INTEGER, team_centre_training INTEGER,
        agt_access INTEGER, ext_mail_id INTEGER, rdp_access INTEGER,
        avd_access INTEGER, teamcenter_access INTEGER, blocking_point TEXT,
        ticket_raised TEXT
    )''')
    
    conn.commit()
    conn.close()

# --- DYNAMIC SQL HELPERS ---
def create_dynamic_table(module_name, table_name, columns, description, icon):
    conn = get_connection()
    c = conn.cursor()
    try:
        # 1. Create the physical table
        # Columns is a list of dicts: [{'name': 'cost', 'type': 'TEXT'}, ...]
        col_str = ", ".join([f"{col['name']} {col['type']}" for col in columns])
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} (id TEXT PRIMARY KEY, {col_str})"
        c.execute(sql)
        
        # 2. Register the module
        mid = str(uuid.uuid4())[:8]
        c.execute("INSERT INTO module_registry VALUES (?,?,?,?,?)", 
                  (mid, module_name, table_name, description, icon))
        conn.commit()
        return True, "Module Created Successfully"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_registered_modules():
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT * FROM module_registry", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

def get_table_schema(table_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute(f"PRAGMA table_info({table_name})")
    schema = c.fetchall() # Returns list of tuples (cid, name, type, notnull, dflt_value, pk)
    conn.close()
    return schema

def save_dynamic_record(table_name, data):
    conn = get_connection()
    c = conn.cursor()
    placeholders = ",".join(["?"] * len(data))
    columns = ",".join(data.keys())
    values = list(data.values())
    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    c.execute(sql, values)
    conn.commit()
    conn.close()

def get_dynamic_data(table_name):
    conn = get_connection()
    try: df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    except: df = pd.DataFrame()
    conn.close()
    return df

# ---------- AUTH ----------
USERS = {
    "admin": {"password": "admin123", "role": "Super Admin", "name": "System Admin", "emp_id": "ADM-001", "tid": "TID-000", "img": ""},
    "leader": {"password": "123", "role": "Team Leader", "name": "Sarah Jenkins", "emp_id": "LDR-001", "tid": "TID-999", "img": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&q=80&w=200&h=200"},
    "member1": {"password": "123", "role": "Team Member", "name": "David Chen", "emp_id": "EMP-101", "tid": "TID-101", "img": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&q=80&w=200&h=200"},
}

def login_page():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        with st.container(border=True):
            st.markdown("<h2 style='text-align:center;'>Portal Login</h2>", unsafe_allow_html=True)
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

# ---------- SUPER ADMIN PANEL ----------
def app_admin():
    c1, c2 = st.columns([1, 6])
    with c1:
        if st.button("⬅ Home"): st.session_state['current_app'] = 'HOME'; st.rerun()
    with c2: st.markdown("### 🛠️ Super Admin: Module Builder")
    st.markdown("---")

    t1, t2 = st.tabs(["🚀 Create New Module", "📂 Manage Database"])

    with t1:
        st.info("Use this tool to create new sections in the app without coding.")
        
        with st.form("builder_form"):
            mod_name = st.text_input("Module Name (e.g., 'Travel Requests')")
            tbl_name = st.text_input("Database Table Name (e.g., 'travel_reqs')").lower().replace(" ", "_")
            mod_desc = st.text_input("Short Description")
            mod_icon = st.selectbox("Icon", ["✈️", "💰", "🏥", "📅", "📝", "📢", "🔧"])
            
            st.markdown("**Define Fields (Columns)**")
            c_a, c_b = st.columns(2)
            # Simplified for demo: limiting to 3 custom columns for the builder UI
            col1_n = c_a.text_input("Field 1 Name"); col1_t = c_b.selectbox("Type 1", ["TEXT", "INTEGER", "DATE"], key="t1")
            col2_n = c_a.text_input("Field 2 Name"); col2_t = c_b.selectbox("Type 2", ["TEXT", "INTEGER", "DATE"], key="t2")
            col3_n = c_a.text_input("Field 3 Name"); col3_t = c_b.selectbox("Type 3", ["TEXT", "INTEGER", "DATE"], key="t3")
            
            if st.form_submit_button("🚀 Build Module"):
                if mod_name and tbl_name:
                    cols = []
                    if col1_n: cols.append({'name': col1_n.replace(" ","_").lower(), 'type': col1_t})
                    if col2_n: cols.append({'name': col2_n.replace(" ","_").lower(), 'type': col2_t})
                    if col3_n: cols.append({'name': col3_n.replace(" ","_").lower(), 'type': col3_t})
                    
                    ok, msg = create_dynamic_table(mod_name, tbl_name, cols, mod_desc, mod_icon)
                    if ok: st.success("Module Created! Go to Home to see it."); time.sleep(2); st.rerun()
                    else: st.error(f"Error: {msg}")
                else:
                    st.error("Name and Table Name are required.")

    with t2:
        st.markdown("#### Existing Custom Modules")
        mods = get_registered_modules()
        if not mods.empty:
            st.dataframe(mods)
            # Deletion logic would go here
        else:
            st.info("No custom modules created yet.")

# ---------- DYNAMIC MODULE RENDERER ----------
def app_dynamic_module(module_row):
    # This function builds the UI for ANY custom module created by the admin
    c1, c2 = st.columns([1, 6])
    with c1:
        if st.button("⬅ Home"): st.session_state['current_app'] = 'HOME'; st.rerun()
    with c2: st.markdown(f"### {module_row['icon']} {module_row['module_name']}")
    st.caption(module_row['description'])
    st.markdown("---")

    # 1. The Form (Automatically generated from DB Schema)
    table_name = module_row['table_name']
    schema = get_table_schema(table_name)
    # Filter out 'id' as it's auto-generated
    input_cols = [col for col in schema if col[1] != 'id']

    with st.expander("➕ Add Entry", expanded=True):
        with st.form(f"dyn_form_{table_name}"):
            form_data = {}
            # Create input widgets based on schema
            for col in input_cols:
                col_name = col[1]
                col_type = col[2]
                label = col_name.replace("_", " ").title()
                
                if col_type == "DATE":
                    form_data[col_name] = str(st.date_input(label))
                elif col_type == "INTEGER":
                    form_data[col_name] = st.number_input(label, step=1)
                else:
                    form_data[col_name] = st.text_input(label)
            
            if st.form_submit_button("Submit"):
                # Add ID
                form_data['id'] = str(uuid.uuid4())[:8]
                try:
                    save_dynamic_record(table_name, form_data)
                    st.success("Record Added!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    # 2. The Data Table
    st.markdown("### Records")
    df = get_dynamic_data(table_name)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        # Download Button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", data=csv, file_name=f"{table_name}.csv", mime="text/csv")
    else:
        st.info("No records found.")

# ---------- APP HOME (DYNAMIC GRID) ----------
def app_home():
    st.markdown(f"## Welcome, {st.session_state['name']}")
    st.write("---")
    
    # 1. Standard Modules (Hardcoded)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        with st.container(border=True):
            st.markdown("### 📊 **KPI**")
            if st.button("Launch KPI", use_container_width=True, type="primary"): st.session_state['current_app']='KPI'; st.rerun()
    with c2:
        with st.container(border=True):
            st.markdown("### 🎓 **Training**")
            if st.button("Launch Training", use_container_width=True, type="primary"): st.session_state['current_app']='TRAINING'; st.rerun()
    with c3:
        with st.container(border=True):
            st.markdown("### 🚀 **Tracker**")
            if st.button("Launch Tracker", use_container_width=True, type="primary"): st.session_state['current_app']='RESOURCE'; st.rerun()
    with c4:
        with st.container(border=True):
            st.markdown("### 🕸️ **Radar**")
            if st.button("View Radar", use_container_width=True): st.toast("🚧 Under Construction!", icon="👷")

    # 2. Dynamic Modules (From Database)
    custom_modules = get_registered_modules()
    if not custom_modules.empty:
        st.markdown("#### Custom Modules")
        # Grid logic for dynamic modules
        rows = [custom_modules.iloc[i:i+4] for i in range(0, len(custom_modules), 4)]
        for row in rows:
            cols = st.columns(4)
            for i, (_, mod) in enumerate(row.iterrows()):
                with cols[i]:
                    with st.container(border=True):
                        st.markdown(f"### {mod['icon']} **{mod['module_name']}**")
                        st.caption(mod['description'])
                        # Store the entire row data so we know which table to load
                        if st.button(f"Open {mod['module_name']}", key=f"dyn_btn_{mod['id']}", use_container_width=True):
                            st.session_state['current_app'] = 'DYNAMIC'
                            st.session_state['active_module'] = mod
                            st.rerun()

# --- OTHER APPS (Placeholders for brevity, assume previous code fits here) ---
# (I am keeping the core structure light here, assume app_kpi, app_training, etc. are defined as before)
def app_kpi():
    st.write("KPI App Loaded (Previous Logic)")
    if st.button("Back"): st.session_state['current_app']='HOME'; st.rerun()

def app_training():
    st.write("Training App Loaded (Previous Logic)")
    if st.button("Back"): st.session_state['current_app']='HOME'; st.rerun()

def app_resource():
    st.write("Resource Tracker Loaded (Previous Logic)")
    if st.button("Back"): st.session_state['current_app']='HOME'; st.rerun()

# ---------- MAIN CONTROLLER ----------
def main():
    init_db()
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['current_app'] = 'HOME'

    if st.session_state['logged_in']:
        with st.sidebar:
            if st.session_state['img']: st.markdown(f"<img src='{st.session_state['img']}' class='profile-img'>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align:center;'>{st.session_state['name']}</h3>", unsafe_allow_html=True)
            
            if st.session_state['role'] == "Super Admin":
                st.markdown("---")
                if st.button("🛠️ Super Admin"): st.session_state['current_app'] = 'ADMIN'; st.rerun()
            
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
        elif app == 'DYNAMIC': 
            # Render the custom module
            if 'active_module' in st.session_state:
                app_dynamic_module(st.session_state['active_module'])

if __name__ == "__main__":
    main()
