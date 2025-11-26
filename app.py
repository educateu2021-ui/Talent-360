import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import date, datetime

# --- CONFIGURATION & SETUP ---
st.set_page_config(page_title="KPI Management System", layout="wide", page_icon="📊")

# Custom CSS for Kanban Board
st.markdown("""
<style>
    .kanban-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        margin-bottom: 15px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .status-header {
        text-align: center;
        padding: 10px;
        background-color: #262730;
        color: white;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 24px;
    }
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
    
    # Auto Calculate OTDs
    # OTD Internal: Actual <= Commitment
    otd_int = "N/A"
    if data['actual_delivery_date'] and data['commitment_date_to_customer']:
        otd_int = "Yes" if data['actual_delivery_date'] <= data['commitment_date_to_customer'] else "NO"
        
    # OTD Customer: Similar logic (assuming same comparison for this demo)
    otd_cust = "N/A" 
    if data['actual_delivery_date'] and data['commitment_date_to_customer']:
         otd_cust = "Yes" if data['actual_delivery_date'] <= data['commitment_date_to_customer'] else "NO"

    c.execute('''
        INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        str(uuid.uuid4())[:8], # Auto ID
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
        # Recalculate OTD if date changes
        c.execute("SELECT commitment_date_to_customer FROM tasks WHERE id=?", (task_id,))
        res = c.fetchone()
        comm_date_str = res[0]
        
        otd_val = "NO"
        if comm_date_str:
            # Convert string date back to date object for comparison
            try:
                comm_date = datetime.strptime(comm_date_str, '%Y-%m-%d').date()
                otd_val = "Yes" if new_actual_date <= comm_date else "NO"
            except:
                pass # Date format error handling

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
    st.markdown("<h1 style='text-align: center;'>KPI System Login</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", use_container_width=True):
            if username in USERS and USERS[username]["password"] == password:
                st.session_state['logged_in'] = True
                st.session_state['user'] = username
                st.session_state['role'] = USERS[username]['role']
                st.session_state['name'] = USERS[username]['name']
                st.rerun()
            else:
                st.error("Invalid Username or Password")
        
        st.info("Demo Credentials:\n\nLeader: leader / 123\n\nMember: member1 / 123")

# --- TEAM LEADER VIEW ---
def team_leader_view():
    st.title(f"👨‍💼 Team Leader Dashboard: {st.session_state['name']}")
    
    tab1, tab2, tab3 = st.tabs(["Create Task", "All Tasks Data", "KPI Metrics"])
    
    # --- Tab 1: Create Task Form ---
    with tab1:
        # Clear Form Logic
        # We use a callback to reset session state variables
        def clear_form_callback():
            st.session_state["form_task_name"] = ""
            st.session_state["form_name_pilot"] = None
            st.session_state["form_activity_type"] = None
            st.session_state["form_ref_part"] = ""
            st.session_state["form_status"] = None
            st.session_state["form_start_date"] = None
            st.session_state["form_date_receipt"] = None
            st.session_state["form_date_clarity"] = None
            st.session_state["form_comm_date"] = None
            st.session_state["form_project_lead"] = st.session_state['name']
            st.session_state["form_cust_manager"] = ""
            st.session_state["form_qual_ref"] = ""
            st.session_state["form_ftr_cust"] = None
            st.session_state["form_ftr_int"] = None
            st.session_state["form_ftr_gate"] = None
            st.session_state["form_desc"] = ""
            st.session_state["form_remarks"] = ""

        st.button("Clear Form", on_click=clear_form_callback)

        with st.form("create_task_form", clear_on_submit=True):
            st.subheader("New Activity Assignment")
            col1, col2, col3 = st.columns(3)
            
            # Prepare Pilot List
            pilots = [u['name'] for k,u in USERS.items() if u['role'] == "Team Member"]

            with col1:
                # Use key=... and set value to session_state keys if they exist, or None for empty
                # Streamlit widgets like selectbox need index=None for empty state
                
                task_name = st.text_input("Task Name", key="form_task_name")
                name_pilot = st.selectbox("NAME_ACTIVITY_PILOT", pilots, index=None, placeholder="Select Pilot...", key="form_name_pilot")
                activity_type = st.selectbox("ACTIVITY_TYPE", ["3d development", "2d drawing", "Release"], index=None, placeholder="Select Type...", key="form_activity_type")
                ref_part = st.text_input("REFERENCE_PART_NUMBER", key="form_ref_part")
                
            with col2:
                status = st.selectbox("STATUS", ["Hold", "Inprogress", "Completed", "Cancelled"], index=None, placeholder="Select Status...", key="form_status")
                start_date = st.date_input("START_DATE", value=None, key="form_start_date")
                date_receipt = st.date_input("DATE_OF_RECEIPT", value=None, key="form_date_receipt")
                date_clarity = st.date_input("DATE_OF_CLARITY_IN_INPUT", value=None, key="form_date_clarity")
                
            with col3:
                comm_date = st.date_input("COMMITMENT_DATE_TO_CUSTOMER", value=None, key="form_comm_date")
                project_lead = st.text_input("PROJECT_LEAD", value=st.session_state['name'], key="form_project_lead")
                cust_manager = st.text_input("CUSTOMER_MANAGER_NAME", key="form_cust_manager")
                qual_ref = st.text_input("NAME_QUALITY_GATE_REFERENT", key="form_qual_ref")

            st.markdown("---")
            col4, col5 = st.columns(2)
            with col4:
                ftr_cust = st.selectbox("FTR_CUSTOMER", ["Yes", "NO"], index=None, placeholder="Select...", key="form_ftr_cust")
                ftr_int = st.selectbox("FTR_INTERNAL", ["Yes", "NO"], index=None, placeholder="Select...", key="form_ftr_int")
            with col5:
                ftr_gate = st.selectbox("FTR_QUALITY_GATE_INTERNAL", ["Yes", "NO"], index=None, placeholder="Select...", key="form_ftr_gate")
            
            desc = st.text_area("DESCRIPTION_OF_ACTIVITY", key="form_desc")
            remarks = st.text_area("CUSTOMER_REMARKS", key="form_remarks")
            
            submitted = st.form_submit_button("Assign Task")
            
            if submitted:
                # Validation: check if essential fields are filled
                if not task_name or not name_pilot or not comm_date:
                    st.error("Please fill in at least Task Name, Pilot, and Commitment Date.")
                else:
                    new_task = {
                        "name_activity_pilot": name_pilot,
                        "task_name": task_name,
                        "date_of_receipt": date_receipt,
                        "actual_delivery_date": None, # Initially None
                        "commitment_date_to_customer": comm_date,
                        "status": status if status else "Hold", # Default if empty
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
                    st.success("Task created successfully!")
                    st.rerun()

    # --- Tab 2: Data Table ---
    with tab2:
        df = get_all_tasks()
        st.dataframe(df, use_container_width=True)

    # --- Tab 3: Metrics ---
    with tab3:
        df = get_all_tasks()
        if not df.empty:
            st.subheader("Monthly Performance Trends")
            
            # --- Preprocessing for Graphs ---
            # Ensure dates are datetime objects
            df['actual_delivery_date'] = pd.to_datetime(df['actual_delivery_date'], errors='coerce')
            df['month_year'] = df['actual_delivery_date'].dt.strftime('%Y-%m')
            
            # Filter only completed tasks for meaningful OTD stats, or all tasks with dates
            metrics_df = df.dropna(subset=['actual_delivery_date'])
            
            if not metrics_df.empty:
                # 1. OTD Analysis Grouped by Month
                monthly_groups = metrics_df.groupby('month_year')
                
                otd_stats = []
                ftr_stats = []
                
                for month, group in monthly_groups:
                    # OTD Calc
                    total_in_month = len(group)
                    otd_yes = len(group[group['otd_internal'] == 'Yes'])
                    otd_percentage = (otd_yes / total_in_month) * 100 if total_in_month > 0 else 0
                    otd_stats.append({'Month': month, 'OTD %': otd_percentage})
                    
                    # FTR Calc (Using all tasks in that month, assuming FTR is marked upon completion/delivery)
                    ftr_yes = len(group[group['ftr_internal'] == 'Yes'])
                    ftr_percentage = (ftr_yes / total_in_month) * 100 if total_in_month > 0 else 0
                    ftr_stats.append({'Month': month, 'FTR %': ftr_percentage})

                otd_df = pd.DataFrame(otd_stats).sort_values('Month')
                ftr_df = pd.DataFrame(ftr_stats).sort_values('Month')
                
                c1, c2 = st.columns(2)
                
                with c1:
                    st.markdown("### 📈 OTD % (Internal)")
                    if not otd_df.empty:
                        st.line_chart(otd_df, x='Month', y='OTD %')
                    else:
                        st.info("No sufficient data for OTD graph.")

                with c2:
                    st.markdown("### ✅ FTR % (Internal)")
                    if not ftr_df.empty:
                        st.line_chart(ftr_df, x='Month', y='FTR %')
                    else:
                        st.info("No sufficient data for FTR graph.")
            
            else:
                st.info("No delivered tasks yet to generate Monthly trends.")

            st.markdown("---")
            st.markdown("### 📊 Task Status Distribution")
            
            # Status Counts
            status_counts = df['status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            
            st.bar_chart(status_counts, x='Status', y='Count', use_container_width=True)

            # High Level Metrics Cards (Existing)
            st.markdown("---")
            c1, c2, c3, c4 = st.columns(4)
            total = len(df)
            completed = len(df[df['status'] == 'Completed'])
            
            # Overall OTD/FTR
            completed_tasks = df[df['status'] == 'Completed']
            otd_count = len(completed_tasks[completed_tasks['otd_internal'] == 'Yes'])
            otd_pct = round((otd_count / len(completed_tasks) * 100), 2) if len(completed_tasks) > 0 else 0
            
            ftr_count = len(df[df['ftr_internal'] == 'Yes'])
            ftr_pct = round((ftr_count / total * 100), 2) if total > 0 else 0

            c1.metric("Total Tasks", total)
            c2.metric("Completed", completed)
            c3.metric("Overall OTD %", f"{otd_pct}%")
            c4.metric("Overall FTR %", f"{ftr_pct}%")
        else:
            st.info("No data available yet.")

# --- TEAM MEMBER VIEW (KANBAN) ---
def team_member_view():
    st.title(f"👷 Team Member Workspace: {st.session_state['name']}")
    
    # Filter options
    show_all = st.checkbox("Show All Team Tasks", value=False)
    
    df = get_all_tasks()
    
    if not show_all:
        # Simple name matching
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
                            
                            # Only show Date Picker if completing
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
            st.write(f"Logged in as: **{st.session_state['user']}**")
            st.write(f"Role: **{st.session_state['role']}**")
            if st.button("Logout"):
                st.session_state['logged_in'] = False
                st.rerun()
        
        # Route based on role
        if st.session_state['role'] == "Team Leader":
            team_leader_view()
        else:
            team_member_view()

if __name__ == "__main__":
    main()
