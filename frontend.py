import streamlit as st
import requests
from datetime import datetime

# Config
st.set_page_config(page_title="AutoTaskr", page_icon="⏱️", layout="wide")

# CSS for modern look
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
</style>
""", unsafe_allow_html=True)

# Sidebar for new tasks
with st.sidebar:
    st.title("➕ Add New Task")
    with st.form("task_form"):
        title = st.text_input("Task Name")
        duration = st.slider("Duration (hours)", 0.5, 8.0, 1.0)
        col1, col2 = st.columns(2)
        urgency = col1.slider("Urgency (1-5)", 1, 5, 3)
        importance = col2.slider("Importance (1-5)", 1, 5, 3)
        
        if st.form_submit_button("Schedule Task"):
            response = requests.post(
                "http://localhost:5000/tasks",
                json={
                    "title": title,
                    "duration": duration,
                    "urgency": urgency,
                    "importance": importance
                }
            )
            if response.status_code == 201:
                st.success("Task added!")
            else:
                st.error("Failed to add task")

# Main dashboard
st.title("⏱️ AutoTaskr Dashboard")
st.caption("Your smart daily schedule")

# Fetch and display schedule
try:
    schedule = requests.get("http://localhost:5000/schedule").json()
    
    for task in schedule:
        # Determine task priority
        priority_class = ""
        if task.get('urgency', 0) >= 4:
            priority_class = "urgent"
        elif task.get('importance', 0) >= 4:
            priority_class = "important"
        
        # Display task card
        st.markdown(f"""
        <div class="task-card {priority_class}">
            <h3>{task['title']}</h3>
            <p>⏳ {task['duration']} hours | 
               🔥 Urgency: {task.get('urgency', '?')}/5 | 
               ⭐ Importance: {task.get('importance', '?')}/5</p>
            <p>🕒 {task['start_time']} - {task['end_time']}</p>
        </div>
        """, unsafe_allow_html=True)
        
except requests.exceptions.RequestException:
    st.error("Couldn't connect to the backend. Is Flask running?")