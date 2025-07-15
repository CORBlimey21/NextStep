import streamlit as st
import datetime
import json
import os
from collections import defaultdict
import pandas as pd

# --- Configuration ---
SUBJECTS_FILE = "subjects.json"
LOG_FILE = "log.json"

# --- Initial Setup ---
st.set_page_config(page_title="NextStep Study Tracker", page_icon="📚", layout="wide")

# --- Data Loading & Saving ---

def load_data(filepath, default_data):
    """Loads data from a JSON file, returning default data if not found or invalid."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            # Convert date strings back to datetime.date objects for subjects
            if filepath == SUBJECTS_FILE:
                 for subject in data:
                    if data[subject].get("exam_date"):
                        data[subject]["exam_date"] = datetime.datetime.strptime(data[subject]["exam_date"], "%Y-%m-%d").date()
            return data
        except (json.JSONDecodeError, TypeError) as e:
            st.error(f"⚠️ Error reading {filepath}: {e}. Using default data.")
            return default_data
    return default_data

def save_data(filepath, data):
    """Saves data to a JSON file."""
    with open(filepath, "w") as f:
        # Custom JSON encoder to handle datetime objects
        def json_default(o):
            if isinstance(o, (datetime.date, datetime.datetime)):
                return o.isoformat()
        json.dump(data, f, indent=4, default=json_default)


# --- Initialize Session State ---
if 'subjects' not in st.session_state:
    default_subjects = {
        "Science": {"confidence": 5, "exam_date": datetime.date.today() + datetime.timedelta(days=30)},
        "Irish": {"confidence": 5, "exam_date": datetime.date.today() + datetime.timedelta(days=30)},
        "Maths": {"confidence": 5, "exam_date": datetime.date.today() + datetime.timedelta(days=30)},
        "English": {"confidence": 5, "exam_date": datetime.date.today() + datetime.timedelta(days=30)},
    }
    st.session_state.subjects = load_data(SUBJECTS_FILE, default_subjects)

if 'session_log' not in st.session_state:
    st.session_state.session_log = load_data(LOG_FILE, [])


# --- Helper Functions ---
def calculate_streak(dates_set):
    if not dates_set:
        return 0
    today = datetime.date.today()
    streak = 0
    # Check consecutive days from today backwards
    while (today - datetime.timedelta(days=streak)) in dates_set:
        streak += 1
    return streak

def get_days_since_last_session(subject):
    relevant_sessions = [
        datetime.datetime.fromisoformat(entry["timestamp"])
        for entry in st.session_state.session_log
        if entry["subject"] == subject
    ]
    if not relevant_sessions:
        return None
    last_session = max(relevant_sessions)
    return (datetime.datetime.now() - last_session).days


# --- Sidebar Navigation ---
st.sidebar.title("NextStep Menu")
page = st.sidebar.radio("Go to", ["Dashboard", "Instant Mode", "Log a Session", "View Sessions", "Settings"])


# --- Page: Dashboard ---
if page == "Dashboard":
    st.title("📈 Study Dashboard")
    st.write("A summary of your study progress.")

    log = st.session_state.session_log
    subjects = st.session_state.subjects

    if not log:
        st.info("📭 No sessions logged yet. Go to 'Log a Session' to get started!")
    else:
        # --- Key Metrics ---
        total_sessions = len(log)
        total_time = sum(entry["duration_mins"] for entry in log)
        dates_studied = set(datetime.datetime.fromisoformat(entry["timestamp"]).date() for entry in log)
        study_streak = calculate_streak(dates_studied)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Sessions", f"{total_sessions} 📚")
        col2.metric("Total Time Studied", f"{total_time} mins ⏱️")
        col3.metric("Study Streak", f"{study_streak} days 🔥")

        st.divider()

        # --- Subject Summary ---
        st.subheader("Subject Breakdown")
        subject_stats = defaultdict(lambda: {"count": 0, "total_time": 0, "total_rating": 0})
        for entry in log:
            subj = entry["subject"]
            subject_stats[subj]["count"] += 1
            subject_stats[subj]["total_time"] += entry["duration_mins"]
            subject_stats[subj]["total_rating"] += entry.get("effectiveness", 0)

        summary_data = []
        for subj, stats in subject_stats.items():
            avg_rating = (stats["total_rating"] / stats["count"]) if stats["count"] > 0 else 0
            summary_data.append({
                "Subject": subj,
                "Sessions": stats['count'],
                "Total Time (mins)": stats['total_time'],
                "Avg. Effectiveness": f"{avg_rating:.1f} ⭐"
            })

        st.table(pd.DataFrame(summary_data).set_index("Subject"))

    # --- Subject Info & Confidence ---
    st.divider()
    st.subheader("Subject Confidence & Deadlines")
    if not subjects:
        st.warning("No subjects configured. Go to 'Settings' to add them.")
    else:
        today = datetime.date.today()
        for subj, data in subjects.items():
            col1, col2, col3 = st.columns([2, 3, 2])
            with col1:
                st.write(f"**{subj}**")
            with col2:
                conf = data.get('confidence', 0)
                st.progress(conf / 10, text=f"Confidence: {conf}/10")
            with col3:
                exam_date = data.get('exam_date')
                if exam_date:
                    days_left = (exam_date - today).days
                    if days_left < 0:
                        st.error(f"Exam was {abs(days_left)} days ago!")
                    else:
                        st.info(f"{days_left} days until exam")
                else:
                    st.write("No exam date set")


# --- Page: Instant Mode ---
elif page == "Instant Mode":
    st.title("🎯 Instant Mode")
    st.write("Get a quick suggestion for what to study right now.")

    subjects = st.session_state.subjects
    if not all(data.get("exam_date") and data.get("confidence") for data in subjects.values()):
        st.warning("⚠️ Please go to 'Settings' to enter your exam dates and confidence levels for all subjects to use Instant Mode.")
    else:
        with st.form("instant_mode_form"):
            mins = st.number_input("How many minutes do you have?", min_value=5, max_value=240, value=30, step=5)
            energy = st.select_slider("Energy level?", options=["low", "medium", "high"], value="medium")
            submitted = st.form_submit_button("Suggest a Subject!")

        if submitted:
            today = datetime.date.today()
            subject_priorities = []
            for subj, data in subjects.items():
                days_left = (data["exam_date"] - today).days
                urgency = 1 / max(days_left, 0.1)
                
                stored_conf = data["confidence"]
                days_since = get_days_since_last_session(subj)

                decay = min(days_since // 7, 3) if days_since is not None else 0
                adjusted_conf = max(1, stored_conf - decay)
                difficulty = 11 - adjusted_conf
                
                recent_count = sum(1 for entry in st.session_state.session_log if entry["subject"] == subj and datetime.datetime.fromisoformat(entry["timestamp"]) >= datetime.datetime.now() - datetime.timedelta(days=7))
                repetition_penalty = recent_count * 0.5
                
                priority_score = (urgency * 1.5) + difficulty - repetition_penalty
                subject_priorities.append((subj, priority_score))

            subject_priorities.sort(key=lambda x: x[1], reverse=True)
            chosen_subject = subject_priorities[0][0]

            st.session_state.instant_suggestion = chosen_subject
            st.session_state.instant_mins = mins
            st.session_state.instant_energy = energy

    if 'instant_suggestion' in st.session_state:
        chosen_subject = st.session_state.instant_suggestion
        mins = st.session_state.instant_mins
        energy = st.session_state.instant_energy

        st.success(f"🎯 **Suggestion:** Revise **{chosen_subject}**!")

        if energy == "low":
            task_type = "Flashcards or Light Revision"
        elif energy == "medium":
            task_type = "Practice Questions or Diagrams"
        else:
            task_type = "Essays or Full Past Paper Sections"

        st.info(f"🧠 **Suggested Task:** {task_type}")
        st.info(f"⏱️ **Time Available:** {mins} mins")

        with st.form("log_instant_session"):
            st.write("---")
            st.write(f"**Log your {chosen_subject} session:**")
            effectiveness = st.slider("How effective was the session?", 1, 10, 5)
            new_conf = st.slider(f"Update your confidence for {chosen_subject}?", 1, 10, st.session_state.subjects[chosen_subject]['confidence'])
            completed = st.form_submit_button("Log Session")

            if completed:
                st.session_state.session_log.append({
                    "subject": chosen_subject,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "task_type": task_type,
                    "duration_mins": mins,
                    "effectiveness": effectiveness,
                })
                st.session_state.subjects[chosen_subject]["confidence"] = new_conf
                save_data(LOG_FILE, st.session_state.session_log)
                save_data(SUBJECTS_FILE, st.session_state.subjects)
                st.success("📒 Session logged successfully!")
                del st.session_state.instant_suggestion # Clear suggestion after logging


# --- Page: Log a Session ---
elif page == "Log a Session":
    st.title("✍️ Manually Log a Study Session")

    subjects = st.session_state.subjects
    if not subjects:
        st.warning("Please add subjects in the 'Settings' page first.")
    else:
        with st.form("log_session_form"):
            subject = st.selectbox("Which subject did you study?", options=list(subjects.keys()))
            duration = st.number_input("How many minutes did you study?", min_value=1, value=30)
            task_type = st.text_input("What kind of task was it?", placeholder="e.g., Flashcards, Essay, Practice Questions")
            effectiveness = st.slider("How effective was it?", 1, 10, 5)
            
            st.write("---")
            update_confidence = st.checkbox(f"Update confidence for {subject}?")
            new_confidence = None
            if update_confidence:
                new_confidence = st.slider("New Confidence Level", 1, 10, value=subjects[subject].get('confidence', 5))

            submitted = st.form_submit_button("Log Session")

            if submitted:
                st.session_state.session_log.append({
                    "subject": subject,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "task_type": task_type,
                    "duration_mins": duration,
                    "effectiveness": effectiveness,
                })
                if update_confidence and new_confidence is not None:
                    st.session_state.subjects[subject]["confidence"] = new_confidence
                
                save_data(LOG_FILE, st.session_state.session_log)
                save_data(SUBJECTS_FILE, st.session_state.subjects)
                st.success("📒 Session logged successfully!")


# --- Page: View Sessions ---
elif page == "View Sessions":
    st.title("📚 View Past Sessions")

    if not st.session_state.session_log:
        st.info("📭 No sessions logged yet.")
    else:
        # --- Filters ---
        col1, col2 = st.columns(2)
        with col1:
            all_subjects = ["All"] + list(st.session_state.subjects.keys())
            filter_subject = st.selectbox("Filter by subject", options=all_subjects)
        with col2:
            filter_days = st.number_input("Show sessions from the last X days (0 for all)", min_value=0, value=0)

        # --- Filtering Logic ---
        filtered_log = st.session_state.session_log
        if filter_subject != "All":
            filtered_log = [s for s in filtered_log if s.get("subject") == filter_subject]
        
        if filter_days > 0:
            cutoff = datetime.datetime.now() - datetime.timedelta(days=filter_days)
            filtered_log = [s for s in filtered_log if datetime.datetime.fromisoformat(s["timestamp"]) >= cutoff]

        if not filtered_log:
            st.warning("🔍 No sessions match your filters.")
        else:
            # Display sessions in reverse chronological order
            for entry in sorted(filtered_log, key=lambda x: x['timestamp'], reverse=True):
                time_obj = datetime.datetime.fromisoformat(entry["timestamp"])
                time_str = time_obj.strftime("%Y-%m-%d %H:%M")
                with st.expander(f"**{entry['subject']}** - {time_str}"):
                    st.markdown(f"**- Duration:** {entry['duration_mins']} mins")
                    st.markdown(f"**- Task:** {entry.get('task_type', 'N/A')}")
                    st.markdown(f"**- Effectiveness:** {entry.get('effectiveness', 'N/A')} ⭐")


# --- Page: Settings ---
elif page == "Settings":
    st.title("⚙️ Settings")
    st.subheader("Manage Your Subjects")

    subjects = st.session_state.subjects
    
    for subject, data in list(subjects.items()): # Use list to allow modification during iteration
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Editing: {subject}**")
            with col2:
                if st.button(f"Delete {subject}", key=f"del_{subject}", type="primary"):
                    del st.session_state.subjects[subject]
                    save_data(SUBJECTS_FILE, st.session_state.subjects)
                    st.rerun()

            new_conf = st.slider(f"Confidence for {subject}", 1, 10, data.get('confidence', 5), key=f"conf_{subject}")
            
            # Ensure exam_date is a datetime.date object
            current_exam_date = data.get('exam_date')
            if isinstance(current_exam_date, str):
                try:
                    current_exam_date = datetime.datetime.strptime(current_exam_date, "%Y-%m-%d").date()
                except ValueError:
                    current_exam_date = datetime.date.today()
            elif current_exam_date is None:
                 current_exam_date = datetime.date.today()


            new_date = st.date_input(f"Exam Date for {subject}", value=current_exam_date, key=f"date_{subject}")
            
            st.session_state.subjects[subject]['confidence'] = new_conf
            st.session_state.subjects[subject]['exam_date'] = new_date

    if st.button("Save Changes"):
        save_data(SUBJECTS_FILE, st.session_state.subjects)
        st.success("💾 Subject data saved!")

    st.divider()

    st.subheader("Add a New Subject")
    with st.form("new_subject_form"):
        new_subject_name = st.text_input("New Subject Name")
        add_button = st.form_submit_button("Add Subject")

        if add_button and new_subject_name:
            if new_subject_name in st.session_state.subjects:
                st.error("This subject already exists.")
            else:
                st.session_state.subjects[new_subject_name] = {
                    "confidence": 5,
                    "exam_date": datetime.date.today() + datetime.timedelta(days=30)
                }
                save_data(SUBJECTS_FILE, st.session_state.subjects)
                st.success(f"Added '{new_subject_name}'! You can now edit its details above.")
                st.rerun()