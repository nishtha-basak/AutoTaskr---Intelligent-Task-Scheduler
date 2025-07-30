# frontend.py (Smart UI for Start/Complete/Status tabs)
import streamlit as st
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="AutoTaskr", page_icon="\u23f1\ufe0f", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.markdown("""
<style>
.task-card {
    border-radius: 10px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    transition: transform 0.2s;
}
.task-card:hover {
    transform: translateY(-2px);
}
.urgent {
    border-left: 5px solid #ff4b4b;
}
.important {
    border-left: 5px solid #ffa700;
}
.overdue {
    background-color: rgba(255, 0, 0, 0.1);
    border-left: 5px solid #dc3545;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("\u2795 Add New Task")
    with st.form("task_form"):
        title = st.text_input("Task Name")
        duration = st.number_input("Duration (in hours)", min_value=0.25, max_value=12.0, value=1.0, step=0.25)
        col1, col2 = st.columns(2)
        urgency = col1.slider("Urgency (1-5)", 1, 5, 3)
        importance = col2.slider("Importance (1-5)", 1, 5, 3)

        if st.form_submit_button("Schedule Task"):
            response = requests.post("http://localhost:5000/tasks", json={
                "title": title,
                "duration": duration,
                "urgency": urgency,
                "importance": importance
            })
            if response.status_code == 201:
                st.success("Task added!")
            else:
                st.error("Failed to add task")

if st.button("\u267b\ufe0f Force Replan"):
    res = requests.post("http://localhost:5000/replan")
    if res.status_code == 200:
        st.success("Replan triggered!")

st.title("\u23f1\ufe0f AutoTaskr Dashboard")
st.caption("Your smart daily schedule")

try:
    schedule = requests.get("http://localhost:5000/schedule").json()
    now = datetime.now()

    tabs = st.tabs(["Upcoming", "In Progress", "Done", "Missed"])
    status_map = {
        "pending": tabs[0],
        "in_progress": tabs[1],
        "done": tabs[2],
        "missed": tabs[3]
    }

    for task in schedule:
        status = task.get("status", "pending")
        start = task.get("start_actual")
        end = task.get("end_actual")
        overdue = False
        if end:
            end_time = datetime.fromisoformat(end)
            overdue = datetime.now() > end_time

        priority_class = ""
        if task.get('urgency', 0) >= 4:
            priority_class = "urgent"
        elif task.get('importance', 0) >= 4:
            priority_class = "important"

        with status_map[status]:
            col1, col2 = st.columns([6, 1])
            with col1:
                st.markdown(f"""
                <div class="task-card {priority_class} {'overdue' if overdue and status=='in_progress' else ''}">
                    <h3>{task['title']}</h3>
                    <p>⏳ {task['duration']} hr | 🔥 {task['urgency']}/5 | ⭐ {task['importance']}/5</p>
                    <p>🟢 Status: {status.upper()}</p>
                    {f"<p>🕒 {datetime.fromisoformat(start).strftime('%I:%M %p')} - {datetime.fromisoformat(end).strftime('%I:%M %p')}</p>" if start and end else ""}
                </div>
                """, unsafe_allow_html=True)

            with col2:
                if status == "pending":
                    if st.button("▶️ Start", key=f"start_{task['id']}"):
                        requests.patch(f"http://localhost:5000/schedule/{task['id']}/start")
                        st.rerun()
                elif status == "in_progress":
                    if st.button("✅ Done", key=f"done_{task['id']}"):
                        res = requests.patch(f"http://localhost:5000/schedule/{task['id']}/complete")
                        if res.status_code == 200:
                            st.success("Marked done")
                        else:
                            st.error("Too late to complete!")
                        st.rerun()
                elif status == "done":
                    st.success("✔️ Done")
                elif status == "missed":
                    st.error("⚠️ Missed")

except Exception as e:
    st.error(f"Backend error: {e}")