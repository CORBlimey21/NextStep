NextStep: Smart Study Companion

# 📚 NextStep

NextStep is a smart, personalised study planner built for Junior & Leaving Cert students — designed to reduce decision fatigue, boost revision efficiency, and make studying feel less like a guessing game.

## 🚀 What It Does

- ⏱️ **Instant Mode** – Suggests the best subject + study task (flashcards, past papers, etc.) based on:
  - Your confidence levels
  - How soon your exam is
  - Your current energy
  - How often you’ve studied it recently

- 📒 **Session Logging** – Records what you studied, how long, and how effective it felt.

- 🔁 **Repetition-Aware** – Avoids over-recommending subjects you’ve studied recently.

- 🔥 **Study Streaks** – Tracks how many days in a row you’ve studied.

- 📊 **CLI Dashboard** – View total time, subject stats, and effectiveness ratings.

## 🛠 How to Use

1. **Run the app** (in terminal):
   ```bash
   python3 NextStep_Core_V2.py
2.	Follow the setup prompts to enter your exam dates and confidence levels.
3.	Choose Instant Mode when you want to study — just enter your time and energy, and it’ll tell you what’s next.
4.	After each session, rate its effectiveness and optionally update your confidence.

Or simply visit https://nextsteps.streamlit.app

 📁 File Structure
 .
├── .gitignore
├── LICENSE
├── NextStep_Core_V2.py
├── subjects.json          # saved subject state
├── log.json               # saved study sessions
└── README.md

Built By

Cillian Ó Ríordáin – student.
