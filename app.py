import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import date, datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# ---------- CONFIG ----------
st.set_page_config(page_title="Corporate Portal", layout="wide", page_icon="🏢")

# ---------- GLOBAL SEARCH ----------
if "global_search" not in st.session_state:
    st.session_state["global_search"] = ""

st.session_state["global_search"] = st.text_input(
    "🔍 Global Search (Tasks / Employees / IDs)",
    st.session_state["global_search"],
    placeholder="Type here to search across current module"
)

st.markdown("---")

# ---------- STYLES ----------
st.markdown("""
<style>
.stApp { background-color: #f8f9fa; }
.profile-img { width:120px;height:120px;border-radius:50%;margin:auto;display:block; }
</style>
""", unsafe_allow_html=True)

# ---------- DATABASE ----------
DB_FILE = "portal_data_final_v15_demo.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS tasks_v2 (
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
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS resource_tracker_v2 (
        id TEXT PRIMARY KEY,
        employee_name TEXT,
        employee_id TEXT,
        dev_code TEXT,
        department TEXT,
        location TEXT,
        reporting_manager TEXT,
        onboarding_date TEXT,
        experience_level TEXT,
        status TEXT,
        po_details TEXT,
        remarks TEXT,
        effective_exit_date TEXT,
        backfill_status TEXT,
        reason_for_leaving TEXT
    )""")

    # ---------- KPI DEMO DATA (20 TASKS) ----------
    c.execute("SELECT COUNT(*) FROM tasks_v2")
    if c.fetchone()[0] == 0:
        statuses = ["Completed", "Inprogress", "Hold", "Cancelled"]
        demo = []
        for i in range(1, 21):
            status = statuses[i % 4]
            commit = date.today() + timedelta(days=5)
            actual = commit - timedelta(days=1) if i % 3 != 0 else commit + timedelta(days=2)
            otd = "OK" if actual <= commit else "NOT OK"

            demo.append((
                str(uuid.uuid4())[:8],
                "David Chen" if i % 2 == 0 else "Emily Davis",
                f"KPI Task {i}",
                str(date.today()),
                str(actual),
                str(commit),
                status,
                "Yes",
                f"PN-{1000+i}",
                "Yes",
                otd,
                f"Demo KPI task {i}",
                "Standard",
                "Yes",
                str(date.today()),
                str(date.today()),
                otd,
                "",
                "QA Lead",
                "Sarah Jenkins",
                "Client Manager"
            ))

        c.executemany("INSERT INTO tasks_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", demo)

    conn.commit()
    conn.close()

# ---------- HELPERS ----------
def get_kpi_data():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM tasks_v2", conn)
    conn.close()
    return df

def get_resource_list():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM resource_tracker_v2", conn)
    conn.close()
    return df

# ---------- AUTH ----------
USERS = {
    "leader": {"password": "123", "role": "Team Leader", "name": "Sarah Jenkins"},
    "member": {"password": "123", "role": "Team Member", "name": "David Chen"}
}

# ---------- LOGIN ----------
def login():
    st.title("Portal Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in USERS and USERS[u]["password"] == p:
            st.session_state["logged_in"] = True
            st.session_state["user"] = USERS[u]
            st.session_state["app"] = "HOME"
            st.rerun()
        else:
            st.error("Invalid login")

# ---------- HOME ----------
def home():
    st.subheader(f"Welcome {st.session_state['user']['name']}")
    c1, c2 = st.columns(2)
    if c1.button("📊 KPI Tracker"):
        st.session_state["app"] = "KPI"
        st.rerun()
    if c2.button("🚀 Resource Tracker"):
        st.session_state["app"] = "RESOURCE"
        st.rerun()

# ---------- KPI ----------
def app_kpi():
    st.subheader("📊 KPI Tracker")
    df = get_kpi_data()

    if st.session_state["global_search"]:
        q = st.session_state["global_search"].lower()
        df = df[df["task_name"].str.lower().str.contains(q)]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total", len(df))
    m2.metric("Completed", len(df[df.status=="Completed"]))
    m3.metric("Inprogress", len(df[df.status=="Inprogress"]))
    m4.metric("Hold", len(df[df.status=="Hold"]))

    fig = px.bar(df, x="status", color="otd_internal", title="OTD Status Overview")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df, use_container_width=True)

    if st.button("⬅ Back"):
        st.session_state["app"] = "HOME"
        st.rerun()

# ---------- RESOURCE ----------
def app_resource():
    st.subheader("🚀 Resource Tracker")

    df = get_resource_list()

    with st.expander("📂 Filters"):
        c1, c2, c3 = st.columns(3)
        dep = c1.multiselect("Department", df.department.unique())
        stat = c2.multiselect("Status", df.status.unique())
        loc = c3.multiselect("Location", df.location.unique())

        if dep: df = df[df.department.isin(dep)]
        if stat: df = df[df.status.isin(stat)]
        if loc: df = df[df.location.isin(loc)]

    if st.session_state["global_search"]:
        q = st.session_state["global_search"].lower()
        df = df[df.employee_name.str.lower().str.contains(q)]

    st.dataframe(df, use_container_width=True)

    if st.button("⬅ Back"):
        st.session_state["app"] = "HOME"
        st.rerun()

# ---------- MAIN ----------
def main():
    init_db()

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login()
    else:
        if st.session_state["app"] == "HOME":
            home()
        elif st.session_state["app"] == "KPI":
            app_kpi()
        elif st.session_state["app"] == "RESOURCE":
            app_resource()

if __name__ == "__main__":
    main()
