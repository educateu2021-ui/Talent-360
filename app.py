# streamlit_kpi_clean.py
import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import date, datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# ---------- CONFIG ----------
st.set_page_config(page_title="KPI Management System", layout="wide", page_icon="📊")

# ---------- LIGHT CSS (keep it minimal to avoid many nested visual boxes) ----------
st.markdown(
    """
    <style>
    .stApp { background-color: #f6f7fb; }
    .main .block-container { padding-top: 1rem; padding-bottom: 1.2rem; }
    /* Make primary blocks look like cards but avoid over-targeting */
    .card {
        background: #ffffff;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(12,18,28,0.04);
        border: 1px solid #eef2f6;
        padding: 14px;
        margin-bottom: 12px;
    }
    .metric { display:flex; justify-content:space-between; align-items:center; padding:10px; border-radius:8px; }
    .metric .label { color:#6b7280; font-size:13px; font-weight:600; text-transform:uppercase; }
    .metric .value { font-size:22px; font-weight:700; color:#111827; }
    .task-header { font-weight:700; color:#6b7280; font-size:13px; text-transform:uppercase; margin-bottom:10px; }
    .badge { padding:6px 10px; border-radius:12px; font-weight:700; font-size:12px; }
    .badge-completed { background:#d1fae5; color:#065f46; }
    .badge-inprogress { background:#dbeafe; color:#1e40af; }
    .badge-hold { background:#fee2e2; color:#991b1b; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- DB helpers ----------
DB_FILE = "kpi_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks_v2 (
            id TEXT PRIMARY KEY,
            name_activity_pilot TEXT,
            task_name TEXT,
            date_of_receipt TEXT,
            actual_delivery_date TEXT,
            commitment_date_to_customer TEXT,
            status TEXT,
            ftr_customer TEXT,
            reference_part_number TEXT,
            ftr_internal TEXT,
            otd_internal TEXT,
            description_of_activity TEXT,
            activity_type TEXT,
            ftr_quality_gate_internal TEXT,
            date_of_clarity_in_input TEXT,
            start_date TEXT,
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
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # compute OTD safe
    otd_val = "N/A"
    try:
        if data.get("actual_delivery_date") and data.get("commitment_date_to_customer"):
            a = pd.to_datetime(str(data["actual_delivery_date"]), dayfirst=True, errors='coerce')
            cm = pd.to_datetime(str(data["commitment_date_to_customer"]), dayfirst=True, errors='coerce')
            if not pd.isna(a) and not pd.isna(cm):
                otd_val = "OK" if a <= cm else "NOT OK"
    except:
        otd_val = "N/A"

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
            data.get('ftr_internal'), otd_val, data.get('description_of_activity'), data.get('activity_type'),
            data.get('ftr_quality_gate_internal'), str(data.get('date_of_clarity_in_input')), str(data.get('start_date')), otd_val,
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
            data.get('ftr_internal'), otd_val, data.get('description_of_activity'), data.get('activity_type'),
            data.get('ftr_quality_gate_internal'), str(data.get('date_of_clarity_in_input')), str(data.get('start_date')), otd_val,
            data.get('customer_remarks'), data.get('name_quality_gate_referent'), data.get('project_lead'), data.get('customer_manager_name')
        ))
    conn.commit()
    conn.close()

def get_all_tasks():
    conn = sqlite3.connect(DB_FILE)
    try:
        df = pd.read_sql_query("SELECT * FROM tasks_v2", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

def update_task_status(task_id, new_status, new_actual_date=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT commitment_date_to_customer FROM tasks_v2 WHERE id=?", (task_id,))
    res = c.fetchone()
    comm_date_str = res[0] if res else None

    otd_val = "N/A"
    try:
        if comm_date_str and new_actual_date:
            comm_d = pd.to_datetime(str(comm_date_str), dayfirst=True, errors='coerce')
            actual_d = pd.to_datetime(str(new_actual_date), dayfirst=True, errors='coerce')
            if not pd.isna(comm_d) and not pd.isna(actual_d):
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
        # ensure columns exist
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
        st.error(f"Import error: {e}")
        return False

# ---------- AUTH ----------
USERS = {
    "leader": {"password": "123", "role": "Team Leader", "name": "Alice (Lead)"},
    "member1": {"password": "123", "role": "Team Member", "name": "Bob (Member)"},
    "member2": {"password": "123", "role": "Team Member", "name": "Charlie (Member)"}
}

def init_session_defaults():
    # safe defaults used every time someone logs in
    st.session_state.setdefault('show_form', False)
    st.session_state.setdefault('edit_mode', False)
    st.session_state.setdefault('edit_task_id', None)
    st.session_state.setdefault('edit_default', None)

def login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col = st.columns([1, 1.2, 1])[1]
    with col:
        st.markdown("<h2 style='text-align:center;color:#111827;'>KPI System Login</h2>", unsafe_allow_html=True)
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Sign in", type="primary", use_container_width=True):
            if username in USERS and USERS[username]["password"] == password:
                st.session_state['logged_in'] = True
                st.session_state['user'] = username
                st.session_state['role'] = USERS[username]['role']
                st.session_state['name'] = USERS[username]['name']
                init_session_defaults()
                # rerun to show dashboard
                st.experimental_rerun()
            else:
                st.error("Invalid credentials. Demo: leader/123, member1/123")

# ---------- UI helpers (charts, metric) ----------
def metric_html(label, value):
    return f"""
    <div class="card">
        <div class="metric">
            <div>
                <div class="label">{label}</div>
                <div class="value">{value}</div>
            </div>
        </div>
    </div>
    """

def get_analytics_chart(df):
    if df.empty:
        return go.Figure()
    df_local = df.copy()
    df_local['start_date'] = pd.to_datetime(df_local['start_date'], dayfirst=True, errors='coerce')
    df_local = df_local.dropna(subset=['start_date'])
    df_local['month'] = df_local['start_date'].dt.strftime('%b')
    monthly = df_local.groupby(['month', 'status']).size().reset_index(name='count')
    fig = px.bar(monthly, x='month', y='count', color='status', barmode='group',
                 color_discrete_map={"Completed":"#10b981","Inprogress":"#3b82f6","Hold":"#ef4444","Cancelled":"#9ca3af"})
    fig.update_layout(margin=dict(l=0,r=0,t=30,b=0), height=330, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return fig

def get_donut(df):
    total = 0
    completed_pct = 0
    if not df.empty:
        total = len(df)
        completed = len(df[df['status']=='Completed'])
        completed_pct = int((completed/total)*100) if total>0 else 0
    fig = go.Figure(data=[go.Pie(labels=['Completed','Pending'], values=[completed_pct, 100-completed_pct], hole=.7, textinfo='none')])
    fig.update_layout(height=240, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      annotations=[dict(text=f"{completed_pct}%", x=0.5, y=0.5, showarrow=False, font=dict(size=20))])
    return fig

def get_ftr_otd_chart(df):
    if df.empty:
        return go.Figure()
    df_local = df.copy()
    df_local['actual_delivery_date'] = pd.to_datetime(df_local['actual_delivery_date'], dayfirst=True, errors='coerce')
    df_local = df_local.dropna(subset=['actual_delivery_date'])
    if df_local.empty:
        fig = go.Figure()
        fig.update_layout(title="No Completed Tasks", height=300)
        return fig
    df_local['month'] = df_local['actual_delivery_date'].dt.strftime('%b')
    monthly_stats = df_local.groupby('month').agg({
        'otd_internal': lambda x: ((x=='OK') | (x=='Yes')).mean()*100,
        'ftr_internal': lambda x: (x=='Yes').mean()*100
    }).reset_index()
    fig = go.Figure()
    fig.add_bar(x=monthly_stats['month'], y=monthly_stats['ftr_internal'], name='FTR %')
    fig.add_bar(x=monthly_stats['month'], y=monthly_stats['otd_internal'], name='OTD %')
    fig.update_layout(barmode='group', height=300, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return fig

# ---------- Form (create/edit) ----------
def parse_date_like(d):
    if d is None:
        return None
    if isinstance(d, date):
        return d
    if isinstance(d, str) and d.strip() != '':
        # try ISO first then dayfirst
        try:
            return datetime.strptime(d.split(" ")[0], "%Y-%m-%d").date()
        except:
            try:
                return pd.to_datetime(d, dayfirst=True, errors='coerce').date()
            except:
                return None
    return None

def task_form(mode="create", task_id=None, default_data=None, key_prefix="form"):
    # default_data must contain only serializable simple values (strings/dates/None)
    if default_data is None:
        default_data = {}
    title = "Create Task" if mode=="create" else "Edit Task"
    st.markdown(f"#### {title}")

    # safe parse helper
    def safe_val(k, fallback=""):
        v = default_data.get(k)
        if v is None: return fallback
        return v

    with st.form(key=f"{key_prefix}_{task_id or 'new'}"):
        col1, col2, col3 = st.columns(3)
        # pilots list
        pilots = [u['name'] for k,u in USERS.items() if u['role']=="Team Member"]
        with col1:
            task_name = st.text_input("Task Name", value=safe_val("task_name",""))
            pilot_index = pilots.index(safe_val("name_activity_pilot")) if safe_val("name_activity_pilot") in pilots else 0
            name_pilot = st.selectbox("Assign To", pilots, index=pilot_index)
            activity_type = st.selectbox("Activity Type", ["3d development","2d drawing","Release"], index=0)
            ref_part = st.text_input("Ref Part Number", value=safe_val("reference_part_number",""))
        with col2:
            statuses = ["Hold","Inprogress","Completed","Cancelled"]
            status_index = statuses.index(safe_val("status")) if safe_val("status") in statuses else 1
            status = st.selectbox("Status", statuses, index=status_index)
            start_date = st.date_input("Start Date", value=parse_date_like(safe_val("start_date")) or date.today())
            date_receipt = st.date_input("Date of Receipt", value=parse_date_like(safe_val("date_of_receipt")) or date.today())
            date_clarity = st.date_input("Date Clarity", value=parse_date_like(safe_val("date_of_clarity_in_input")) or date.today())
        with col3:
            comm_date = st.date_input("Commitment Date", value=parse_date_like(safe_val("commitment_date_to_customer")) or (date.today()+timedelta(days=7)))
            actual_date = st.date_input("Actual Delivery", value=parse_date_like(safe_val("actual_delivery_date")) or date.today())
            project_lead = st.text_input("Project Lead", value=safe_val("project_lead", st.session_state.get('name','')))
            qual_ref = st.text_input("Quality Gate Ref", value=safe_val("name_quality_gate_referent",""))

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            ftr_internal = st.selectbox("FTR Internal", options=["Yes","NO"], index=0)
            description = st.text_area("Description", value=safe_val("description_of_activity",""))
        with c2:
            customer_manager = st.text_input("Customer Manager", value=safe_val("customer_manager_name",""))
            remarks = st.text_area("Remarks", value=safe_val("customer_remarks",""))

        # compute OTD display
        otd_display = "N/A"
        try:
            if comm_date and actual_date:
                otd_display = "OK" if actual_date <= comm_date else "NOT OK"
        except:
            otd_display = "N/A"
        st.markdown(f"**OTD:** {otd_display}")

        submitted = st.form_submit_button("Save", type="primary")
        if submitted:
            if not task_name or not comm_date:
                st.error("Task Name and Commitment Date required.")
            else:
                payload = {
                    "name_activity_pilot": name_pilot,
                    "task_name": task_name,
                    "date_of_receipt": str(date_receipt),
                    "actual_delivery_date": str(actual_date),
                    "commitment_date_to_customer": str(comm_date),
                    "status": status,
                    "ftr_customer": "N/A",
                    "reference_part_number": ref_part,
                    "ftr_internal": ftr_internal,
                    "description_of_activity": description,
                    "activity_type": activity_type,
                    "ftr_quality_gate_internal": "N/A",
                    "date_of_clarity_in_input": str(date_clarity),
                    "start_date": str(start_date),
                    "customer_remarks": remarks,
                    "name_quality_gate_referent": qual_ref,
                    "project_lead": project_lead,
                    "customer_manager_name": customer_manager
                }
                add_task(payload, task_id=task_id)
                st.success("Saved.")
                # reset edit flags
                st.session_state['show_form'] = False
                st.session_state['edit_mode'] = False
                st.session_state['edit_task_id'] = None
                st.session_state['edit_default'] = None
                # reflect changes immediately
                st.experimental_rerun()

# ---------- VIEWS ----------
def team_leader_view():
    df = get_all_tasks()
    # top row: title + actions
    left, right = st.columns([3,1])
    with left:
        st.markdown("<div class='card'><h2 style='margin:0'>Dashboard</h2></div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        uploaded = st.file_uploader("Import CSV", type=['csv'], key="imp_uploader")
        if uploaded:
            ok = import_data_from_csv(uploaded)
            if ok:
                st.success("Imported CSV.")
                st.experimental_rerun()
        st.download_button("Export CSV", data=(df.to_csv(index=False).encode('utf-8') if not df.empty else ""), file_name="kpi_tasks.csv", mime="text/csv")
        if st.button("➕ New Task"):
            st.session_state['show_form'] = True
            st.session_state['edit_mode'] = False
        st.markdown("</div>", unsafe_allow_html=True)

    # show create form (simple card) if requested
    if st.session_state.get('show_form', False) and not st.session_state.get('edit_mode', False):
        with st.container():
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            task_form(mode="create", key_prefix="create")
            st.markdown("</div>", unsafe_allow_html=True)

    # metrics row
    st.write("")  # spacer
    m1, m2, m3, m4 = st.columns(4)
    total = len(df) if not df.empty else 0
    inprogress = len(df[df['status']=='Inprogress']) if not df.empty else 0
    hold = len(df[df['status']=='Hold']) if not df.empty else 0
    done = len(df[df['status']=='Completed']) if not df.empty else 0
    m1.markdown(metric_html("Jobs Created", total), unsafe_allow_html=True)
    m2.markdown(metric_html("In Progress", inprogress), unsafe_allow_html=True)
    m3.markdown(metric_html("On Hold", hold), unsafe_allow_html=True)
    m4.markdown(metric_html("Delivered", done), unsafe_allow_html=True)

    # analytics / donut
    chart_col, donut_col = st.columns([2,1])
    with chart_col:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        if not df.empty:
            st.plotly_chart(get_analytics_chart(df), use_container_width=True)
        else:
            st.info("No data to show.")
        st.markdown("</div>", unsafe_allow_html=True)
    with donut_col:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### My Progress")
        if not df.empty:
            st.plotly_chart(get_donut(df), use_container_width=True)
        else:
            st.info("No data.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Filter and Task list
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='task-header'>Active Tasks</div>", unsafe_allow_html=True)
    # simple date filter
    colf1, colf2, colf3 = st.columns([2,2,1])
    with colf1:
        d_from = st.date_input("From", value=date.today()-timedelta(days=90), key="filter_from")
    with colf2:
        d_to = st.date_input("To", value=date.today()+timedelta(days=30), key="filter_to")
    with colf3:
        prio = st.selectbox("Priority", ["All","High","Medium","Low"], index=0)
    st.write("")  # small gap

    df_display = df.copy() if not df.empty else pd.DataFrame()
    if not df_display.empty and 'start_date' in df_display.columns:
        df_display['start_date'] = pd.to_datetime(df_display['start_date'], dayfirst=True, errors='coerce').dt.date
        df_display = df_display[(df_display['start_date'] >= d_from) & (df_display['start_date'] <= d_to)]

    if df_display.empty:
        st.info("No tasks in this date range.")
    else:
        # Render each row simply (no nested containers), with an expander for edit inline
        for _, row in df_display.iterrows():
            # row bar
            cols = st.columns([3,2,2,1.2,1])
            with cols[0]:
                st.markdown(f"**{row.get('task_name','-')}**")
                st.caption(row.get('description_of_activity',''))
            with cols[1]:
                st.markdown(f"<small style='color:gray'>{row.get('name_activity_pilot','-')}</small>", unsafe_allow_html=True)
            with cols[2]:
                st.markdown(f"Due: {row.get('commitment_date_to_customer','-')}")
            with cols[3]:
                st.markdown(f"<span class='badge {'badge-completed' if row.get('status')=='Completed' else 'badge-inprogress' if row.get('status')=='Inprogress' else 'badge-hold'}'>{row.get('status','-')}</span>", unsafe_allow_html=True)
            with cols[4]:
                if st.button("Edit", key=f"edit_{row['id']}"):
                    # store safe defaults (convert Timestamps -> ISO strings)
                    safe = {}
                    for k, v in row.to_dict().items():
                        if pd.isna(v):
                            safe[k] = None
                        else:
                            safe[k] = str(v)
                    st.session_state['show_form'] = True
                    st.session_state['edit_mode'] = True
                    st.session_state['edit_task_id'] = row['id']
                    st.session_state['edit_default'] = safe
                    # do not call rerun here (Streamlit widget action triggers rerun)

            # if this row is being edited show an expander directly below it (no extra containers)
            if st.session_state.get('edit_mode') and st.session_state.get('edit_task_id') == row['id']:
                with st.expander("Edit Task", expanded=True):
                    # default data stored are strings (ISO-like). task_form will parse them.
                    task_form(mode="edit", task_id=row['id'], default_data=st.session_state.get('edit_default', {}), key_prefix=f"edit_{row['id']}")

            st.markdown("---")

    st.markdown("</div>", unsafe_allow_html=True)

    # bottom: team members + performance chart
    lower_left, lower_right = st.columns([1.5,1])
    with lower_left:
        st.markdown("<div class='card'><h4 style='margin:6px 0'>Team Members</h4>", unsafe_allow_html=True)
        if not df.empty:
            members = df['name_activity_pilot'].fillna('Unassigned').unique()
            for m in members:
                m_tasks = df[df['name_activity_pilot']==m]
                cnt = len(m_tasks)
                comp = len(m_tasks[m_tasks['status']=='Completed'])
                pct = int((comp/cnt)*100) if cnt>0 else 0
                st.markdown(f"**{m}** — {cnt} tasks • {pct}% perf")
        else:
            st.write("No members yet.")
        st.markdown("</div>", unsafe_allow_html=True)
    with lower_right:
        st.markdown("<div class='card'><h4 style='margin:6px 0'>Performance</h4>", unsafe_allow_html=True)
        if not df.empty:
            st.plotly_chart(get_ftr_otd_chart(df), use_container_width=True)
        else:
            st.info("No performance data")
        st.markdown("</div>", unsafe_allow_html=True)

def team_member_view():
    st.markdown("<div class='card'><h3 style='margin:0'>My Tasks</h3></div>", unsafe_allow_html=True)
    df = get_all_tasks()
    name = st.session_state.get('name','')
    my_tasks = df[df['name_activity_pilot']==name] if not df.empty else pd.DataFrame()
    if my_tasks.empty:
        st.info("You have no tasks assigned.")
        return
    # simple columns for statuses
    statuses = ["Hold","Inprogress","Completed","Cancelled"]
    cols = st.columns(4)
    for i, s in enumerate(statuses):
        with cols[i]:
            st.markdown(f"**{s}**")
            subset = my_tasks[my_tasks['status']==s]
            for _, r in subset.iterrows():
                st.markdown(f"**{r['task_name']}**")
                st.caption(f"Due: {r.get('commitment_date_to_customer','-')}")
                with st.expander("Update"):
                    with st.form(key=f"m_{r['id']}"):
                        new_status = st.selectbox("Status", statuses, index=statuses.index(s))
                        actual_date = st.date_input("Actual Delivery", value=date.today())
                        if st.form_submit_button("Save"):
                            update_task_status(r['id'], new_status, actual_date)
                            st.success("Updated.")
                            st.experimental_rerun()

# ---------- MAIN ----------
def main():
    init_db()
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        login_page()
        return

    # Sidebar - show user + logout
    with st.sidebar:
        st.image("https://api.dicebear.com/7.x/avataaars/svg?seed=Felix", width=80)
        st.markdown(f"**{st.session_state.get('name','')}**")
        st.markdown(f"Role: {st.session_state.get('role','')}")
        st.markdown("---")
        if st.button("Logout"):
            # clear keys that can break later
            keys_to_remove = ['logged_in','user','role','name','show_form','edit_mode','edit_task_id','edit_default']
            for k in keys_to_remove:
                if k in st.session_state:
                    del st.session_state[k]
            # safe full rerun so login page appears
            st.experimental_rerun()

    # route based on role
    role = st.session_state.get('role','')
    if role == "Team Leader":
        team_leader_view()
    else:
        team_member_view()

if __name__ == "__main__":
    main()
