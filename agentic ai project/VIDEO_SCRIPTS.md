# Explanatory Video Walkthrough Scripts (30 to 45 Seconds Each)
**Course:** AGENTIC AI ENGINEERING  
**Project:** Apex Intelligent Student Support Agent (Assignments 1 & 2)  
**Model:** Groq Llama 3.3 70B + Code-Level Security Layer  

---

## 🎬 Tips for Recording within 30–45 Seconds
- **Pacing:** Speak at an energetic, clear, professional pace (~120–135 words total).
- **Setup:** Open your browser with `streamlit run app.py` at `http://localhost:8501`, and split-screen or keep VS Code open in background.
- **Pre-load:** Have the quick-click buttons ready on screen so you don't waste seconds typing.

---

# 📹 Video 1: Assignment 1 – Intelligent Student Support Agent
**Target Duration:** ~40–45 Seconds  
**Word Count:** ~105 words  
**Core Topics:** Architecture & Groq agent loop, Tools, Selective RAG policy retrieval, Persistent Memory & Ephemeral filter, Tracing & Telemetry (Latency, Tokens, Accuracy).

| Timestamp | Visual on Screen (What to Show) | Spoken Audio Voiceover (What to Say) |
| :--- | :--- | :--- |
| **0:00 – 0:08** *(8s)* | Show Streamlit UI Chat Tab. Click button: *"What is my current fee status?"* | *"Hello! This is my Agentic AI Student Support Agent built with Groq's Llama 3.3 70B. Here, our autonomous agent loop analyzes the student query and calls the `get_fee_status` tool to retrieve live financial balances."* |
| **0:09 – 0:18** *(10s)* | Click button: *"Payment portal failed. Can I pay next working day?"* | *"For policy queries, instead of sending the entire handbook, our selective retriever extracts only relevant policy chunks—like chunk POL-FEE-02 for portal downtime grace periods."* |
| **0:19 – 0:28** *(10s)* | Click sidebar Memory Inspector, then click button: *"What facts do you remember about me?"* | *"The agent maintains cross-session persistent memory for career tracks while actively filtering out temporary feelings and greetings."* |
| **0:29 – 0:42** *(13s)* | Switch to **📊 Tracing & Telemetry** Tab. Hover over metrics & table. | *"In the Tracing tab, every run logs latency, input-output token counts, retrieved evidence, and tool appropriateness. In our benchmark, the agent achieves 100% task accuracy with sub-second response times!"* |

---

# 📹 Video 2: Assignment 2 – Safe & Production-Aware Agent
**Target Duration:** ~40–45 Seconds  
**Word Count:** ~110 words  
**Core Topics:** Student Identity, Code-level Python Authorization, Privacy attack blocked, Sensitive action Human-in-the-Loop (HITL) approval, Rejection safety, Sensitive credential filter, Audit Trail.

| Timestamp | Visual on Screen (What to Show) | Spoken Audio Voiceover (What to Say) |
| :--- | :--- | :--- |
| **0:00 – 0:09** *(9s)* | Show Sidebar Student Switcher (`S101 Rohan Sharma`). Click button: *"Check fee status of student S102 Priya"* | *"Welcome to Assignment 2! Here we hardened the agent for institutional production. Notice I am signed in as Student S101. When I attempt to access Student S102's private data, the system strictly blocks it."* |
| **0:10 – 0:19** *(10s)* | Flash [`security/authorization.py`](file:///security/authorization.py) code snippet on screen for 2-3 seconds, then back to UI. | *"Crucially, this privacy guard is enforced in Python tool code, not just prompt instructions, preventing prompt injection attacks."* |
| **0:20 – 0:31** *(12s)* | Click button: *"I want to change my course BDA504 to AI602"*. Show the interactive **Approve / Reject** card. Click **Reject**. | *"For sensitive actions like elective course changes, the agent enters a Human-in-the-Loop approval state. If the faculty advisor clicks 'Reject', the action is aborted and no records are modified."* |
| **0:32 – 0:44** *(12s)* | Switch to **🛡️ Audit Trail & Privacy** Tab. Scroll through the rows. | *"Passwords and OTPs are also blocked from memory. Finally, every action, authorization decision, and approval status is indelibly logged to our institutional audit trail for full compliance!"* |
