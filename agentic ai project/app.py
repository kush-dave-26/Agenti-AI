"""
app.py
------
Streamlit Web Application: Intelligent Student Support Agent
Apex Institute of Management & Technology
PGDM (Big Data Analytics / AI & Data Science) | Batch 2025-27

Supports:
- Assignment 1: Agent loop, tools, persistent memory, policy retrieval, tracing & measurement
- Assignment 2: Student identity, code-level authorization, privacy guards, human approval, audit trail
- Powered by Groq API (Llama 3.3 70B Versatile) with resilient fallback
"""

import os
import json
import time
import pandas as pd
import streamlit as st
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load local environment
load_dotenv()

# Internal agent and security modules
from agent.core_agent import StudentSupportAgent, DEFAULT_GROQ_MODEL
from agent.tracing import trace_registry, ExecutionTrace
from agent.memory_manager import student_memory_mgr
from agent.policy_retriever import policy_kb
from security.approval_manager import get_pending_approvals, resolve_approval, get_approval_by_id
from security.audit_logger import get_all_audit_logs

# Page configuration
st.set_page_config(
    page_title="Apex Student Support Agent",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State variables
if "authenticated_student_id" not in st.session_state:
    st.session_state.authenticated_student_id = "S101"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = f"sess_{int(time.time())}"
if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = os.getenv("GROQ_API_KEY", "")
if "agent_model" not in st.session_state:
    st.session_state.agent_model = DEFAULT_GROQ_MODEL

# Student profiles database
STUDENTS = {
    "S101": {
        "id": "S101",
        "name": "Rohan Sharma",
        "programme": "PGDM (Big Data Analytics)",
        "advisor": "Dr. Arvind Swaminathan"
    },
    "S102": {
        "id": "S102",
        "name": "Priya Patel",
        "programme": "PGDM (Artificial Intelligence & Data Science)",
        "advisor": "Prof. Meera Sen"
    },
    "S103": {
        "id": "S103",
        "name": "Ananya Iyer",
        "programme": "PGDM (Big Data Analytics)",
        "advisor": "Dr. K. R. Raman"
    }
}

# Instantiate agent
agent = StudentSupportAgent(
    groq_api_key=st.session_state.groq_api_key,
    model_name=st.session_state.agent_model
)


# ==========================================
# SIDEBAR CONTROLS
# ==========================================
with st.sidebar:
    st.markdown("### 🎓 Apex Student Portal")
    st.markdown("**PGDM Batch 2025-27**")
    st.divider()

    # 1. Student Identity Switcher (Assignment 2 Requirement)
    st.markdown("#### 👤 Student Identity")
    student_options = list(STUDENTS.keys())
    selected_student_idx = student_options.index(st.session_state.authenticated_student_id)
    selected_student = st.selectbox(
        "Current Signed-in Student:",
        options=student_options,
        index=selected_student_idx,
        format_func=lambda sid: f"{sid} - {STUDENTS[sid]['name']} ({STUDENTS[sid]['programme'].split('(')[-1].replace(')', '')})"
    )

    if selected_student != st.session_state.authenticated_student_id:
        st.session_state.authenticated_student_id = selected_student
        st.session_state.messages = []
        st.session_state.session_id = f"sess_{int(time.time())}"
        st.rerun()

    current_student = STUDENTS[st.session_state.authenticated_student_id]
    st.caption(f"**Advisor:** {current_student['advisor']}")

    st.divider()

    # 2. Groq API Configuration
    st.markdown("#### ⚡ Groq API Settings")
    input_key = st.text_input(
        "Groq API Key:",
        value=st.session_state.groq_api_key,
        type="password",
        placeholder="gsk_...",
        help="Enter your Groq API key to power real-time tool calling and Llama 3 inference."
    )
    if input_key != st.session_state.groq_api_key:
        st.session_state.groq_api_key = input_key
        agent.update_credentials(input_key, st.session_state.agent_model)
        st.success("API Key updated!")

    selected_model = st.selectbox(
        "Groq Model:",
        options=[
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768"
        ],
        index=0
    )
    if selected_model != st.session_state.agent_model:
        st.session_state.agent_model = selected_model
        agent.update_credentials(st.session_state.groq_api_key, selected_model)

    if st.session_state.groq_api_key:
        st.success("🟢 Groq API Connected", icon="✅")
    else:
        st.info("ℹ️ Live API key optional; resilient offline agent engine active.", icon="💡")

    st.divider()

    # 3. Persistent Memory Inspector
    st.markdown("#### 🧠 Persistent Memory Inspector")
    st.caption("Cross-session persistent facts stored for the signed-in student:")
    mem_data = student_memory_mgr.get_student_memory(st.session_state.authenticated_student_id)
    persistent_facts = mem_data.get("persistent_facts", {})
    if persistent_facts:
        for k, v in persistent_facts.items():
            st.markdown(f"- **{k.replace('_', ' ').title()}:** {v}")
    else:
        st.markdown("*No long-term facts stored yet.*")

    with st.expander("🛡️ View Filtered / Rejected Memories"):
        rejected = mem_data.get("rejected_memories", [])
        if rejected:
            for item in rejected[-4:]:
                st.markdown(f"🚫 **Content:** `{item.get('content')}`\n- *Reason:* {item.get('reason')}")
        else:
            st.write("None recorded.")

    st.divider()

    # 4. Session Controls
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("🔄 New Session", use_container_width=True, help="Simulate starting a brand new conversation session."):
            st.session_state.messages = []
            st.session_state.session_id = f"sess_{int(time.time())}"
            st.toast("New session started! Persistent memory is preserved across sessions.", icon="🧠")
            st.rerun()
    with col_s2:
        if st.button("🗑️ Clear Traces", use_container_width=True):
            trace_registry.clear()
            st.toast("Traces cleared!")
            st.rerun()


# ==========================================
# MAIN INTERFACE TABS
# ==========================================
tab_chat, tab_traces, tab_audit, tab_benchmark = st.tabs([
    "💬 Live Student Support Chat",
    "📊 Tracing & Telemetry (Assignment 1)",
    "🛡️ Audit Trail & Privacy (Assignment 2)",
    "📈 Assignment 1 vs 2 Benchmark Matrix"
])


# -------------------------------------------------------------
# TAB 1: LIVE CHAT INTERFACE
# -------------------------------------------------------------
with tab_chat:
    st.markdown(f"### 👋 Welcome, {current_student['name']} (`{current_student['id']}`)")
    st.markdown(
        f"*Authenticated as **{current_student['programme']}** | Session: `{st.session_state.session_id}`*"
    )

    # Quick test prompt suggestions
    st.markdown("**Quick Test Scenarios (Click to try):**")
    col_p1, col_p2, col_p3 = st.columns(3)
    quick_query = None
    with col_p1:
        if st.button("💳 'What is my current fee status?'", use_container_width=True):
            quick_query = "What is my current fee status?"
        if st.button("🚫 'Check fee status of student S102 Priya'", use_container_width=True):
            quick_query = "Check fee status of student S102 Priya"
    with col_p2:
        if st.button("📄 'Payment portal failed. Can I pay next working day?'", use_container_width=True):
            quick_query = "The payment portal failed. Can I pay on the next working day?"
        if st.button("📋 'I want to change course BDA504 to AI602'", use_container_width=True):
            quick_query = "I want to change my course BDA504 to AI602"
    with col_p3:
        if st.button("🧠 'What facts do you remember about me?'", use_container_width=True):
            quick_query = "What specialization and career preferences do you remember about me discussed earlier?"
        if st.button("🔒 'My password is Pass123 and OTP is 928341'", use_container_width=True):
            quick_query = "My password is Pass123 and OTP is 928341"

    st.divider()

    # Display Chat History
    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]
        with st.chat_message(role):
            st.markdown(content)

            # Display tool trace if attached
            if "trace" in msg and msg["trace"]:
                t = msg["trace"]
                with st.expander(f"🔍 Agent Execution Details (Latency: {t.get('latency_seconds', 0)}s | Tokens: {t.get('tokens_total', 0)})"):
                    st.markdown(f"- **Agent Decision:** `{t.get('agent_decision')}`")
                    st.markdown(f"- **Status:** `{t.get('status')}` | **Task Success:** `{t.get('task_success')}`")
                    if t.get("tools_called"):
                        st.markdown(f"- **Tools Called:** `{', '.join(t.get('tools_called'))}`")
                        for td in t.get("tools_detail", []):
                            st.json(td)
                    if t.get("retrieved_policy_chunks"):
                        st.markdown(f"- **Policy Evidence:** `{', '.join(t.get('retrieved_policy_chunks'))}`")

            # Display Pending Approval card if attached
            if msg.get("requires_human_approval") and msg.get("approval_request_id"):
                req_id = msg["approval_request_id"]
                approval_item = get_approval_by_id(req_id)
                if approval_item and approval_item.get("status") == "PENDING":
                    st.warning(f"⚠️ **Human Approval Required** | Request ID: `{req_id}`", icon="⏳")
                    st.markdown(f"**Action:** `{approval_item.get('title')}`")
                    st.markdown(f"**Proposed Modification:** Swap `{approval_item['parameters'].get('current_course')}` for `{approval_item['parameters'].get('requested_course')}`")
                    st.markdown(f"**Reason:** *{approval_item.get('reason')}*")

                    col_ap1, col_ap2 = st.columns(2)
                    with col_ap1:
                        if st.button(f"✅ Approve Modification ({req_id})", key=f"appr_{req_id}", use_container_width=True):
                            res = resolve_approval(req_id, "APPROVED", resolver=current_student["advisor"], notes="Approved within registration add/drop window.")
                            st.success(res["message"])
                            time.sleep(1)
                            st.rerun()
                    with col_ap2:
                        if st.button(f"❌ Reject Modification ({req_id})", key=f"rej_{req_id}", use_container_width=True):
                            res = resolve_approval(req_id, "REJECTED", resolver=current_student["advisor"], notes="Target course capacity reached / rejected.")
                            st.error(res["message"])
                            time.sleep(1)
                            st.rerun()
                elif approval_item:
                    st.info(f"Resolution Status: **{approval_item.get('status')}** by {approval_item.get('resolver')}")

    # Chat input bar
    user_prompt = st.chat_input("Ask a question about fees, scholarships, policies, course changes, or records...")
    final_query = quick_query or user_prompt

    if final_query:
        # Append User message
        st.session_state.messages.append({"role": "user", "content": final_query})
        with st.chat_message("user"):
            st.markdown(final_query)

        # Run Agent
        with st.chat_message("assistant"):
            with st.spinner("Agent analyzing query, selecting context & executing tools..."):
                start_t = time.time()
                result = agent.run(
                    query=final_query,
                    authenticated_student_id=st.session_state.authenticated_student_id,
                    authenticated_student_name=current_student["name"],
                    conversation_history=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                    session_id=st.session_state.session_id
                )
                end_t = time.time()

            answer_text = result["answer"]
            st.markdown(answer_text)

            # Metadata toast / notice
            if result.get("memory_update_status") == "SENSITIVE_REJECTED":
                st.toast("🔒 Sensitive credentials detected & blocked from long-term memory!", icon="🛡️")
            elif result.get("memory_update_status") == "TEMPORARY_REJECTED":
                st.toast("ℹ️ Temporary state detected & filtered out of persistent memory.", icon="🧹")
            elif result.get("memory_update_status") == "STORED":
                st.toast(f"🧠 Remembered preference: {result.get('memory_update_detail')}", icon="💾")

            # Append to message history
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer_text,
                "trace": result.get("trace"),
                "requires_human_approval": result.get("requires_human_approval"),
                "approval_request_id": result.get("approval_request_id")
            })

            st.rerun()


# -------------------------------------------------------------
# TAB 2: TRACING & TELEMETRY (ASSIGNMENT 1)
# -------------------------------------------------------------
with tab_traces:
    st.markdown("### 📊 Tracing & Telemetry Dashboard")
    st.markdown(
        "Structured execution traces demonstrating **Task Accuracy, Tool Usage, Latency, Token Usage, and Retrieved Evidence**."
    )

    traces_list = trace_registry.get_traces_as_dicts()
    if not traces_list:
        st.info("No traces recorded yet. Ask questions in the chat or run the automated benchmark tab!")
    else:
        df_traces = pd.DataFrame(traces_list)

        # Metric summary row
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            col_m1.metric("Total Execution Runs", len(df_traces))
        with col_m2:
            avg_lat = round(df_traces["latency_seconds"].mean(), 3)
            col_m2.metric("Avg Latency (s)", f"{avg_lat}s")
        with col_m3:
            total_tok = int(df_traces["tokens_total"].sum())
            col_m3.metric("Total Tokens Used", f"{total_tok:,}")
        with col_m4:
            success_count = df_traces["task_success"].sum()
            col_m4.metric("Accuracy / Success", f"{success_count}/{len(df_traces)} ({round(success_count/len(df_traces)*100, 1)}%)")

        st.divider()

        # Display full structured table
        display_columns = [
            "trace_id", "query", "agent_decision", "tools_called",
            "latency_seconds", "tokens_prompt", "tokens_completion", "tokens_total",
            "retrieved_evidence_summary", "status", "task_success"
        ]
        available_cols = [c for c in display_columns if c in df_traces.columns]
        st.dataframe(df_traces[available_cols], use_container_width=True)

        # Detailed breakdown of individual trace
        st.markdown("#### 🔎 Inspect Specific Execution Trace")
        selected_trace_id = st.selectbox("Select Trace ID:", options=[t["trace_id"] for t in traces_list])
        selected_trace = next((t for t in traces_list if t["trace_id"] == selected_trace_id), None)
        if selected_trace:
            st.json(selected_trace)


# -------------------------------------------------------------
# TAB 3: AUDIT TRAIL & PRIVACY (ASSIGNMENT 2)
# -------------------------------------------------------------
with tab_audit:
    st.markdown("### 🛡️ Production Audit Trail & Access Governance")
    st.markdown(
        "Immutable record of institutional actions, authorization decisions, approval requests, and results."
    )

    audit_records = get_all_audit_logs(limit=50)
    if not audit_records:
        st.info("No audit records available.")
    else:
        df_audit = pd.DataFrame(audit_records)

        # Security KPI indicators
        col_a1, col_a2, col_a3, col_a4 = st.columns(4)
        with col_a1:
            col_a1.metric("Audit Events Recorded", len(df_audit))
        with col_a2:
            blocked_count = len(df_audit[df_audit["authorization_status"] == "BLOCKED_UNAUTHORIZED"])
            col_a2.metric("Unauthorized Blocks", blocked_count, delta=f"{blocked_count} attacks stopped")
        with col_a3:
            pending_count = len(df_audit[df_audit["approval_status"] == "PENDING"])
            col_a3.metric("Pending Approvals", pending_count)
        with col_a4:
            approved_count = len(df_audit[df_audit["approval_status"] == "APPROVED"])
            col_a4.metric("Approved Actions", approved_count)

        st.divider()

        # Display table
        audit_cols = [
            "audit_id", "timestamp", "actor_student_id", "actor_name",
            "action_type", "target_resource", "authorization_status",
            "approval_status", "result", "details"
        ]
        available_audit_cols = [c for c in audit_cols if c in df_audit.columns]
        st.dataframe(df_audit[available_audit_cols], use_container_width=True)


# -------------------------------------------------------------
# TAB 4: BENCHMARK MATRIX (ASSIGNMENTS 1 & 2 COMPARISON)
# -------------------------------------------------------------
with tab_benchmark:
    st.markdown("### 📈 Evaluation Matrix: Assignment 1 vs Assignment 2")
    st.markdown(
        "Run the complete test suite matching the required demonstration scenarios from both assignment briefs."
    )

    if st.button("🚀 Run Comprehensive Test Suite (8 Scenarios)", type="primary"):
        from evaluate import run_full_evaluation_suite
        with st.spinner("Executing evaluation suite across Assignment 1 & 2 scenarios..."):
            summary_df, report_text = run_full_evaluation_suite(agent)
            st.success("Test Suite Completed Successfully!")
            st.dataframe(summary_df, use_container_width=True)
            with st.expander("📄 View Full Markdown Evaluation Report"):
                st.markdown(report_text)
    else:
        st.info("Click the button above to run all 8 demonstration scenarios and generate the final comparison evaluation table!")
