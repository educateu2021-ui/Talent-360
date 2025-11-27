import streamlit as st
import pandas as pd
import sqlite3
import uuid
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import random

# --- CONFIGURATION & SETUP ---
st.set_page_config(page_title="KPI Management System", layout="wide", page_icon="📊")

# --- CUSTOM CSS FOR MODERN UI ---
st.markdown("""
<style>
    /* Global Reset & Background */
    .stApp {
        background-color: #f4f7f6;
    }
    
    /* Remove default top padding */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* AUTOMATIC CARD STYLING FOR ST.CONTAINER(BORDER=TRUE) */
    /* Forces white background on containers */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important; /* EXPLICIT WHITE */
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border: 1px solid #e1e4e8;
        padding: 20px;
        margin-bottom: 20px;
        height: 100%;
    }
    
    /* Ensure inner div is transparent so white shows through */
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: transparent !important;
    }

    /* METRIC CARDS */
    .metric-card {
        background-color: #FFFFFF !important;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        border: 1px solid #e1e4e8;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    
    /* TEXT STYLES */
    .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: #2c3e50;
        margin: 0;
    }
    .metric-label {
        font-size: 13px;
        color: #7f8c8d;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-trend {
        font-size: 12px;
        font-weight: 600;
    }
    .trend-up { color: #27ae60; background: #eafaf1; padding: 2px 6px; border-radius: 4px; }
    .trend-down { color: #c0392b; background: #fdedec; padding: 2px 6px; border-radius: 4px; }
    
    /* ICON BOXES */
    .icon-box {
        width: 45px;
        height: 45px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
    }
    
    /* TABLE & LIST STYLES */
    .task-header {
        font-weight: 600;
        color: #95a5a6;
        font-size: 12px;
        text-transform: uppercase;
        padding-bottom: 10px;
        border-bottom: 2px solid #ecf0f1;
    }
    .task-row {
        padding: 12px 0;
        border-bottom: 1px solid #ecf0f1;
        font-size: 14px;
        color: #34495e;
        display: flex;
        align-items: center;
    }
    
    /* STATUS BADGES */
    .badge {
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
    }
    .badge-completed { background-color: #d5f5e3; color: #196f3d; }
    .badge-inprogress { background-color: #d6eaf8; color: #2874a6; }
    .badge-hold { background-color: #fce4ec; color: #c2185b; }
    
    /* KANBAN */
    .kanban-col {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 8px;
        min-height: 500px;
    }
    .kanban-card {
        background-color: white;
        padding: 15px;
        border-radius: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 10px;
        border-left: 4px solid #3498db;
    }
    
    /* Button tweaks */
    [data-testid="stFileUploader"] {
        padding-top: 0px;
    }
</style>
""", unsafe_allow_html=True)

# --- DATABASE FUNCTIONS ---

def init_db():
    conn = sqlite3.connect('kpi_data.db')
    c = conn.cursor()
    
    # Using tasks_v2 schema
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks_v2 (
            id TEXT PRIMARY KEY,
            name_activity_pilot TEXT,
            task_name TEXT,
            date_of_receipt DATE,
            actual_delivery_date DATE,
            commitment_date_to_customer DATE,
            status TEXT,
            ftr_customer TEXT,
            reference_part_number TEXT,
            ftr_internal TEXT,
            otd_internal TEXT,
            description_of_activity TEXT,
            activity_type TEXT,
            ftr_quality_gate_internal TEXT,
            date_of_clarity_in_input DATE,
            start_date DATE,
            otd_customer TEXT,
            customer_remarks TEXT,
            name_quality_gate_referent TEXT,
            project_lead TEXT,
            customer_manager_name TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_demo_data():
    """Generates 100 random demo data entries if database is empty"""
    conn = sqlite3.connect('kpi_data.db')
    c = conn.cursor()
    # Check if table exists first to avoid error
    try:
        c.execute("SELECT count(*) FROM tasks_v2")
        count = c.fetchone()[0]
    except:
        count = 0
    
    if count == 0:
        pilots = ["Bob (Member)", "Charlie (Member)"]
        statuses = ["Inprogress", "Completed", "Hold", "Cancelled"]
        task_names = ["Design Update", "Website Develop", "App Testing", "Database Setup", "API Integration", "UI Cleanup", "Backend Refactor", "Security Audit"]
        
        today = date.today()
        
        # Generate 100 records
        for _ in range(100):
            t_name = random.choice(task_names)
            pilot = random.choice(pilots)
            status = random.choice(statuses)
            
            # Randomize dates
            start = today - timedelta(days=random.randint(1, 60))
            due = start + timedelta(days=random.randint(5, 20))
            
            actual = None
            if status == "Completed":
                # 80% chance of being on time
                if random.random() > 0.2:
                    actual = due - timedelta(days=random.randint(0, 3))
                else:
                    actual = due + timedelta(days=random.randint(1, 5))
            
            otd_int = "Yes" if actual and actual <= due else "N/A" if not actual else "NO"
            ftr_int = "Yes" if random.random() > 0.1 else "NO" # 90% FTR
            
            c.execute('''INSERT INTO tasks_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
                str(uuid.uuid4())[:8], pilot, t_name, start, actual, due, status, 
                "Yes", f"REF-{random.randint(1000,9999)}", ftr_int, otd_int, 
                "Demo Task Description generated automatically.", "3d development", "Yes", start, start, 
                "Yes", "No remarks", "Quality Ref", "Alice (Lead)", "Manager X"
            ))
        conn.commit()
    conn.close()

def add_task(data, task_id=None):
    conn = sqlite3.connect('kpi_data.db')
    c = conn.cursor()
    
    # OTD Logic
    otd_int = "N/A"
    if data['actual_delivery_date'] and data['commitment_date_to_customer']:
        otd_int = "Yes" if str(data['actual_delivery_date']) <= str(data['commitment_date_to_customer']) else "NO"
        
    otd_cust = "N/A" 
    if data['actual_delivery_date'] and data['commitment_date_to_customer']:
         otd_cust = "Yes" if str(data['actual_delivery_date']) <= str(data['commitment_date_to_customer']) else "NO"

    if task_id:
        c.execute('''
            UPDATE tasks_v2 SET
            name_activity_pilot=?, task_name=?, date_of_receipt=?, actual_delivery_date=?, 
            commitment_date_to_customer=?, status=?, ftr_customer=?, reference_part_number=?, 
            ftr_internal=?, otd_internal=?, description_of_activity=?, activity_type=?, 
            ftr_quality_gate_internal=?, date_of_clarity_in_input=?, start_date=?, otd_customer=?, 
            customer_remarks=?, name_quality_gate_referent=?, project_lead=?, customer_manager_name=?
            WHERE id=?
        ''', (
            data['name_activity_pilot'], data['task_name'], data['date_of_receipt'], data['actual_delivery_date'],
            data['commitment_date_to_customer'], data['status'], data['ftr_customer'], data['reference_part_number'],
            data['ftr_internal'], otd_int, data['description_of_activity'], data['activity_type'],
            data['ftr_quality_gate_internal'], data['date_of_clarity_in_input'], data['start_date'], otd_cust,
            data['customer_remarks'], data['name_quality_gate_referent'], data['project_lead'], data['customer_manager_name'],
            task_id
        ))
    else:
        new_id = str(uuid.uuid4())[:8]
        c.execute('''
            INSERT INTO tasks_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            new_id, 
            data['name_activity_pilot'], data['task_name'], data['date_of_receipt'], data['actual_delivery_date'],
            data['commitment_date_to_customer'], data['status'], data['ftr_customer'], data['reference_part_number'],
            data['ftr_internal'], otd_int, data['description_of_activity'], data['activity_type'],
            data['ftr_quality_gate_internal'], data['date_of_clarity_in_input'], data['start_date'], otd_cust,
            data['customer_remarks'], data['name_quality_gate_referent'], data['project_lead'], data['customer_manager_name']
        ))
        
    conn.commit()
    conn.close()

def get_all_tasks():
    conn = sqlite3.connect('kpi_data.db')
    try:
        df = pd.read_sql_query("SELECT * FROM tasks_v2", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

def update_task_status(task_id, new_status, new_actual_date=None):
    conn = sqlite3.connect('kpi_data.db')
    c = conn.cursor()
    c.execute("SELECT commitment_date_to_customer FROM tasks_v2 WHERE id=?", (task_id,))
    res = c.fetchone()
    comm_date_str = res[0]
    
    otd_val = "N/A"
    if comm_date_str and new_actual_date:
        otd_val = "Yes" if str(new_actual_date) <= str(comm_date_str) else "NO"

    if new_actual_date:
        c.execute('''UPDATE tasks_v2 SET status = ?, actual_delivery_date = ?, otd_internal = ?, otd_customer = ? WHERE id = ?''', 
                  (new_status, new_actual_date, otd_val, otd_val, task_id))
    else:
        c.execute("UPDATE tasks_v2 SET status = ? WHERE id = ?", (new_status, task_id))
    conn.commit()
    conn.close()

def import_data_from_csv(file):
    try:
        df = pd.read_csv(file)
        conn = sqlite3.connect('kpi_data.db')
        df.to_sql('tasks_v2', conn, if_exists='append', index=False)
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error importing: {e}")
        return False

# --- AUTH & USERS ---
USERS = {
    "leader": {"password": "123", "role": "Team Leader", "name": "Alice (Lead)"},
    "member1": {"password": "123", "role": "Team Member", "name": "Bob (Member)"},
    "member2": {"password": "123", "role": "Team Member", "name": "Charlie (Member)"}
}

def login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        with st.container(border=True):
            st.markdown("""
            <div style="text-align: center;">
                <h2 style="color: #2c3e50;">KPI System Login</h2>
            </div>
            """, unsafe_allow_html=True)
            
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.button("Sign In", type="primary", use_container_width=True):
                if username in USERS and USERS[username]["password"] == password:
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = username
                    st.session_state['role'] = USERS[username]['role']
                    st.session_state['name'] = USERS[username]['name']
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
            st.info("Demo: leader/123, member1/123")

# --- UI COMPONENTS ---

def metric_card(title, value, trend, icon_color, icon_char):
    trend_cls = "trend-up" if "+" in trend else "trend-down"
    st.markdown(f"""
    <div class="metric-card">
        <div>
            <div class="metric-label">{title}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-trend {trend_cls}">{trend}</div>
        </div>
        <div class="icon-box" style="background-color: {icon_color}20; color: {icon_color};">
            {icon_char}
        </div>
    </div>
    """, unsafe_allow_html=True)

def get_analytics_chart(df):
    if df.empty:
        return go.Figure()
    
    # Ensure date format
    df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')
    # Use a format that sorts correctly if using pandas sort, but here we can just use Month string
    # For a real bar chart, sorting by date is better.
    df = df.sort_values('start_date')
    df['month'] = df['start_date'].dt.strftime('%b')
    
    # Aggregate counts
    monthly_counts = df.groupby(['month', 'status'], sort=False).size().reset_index(name='count')
    
    # Changed to Bar Chart as requested
    fig = px.bar(monthly_counts, x="month", y="count", color="status",
                  color_discrete_map={"Completed": "#2ecc71", "Inprogress": "#3498db", "Hold": "#e74c3c", "Cancelled": "#95a5a6"},
                  title="Project Analytics (Bar Chart)", barmode='group')
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=30, b=0),
        height=350,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def get_donut_chart(df):
    if df.empty:
        completed_pct = 0
    else:
        total = len(df)
        completed = len(df[df['status'] == 'Completed'])
        completed_pct = int((completed / total) * 100) if total > 0 else 0
        
    fig = go.Figure(data=[go.Pie(
        labels=['Completed', 'Pending'], 
        values=[completed_pct, 100-completed_pct], 
        hole=.7,
        marker_colors=['#00C49F', '#f3f3f3'],
        textinfo='none'
    )])
    fig.update_layout(
        showlegend=False, 
        height=250, 
        margin=dict(l=0, r=0, t=0, b=0),
        annotations=[dict(text=f"{completed_pct}%", x=0.5, y=0.5, font_size=24, showarrow=False, font_weight="bold")]
    )
    return fig

def get_ftr_otd_chart(df):
    if df.empty:
        return go.Figure()
        
    df['actual_delivery_date'] = pd.to_datetime(df['actual_delivery_date'], errors='coerce')
    df_del = df.dropna(subset=['actual_delivery_date'])
    
    if df_del.empty:
        # Return empty placeholder if no delivered tasks
        fig = go.Figure()
        fig.update_layout(title="No Delivery Data Yet", height=300)
        return fig
    
    df_del['month'] = df_del['actual_delivery_date'].dt.strftime('%b')
    
    monthly_stats = df_del.groupby('month').agg({
        'otd_internal': lambda x: (x == 'Yes').mean() * 100,
        'ftr_internal': lambda x: (x == 'Yes').mean() * 100
    }).reset_index()
    
    fig = go.Figure(data=[
        go.Bar(name='FTR', x=monthly_stats['month'], y=monthly_stats['ftr_internal'], marker_color='#1cc88a'),
        go.Bar(name='OTD', x=monthly_stats['month'], y=monthly_stats['otd_internal'], marker_color='#4e73df')
    ])
    fig.update_layout(
        title="Team Performance (Weekly)", 
        barmode='group', 
        height=300, 
        margin=dict(l=0, r=0, t=40, b=0), 
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    return fig

# --- FORM COMPONENT ---
def task_form(mode="create", task_id=None, default_data=None):
    form_title = "Create New Job" if mode == "create" else "Edit Job Details"
    btn_text = "Create Job" if mode == "create" else "Update Job"
    
    # Form Container
    st.markdown(f"### {form_title}")
    
    if not default_data:
        default_data = {k: None for k in ["task_name", "name_activity_pilot", "activity_type", "reference_part_number", 
                                          "status", "start_date", "date_of_receipt", "date_of_clarity_in_input", 
                                          "commitment_date_to_customer", "project_lead", "name_quality_gate_referent", 
                                          "ftr_internal", "description_of_activity", "customer_manager_name", 
                                          "customer_remarks", "actual_delivery_date"]}
        default_data["project_lead"] = st.session_state.get('name', '')

    with st.form("task_form_component", clear_on_submit=(mode=="create")):
        col1, col2, col3 = st.columns(3)
        pilots = [u['name'] for k,u in USERS.items() if u['role'] == "Team Member"]

        def parse_d(d_val):
            if isinstance(d_val, str) and d_val:
                try: return datetime.strptime(d_val, '%Y-%m-%d').date()
                except: return None
            return d_val

        with col1:
            task_name = st.text_input("Task Name", value=default_data.get("task_name"))
            p_idx = pilots.index(default_data["name_activity_pilot"]) if default_data.get("name_activity_pilot") in pilots else None
            name_pilot = st.selectbox("Assign To", pilots, index=p_idx)
            
            types = ["3d development", "2d drawing", "Release"]
            t_idx = types.index(default_data["activity_type"]) if default_data.get("activity_type") in types else None
            activity_type = st.selectbox("Type", types, index=t_idx)
            
            ref_part = st.text_input("Ref Part Number", value=default_data.get("reference_part_number"))
            
        with col2:
            statuses = ["Hold", "Inprogress", "Completed", "Cancelled"]
            s_idx = statuses.index(default_data["status"]) if default_data.get("status") in statuses else 1
            status = st.selectbox("Current Status", statuses, index=s_idx)
            
            start_date = st.date_input("Start Date", value=parse_d(default_data.get("start_date")))
            date_receipt = st.date_input("Date of Receipt", value=parse_d(default_data.get("date_of_receipt")))
            date_clarity = st.date_input("Date Clarity", value=parse_d(default_data.get("date_of_clarity_in_input")))
            
        with col3:
            comm_date = st.date_input("Commitment Date", value=parse_d(default_data.get("commitment_date_to_customer")))
            act_date_val = parse_d(default_data.get("actual_delivery_date"))
            actual_date = st.date_input("Actual Delivery", value=act_date_val)
            project_lead = st.text_input("Project Lead", value=default_data.get("project_lead"))
            qual_ref = st.text_input("Quality Gate Ref", value=default_data.get("name_quality_gate_referent"))

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            ftr_opts = ["Yes", "NO"]
            f_idx = ftr_opts.index(default_data["ftr_internal"]) if default_data.get("ftr_internal") in ftr_opts else 0
            ftr_int = st.selectbox("FTR Internal Target", ftr_opts, index=f_idx)
            desc = st.text_area("Description", value=default_data.get("description_of_activity"))
        with c2:
            cust_manager = st.text_input("Customer Manager", value=default_data.get("customer_manager_name"))
            remarks = st.text_area("Remarks", value=default_data.get("customer_remarks"))
        
        submitted = st.form_submit_button(btn_text, type="primary")
        
        if submitted:
            if not task_name or not comm_date:
                st.error("Task Name and Commitment Date are required.")
            else:
                form_data = {
                    "name_activity_pilot": name_pilot,
                    "task_name": task_name,
                    "date_of_receipt": date_receipt,
                    "actual_delivery_date": actual_date, 
                    "commitment_date_to_customer": comm_date,
                    "status": status,
                    "ftr_customer": "N/A",
                    "reference_part_number": ref_part,
                    "ftr_internal": ftr_int,
                    "description_of_activity": desc,
                    "activity_type": activity_type,
                    "ftr_quality_gate_internal": "N/A",
                    "date_of_clarity_in_input": date_clarity,
                    "start_date": start_date,
                    "customer_remarks": remarks,
                    "name_quality_gate_referent": qual_ref,
                    "project_lead": project_lead,
                    "customer_manager_name": cust_manager
                }
                add_task(form_data, task_id=task_id)
                st.success(f"{btn_text} Successfully!")
                st.session_state['show_form'] = False
                st.session_state['edit_mode'] = False
                st.rerun()
    
    if st.button("Close Form"):
        st.session_state['show_form'] = False
        st.session_state['edit_mode'] = False
        st.rerun()

# --- DASHBOARD VIEWS ---

def team_leader_view():
    raw_df = get_all_tasks()
    
    # 1. HEADER & ACTIONS
    c1, c2 = st.columns([5, 3])
    with c1: st.title("Dashboard")
    with c2: 
        # Action Buttons Layout: Import | Export | New
        ac1, ac2, ac3 = st.columns([1, 1, 1])
        with ac1:
            uploaded_file = st.file_uploader("Import", type=['csv'], label_visibility="collapsed")
            if uploaded_file:
                if import_data_from_csv(uploaded_file):
                    st.success("Done!")
                    st.rerun()
        with ac2:
            if not raw_df.empty:
                csv = raw_df.to_csv(index=False).encode('utf-8')
                st.download_button("Export", csv, "kpi_tasks.csv", "text/csv", use_container_width=True)
        with ac3:
            if st.button("✚ New", type="primary", use_container_width=True):
                 st.session_state['show_form'] = True
                 st.session_state['edit_mode'] = False
    
    # Form Overlay
    if st.session_state.get('show_form', False):
        if st.session_state.get('edit_mode', False) and st.session_state.get('edit_task_id'):
            t_data = raw_df[raw_df['id'] == st.session_state['edit_task_id']].iloc[0].to_dict()
            task_form(mode="edit", task_id=st.session_state['edit_task_id'], default_data=t_data)
        else:
            task_form(mode="create")
    
    # 2. METRICS ROW
    m1, m2, m3, m4 = st.columns(4)
    total = len(raw_df)
    active = len(raw_df[raw_df['status'] == 'Inprogress'])
    hold = len(raw_df[raw_df['status'] == 'Hold'])
    done = len(raw_df[raw_df['status'] == 'Completed'])
    
    with m1: metric_card("Jobs Created", total, "+4.6%", "#3498db", "💼")
    with m2: metric_card("In Progress", active, "+2.1%", "#f1c40f", "⚡")
    with m3: metric_card("On Hold", hold, "-0.5%", "#e74c3c", "⏸️")
    with m4: metric_card("Delivered", done, "+12%", "#2ecc71", "✅")

    # 3. CHARTS ROW (Area & Donut)
    st.markdown("<br>", unsafe_allow_html=True)
    c_left, c_right = st.columns([2, 1])
    
    with c_left:
        with st.container(border=True):
            if not raw_df.empty:
                st.plotly_chart(get_analytics_chart(raw_df), use_container_width=True)
            else:
                st.info("No data available.")
            
    with c_right:
        with st.container(border=True):
            st.markdown("##### My Progress")
            st.markdown("<small style='color:grey'>Task completion rate</small>", unsafe_allow_html=True)
            if not raw_df.empty:
                st.plotly_chart(get_donut_chart(raw_df), use_container_width=True)
            else:
                st.info("No data.")
            
    # 4. FILTER BAR & TABLE
    st.markdown("### Active Tasks")
    
    # Filter Container
    with st.container(border=True):
        c_f1, c_f2, c_f3, c_btn = st.columns([1.5, 1.5, 1.5, 1])
        with c_f1: d_from = st.date_input("From:", value=date.today()-timedelta(days=30))
        with c_f2: d_to = st.date_input("To:", value=date.today())
        with c_f3: prio = st.selectbox("Priority", ["All", "High", "Medium", "Low"])
        with c_btn: 
            st.write("") # Spacer
            st.write("") # Spacer
            st.button("Filter", use_container_width=True)
    
    # Apply Filters
    df_filtered = raw_df.copy()
    if not df_filtered.empty and 'start_date' in df_filtered.columns:
        df_filtered['start_date'] = pd.to_datetime(df_filtered['start_date'], errors='coerce').dt.date
        df_filtered = df_filtered[(df_filtered['start_date'] >= d_from) & (df_filtered['start_date'] <= d_to)]

    # Task List Container
    with st.container(border=True):
        # Custom Table Header
        h1, h2, h3, h4, h5 = st.columns([3, 2, 2, 1.5, 1])
        h1.markdown("<div class='task-header'>TASK NAME</div>", unsafe_allow_html=True)
        h2.markdown("<div class='task-header'>ASSIGNED TO</div>", unsafe_allow_html=True)
        h3.markdown("<div class='task-header'>DUE DATE</div>", unsafe_allow_html=True)
        h4.markdown("<div class='task-header'>STATUS</div>", unsafe_allow_html=True)
        h5.markdown("<div class='task-header'>ACTION</div>", unsafe_allow_html=True)
        
        if not df_filtered.empty:
            for _, row in df_filtered.iterrows():
                r1, r2, r3, r4, r5 = st.columns([3, 2, 2, 1.5, 1])
                
                with r1: st.markdown(f"**{row['task_name']}**")
                with r2: st.markdown(f"<span style='color:grey'>{row['name_activity_pilot']}</span>", unsafe_allow_html=True)
                with r3: st.write(row['commitment_date_to_customer'])
                
                # Status Badge
                s_cls = "badge-completed" if row['status'] == "Completed" else "badge-inprogress" if row['status'] == "Inprogress" else "badge-hold"
                with r4: st.markdown(f"<span class='badge {s_cls}'>{row['status']}</span>", unsafe_allow_html=True)
                
                with r5:
                    if st.button("Edit", key=f"edit_{row['id']}"):
                        st.session_state['show_form'] = True
                        st.session_state['edit_mode'] = True
                        st.session_state['edit_task_id'] = row['id']
                        st.rerun()
                st.markdown("<hr style='margin:0; border-top: 1px solid #f0f0f0;'>", unsafe_allow_html=True)
        else:
            st.info("No active tasks found in this range.")

    # 5. BOTTOM ROW: TEAM & PERFORMANCE
    b_left, b_right = st.columns([1, 1])
    
    with b_left:
        with st.container(border=True):
            st.markdown("### Team Members")
            st.markdown("<div style='margin-bottom:15px'></div>", unsafe_allow_html=True)
            
            if not raw_df.empty:
                members = raw_df['name_activity_pilot'].unique()
                for member in members:
                    m_tasks = raw_df[raw_df['name_activity_pilot'] == member]
                    count = len(m_tasks)
                    comp = len(m_tasks[m_tasks['status'] == 'Completed'])
                    pct = int((comp/count)*100) if count > 0 else 0
                    
                    st.markdown(f"""
                    <div class="team-row">
                        <div style="display:flex; align-items:center;">
                            <div class="team-avatar">👤</div>
                            <div class="team-info">
                                <div class="team-name">{member}</div>
                                <div class="team-role">Frontend Dev</div>
                            </div>
                        </div>
                        <div style="text-align:right">
                            <div class="team-stat">{count} Tasks</div>
                            <small style="color:#27ae60; font-weight:bold;">{pct}% Perf</small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.write("No team data.")
            
    with b_right:
        with st.container(border=True):
            if not raw_df.empty:
                st.plotly_chart(get_ftr_otd_chart(raw_df), use_container_width=True)
            else:
                st.write("No performance data.")

def team_member_view():
    st.title(f"Tasks: {st.session_state['name']}")
    
    df = get_all_tasks()
    my_tasks = df[df['name_activity_pilot'] == st.session_state['name']] if not df.empty else pd.DataFrame()
    
    # Kanban Board
    cols = st.columns(4)
    statuses = ["Hold", "Inprogress", "Completed", "Cancelled"]
    colors = ["#f39c12", "#3498db", "#2ecc71", "#e74c3c"]
    
    for i, status in enumerate(statuses):
        with cols[i]:
            st.markdown(f"<div style='background:{colors[i]}; color:white; padding:8px; text-align:center; border-radius:6px; font-weight:bold; margin-bottom:10px;'>{status}</div>", unsafe_allow_html=True)
            
            if not my_tasks.empty:
                tasks_in_col = my_tasks[my_tasks['status'] == status]
                for _, row in tasks_in_col.iterrows():
                    with st.container(border=True):
                        st.markdown(f"**{row['task_name']}**")
                        st.caption(f"Due: {row['commitment_date_to_customer']}")
                        
                        with st.expander("Update"):
                            with st.form(key=f"k_{row['id']}"):
                                new_s = st.selectbox("Status", statuses, index=statuses.index(status))
                                n_date = st.date_input("Actual Date", value=date.today())
                                if st.form_submit_button("Save"):
                                    update_task_status(row['id'], new_s, n_date)
                                    st.rerun()

# --- MAIN ---

def main():
    init_db()
    create_demo_data() # Ensure DB is not empty on first run
    
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        login_page()
    else:
        with st.sidebar:
            st.image("https://api.dicebear.com/7.x/avataaars/svg?seed=Felix", width=80)
            st.write(f"**{st.session_state['name']}**")
            st.write(f"Role: {st.session_state['role']}")
            st.markdown("---")
            if st.button("Logout", use_container_width=True):
                st.session_state['logged_in'] = False
                st.rerun()
        
        if st.session_state['role'] == "Team Leader":
            team_leader_view()
        else:
            team_member_view()

if __name__ == "__main__":
    main()
