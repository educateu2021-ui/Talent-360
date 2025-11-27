import streamlit as st
import pandas as pd
import sqlite3
import uuid
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import io

# --- CONFIGURATION & SETUP ---
st.set_page_config(page_title="KPI Management System", layout="wide", page_icon="📊")

# --- CUSTOM CSS FOR MODERN UI ---
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Card Style - Ensuring full width and proper spacing */
    .dashboard-card {
        background-color: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        width: 100%;
        overflow: hidden; /* Prevent content spill */
    }
    
    /* Kanban Card */
    .kanban-card {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #4CAF50;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .kanban-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.15);
    }
    
    /* Status Header for Kanban */
    .status-header {
        text-align: center;
        padding: 8px;
        color: white;
        border-radius: 5px;
        margin-bottom: 15px;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 0.9em;
    }

    /* Metric Card Styling */
    .metric-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: #1f1f1f;
    }
    .metric-label {
        color: #6c757d;
        font-size: 14px;
        margin-bottom: 5px;
    }
    .metric-trend {
        font-size: 12px;
        padding: 2px 8px;
        border-radius: 10px;
        font-weight: 600;
    }
    .trend-up {
        background-color: #e6f4ea;
        color: #1e7e34;
    }
    .trend-down {
        background-color: #fbecec;
        color: #d93025;
    }
    .icon-box {
        width: 45px;
        height: 45px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
    }
    
    /* Custom Button Styling */
    div.stButton > button:first-child {
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Team Member Row Styling */
    .team-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid #f1f3f5;
    }
    .team-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background-color: #e9ecef;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        margin-right: 15px;
    }
    .team-info {
        flex-grow: 1;
    }
    .team-name {
        font-weight: 600;
        font-size: 14px;
        color: #343a40;
    }
    .team-role {
        font-size: 12px;
        color: #868e96;
    }
    .team-stat {
        background-color: #f8f9fa;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        color: #495057;
    }
</style>
""", unsafe_allow_html=True)

# --- DATABASE FUNCTIONS ---

def init_db():
    conn = sqlite3.connect('kpi_data.db')
    c = conn.cursor()
    
    # Using tasks_v2 to match schema
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

def add_task(data, task_id=None):
    conn = sqlite3.connect('kpi_data.db')
    c = conn.cursor()
    
    # Logic for OTD
    otd_int = "N/A"
    if data['actual_delivery_date'] and data['commitment_date_to_customer']:
        # Ensure string comparison works or convert to date
        otd_int = "Yes" if str(data['actual_delivery_date']) <= str(data['commitment_date_to_customer']) else "NO"
        
    otd_cust = "N/A" 
    if data['actual_delivery_date'] and data['commitment_date_to_customer']:
         otd_cust = "Yes" if str(data['actual_delivery_date']) <= str(data['commitment_date_to_customer']) else "NO"

    if task_id:
        # Update existing
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
        # Create new
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
        df = pd.DataFrame() # Handle case where table might not exist yet
    conn.close()
    return df

def update_task_status(task_id, new_status, new_actual_date=None):
    conn = sqlite3.connect('kpi_data.db')
    c = conn.cursor()
    
    # Recalculate OTD if date provided
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
        # Append to database, ensure columns match
        df.to_sql('tasks_v2', conn, if_exists='append', index=False)
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error importing: {e}")
        return False

# --- AUTHENTICATION MOCK ---
USERS = {
    "leader": {"password": "123", "role": "Team Leader", "name": "Alice (Lead)"},
    "member1": {"password": "123", "role": "Team Member", "name": "Bob (Member)"},
    "member2": {"password": "123", "role": "Team Member", "name": "Charlie (Member)"}
}

def login_page():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        with st.container():
            st.markdown("""
            <div style="background-color: white; padding: 40px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center;">
                <h2 style="color: #333;">Welcome Back</h2>
                <p style="color: #666;">Enter your credentials to access the KPI System</p>
            </div>
            <br>
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

# --- UI COMPONENT FUNCTIONS ---

def metric_card(title, value, trend, icon_color, icon_char):
    trend_cls = "trend-up" if "+" in trend else "trend-down"
    st.markdown(f"""
    <div class="dashboard-card" style="margin-bottom: 0px; height: 100%;">
        <div class="metric-container">
            <div>
                <div class="metric-value">{value}</div>
                <div class="metric-label">{title}</div>
                <div class="metric-trend {trend_cls}">{trend}</div>
            </div>
            <div class="icon-box" style="background-color: {icon_color}20; color: {icon_color};">
                {icon_char}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- REAL DATA GRAPHS ---
def get_analytics_chart(df):
    if df.empty:
        return go.Figure()

    # Ensure date format
    df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')
    df['month'] = df['start_date'].dt.strftime('%Y-%m')
    
    # Aggregate
    monthly_counts = df.groupby(['month', 'status']).size().reset_index(name='count')
    
    # Pivot for chart
    pivot_df = monthly_counts.pivot(index='month', columns='status', values='count').fillna(0).reset_index()
    
    fig = go.Figure()
    if 'Completed' in pivot_df.columns:
        fig.add_trace(go.Scatter(x=pivot_df['month'], y=pivot_df['Completed'], fill='tozeroy', name='Completed', line=dict(color='#1cc88a')))
    if 'Inprogress' in pivot_df.columns:
        fig.add_trace(go.Scatter(x=pivot_df['month'], y=pivot_df['Inprogress'], fill='tozeroy', name='In Progress', line=dict(color='#4e73df')))
    
    fig.update_layout(
        title="Project Analytics",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=30, b=0),
        height=300,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title="Month",
        yaxis_title="Tasks"
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
        height=200, 
        margin=dict(l=0, r=0, t=0, b=0),
        annotations=[dict(text=f"{completed_pct}%", x=0.5, y=0.5, font_size=20, showarrow=False)]
    )
    return fig

def get_ftr_otd_chart(df):
    if df.empty:
        return go.Figure()
        
    df['actual_delivery_date'] = pd.to_datetime(df['actual_delivery_date'], errors='coerce')
    df = df.dropna(subset=['actual_delivery_date']) # Only count delivered tasks
    
    # Group by month for simplicity in bar chart
    df['month'] = df['actual_delivery_date'].dt.strftime('%b')
    
    # Calculate % Yes for OTD and FTR per month
    monthly_stats = df.groupby('month').agg({
        'otd_internal': lambda x: (x == 'Yes').mean() * 100,
        'ftr_internal': lambda x: (x == 'Yes').mean() * 100
    }).reset_index()
    
    fig = go.Figure(data=[
        go.Bar(name='FTR', x=monthly_stats['month'], y=monthly_stats['ftr_internal'], marker_color='#1cc88a'),
        go.Bar(name='OTD', x=monthly_stats['month'], y=monthly_stats['otd_internal'], marker_color='#4e73df')
    ])
    fig.update_layout(
        title="Team Performance (FTR / OTD)", 
        barmode='group', 
        height=300, 
        margin=dict(l=0, r=0, t=40, b=0), 
        showlegend=False
    )
    return fig

# --- FORM COMPONENT (Create / Edit) ---
def task_form(mode="create", task_id=None, default_data=None):
    form_title = "Create New Job" if mode == "create" else "Edit Job Details"
    btn_text = "Create Job" if mode == "create" else "Update Job"
    
    st.markdown(f"### {form_title}")
    
    # If no default data (create mode), create empty dict structure
    if not default_data:
        default_data = {k: None for k in ["task_name", "name_activity_pilot", "activity_type", "reference_part_number", 
                                          "status", "start_date", "date_of_receipt", "date_of_clarity_in_input", 
                                          "commitment_date_to_customer", "project_lead", "name_quality_gate_referent", 
                                          "ftr_internal", "description_of_activity", "customer_manager_name", 
                                          "customer_remarks", "actual_delivery_date"]}
        # Set defaults for required fields to avoid NoneType errors in widgets if needed
        default_data["project_lead"] = st.session_state['name']

    with st.form("task_form_component", clear_on_submit=(mode=="create")):
        col1, col2, col3 = st.columns(3)
        pilots = [u['name'] for k,u in USERS.items() if u['role'] == "Team Member"]

        # Parse dates if they are strings from DB
        def parse_d(d_val):
            if isinstance(d_val, str) and d_val:
                try: return datetime.strptime(d_val, '%Y-%m-%d').date()
                except: return None
            return d_val

        with col1:
            task_name = st.text_input("Task Name", value=default_data.get("task_name"))
            
            # Handle Selectbox defaults
            p_idx = pilots.index(default_data["name_activity_pilot"]) if default_data.get("name_activity_pilot") in pilots else None
            name_pilot = st.selectbox("Assign To", pilots, index=p_idx, placeholder="Select Pilot...")
            
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
            
            # Show actual date if editing
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
        
        # Hidden defaults
        ftr_cust = default_data.get("ftr_customer", "N/A")
        ftr_gate = default_data.get("ftr_quality_gate_internal", "N/A")

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
                    "ftr_customer": ftr_cust,
                    "reference_part_number": ref_part,
                    "ftr_internal": ftr_int,
                    "description_of_activity": desc,
                    "activity_type": activity_type,
                    "ftr_quality_gate_internal": ftr_gate,
                    "date_of_clarity_in_input": date_clarity,
                    "start_date": start_date,
                    "customer_remarks": remarks,
                    "name_quality_gate_referent": qual_ref,
                    "project_lead": project_lead,
                    "customer_manager_name": cust_manager
                }
                
                add_task(form_data, task_id=task_id) # Pass ID if editing
                st.success(f"{btn_text} Successfully!")
                st.session_state['show_form'] = False
                st.session_state['edit_mode'] = False
                st.session_state['edit_task_id'] = None
                st.rerun()

    if st.button("Cancel / Close Form"):
        st.session_state['show_form'] = False
        st.session_state['edit_mode'] = False
        st.session_state['edit_task_id'] = None
        st.rerun()

# --- TEAM LEADER DASHBOARD ---
def team_leader_view():
    raw_df = get_all_tasks()
    
    # --- Top Bar with Import/Export ---
    col_title, col_actions, col_profile = st.columns([4, 4, 1])
    with col_title:
        st.title("Dashboard")
        
    with col_actions:
        # Import / Export Layout
        c_imp, c_exp, c_new = st.columns([1.5, 1, 1])
        with c_imp:
             uploaded_file = st.file_uploader("Import CSV", type=['csv'], label_visibility="collapsed")
             if uploaded_file:
                 if import_data_from_csv(uploaded_file):
                     st.success("Imported!")
                     st.rerun()
        with c_exp:
             if not raw_df.empty:
                 csv = raw_df.to_csv(index=False).encode('utf-8')
                 st.download_button("Export CSV", csv, "kpi_tasks.csv", "text/csv", use_container_width=True)
        with c_new:
            if st.button("✚ New Job", type="primary", use_container_width=True):
                st.session_state['show_form'] = True
                st.session_state['edit_mode'] = False
                
    with col_profile:
        st.image("https://api.dicebear.com/7.x/avataaars/svg?seed=Felix", width=50)

    # --- CONDITIONAL FORM RENDER (CREATE or EDIT) ---
    if st.session_state.get('show_form', False):
        st.markdown("---")
        if st.session_state.get('edit_mode', False) and st.session_state.get('edit_task_id'):
            # Fetch specific task data
            task_data = raw_df[raw_df['id'] == st.session_state['edit_task_id']].iloc[0].to_dict()
            task_form(mode="edit", task_id=st.session_state['edit_task_id'], default_data=task_data)
        else:
            task_form(mode="create")
        st.markdown("---")
    
    # --- DATE FILTERS (ADDED) ---
    with st.container():
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        f1, f2, f3 = st.columns([1,1,1])
        with f1: 
            d_from = st.date_input("From Date", value=date.today() - timedelta(days=30))
        with f2: 
            d_to = st.date_input("To Date", value=date.today())
        with f3:
             f_priority = st.selectbox("Priority (Demo)", ["All", "High", "Medium", "Low"]) # Placeholder as Priority not in DB
        st.markdown('</div>', unsafe_allow_html=True)
        
    # --- FILTER LOGIC ---
    df = raw_df.copy()
    if not df.empty and 'start_date' in df.columns:
        # Convert start_date to datetime for filtering
        df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce').dt.date
        df = df[(df['start_date'] >= d_from) & (df['start_date'] <= d_to)]
    
    # --- METRICS ROW ---
    c1, c2, c3, c4 = st.columns(4)
    
    total_jobs = len(df)
    in_progress = len(df[df['status'] == 'Inprogress'])
    on_hold = len(df[df['status'] == 'Hold'])
    delivered = len(df[df['status'] == 'Completed'])
    
    with c1: metric_card("Jobs Created", total_jobs, "Total", "#4e73df", "💼")
    with c2: metric_card("Task InProgress", in_progress, "Active", "#36b9cc", "📂")
    with c3: metric_card("Hold", on_hold, "Paused", "#e74a3b", "🛑")
    with c4: metric_card("Delivered", delivered, "Done", "#1cc88a", "🤝")

    # --- CHARTS ROW ---
    st.markdown("<br>", unsafe_allow_html=True)
    c_left, c_right = st.columns([2, 1])
    
    with c_left:
        with st.container():
            st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
            if not df.empty:
                st.plotly_chart(get_analytics_chart(df), use_container_width=True)
            else:
                st.info("No data for analytics.")
            st.markdown('</div>', unsafe_allow_html=True)
            
    with c_right:
        with st.container():
            st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
            st.markdown("##### Progress Rate")
            if not df.empty:
                st.plotly_chart(get_donut_chart(df), use_container_width=True)
            else:
                st.info("No data.")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- ACTIVE TASKS LIST ---
    with st.container():
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown("### Active Tasks List")
        
        # Header - Adjusted ratios for better spacing
        h1, h2, h3, h4, h5 = st.columns([3, 2, 2, 1.5, 1])
        h1.markdown("**Task Name**")
        h2.markdown("**Assigned To**")
        h3.markdown("**Deadline**")
        h4.markdown("**Status**")
        h5.markdown("**Action**")
        st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)
        
        # Rows
        if not df.empty:
            for index, row in df.iterrows():
                c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 1.5, 1])
                
                with c1: st.write(row['task_name'])
                with c2: st.write(row['name_activity_pilot'])
                with c3: st.write(row['commitment_date_to_customer'])
                
                # Status Badge logic
                s_color = "gray"
                if row['status'] == "Completed": s_color = "green"
                elif row['status'] == "Inprogress": s_color = "blue"
                elif row['status'] == "Hold": s_color = "orange"
                
                with c4: st.markdown(f":{s_color}[{row['status']}]")
                
                with c5:
                    if st.button("Edit", key=f"btn_edit_{row['id']}"):
                        st.session_state['show_form'] = True
                        st.session_state['edit_mode'] = True
                        st.session_state['edit_task_id'] = row['id']
                        st.rerun()
                
                st.markdown("<hr style='margin: 5px 0; opacity: 0.2;'>", unsafe_allow_html=True)
        else:
            st.info("No active tasks found in this date range.")
            
        st.markdown('</div>', unsafe_allow_html=True)

    # --- TEAM MEMBERS & PERFORMANCE ROW (RESTORED) ---
    c_team, c_perf = st.columns([1, 1])
    
    with c_team:
        with st.container():
            st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
            st.markdown("### Team Members")
            
            # Aggregate stats per user from df
            if not df.empty:
                # Get unique members
                members = df['name_activity_pilot'].unique()
                for member in members:
                    # Filter for specific member
                    m_tasks = df[df['name_activity_pilot'] == member]
                    count = len(m_tasks)
                    # Simple performance metric logic (e.g. % completed)
                    completed = len(m_tasks[m_tasks['status'] == 'Completed'])
                    perf_score = int((completed / count * 100)) if count > 0 else 0
                    
                    role = "Team Member" # Default
                    
                    st.markdown(f"""
                    <div class="team-row">
                        <div class="team-avatar">👤</div>
                        <div class="team-info">
                            <div class="team-name">{member}</div>
                            <div class="team-role">{role}</div>
                        </div>
                        <div class="team-stat">{count} Tasks</div>
                        <div style="margin-left:10px; color:green; font-weight:bold;">{perf_score}% Done</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No team data available.")
                
            st.markdown('</div>', unsafe_allow_html=True)

    with c_perf:
        with st.container():
            st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
            if not df.empty:
                st.plotly_chart(get_ftr_otd_chart(df), use_container_width=True)
            else:
                st.info("Not enough data for FTR/OTD.")
            st.markdown('</div>', unsafe_allow_html=True)


# --- TEAM MEMBER VIEW (Kanban Restored) ---
def team_member_view():
    st.title(f"👷 Team Member Workspace: {st.session_state['name']}")
    
    # Filter options
    show_all = st.checkbox("Show All Team Tasks", value=False)
    
    df = get_all_tasks()
    
    if not show_all:
        df = df[df['name_activity_pilot'] == st.session_state['name']]
    
    st.markdown("### Kanban Board")
    
    # Kanban Columns
    cols = st.columns(4, gap="medium")
    statuses = ["Hold", "Inprogress", "Completed", "Cancelled"]
    colors = ["#FFA500", "#3498DB", "#2ECC71", "#E74C3C"]
    
    for i, status in enumerate(statuses):
        with cols[i]:
            st.markdown(f"<div class='status-header' style='background-color:{colors[i]}'>{status}</div>", unsafe_allow_html=True)
            
            # Filter tasks for this column
            tasks_in_col = df[df['status'] == status]
            
            for index, row in tasks_in_col.iterrows():
                # Kanban Card
                with st.container():
                    st.markdown(f"""
                    <div class='kanban-card'>
                        <b>{row['task_name']}</b><br>
                        <small>ID: {row['id']}</small><br>
                        <small>Ref: {row['reference_part_number']}</small><br>
                        <small>Due: {row['commitment_date_to_customer']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Update functionality inside expader
                    with st.expander("Update / Details"):
                        st.text(f"Desc: {row['description_of_activity']}")
                        st.text(f"Internal OTD: {row['otd_internal']}")
                        
                        # Form to prevent auto-reloading on every change
                        with st.form(key=f"form_{row['id']}"):
                            new_status = st.selectbox("Status", statuses, index=statuses.index(status))
                            
                            # Only show Date Picker if completing or need to update
                            actual_date_val = None
                            if row['actual_delivery_date']:
                                try:
                                    default_date = datetime.strptime(row['actual_delivery_date'], '%Y-%m-%d').date()
                                except:
                                    default_date = date.today()
                            else:
                                default_date = date.today()
                                
                            new_actual_date = st.date_input("Actual Delivery Date", value=default_date)
                            
                            update_btn = st.form_submit_button("Update")
                            
                            if update_btn:
                                update_task_status(row['id'], new_status, new_actual_date)
                                st.success("Updated!")
                                st.rerun()

# --- MAIN APP LOGIC ---

def main():
    init_db()
    
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        login_page()
    else:
        # Sidebar for logout
        with st.sidebar:
            st.image("https://api.dicebear.com/7.x/avataaars/svg?seed=Felix", width=100)
            st.markdown(f"### {st.session_state['name']}")
            st.write(f"Role: **{st.session_state['role']}**")
            st.markdown("---")
            if st.button("Logout", use_container_width=True):
                st.session_state['logged_in'] = False
                st.rerun()
        
        # Route based on role
        if st.session_state['role'] == "Team Leader":
            team_leader_view()
        else:
            team_member_view()

if __name__ == "__main__":
    main()
