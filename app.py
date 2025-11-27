import streamlit as st
import pandas as pd
import sqlite3
import uuid
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta

# --- CONFIGURATION & SETUP ---
st.set_page_config(page_title="KPI Management System", layout="wide", page_icon="📊")

# --- CUSTOM CSS FOR MODERN UI (improved targeting for white cards) ---
st.markdown("""
<style>
    /* App background */
    .stApp { background-color: #f0f2f6; }

    /* Reduce top padding */
    .main .block-container { padding-top: 1rem; padding-bottom: 2rem; }

    /* Make all container-like blocks white with rounded corners and shadow */
    /* Targets many streamlit wrappers used for containers, columns, and cards */
    div[data-testid^="stVerticalBlock"], div[data-testid^="stContainer"], div[data-testid^="stHorizontalBlock"], section[data-testid^="stVerticalBlock"] {
        background-color: #ffffff !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04) !important;
        border: 1px solid #e8eaf0 !important;
        padding: 16px !important;
        margin-bottom: 16px !important;
    }
    /* inner wrappers sometimes inherit grey; force transparent inner backgrounds */
    div[data-testid^="stVerticalBlock"] > div, div[data-testid^="stContainer"] > div { background-color: transparent !important; }

    /* Metric card */
    .metric-card { background-color: #FFFFFF !important; padding: 16px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.03); border: 1px solid #e0e0e0; display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
    .metric-value { font-size: 26px; font-weight:700; color:#2c3e50; margin:0; }
    .metric-label { font-size:14px; color:#7f8c8d; margin-bottom:4px; text-transform:uppercase; letter-spacing:0.5px; font-weight:600; }
    .metric-trend { font-size:13px; font-weight:600; }
    .trend-up { color:#16a34a; background:#eafaf1; padding:2px 8px; border-radius:4px; }
    .trend-down { color:#b91c1c; background:#fff5f5; padding:2px 8px; border-radius:4px; }
    .icon-box { width:50px; height:50px; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:24px; }

    /* Task header style */
    .task-header { font-weight:700; color:#95a5a6; font-size:12px; text-transform:uppercase; padding-bottom:10px; border-bottom:2px solid #f0f2f6; }

    /* Badges */
    .badge { padding:5px 12px; border-radius:15px; font-size:12px; font-weight:600; }
    .badge-completed { background-color:#d1fae5; color:#065f46; }
    .badge-inprogress { background-color:#dbeafe; color:#1e40af; }
    .badge-hold { background-color:#fee2e2; color:#991b1b; }

    /* Fix for charts overflow */
    .js-plotly-plot { width:100% !important; }
</style>
""", unsafe_allow_html=True)

# --- DATABASE FUNCTIONS ---

def init_db():
    conn = sqlite3.connect('kpi_data.db')
    c = conn.cursor()
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
    
    # compute OTD based on commitment vs actual (string compare avoided; use date objects if present)
    otd_int = "N/A"
    if data.get('actual_delivery_date') and data.get('commitment_date_to_customer'):
        try:
            a = pd.to_datetime(data['actual_delivery_date']).date()
            cmt = pd.to_datetime(data['commitment_date_to_customer']).date()
            otd_int = "OK" if a <= cmt else "NOT OK"
        except:
            otd_int = "N/A"
    # Keep otd_customer same logic
    otd_cust = otd_int

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
            data.get('name_activity_pilot'), data.get('task_name'), str(data.get('date_of_receipt')), str(data.get('actual_delivery_date')),
            str(data.get('commitment_date_to_customer')), data.get('status'), data.get('ftr_customer'), data.get('reference_part_number'),
            data.get('ftr_internal'), otd_int, data.get('description_of_activity'), data.get('activity_type'),
            data.get('ftr_quality_gate_internal'), str(data.get('date_of_clarity_in_input')), str(data.get('start_date')), otd_cust,
            data.get('customer_remarks'), data.get('name_quality_gate_referent'), data.get('project_lead'), data.get('customer_manager_name'),
            task_id
        ))
    else:
        new_id = str(uuid.uuid4())[:8]
        c.execute('''
            INSERT INTO tasks_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            new_id, 
            data.get('name_activity_pilot'), data.get('task_name'), str(data.get('date_of_receipt')), str(data.get('actual_delivery_date')),
            str(data.get('commitment_date_to_customer')), data.get('status'), data.get('ftr_customer'), data.get('reference_part_number'),
            data.get('ftr_internal'), otd_int, data.get('description_of_activity'), data.get('activity_type'),
            data.get('ftr_quality_gate_internal'), str(data.get('date_of_clarity_in_input')), str(data.get('start_date')), otd_cust,
            data.get('customer_remarks'), data.get('name_quality_gate_referent'), data.get('project_lead'), data.get('customer_manager_name')
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
    comm_date_str = res[0] if res else None
    
    otd_val = "N/A"
    if comm_date_str and new_actual_date:
        try:
            comm_d = pd.to_datetime(comm_date_str).date()
            if isinstance(new_actual_date, (str,)):
                actual_d = pd.to_datetime(new_actual_date).date()
            else:
                actual_d = new_actual_date
            otd_val = "OK" if actual_d <= comm_d else "NOT OK"
        except:
            otd_val = "N/A"

    if new_actual_date:
        c.execute('''UPDATE tasks_v2 SET status = ?, actual_delivery_date = ?, otd_internal = ?, otd_customer = ? WHERE id = ?''', 
                  (new_status, str(new_actual_date), otd_val, otd_val, task_id))
    else:
        c.execute("UPDATE tasks_v2 SET status = ? WHERE id = ?", (new_status, task_id))
    conn.commit()
    conn.close()

def import_data_from_csv(file):
    try:
        df = pd.read_csv(file)
        
        if 'id' not in df.columns:
            df['id'] = [str(uuid.uuid4())[:8] for _ in range(len(df))]
        else:
            df['id'] = df['id'].apply(lambda x: str(uuid.uuid4())[:8] if pd.isna(x) or x == '' else x)
            
        required_cols = [
            "name_activity_pilot", "task_name", "date_of_receipt", "actual_delivery_date", 
            "commitment_date_to_customer", "status", "ftr_customer", "reference_part_number", 
            "ftr_internal", "otd_internal", "description_of_activity", "activity_type", 
            "ftr_quality_gate_internal", "date_of_clarity_in_input", "start_date", "otd_customer", 
            "customer_remarks", "name_quality_gate_referent", "project_lead", "customer_manager_name"
        ]
        
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
        
        cols_to_keep = ['id'] + required_cols
        df = df[cols_to_keep]

        conn = sqlite3.connect('kpi_data.db')
        c = conn.cursor()
        
        for index, row in df.iterrows():
            placeholders = ', '.join(['?'] * len(row))
            sql = f"INSERT OR REPLACE INTO tasks_v2 VALUES ({placeholders})"
            c.execute(sql, tuple(row))
            
        conn.commit()
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
        with st.container():
            st.markdown("<h2 style='text-align: center; color: #2c3e50;'>KPI System Login</h2>", unsafe_allow_html=True)
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
    trend_cls = "trend-up" if "+" in str(trend) else "trend-down"
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
    df['start_date'] = pd.to_datetime(df['start_date'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['start_date'])
    df = df.sort_values('start_date')
    df['month'] = df['start_date'].dt.strftime('%b')
    monthly_counts = df.groupby(['month', 'status'], sort=False).size().reset_index(name='count')
    fig = px.bar(monthly_counts, x="month", y="count", color="status",
                  color_discrete_map={"Completed": "#10b981", "Inprogress": "#3b82f6", "Hold": "#ef4444", "Cancelled": "#9ca3af"},
                  title="Project Analytics (Count by Status)", barmode='group')
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,t=40,b=0), height=350, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    return fig

def get_donut_chart(df):
    if df.empty:
        completed_pct = 0
    else:
        total = len(df)
        completed = len(df[df['status'] == 'Completed'])
        completed_pct = int((completed / total) * 100) if total > 0 else 0
    fig = go.Figure(data=[go.Pie(labels=['Completed', 'Pending'], values=[completed_pct, 100-completed_pct], hole=.7, marker_colors=['#10b981', '#f3f4f6'], textinfo='none')])
    fig.update_layout(showlegend=False, height=250, margin=dict(l=0,r=0,t=0,b=0), annotations=[dict(text=f"{completed_pct}%", x=0.5, y=0.5, font_size=24, showarrow=False)])
    return fig

def get_ftr_otd_chart(df):
    if df.empty:
        return go.Figure()
    df['actual_delivery_date'] = pd.to_datetime(df['actual_delivery_date'], dayfirst=True, errors='coerce')
    df_del = df.dropna(subset=['actual_delivery_date'])
    if df_del.empty:
        fig = go.Figure()
        fig.update_layout(title="No Completed Tasks Yet", height=300)
        return fig
    df_del['month'] = df_del['actual_delivery_date'].dt.strftime('%b')
    monthly_stats = df_del.groupby('month').agg({
        'otd_internal': lambda x: ((x == 'OK') | (x == 'Yes')).mean() * 100,
        'ftr_internal': lambda x: (x == 'Yes').mean() * 100
    }).reset_index()
    fig = go.Figure(data=[
        go.Bar(name='FTR %', x=monthly_stats['month'], y=monthly_stats['ftr_internal'], marker_color='#10b981'),
        go.Bar(name='OTD %', x=monthly_stats['month'], y=monthly_stats['otd_internal'], marker_color='#3b82f6')
    ])
    fig.update_layout(title="Team Performance (FTR / OTD)", barmode='group', height=300, margin=dict(l=0,r=0,t=40,b=0), showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    return fig

# --- FORM COMPONENT (now supports custom form_key for inline edit forms) ---
def task_form(mode="create", task_id=None, default_data=None, form_key="task_form_component"):
    form_title = "Create New Job" if mode == "create" else "Edit Job Details"
    btn_text = "Create Job" if mode == "create" else "Update Job"
    
    st.markdown(f"### {form_title}")
    
    if not default_data:
        default_data = {k: None for k in ["task_name", "name_activity_pilot", "activity_type", "reference_part_number", 
                                          "status", "start_date", "date_of_receipt", "date_of_clarity_in_input", 
                                          "commitment_date_to_customer", "project_lead", "name_quality_gate_referent", 
                                          "ftr_internal", "description_of_activity", "customer_manager_name", 
                                          "customer_remarks", "actual_delivery_date"]}
        default_data["project_lead"] = st.session_state.get('name', '')

    # helper to safely parse provided values to date objects
    def parse_d(d_val):
        if isinstance(d_val, str) and d_val:
            try: return datetime.strptime(d_val.split(" ")[0], '%Y-%m-%d').date()
            except: 
                try:
                    return pd.to_datetime(d_val, dayfirst=True).date()
                except:
                    return None
        if isinstance(d_val, (date,)):
            return d_val
        return None

    with st.form(form_key, clear_on_submit=(mode=="create")):
        col1, col2, col3 = st.columns(3)
        pilots = [u['name'] for k,u in USERS.items() if u['role'] == "Team Member"]
        # safe index handling
        with col1:
            task_name = st.text_input("Task Name", value=default_data.get("task_name") or "")
            try:
                p_idx = pilots.index(default_data.get("name_activity_pilot")) if default_data.get("name_activity_pilot") in pilots else 0
            except:
                p_idx = 0
            name_pilot = st.selectbox("Assign To", pilots, index=p_idx)
            types = ["3d development", "2d drawing", "Release"]
            try:
                t_idx = types.index(default_data.get("activity_type")) if default_data.get("activity_type") in types else 0
            except:
                t_idx = 0
            activity_type = st.selectbox("Type", types, index=t_idx)
            ref_part = st.text_input("Ref Part Number", value=default_data.get("reference_part_number") or "")
            
        with col2:
            statuses = ["Hold", "Inprogress", "Completed", "Cancelled"]
            try:
                s_idx = statuses.index(default_data.get("status")) if default_data.get("status") in statuses else 1
            except:
                s_idx = 1
            status = st.selectbox("Current Status", statuses, index=s_idx)
            start_date = st.date_input("Start Date", value=parse_d(default_data.get("start_date")) or date.today())
            date_receipt = st.date_input("Date of Receipt", value=parse_d(default_data.get("date_of_receipt")) or date.today())
            date_clarity = st.date_input("Date Clarity", value=parse_d(default_data.get("date_of_clarity_in_input")) or date.today())
            
        with col3:
            comm_date = st.date_input("Commitment Date", value=parse_d(default_data.get("commitment_date_to_customer")) or (date.today() + timedelta(days=7)))
            act_date_val = parse_d(default_data.get("actual_delivery_date"))
            actual_date = st.date_input("Actual Delivery", value=act_date_val or date.today())
            project_lead = st.text_input("Project Lead", value=default_data.get("project_lead") or st.session_state.get('name',''))
            qual_ref = st.text_input("Quality Gate Ref", value=default_data.get("name_quality_gate_referent") or "")

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            ftr_opts = ["Yes", "NO"]
            try:
                f_idx = ftr_opts.index(default_data.get("ftr_internal")) if default_data.get("ftr_internal") in ftr_opts else 0
            except:
                f_idx = 0
            ftr_int = st.selectbox("FTR Internal Target", ftr_opts, index=f_idx)
            desc = st.text_area("Description", value=default_data.get("description_of_activity") or "")
        with c2:
            cust_manager = st.text_input("Customer Manager", value=default_data.get("customer_manager_name") or "")
            remarks = st.text_area("Remarks", value=default_data.get("customer_remarks") or "")

        # --- OTD display: automatically compute as user changes dates ---
        otd_display = "N/A"
        try:
            if comm_date and actual_date:
                otd_display = "OK" if actual_date <= comm_date else "NOT OK"
        except:
            otd_display = "N/A"

        st.markdown(f"**OTD (Commitment vs Actual):** <span style='font-weight:700'>{otd_display}</span>", unsafe_allow_html=True)

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
                # close form flags (if any)
                st.session_state['show_form'] = False
                st.session_state['edit_mode'] = False
                st.session_state.pop('edit_task_id', None)
                st.experimental_rerun()
    
    if st.button("Close Form", key=form_key + "_close"):
        st.session_state['show_form'] = False
        st.session_state['edit_mode'] = False
        st.session_state.pop('edit_task_id', None)
        st.experimental_rerun()

# --- DASHBOARD VIEWS ---

def team_leader_view():
    raw_df = get_all_tasks()
    
    # 1. HEADER & ACTIONS
    c1, c2 = st.columns([5, 3])
    with c1: st.title("Dashboard")
    with c2: 
        ac1, ac2, ac3 = st.columns([1, 1, 1])
        with ac1:
            uploaded_file = st.file_uploader("Import", type=['csv'], label_visibility="collapsed")
            if uploaded_file:
                if import_data_from_csv(uploaded_file):
                    st.success("Imported successfully")
                    st.experimental_rerun()
        with ac2:
            if not raw_df.empty:
                csv = raw_df.to_csv(index=False).encode('utf-8')
                st.download_button("Export", csv, "kpi_tasks.csv", "text/csv", use_container_width=True)
        with ac3:
            if st.button("✚ New", type="primary", use_container_width=True):
                 st.session_state['show_form'] = True
                 st.session_state['edit_mode'] = False

    # if creating a new job, show the create form at the top
    if st.session_state.get('show_form', False) and not st.session_state.get('edit_mode', False):
        with st.container():
            task_form(mode="create", form_key="create_form_unique")

    # 2. METRICS ROW
    m1, m2, m3, m4 = st.columns(4)
    total = len(raw_df)
    active = len(raw_df[raw_df['status'] == 'Inprogress']) if not raw_df.empty else 0
    hold = len(raw_df[raw_df['status'] == 'Hold']) if not raw_df.empty else 0
    done = len(raw_df[raw_df['status'] == 'Completed']) if not raw_df.empty else 0
    
    with m1: metric_card("Jobs Created", total, "+4.6%", "#3b82f6", "💼")
    with m2: metric_card("In Progress", active, "+2.1%", "#eab308", "⚡")
    with m3: metric_card("On Hold", hold, "-0.5%", "#ef4444", "⏸️")
    with m4: metric_card("Delivered", done, "+12%", "#10b981", "✅")

    # 3. CHARTS ROW
    st.markdown("<br>", unsafe_allow_html=True)
    c_left, c_right = st.columns([2, 1])
    
    with c_left:
        with st.container():
            if not raw_df.empty:
                st.plotly_chart(get_analytics_chart(raw_df), use_container_width=True)
            else:
                st.info("No data available.")
            
    with c_right:
        with st.container():
            st.markdown("##### My Progress")
            st.markdown("<small style='color:grey'>Task completion rate</small>", unsafe_allow_html=True)
            if not raw_df.empty:
                st.plotly_chart(get_donut_chart(raw_df), use_container_width=True)
            else:
                st.info("No data.")
            
    # 4. FILTER BAR & TABLE
    st.markdown("### Active Tasks")
    
    with st.container():
        c_f1, c_f2, c_f3, c_btn = st.columns([1.5, 1.5, 1.5, 1])
        with c_f1: d_from = st.date_input("From:", value=date.today()-timedelta(days=90))
        with c_f2: d_to = st.date_input("To:", value=date.today() + timedelta(days=30))
        with c_f3: prio = st.selectbox("Priority", ["All", "High", "Medium", "Low"])
        with c_btn: 
            st.write("") 
            st.write("") 
            st.button("Filter", use_container_width=True)
    
    df_filtered = raw_df.copy() if raw_df is not None else pd.DataFrame()
    if not df_filtered.empty and 'start_date' in df_filtered.columns:
        df_filtered['start_date'] = pd.to_datetime(df_filtered['start_date'], dayfirst=True, errors='coerce').dt.date
        df_filtered = df_filtered[(df_filtered['start_date'] >= d_from) & (df_filtered['start_date'] <= d_to)]

    with st.container():
        h1, h2, h3, h4, h5 = st.columns([3, 2, 2, 1.5, 1])
        h1.markdown("<div class='task-header'>TASK NAME</div>", unsafe_allow_html=True)
        h2.markdown("<div class='task-header'>ASSIGNED TO</div>", unsafe_allow_html=True)
        h3.markdown("<div class='task-header'>DUE DATE</div>", unsafe_allow_html=True)
        h4.markdown("<div class='task-header'>STATUS</div>", unsafe_allow_html=True)
        h5.markdown("<div class='task-header'>ACTION</div>", unsafe_allow_html=True)
        
        if not df_filtered.empty:
            for _, row in df_filtered.iterrows():
                # build the row
                r1, r2, r3, r4, r5 = st.columns([3, 2, 2, 1.5, 1])
                with r1:
                    st.markdown(f"**{row['task_name']}**")
                    # if this is the task currently being edited, show the inline edit form below
                with r2:
                    st.markdown(f"<span style='color:grey'>{row['name_activity_pilot']}</span>", unsafe_allow_html=True)
                with r3:
                    st.write(row['commitment_date_to_customer'])
                s_cls = "badge-completed" if row['status'] == "Completed" else "badge-inprogress" if row['status'] == "Inprogress" else "badge-hold"
                with r4:
                    st.markdown(f"<span class='badge {s_cls}'>{row['status']}</span>", unsafe_allow_html=True)
                with r5:
                    if st.button("Edit", key=f"edit_{row['id']}"):
                        st.session_state['show_form'] = True
                        st.session_state['edit_mode'] = True
                        st.session_state['edit_task_id'] = row['id']
                        # store defaults for the inline form
                        st.session_state['edit_default'] = row.to_dict()
                        st.experimental_rerun()

                # if this row is being edited, render the form inline below these columns
                if st.session_state.get('edit_mode', False) and st.session_state.get('edit_task_id') == row['id']:
                    # show the edit form inline inside a container to visually attach it to the row
                    with st.container():
                        defaults = st.session_state.get('edit_default', row.to_dict())
                        # ensure keys exist and dates passed in parseable form
                        task_form(mode="edit", task_id=row['id'], default_data=defaults, form_key=f"edit_form_{row['id']}")
                st.markdown("<hr style='margin:0; border-top: 1px solid #f0f0f0;'>", unsafe_allow_html=True)
        else:
            st.info("No active tasks found in this range.")

    # 5. BOTTOM ROW
    b_left, b_right = st.columns([1, 1])
    
    with b_left:
        with st.container():
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
                    <div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid #eee;">
                        <div style="display:flex; align-items:center;">
                            <div style="width:40px; height:40px; border-radius:50%; background:#e5e7eb; display:flex; align-items:center; justify-content:center; margin-right:15px;">👤</div>
                            <div>
                                <div style="font-weight:bold; color:#374151;">{member}</div>
                                <div style="font-size:12px; color:#9ca3af;">Frontend Dev</div>
                            </div>
                        </div>
                        <div style="text-align:right">
                            <div style="font-weight:bold; color:#374151;">{count} Tasks</div>
                            <small style="color:#10b981; font-weight:bold;">{pct}% Perf</small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.write("No team data.")
            
    with b_right:
        with st.container():
            if not raw_df.empty:
                st.plotly_chart(get_ftr_otd_chart(raw_df), use_container_width=True)
            else:
                st.write("No performance data.")

def team_member_view():
    st.title(f"Tasks: {st.session_state['name']}")
    df = get_all_tasks()
    my_tasks = df[df['name_activity_pilot'] == st.session_state['name']] if not df.empty else pd.DataFrame()
    cols = st.columns(4)
    statuses = ["Hold", "Inprogress", "Completed", "Cancelled"]
    colors = ["#f59e0b", "#3b82f6", "#10b981", "#ef4444"]
    for i, status in enumerate(statuses):
        with cols[i]:
            st.markdown(f"<div style='background:{colors[i]}; color:white; padding:8px; text-align:center; border-radius:6px; font-weight:bold; margin-bottom:10px;'>{status}</div>", unsafe_allow_html=True)
            if not my_tasks.empty:
                tasks_in_col = my_tasks[my_tasks['status'] == status]
                for _, row in tasks_in_col.iterrows():
                    with st.container():
                        st.markdown(f"**{row['task_name']}**")
                        st.caption(f"Due: {row['commitment_date_to_customer']}")
                        with st.expander("Update"):
                            with st.form(key=f"k_{row['id']}"):
                                new_s = st.selectbox("Status", statuses, index=statuses.index(status))
                                n_date = st.date_input("Actual Date", value=date.today())
                                if st.form_submit_button("Save"):
                                    update_task_status(row['id'], new_s, n_date)
                                    st.experimental_rerun()

# --- MAIN ---

def main():
    init_db()
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
                st.experimental_rerun()
        if st.session_state['role'] == "Team Leader":
            team_leader_view()
        else:
            team_member_view()

if __name__ == "__main__":
    main()
