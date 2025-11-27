import streamlit as st
import pandas as pd
import sqlite3
import uuid
import plotly.express as px
import plotly.graph_objects as go
import random
from datetime import date, datetime, timedelta

# --- CONFIGURATION & SETUP ---
st.set_page_config(page_title="KPI Management System", layout="wide", page_icon="📊")

# --- CUSTOM CSS FOR MODERN UI ---
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Card Style */
    .dashboard-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
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
    
    /* Custom Button Styling to match 'New Job' */
    div.stButton > button:first-child {
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Table Styling */
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        font-family: sans-serif;
    }
    .styled-table thead tr {
        background-color: #f8f9fa;
        color: #6c757d;
        text-align: left;
    }
    
    /* Status Badges */
    .badge {
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
    }
    .badge-high { background-color: #ffebee; color: #c62828; }
    .badge-medium { background-color: #fff3e0; color: #ef6c00; }
    .badge-low { background-color: #e8f5e9; color: #2e7d32; }
    
</style>
""", unsafe_allow_html=True)

# --- DATABASE FUNCTIONS ---

def init_db():
    conn = sqlite3.connect('kpi_data.db')
    c = conn.cursor()
    
    # Create Tasks Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
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

def add_task(data):
    conn = sqlite3.connect('kpi_data.db')
    c = conn.cursor()
    
    otd_int = "N/A"
    if data['actual_delivery_date'] and data['commitment_date_to_customer']:
        otd_int = "Yes" if data['actual_delivery_date'] <= data['commitment_date_to_customer'] else "NO"
        
    otd_cust = "N/A" 
    if data['actual_delivery_date'] and data['commitment_date_to_customer']:
         otd_cust = "Yes" if data['actual_delivery_date'] <= data['commitment_date_to_customer'] else "NO"

    c.execute('''
        INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        str(uuid.uuid4())[:8], 
        data['name_activity_pilot'],
        data['task_name'],
        data['date_of_receipt'],
        data['actual_delivery_date'],
        data['commitment_date_to_customer'],
        data['status'],
        data['ftr_customer'],
        data['reference_part_number'],
        data['ftr_internal'],
        otd_int,
        data['description_of_activity'],
        data['activity_type'],
        data['ftr_quality_gate_internal'],
        data['date_of_clarity_in_input'],
        data['start_date'],
        otd_cust,
        data['customer_remarks'],
        data['name_quality_gate_referent'],
        data['project_lead'],
        data['customer_manager_name']
    ))
    conn.commit()
    conn.close()

def get_all_tasks():
    conn = sqlite3.connect('kpi_data.db')
    df = pd.read_sql_query("SELECT * FROM tasks", conn)
    conn.close()
    return df

def update_task_status(task_id, new_status, new_actual_date=None):
    conn = sqlite3.connect('kpi_data.db')
    c = conn.cursor()
    
    if new_actual_date:
        c.execute("SELECT commitment_date_to_customer FROM tasks WHERE id=?", (task_id,))
        res = c.fetchone()
        comm_date_str = res[0]
        
        otd_val = "NO"
        if comm_date_str:
            try:
                comm_date = datetime.strptime(comm_date_str, '%Y-%m-%d').date()
                otd_val = "Yes" if new_actual_date <= comm_date else "NO"
            except:
                pass 

        c.execute('''UPDATE tasks SET status = ?, actual_delivery_date = ?, otd_internal = ?, otd_customer = ? WHERE id = ?''', 
                  (new_status, new_actual_date, otd_val, otd_val, task_id))
    else:
        c.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
        
    conn.commit()
    conn.close()

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
    <div class="dashboard-card">
        <div class="metric-container">
            <div>
                <div class="metric-value">{value}</div>
                <div class="metric-label">{title}</div>
                <div class="metric-trend {trend_cls}">{trend} last month</div>
            </div>
            <div class="icon-box" style="background-color: {icon_color}20; color: {icon_color};">
                {icon_char}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def project_analytics_chart():
    # Demo data generation if empty
    dates = pd.date_range(start="2024-01-01", periods=12, freq="M")
    df_chart = pd.DataFrame({
        "Date": dates,
        "Completed": [random.randint(10, 40) for _ in range(12)],
        "InProgress": [random.randint(5, 20) for _ in range(12)]
    })
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_chart['Date'], y=df_chart['Completed'], fill='tozeroy', name='Completed', line=dict(color='#82ca9d')))
    fig.add_trace(go.Scatter(x=df_chart['Date'], y=df_chart['InProgress'], fill='tozeroy', name='In Progress', line=dict(color='#8884d8')))
    
    fig.update_layout(
        title="Project Analytics",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=30, b=0),
        height=300,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def progress_donut_chart(completed_pct):
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

# --- FORM COMPONENT ---
def create_job_form():
    st.markdown("### Create New Job")
    with st.form("create_task_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        pilots = [u['name'] for k,u in USERS.items() if u['role'] == "Team Member"]

        with col1:
            task_name = st.text_input("Task Name")
            name_pilot = st.selectbox("Assign To", pilots, index=None, placeholder="Select Pilot...")
            activity_type = st.selectbox("Type", ["3d development", "2d drawing", "Release"], index=None)
            ref_part = st.text_input("Ref Part Number")
            
        with col2:
            status = st.selectbox("Initial Status", ["Hold", "Inprogress"], index=1)
            start_date = st.date_input("Start Date", value=date.today())
            date_receipt = st.date_input("Date of Receipt", value=date.today())
            date_clarity = st.date_input("Date Clarity", value=date.today())
            
        with col3:
            comm_date = st.date_input("Commitment Date", value=None)
            project_lead = st.text_input("Project Lead", value=st.session_state['name'])
            qual_ref = st.text_input("Quality Gate Ref")

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            ftr_int = st.selectbox("FTR Internal Target", ["Yes", "NO"], index=0)
            desc = st.text_area("Description")
        with c2:
            cust_manager = st.text_input("Customer Manager")
            remarks = st.text_area("Initial Remarks")

        # Hidden/Default fields
        ftr_cust = "N/A"
        ftr_gate = "N/A"
        
        submitted = st.form_submit_button("Create Job", type="primary")
        
        if submitted:
            if not task_name or not comm_date:
                st.error("Task Name and Commitment Date are required.")
            else:
                new_task = {
                    "name_activity_pilot": name_pilot,
                    "task_name": task_name,
                    "date_of_receipt": date_receipt,
                    "actual_delivery_date": None, 
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
                add_task(new_task)
                st.success("Job Created Successfully!")
                st.session_state['show_form'] = False # Close form
                st.rerun()

    if st.button("Cancel"):
        st.session_state['show_form'] = False
        st.rerun()

# --- TEAM LEADER DASHBOARD ---
def team_leader_view():
    # --- Top Bar ---
    col_title, col_btn, col_profile = st.columns([6, 1.5, 0.5])
    with col_title:
        st.title("Home")
    with col_btn:
        st.write("") # Spacer
        if st.button("✚ New Job", type="primary", use_container_width=True):
            st.session_state['show_form'] = True
    with col_profile:
        st.image("https://api.dicebear.com/7.x/avataaars/svg?seed=Felix", width=50)

    # --- CONDITIONAL FORM RENDER ---
    if st.session_state.get('show_form', False):
        st.markdown("---")
        create_job_form()
        st.markdown("---")

    df = get_all_tasks()
    
    # --- METRICS ROW ---
    c1, c2, c3, c4 = st.columns(4)
    
    total_jobs = len(df)
    in_progress = len(df[df['status'] == 'Inprogress'])
    on_hold = len(df[df['status'] == 'Hold'])
    delivered = len(df[df['status'] == 'Completed'])
    
    with c1: metric_card("Jobs Created", total_jobs, "+4.65%", "#4e73df", "💼")
    with c2: metric_card("Task InProgress", in_progress, "+2.65%", "#36b9cc", "📂")
    with c3: metric_card("Hold", on_hold, "-1.2%", "#e74a3b", "🛑")
    with c4: metric_card("Delivered", delivered, "+6.65%", "#1cc88a", "🤝")

    # --- CHARTS ROW ---
    c_left, c_right = st.columns([2, 1])
    
    with c_left:
        with st.container():
            st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
            st.plotly_chart(project_analytics_chart(), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
    with c_right:
        with st.container():
            st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
            st.markdown("##### My Progress")
            st.markdown("<p style='font-size:12px;color:grey;'>Your task completion rate</p>", unsafe_allow_html=True)
            
            completion_rate = int((delivered / total_jobs * 100)) if total_jobs > 0 else 0
            st.plotly_chart(progress_donut_chart(completion_rate), use_container_width=True)
            
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-top:10px;">
                <div style="text-align:center;"><b>{completion_rate}%</b><br><span style="color:grey">Completed</span></div>
                <div style="text-align:center;"><b>{100-completion_rate}%</b><br><span style="color:grey">Pending</span></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # --- FILTER & TABLE ROW ---
    with st.container():
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        
        # Filter Bar
        f1, f2, f3, f4 = st.columns([1,1,1,1])
        with f1: st.date_input("From", date.today() - timedelta(days=30), key="f_from")
        with f2: st.date_input("To", date.today(), key="f_to")
        with f3: st.selectbox("Select Priority", ["All", "High", "Medium", "Low"], key="f_prio")
        with f4: 
            st.write("")
            st.write("")
            st.button("Search", use_container_width=True)
        
        st.markdown("### Active Tasks")
        
        # Display Table
        if not df.empty:
            # Customizing DF for display
            display_df = df[['task_name', 'status', 'start_date', 'commitment_date_to_customer', 'name_activity_pilot']].copy()
            display_df.columns = ['Task', 'Work Status', 'Start Date', 'Deadline', 'Assigned To']
            
            # Add mock Priority for visuals (not in DB yet)
            display_df['Priority'] = [random.choice(['High', 'Medium', 'Low']) for _ in range(len(display_df))]
            
            # Reorder
            display_df = display_df[['Task', 'Priority', 'Start Date', 'Deadline', 'Work Status', 'Assigned To']]
            
            st.dataframe(
                display_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Work Status": st.column_config.TextColumn(
                        "Work Status",
                        help="Current status",
                        width="medium"
                    ),
                    "Priority": st.column_config.TextColumn(
                        "Priority",
                        width="small"
                    )
                }
            )
        else:
            st.info("No active tasks found.")
            
        st.markdown('</div>', unsafe_allow_html=True)

    # --- TEAM MEMBERS ROW ---
    c_team, c_perf = st.columns([2, 1])
    
    with c_team:
        with st.container():
            st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
            st.markdown("### Team Members")
            
            # Mock Team Data
            team_data = [
                {"name": "Alice (Lead)", "role": "UI/UX Designer", "tasks": "18/20", "perf": "+12%"},
                {"name": "Bob (Member)", "role": "Frontend Dev", "tasks": "24/30", "perf": "+8%"},
                {"name": "Charlie (Member)", "role": "Backend Dev", "tasks": "14/15", "perf": "+15%"},
            ]
            
            for member in team_data:
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; padding: 10px 0; border-bottom: 1px solid #eee;">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <div style="width:40px; height:40px; border-radius:50%; background-color:#eee; display:flex; align-items:center; justify-content:center;">👤</div>
                        <div>
                            <div style="font-weight:bold;">{member['name']}</div>
                            <div style="font-size:12px; color:grey;">{member['role']}</div>
                        </div>
                    </div>
                    <div><span style="font-weight:bold;">{member['tasks']}</span> tasks</div>
                    <div style="color:green; font-weight:bold; background-color:#e8f5e9; padding:2px 8px; border-radius:10px; font-size:12px;">{member['perf']}</div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown('</div>', unsafe_allow_html=True)

    with c_perf:
        with st.container():
            st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
            st.markdown("### FTR / OTD")
            
            # Simple Bar Chart for FTR/OTD
            x = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
            fig_bar = go.Figure(data=[
                go.Bar(name='FTR', x=x, y=[80, 50, 90, 60], marker_color='#1cc88a'),
                go.Bar(name='OTD', x=x, y=[60, 70, 80, 50], marker_color='#4e73df')
            ])
            fig_bar.update_layout(barmode='group', height=250, margin=dict(l=0, r=0, t=20, b=0), showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
            
            st.markdown('</div>', unsafe_allow_html=True)


# --- TEAM MEMBER VIEW (KANBAN - Kept Functionality) ---
def team_member_view():
    st.title(f"👷 Team Member Workspace: {st.session_state['name']}")
    
    # Filter options
    show_all = st.checkbox("Show All Team Tasks", value=False)
    
    df = get_all_tasks()
    
    if not show_all:
        df = df[df['name_activity_pilot'] == st.session_state['name']]
    
    st.markdown("### Kanban Board")
    
    # Kanban Columns
    cols = st.columns(4)
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
