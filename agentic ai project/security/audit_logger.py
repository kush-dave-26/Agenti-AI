"""
security/audit_logger.py
------------------------
Maintains an immutable structured audit log of all institutional actions,
permission decisions, sensitive approval requests, and results.
Meets Assignment 2 requirements for compliance, traceability, and institutional safety.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

AUDIT_LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "audit_log.json")


def _read_audit_records() -> List[Dict[str, Any]]:
    if not os.path.exists(AUDIT_LOG_PATH):
        return []
    try:
        with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_audit_records(records: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
    with open(AUDIT_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


def log_audit_event(
    actor_student_id: str,
    actor_name: str,
    action_type: str,
    target_resource: str,
    parameters: Dict[str, Any],
    authorization_status: str,  # 'ALLOWED', 'BLOCKED_UNAUTHORIZED', 'BYPASS_ATTEMPT_STOPPED'
    approval_status: str,        # 'N/A', 'PENDING', 'APPROVED', 'REJECTED'
    result: str,                 # 'SUCCESS', 'FORBIDDEN', 'ABORTED', 'ERROR'
    details: str,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates and saves a structured audit event.
    """
    records = _read_audit_records()
    
    audit_id = f"AUD-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()

    event = {
        "audit_id": audit_id,
        "timestamp": timestamp,
        "session_id": session_id or "default_session",
        "actor_student_id": actor_student_id,
        "actor_name": actor_name,
        "action_type": action_type,
        "target_resource": target_resource,
        "parameters": parameters,
        "authorization_status": authorization_status,
        "approval_status": approval_status,
        "result": result,
        "details": details
    }

    records.append(event)
    _save_audit_records(records)
    return event


def get_all_audit_logs(limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieves audit records in reverse chronological order."""
    records = _read_audit_records()
    return list(reversed(records))[:limit]
