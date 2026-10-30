"""
agent/tracing.py
----------------
Structured telemetry and tracing logger for Agentic AI execution runs.
Meets Assignment 1 & 2 requirements:
- Task accuracy / success
- Tools used (and appropriateness)
- Latency (approx end-to-end response time in seconds)
- Token usage (input and output tokens reported by model API)
- Retrieved evidence (which policy chunk(s) or memory items were used)
"""

import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class ExecutionTrace:
    def __init__(self, query: str, student_id: str, session_id: Optional[str] = None):
        self.trace_id = f"TRC-{uuid.uuid4().hex[:8].upper()}"
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.query = query
        self.student_id = student_id
        self.session_id = session_id or "default_session"
        self.start_time = time.time()
        self.end_time = None
        self.latency_seconds = 0.0

        # Telemetry fields
        self.tools_called: List[Dict[str, Any]] = []
        self.retrieved_policy_chunks: List[Dict[str, Any]] = []
        self.retrieved_memory_items: List[str] = []
        self.tokens_prompt: int = 0
        self.tokens_completion: int = 0
        self.tokens_total: int = 0
        self.model_name: str = ""

        # Status & evaluation
        self.status: str = "IN_PROGRESS"  # 'SUCCESS', 'BLOCKED_UNAUTHORIZED', 'PENDING_APPROVAL', 'POLICY_NOT_FOUND', 'ERROR'
        self.task_success: bool = False
        self.agent_decision: str = "DIRECT_ANSWER"  # 'DIRECT_ANSWER', 'TOOL_USE', 'POLICY_RETRIEVAL', 'MEMORY_LOOKUP', 'HYBRID'
        self.response_preview: str = ""
        self.notes: str = ""

    def record_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Any,
        is_appropriate: bool = True
    ):
        self.tools_called.append({
            "tool_name": tool_name,
            "arguments": arguments,
            "result_preview": str(result)[:200],
            "is_appropriate": is_appropriate
        })
        self.agent_decision = "TOOL_USE"

    def record_policy_retrieval(self, chunks: List[Dict[str, Any]]):
        self.retrieved_policy_chunks = chunks
        if chunks and self.agent_decision == "DIRECT_ANSWER":
            self.agent_decision = "POLICY_RETRIEVAL"

    def record_memory_retrieval(self, memory_items: List[str]):
        self.retrieved_memory_items = memory_items
        if memory_items and self.agent_decision == "DIRECT_ANSWER":
            self.agent_decision = "MEMORY_LOOKUP"

    def record_token_usage(self, prompt: int, completion: int, total: int, model: str = ""):
        self.tokens_prompt += prompt
        self.tokens_completion += completion
        self.tokens_total += total
        if model:
            self.model_name = model

    def complete(self, status: str, success: bool, response_text: str = "", notes: str = ""):
        self.end_time = time.time()
        self.latency_seconds = round(self.end_time - self.start_time, 3)
        self.status = status
        self.task_success = success
        self.response_preview = response_text[:250] + ("..." if len(response_text) > 250 else "")
        self.notes = notes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "timestamp": self.timestamp,
            "student_id": self.student_id,
            "query": self.query,
            "latency_seconds": self.latency_seconds,
            "tokens_prompt": self.tokens_prompt,
            "tokens_completion": self.tokens_completion,
            "tokens_total": self.tokens_total,
            "model_name": self.model_name,
            "agent_decision": self.agent_decision,
            "tools_called": [t["tool_name"] for t in self.tools_called],
            "tools_detail": self.tools_called,
            "retrieved_policy_chunks": [c["chunk_id"] for c in self.retrieved_policy_chunks],
            "retrieved_evidence_summary": (
                f"Policy: {[c['chunk_id'] for c in self.retrieved_policy_chunks]}; "
                f"Memory: {len(self.retrieved_memory_items)} items"
            ),
            "status": self.status,
            "task_success": self.task_success,
            "response_preview": self.response_preview,
            "notes": self.notes
        }


class GlobalTraceRegistry:
    """In-memory and exportable registry of all execution traces."""
    def __init__(self):
        self.traces: List[ExecutionTrace] = []

    def add_trace(self, trace: ExecutionTrace):
        self.traces.append(trace)

    def get_traces_as_dicts(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self.traces]

    def clear(self):
        self.traces.clear()


# Global singleton instance
trace_registry = GlobalTraceRegistry()
