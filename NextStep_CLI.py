import datetime
import json
import os

# This dictionary is used if no save file is found.
default_subjects = {
    "Science": {"confidence": None, "exam_date": None},
    "Irish": {"confidence": None, "exam_date": None},
    "Maths": {"confidence": None, "exam_date": None},
    "English": {"confidence": None, "exam_date": None},
}

global session_logs
session_log = []

def calculate_streak(dates_set):
    if not dates_set:
        return 0

    today = datetime.date.today()
    streak = 0

    for i in range(100):  # Look back up to 100 days
        day = today - datetime.timedelta(days=i)
        if day in dates_set:
            streak += 1
        else:
            break

    return streak

from collections import defaultdict

def view_summary():
    if not session_log:
        print("📭 No sessions logged yet.")
        return

    print("\n📈 Study Summary\n")

    total_sessions = len(session_log)
    total_time = sum(entry["duration_mins"] for entry in session_log)

    print(f"Total Sessions: {total_sessions}")
    print(f"Total Time Studied: {total_time} mins\n")

    subject_stats = defaultdict(lambda: {"count": 0, "total_time": 0, "total_rating": 0})

    dates_studied = set()

    for entry in session_log:
        subj = entry["subject"]
        subject_stats[subj]["count"] += 1
        subject_stats[subj]["total_time"] += entry["duration_mins"]
        subject_stats[subj]["total_rating"] += entry.get("effectiveness", 0)

        # Track date for streaks
        dt = datetime.datetime.fromisoformat(entry["timestamp"])
        dates_studied.add(dt.date())

    for subj, stats in subject_stats.items():
        avg_rating = stats["total_rating"] / stats["count"]
        print(f"{subj} — {stats['count']} sessions | {stats['total_time']} mins | Avg effectiveness: {avg_rating:.1f}")

    print(f"\n🔥 Study Streak: {calculate_streak(dates_studied)} day(s) in a row")


# === SAVE & LOAD ===
def save_subjects(subjects_data, filename="subjects.json"):
    """Saves the subjects dictionary to a JSON file."""
    with open(filename, "w") as f:
        # default=str handles datetime objects
        json.dump(subjects_data, f, indent=4, default=str)
    print("💾 Subject data saved.")

def load_subjects(fallback_subjects, filename="subjects.json"):
    """Loads subjects from a JSON file, or returns the fallback if not found."""
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                data = json.load(f)
            # Convert date strings back to datetime.date objects
            for subject in data:
                # Check if exam_date exists and is not None before converting
                if data[subject].get("exam_date"):
                    data[subject]["exam_date"] = datetime.datetime.strptime(data[subject]["exam_date"], "%Y-%m-%d").date()
            print("📂 Loaded saved subject data.\n")
            return data
        except (json.JSONDecodeError, TypeError) as e:
            print(f"⚠️ Error reading file: {e}. Using default subjects.")
            return fallback_subjects
    else:
        print("🆕 No saved subject data found. Using default subjects.\n")
        return fallback_subjects
    
def save_log(filename="log.json"):
    with open(filename, "w") as f:
        json.dump(session_log, f, default=str)

def load_log(filename="log.json"):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)
        # Optional: parse timestamps if you want datetime later
        return data
    else:
        return []
    
from datetime import timedelta  # add to your existing imports

def recent_session_count(subject, days=7):
    """
    Return how many times `subject` appears in `session_log`
    within the last `days` days.
    """
    cutoff = datetime.datetime.now() - timedelta(days=days)
    return sum(
        1
        for entry in session_log
        if entry["subject"] == subject and datetime.datetime.fromisoformat(entry["timestamp"]) >= cutoff
    )

def get_days_since_last_session(subject):
    relevant_sessions = [
        datetime.datetime.fromisoformat(entry["timestamp"])
        for entry in session_log
        if entry["subject"] == subject
    ]
    if not relevant_sessions:
        return None  # No sessions yet
    last_session = max(relevant_sessions)
    return (datetime.datetime.now() - last_session).days

def manual_log_session(subjects):
    print("\n=== MANUAL SESSION LOGGING ===")

    subject = None
    while subject not in subjects:
        print("Subjects:", ", ".join(subjects.keys()))
        subject = input("Which subject did you study? ").strip().title()
        if subject not in subjects:
            print("❌ Invalid subject. Please try again.")

    while True:
        try:
            mins = int(input("How many minutes did you study? "))
            break
        except ValueError:
            print("Invalid input. Please enter a number.")

    task_type = input("What kind of task was it? (e.g. Flashcards, Essay): ")

    while True:
        try:
            effectiveness = int(input("How effective was it? (1–10): "))
            if 1 <= effectiveness <= 10:
                break
            else:
                print("Please enter a number from 1 to 10.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    new_conf = input("🎯 Update your confidence in this subject? (1–10 or leave blank): ").strip()
    if new_conf:
        try:
            conf_val = int(new_conf)
            if 1 <= conf_val <= 10:
                subjects[subject]["confidence"] = conf_val
                print("✅ Confidence updated.")
            else:
                print("❌ Invalid confidence value, ignored.")
        except ValueError:
            print("❌ Invalid confidence value, ignored.")

    session_log.append({
        "subject": subject,
        "timestamp": str(datetime.datetime.now()),
        "task_type": task_type,
        "duration_mins": mins,
        "effectiveness": effectiveness,
    })

    print("📒 Session logged.")

def view_sessions():
    print("\n📚 View Past Sessions")

    if not session_log:
        print("📭 No sessions logged yet.")
        return

    filter_subject = input("🔍 Filter by subject? (leave blank to show all): ").strip().title()
    filter_days = input("📅 Show only sessions from the last X days? (leave blank for all): ").strip()

    filtered = session_log
    if filter_subject:
        filtered = [s for s in filtered if s["subject"] == filter_subject]

    if filter_days:
        try:
            days = int(filter_days)
            cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
            filtered = [s for s in filtered if datetime.datetime.fromisoformat(s["timestamp"]) >= cutoff]
        except ValueError:
            print("⚠️ Invalid number of days. Showing all instead.")

    if not filtered:
        print("🔍 No sessions match your filters.")
        return

    for i, entry in enumerate(filtered, 1):
        time_obj = datetime.datetime.fromisoformat(entry["timestamp"])
        time_str = time_obj.strftime("%Y-%m-%d %H:%M")
        print(f"\nSession {i}:")
        print(f"📅 Date: {time_str}")
        print(f"📘 Subject: {entry['subject']}")
        print(f"⏱️ Duration: {entry['duration_mins']} mins")
        print(f"📌 Task: {entry['task_type']}")
        print(f"⭐ Effectiveness: {entry['effectiveness']}")

# === SETUP ===
def setup_subjects(subjects):
    """Guides the user through setting up their subjects."""
    print("Let's set up your subjects:\n")
    for subject in subjects:
        while True:
            try:
                conf_input = input(f"Rate your confidence in {subject} (1–10): ")
                conf = int(conf_input)
                if 1 <= conf <= 10:
                    subjects[subject]["confidence"] = conf
                    break
                else:
                    print("Please enter a number between 1 and 10.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        while True:
            try:
                date_str = input(f"When is your {subject} exam? (DD/MM/YYYY): ")
                exam_date = datetime.datetime.strptime(date_str, "%d/%m/%Y").date()
                subjects[subject]["exam_date"] = exam_date
                break
            except ValueError:
                print("Invalid date format. Please use DD/MM/YYYY.")
    print("\n✅ Setup complete.")
    save_subjects()
    print("\n💾 Subject data saved.")
    return subjects




# === INSTANT MODE ===
def instant_mode(subjects):
    """Suggests a subject to study based on urgency and confidence."""
    print("\n=== INSTANT MODE ===")
    
    # Check if subjects have been configured
    if not all(data.get("exam_date") and data.get("confidence") for data in subjects.values()):
        print("⚠️ Please run 'Set up subjects' (option 1) first to enter your exam dates and confidence levels.")
        return

    while True:
        try:
            mins_input = input("How many minutes do you have? ")
            mins = int(mins_input)
            break
        except ValueError:
            print("Invalid input. Please enter a number.")

    energy = ""
    while energy not in ["low", "medium", "high"]:
        energy = input("Energy level? (low / medium / high): ").strip().lower()
        if energy not in ["low", "medium", "high"]:
            print("Invalid input. Please choose 'low', 'medium', or 'high'.")

    today = datetime.date.today()


    # Calculate priority for each subject
    subject_priorities = []
    for subj, data in subjects.items():
        days_left = (data["exam_date"] - today).days
        urgency    = 1 / max(days_left, 0.1)                  # higher if exam soon
        stored_conf = data["confidence"]
        days_since = get_days_since_last_session(subj)

        # Apply decay: -1 confidence for every 7 days (up to -3)
        if days_since is not None:
            decay = min(days_since // 7, 3)
            adjusted_conf = max(1, stored_conf - decay)
        else:
            adjusted_conf = stored_conf  # no decay if never studied

        difficulty = 11 - adjusted_conf                # higher if confidence low
        recent     = recent_session_count(subj, days=7)       # studies in last week
        repetition_penalty = recent * 0.5                     # tweak this weight later

        priority_score = (urgency * 1.5) + difficulty - repetition_penalty
        subject_priorities.append((subj, priority_score))

    # Sort subjects by the calculated priority score in descending order
    subject_priorities.sort(key=lambda x: x[1], reverse=True)

    # Offer subjects in priority order
    chosen_subject = None
    for subj, score in subject_priorities:
        response = input(f"Do you want to revise {subj}? (yes/no): ").strip().lower()
        if response == "yes":
            chosen_subject = subj
            break

    # Fallback to the highest priority subject if they said no to everything
    if not chosen_subject:
        chosen_subject = subject_priorities[0][0]
        print(f"You said no to all options. Defaulting to the highest priority: {chosen_subject}")

    print(f"\n🎯 You'll be revising: {chosen_subject}")

    # Pick task type based on energy
    if energy == "low":
        task_type = "Flashcards or Light Revision"
    elif energy == "medium":
        task_type = "Practice Questions or Diagrams"
    else: # high
        task_type = "Essays or Full Past Paper Sections"

    print(f"🧠 Suggested Task: {task_type}")
    print(f"⏱️ Time Available: {mins} mins")

    completed = input("✅ Did you complete the session? (yes/no): ").strip().lower()

    if completed == "yes":
        rating = input("⭐ How effective was it? (1–10): ")
        new_conf = input("🎯 Want to update your confidence for this subject? (1–10 or leave blank): ")

        if new_conf.strip():
            subjects[chosen_subject]["confidence"] = int(new_conf)
            print("✅ Confidence updated.")

        # Log the session
        session_log.append({
            "subject": chosen_subject,
            "timestamp": str(datetime.datetime.now()),
            "task_type": task_type,
            "duration_mins": mins,
            "effectiveness": int(rating),
        })

        print("📒 Session logged.")
    else:
        print("📝 Session not logged.")



# === MAIN LOOP ===
def main():
    """Main function to run the CLI application."""
    # FIX: Pass the 'default_subjects' dictionary to the load function.
    global session_log
    subjects = load_subjects(default_subjects)
    session_log = load_log()

    
    while True:
        print("\n=== NEXTSTEP CLI ===")
        print("1. Set up subjects")
        print("2. Run instant mode")
        print("3. View subject info")
        print("4. View study summary")
        print("5. Manually log a session")
        print("6. View past sessions")
        print("7. Exit")

        choice = input("Pick an option: ").strip()

        if choice == "1":
            subjects = setup_subjects(subjects)
        elif choice == "2":
            instant_mode(subjects)
        elif choice == "3":
            print("\n--- Subject Information ---")
            for subj, data in subjects.items():
                conf = data.get('confidence', 'Not set')
                date_val = data.get('exam_date', 'Not set')
                print(f"{subj:<10} | Confidence: {conf:<10} | Exam Date: {date_val}")
            print("---------------------------")
        elif choice == "4":
            view_summary()
        elif choice == "5":
            manual_log_session(subjects)
        elif choice == "6":
            view_sessions()
        elif choice == "7":
            save_subjects(subjects)
            save_log()
            print("Exiting. Goodbye!")
            break
        else:
            print("Invalid choice. Please pick a number from 1 to 7.")

# This ensures the script runs when executed directly.
if __name__ == "__main__":
    main()