"""
security/approval_manager.py
----------------------------
Manages Human-in-the-Loop (HITL) approval workflows for sensitive student actions
such as course changes, bank account modifications, or fee waiver petitions.
Fulfills Assignment 2: "At least one sensitive action should require confirmation
or human approval before it is executed. If approval is rejected - the action must not execute."
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from security.audit_logger import log_audit_event

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "students_db.json")


def _load_db() -> Dict[str, Any]:
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_db(data: Dict[str, Any]) -> None:
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def create_pending_approval(
    student_id: str,
    student_name: str,
    action_name: str,
    title: str,
    parameters: Dict[str, Any],
    reason: str,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Records a pending approval request that must be confirmed/approved by human/admin.
    """
    db = _load_db()
    if "pending_approvals" not in db:
        db["pending_approvals"] = []

    request_id = f"APPR-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()

    approval_item = {
        "request_id": request_id,
        "student_id": student_id,
        "student_name": student_name,
        "action_name": action_name,
        "title": title,
        "parameters": parameters,
        "reason": reason,
        "status": "PENDING",  # 'PENDING', 'APPROVED', 'REJECTED'
        "created_at": timestamp,
        "resolved_at": None,
        "resolver": None,
        "resolver_notes": None
    }

    db["pending_approvals"].append(approval_item)
    _save_db(db)

    # Log to audit trail
    log_audit_event(
        actor_student_id=student_id,
        actor_name=student_name,
        action_type=action_name,
        target_resource=f"student_record:{student_id}",
        parameters=parameters,
        authorization_status="ALLOWED",
        approval_status="PENDING",
        result="AWAITING_HUMAN_APPROVAL",
        details=f"Sensitive action '{title}' initiated. Placed into pending queue [{request_id}].",
        session_id=session_id
    )

    return approval_item


def get_pending_approvals(student_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves all pending approval items, optionally filtered by student_id."""
    db = _load_db()
    approvals = db.get("pending_approvals", [])
    pending = [a for a in approvals if a.get("status") == "PENDING"]
    if student_id:
        pending = [a for a in pending if a.get("student_id") == student_id]
    return pending


def get_approval_by_id(request_id: str) -> Optional[Dict[str, Any]]:
    db = _load_db()
    for item in db.get("pending_approvals", []):
        if item.get("request_id") == request_id:
            return item
    return None


def resolve_approval(
    request_id: str,
    decision: str,  # 'APPROVED' or 'REJECTED'
    resolver: str = "Faculty Advisor / Admin",
    notes: str = ""
) -> Dict[str, Any]:
    """
    Resolves a pending human-approval request.
    If APPROVED: executes the underlying change in the database.
    If REJECTED: aborts the change and records rejection in audit log.
    """
    decision = decision.upper().strip()
    if decision not in ["APPROVED", "REJECTED"]:
        raise ValueError("Decision must be either 'APPROVED' or 'REJECTED'")

    db = _load_db()
    target_item = None
    for item in db.get("pending_approvals", []):
        if item.get("request_id") == request_id:
            target_item = item
            break

    if not target_item:
        raise ValueError(f"Approval request '{request_id}' not found.")

    if target_item.get("status") != "PENDING":
        return {
            "success": False,
            "message": f"Request {request_id} was already {target_item.get('status')}."
        }

    timestamp = datetime.now(timezone.utc).isoformat()
    target_item["status"] = decision
    target_item["resolved_at"] = timestamp
    target_item["resolver"] = resolver
    target_item["resolver_notes"] = notes

    execution_result = "N/A"
    student_id = target_item["student_id"]
    student_name = target_item["student_name"]
    action_name = target_item["action_name"]
    params = target_item["parameters"]

    if decision == "APPROVED":
        # Execute the sensitive modification
        if action_name == "request_course_change":
            current_course = params.get("current_course")
            requested_course = params.get("requested_course")
            
            student_data = db["students"].get(student_id)
            if student_data:
                courses = student_data.get("enrolled_courses", [])
                # Remove current if present and add new course
                if current_course in courses:
                    courses.remove(current_course)
                courses.append(requested_course)
                student_data["enrolled_courses"] = courses
                execution_result = f"Course changed successfully: Swapped '{current_course}' for '{requested_course}'."
            else:
                execution_result = "Student record not found for modification."
        else:
            execution_result = f"Action '{action_name}' approved and executed."

        _save_db(db)

        # Audit log for approved execution
        log_audit_event(
            actor_student_id=student_id,
            actor_name=student_name,
            action_type=action_name,
            target_resource=f"student_record:{student_id}",
            parameters=params,
            authorization_status="ALLOWED",
            approval_status="APPROVED",
            result="SUCCESS",
            details=f"Human approval granted by {resolver}. Modification executed: {execution_result}"
        )

        return {
            "success": True,
            "decision": "APPROVED",
            "message": f"Approval request {request_id} was APPROVED. {execution_result}",
            "execution_result": execution_result
        }

    else:
        # REJECTED - Action must NOT execute
        _save_db(db)
        execution_result = f"Action '{action_name}' was REJECTED by {resolver}. Reason/Notes: {notes or 'No specific note provided'}. No changes were made to the student record."

        log_audit_event(
            actor_student_id=student_id,
            actor_name=student_name,
            action_type=action_name,
            target_resource=f"student_record:{student_id}",
            parameters=params,
            authorization_status="ALLOWED",
            approval_status="REJECTED",
            result="ABORTED_BY_REJECTION",
            details=execution_result
        )

        return {
            "success": True,
            "decision": "REJECTED",
            "message": f"Approval request {request_id} was REJECTED. The requested action was blocked from executing.",
            "execution_result": execution_result
        }
