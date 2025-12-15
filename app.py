import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import date, datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# ---------------- CONFIG ----------------
st.set_page_config("KPI Management System", layout="wide", page_icon="📊")
DB_FILE = "kpi_data.db"

# ---------------- CSS ----------------
st.markdown("""
<style>
.stApp { background:#f6f7fb; }
.card { background:#fff; padding:14px; border-radius:10px;
        border:1px solid #eef2f6; margin-bottom:12px; }
.metric { display:flex; justify-content:space-between; }
.label { font-size:13px; color:#6b7280; font-weight:600; }
.value { font-size:22px; font-weight:700; }
.badge { padding:5px 10px; border-radius:12px; font-size:12px; font-weight:700; }
.badge-completed { background:#d1fae5; color:#065f46; }
.badge-inprogress { background:#dbeafe; color:#1e40af; }
.badge-hold { background:#fee2e2; color:#991b1b; }
</style>
""", unsafe_allow_html=True)

# ---------------- DB ----------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        task_name TEXT,
        owner TEXT,
        status TEXT,
        start_date TEXT,
        commitment_date TEXT,
        actual_date TEXT,
        otd TEXT
    )
    """)
    conn.commit()
    conn.close()

def otd_calc(actual, commit):
    if not actual or not commit:
        return "N/A"
    return "OK" if actual <= commit else "NOT OK"

def save_task(data, task_id=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    otd = otd_calc(data["actual_date"], data["commitment_date"])

    if task_id:
        c.execute("""
        UPDATE tasks SET task_name=?, owner=?, status=?, start_date=?,
        commitment_date=?, actual_date=?, otd=? WHERE id=?
        """, (*data.values(), otd, task_id))
    else:
        c.execute("""
        INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?)
        """, (str(uuid.uuid4())[:8], *data.values(), otd))

    conn.commit()
    conn.close()

def load_tasks():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM tasks", conn)
    conn.close()
    return df

# ---------------- AUTH ----------------
USERS = {
    "leader": {"pwd":"123","role":"Leader","name":"Alice"},
    "member": {"pwd":"123","role":"Member","name":"Bob"}
}

def login():
    st.markdown("## Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in USERS and USERS[u]["pwd"] == p:
            st.session_state.clear()
            st.session_state.update({
                "logged":True,
                "user":u,
                "role":USERS[u]["role"],
                "name":USERS[u]["name"],
                "edit_id":None
            })
            st.rerun()
        else:
            st.error("Invalid credentials")

# ---------------- UI ----------------
def metric(label, val):
    st.markdown(f"""
    <div class="card metric">
      <div>
        <div class="label">{label}</div>
        <div class="value">{val}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

def task_form(task=None):
    with st.form("task_form"):
        name = st.text_input("Task Name", task.get("task_name","") if task else "")
        owner = st.text_input("Owner", task.get("owner","") if task else "")
        status = st.selectbox("Status", ["Inprogress","Hold","Completed"],
                              index=["Inprogress","Hold","Completed"].index(task["status"]) if task else 0)
        start = st.date_input("Start Date", date.today())
        commit = st.date_input("Commitment Date", date.today()+timedelta(days=7))
        actual = st.date_input("Actual Date", date.today())
        otd = otd_calc(actual, commit)
        st.info(f"OTD: **{otd}**")

        if st.form_submit_button("Save"):
            save_task({
                "task_name":name,
                "owner":owner,
                "status":status,
                "start_date":str(start),
                "commitment_date":str(commit),
                "actual_date":str(actual)
            }, st.session_state.get("edit_id"))
            st.session_state["edit_id"] = None
            st.rerun()

# ---------------- DASHBOARD ----------------
def leader_view():
    df = load_tasks()

    st.markdown("<div class='card'><h2>Dashboard</h2></div>", unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    c1.markdown(metric("Total Tasks", len(df)), unsafe_allow_html=True)
    c2.markdown(metric("In Progress", len(df[df.status=="Inprogress"])), unsafe_allow_html=True)
    c3.markdown(metric("Completed", len(df[df.status=="Completed"])), unsafe_allow_html=True)

    left,right = st.columns([2,1])

    with left:
        st.markdown("<div class='card'><h4>Tasks</h4></div>", unsafe_allow_html=True)

        for _,r in df.iterrows():
            cols = st.columns([3,2,1,1])
            cols[0].markdown(f"**{r.task_name}**")
            cols[1].write(r.owner)
            badge = "badge-completed" if r.status=="Completed" else "badge-inprogress"
            cols[2].markdown(f"<span class='badge {badge}'>{r.status}</span>", unsafe_allow_html=True)

            if cols[3].button("Edit", key=r.id):
                st.session_state["edit_id"] = r.id
                st.rerun()

            if st.session_state.get("edit_id") == r.id:
                with st.expander("Edit Task", expanded=True):
                    task_form(r)

    with right:
        st.markdown("<div class='card'><h4>Create Task</h4></div>", unsafe_allow_html=True)
        if st.session_state.get("edit_id") is None:
            task_form()

def member_view():
    st.markdown("## My Tasks")
    df = load_tasks()
    df = df[df.owner == st.session_state["name"]]
    st.dataframe(df)

# ---------------- MAIN ----------------
def main():
    init_db()

    if not st.session_state.get("logged"):
        login()
        return

    with st.sidebar:
        st.write(st.session_state["name"])
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

    if st.session_state["role"] == "Leader":
        leader_view()
    else:
        member_view()

main()
