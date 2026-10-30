"""
tools/student_tools.py
----------------------
Core tools for the Student Support Agent with built-in code-level authorization,
privacy isolation, audit logging, and human approval enforcement.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from security.authorization import authorize_student_access, check_sensitive_action
from security.audit_logger import log_audit_event
from security.approval_manager import create_pending_approval

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "students_db.json")


def _read_db() -> Dict[str, Any]:
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_db(db: Dict[str, Any]) -> None:
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)


def get_student_record(
    student_id: str,
    current_user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves the academic profile and registration details of a student.
    Authorization is enforced in Python code.
    """
    effective_user = current_user_id or student_id
    allowed, message = authorize_student_access(effective_user, student_id, "get_student_record")

    if not allowed:
        log_audit_event(
            actor_student_id=effective_user,
            actor_name="Unknown",
            action_type="GET_STUDENT_RECORD",
            target_resource=f"student_record:{student_id}",
            parameters={"student_id": student_id},
            authorization_status="BLOCKED_UNAUTHORIZED",
            approval_status="N/A",
            result="FORBIDDEN",
            details=message
        )
        return {
            "error": True,
            "error_type": "AUTHORIZATION_ERROR",
            "message": message
        }

    db = _read_db()
    student = db.get("students", {}).get(student_id)
    if not student:
        return {
            "error": True,
            "error_type": "NOT_FOUND",
            "message": f"Student ID '{student_id}' does not exist in the institutional registry."
        }

    log_audit_event(
        actor_student_id=effective_user,
        actor_name=student.get("name", "Student"),
        action_type="GET_STUDENT_RECORD",
        target_resource=f"student_record:{student_id}",
        parameters={"student_id": student_id},
        authorization_status="ALLOWED",
        approval_status="N/A",
        result="SUCCESS",
        details="Authorized access to academic profile."
    )

    return {
        "success": True,
        "student_id": student["student_id"],
        "name": student["name"],
        "programme": student["programme"],
        "batch": student["batch"],
        "current_term": student["current_term"],
        "cgpa": student["cgpa"],
        "attendance_percentage": student["attendance_percentage"],
        "enrolled_courses": student["enrolled_courses"],
        "academic_advisor": student["academic_advisor"]
    }


def get_fee_status(
    student_id: str,
    current_user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves fee payment status, installment balances, and due dates.
    Authorization is enforced in Python code.
    """
    effective_user = current_user_id or student_id
    allowed, message = authorize_student_access(effective_user, student_id, "get_fee_status")

    if not allowed:
        log_audit_event(
            actor_student_id=effective_user,
            actor_name="Unknown",
            action_type="GET_FEE_STATUS",
            target_resource=f"fee_statement:{student_id}",
            parameters={"student_id": student_id},
            authorization_status="BLOCKED_UNAUTHORIZED",
            approval_status="N/A",
            result="FORBIDDEN",
            details=message
        )
        return {
            "error": True,
            "error_type": "AUTHORIZATION_ERROR",
            "message": message
        }

    db = _read_db()
    student = db.get("students", {}).get(student_id)
    if not student:
        return {
            "error": True,
            "error_type": "NOT_FOUND",
            "message": f"Student record for ID '{student_id}' not found."
        }

    fee_info = student.get("fee_details", {})
    log_audit_event(
        actor_student_id=effective_user,
        actor_name=student.get("name", "Student"),
        action_type="GET_FEE_STATUS",
        target_resource=f"fee_statement:{student_id}",
        parameters={"student_id": student_id},
        authorization_status="ALLOWED",
        approval_status="N/A",
        result="SUCCESS",
        details=f"Viewed fee status: Pending balance INR {fee_info.get('pending_balance')}."
    )

    return {
        "success": True,
        "student_id": student_id,
        "student_name": student["name"],
        "total_fee_due": fee_info.get("total_fee_due"),
        "amount_paid": fee_info.get("amount_paid"),
        "pending_balance": fee_info.get("pending_balance"),
        "due_date": fee_info.get("due_date"),
        "payment_status": fee_info.get("payment_status"),
        "last_payment_date": fee_info.get("last_payment_date"),
        "last_transaction_id": fee_info.get("last_transaction_id")
    }


def get_scholarship_status(
    student_id: str,
    current_user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves merit scholarship category, awarded amounts, and disbursement records.
    Authorization is enforced in Python code.
    """
    effective_user = current_user_id or student_id
    allowed, message = authorize_student_access(effective_user, student_id, "get_scholarship_status")

    if not allowed:
        log_audit_event(
            actor_student_id=effective_user,
            actor_name="Unknown",
            action_type="GET_SCHOLARSHIP_STATUS",
            target_resource=f"scholarship_record:{student_id}",
            parameters={"student_id": student_id},
            authorization_status="BLOCKED_UNAUTHORIZED",
            approval_status="N/A",
            result="FORBIDDEN",
            details=message
        )
        return {
            "error": True,
            "error_type": "AUTHORIZATION_ERROR",
            "message": message
        }

    db = _read_db()
    student = db.get("students", {}).get(student_id)
    if not student:
        return {
            "error": True,
            "error_type": "NOT_FOUND",
            "message": f"Student record for ID '{student_id}' not found."
        }

    sch = student.get("scholarship_details", {})
    log_audit_event(
        actor_student_id=effective_user,
        actor_name=student.get("name", "Student"),
        action_type="GET_SCHOLARSHIP_STATUS",
        target_resource=f"scholarship_record:{student_id}",
        parameters={"student_id": student_id},
        authorization_status="ALLOWED",
        approval_status="N/A",
        result="SUCCESS",
        details="Authorized access to scholarship statement."
    )

    return {
        "success": True,
        "student_id": student_id,
        "student_name": student["name"],
        "scholarship_name": sch.get("scholarship_name"),
        "status": sch.get("status"),
        "awarded_amount": sch.get("awarded_amount"),
        "disbursed_amount": sch.get("disbursed_amount"),
        "next_disbursement_date": sch.get("next_disbursement_date"),
        "bank_account_verified": sch.get("bank_account_verified"),
        "bank_masked_account": sch.get("bank_masked_account")
    }


def create_support_request(
    student_id: str,
    category: str,
    subject: str,
    description: str,
    priority: str = "Medium",
    current_user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Submits a formal student support ticket to the institutional helpdesk.
    """
    effective_user = current_user_id or student_id
    allowed, message = authorize_student_access(effective_user, student_id, "create_support_request")

    if not allowed:
        log_audit_event(
            actor_student_id=effective_user,
            actor_name="Unknown",
            action_type="CREATE_SUPPORT_REQUEST",
            target_resource="support_tickets",
            parameters={"student_id": student_id, "category": category, "subject": subject},
            authorization_status="BLOCKED_UNAUTHORIZED",
            approval_status="N/A",
            result="FORBIDDEN",
            details=message
        )
        return {
            "error": True,
            "error_type": "AUTHORIZATION_ERROR",
            "message": message
        }

    db = _read_db()
    student = db.get("students", {}).get(student_id)
    student_name = student.get("name", "Student") if student else "Student"

    ticket_id = f"TICK-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()

    ticket = {
        "ticket_id": ticket_id,
        "student_id": student_id,
        "student_name": student_name,
        "category": category,
        "subject": subject,
        "description": description,
        "priority": priority,
        "status": "OPEN",
        "created_at": timestamp
    }

    if "support_tickets" not in db:
        db["support_tickets"] = []
    db["support_tickets"].append(ticket)
    _write_db(db)

    log_audit_event(
        actor_student_id=effective_user,
        actor_name=student_name,
        action_type="CREATE_SUPPORT_REQUEST",
        target_resource=f"support_ticket:{ticket_id}",
        parameters={"ticket_id": ticket_id, "category": category, "subject": subject, "priority": priority},
        authorization_status="ALLOWED",
        approval_status="N/A",
        result="SUCCESS",
        details=f"Created support ticket {ticket_id} for issue: '{subject}'."
    )

    return {
        "success": True,
        "ticket_id": ticket_id,
        "status": "OPEN",
        "category": category,
        "subject": subject,
        "message": f"Support ticket #{ticket_id} logged successfully with priority '{priority}'. Expected response within standard SLA."
    }


def request_course_change(
    student_id: str,
    current_course: str,
    requested_course: str,
    reason: str,
    current_user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    SENSITIVE ACTION: Requests a course/elective swap.
    Must NOT execute immediately. Enforces Human-in-the-Loop approval workflow.
    """
    effective_user = current_user_id or student_id
    allowed, message = authorize_student_access(effective_user, student_id, "request_course_change")

    if not allowed:
        log_audit_event(
            actor_student_id=effective_user,
            actor_name="Unknown",
            action_type="REQUEST_COURSE_CHANGE",
            target_resource=f"student_record:{student_id}",
            parameters={"current_course": current_course, "requested_course": requested_course},
            authorization_status="BLOCKED_UNAUTHORIZED",
            approval_status="N/A",
            result="FORBIDDEN",
            details=message
        )
        return {
            "error": True,
            "error_type": "AUTHORIZATION_ERROR",
            "message": message
        }

    db = _read_db()
    student = db.get("students", {}).get(student_id)
    if not student:
        return {
            "error": True,
            "error_type": "NOT_FOUND",
            "message": f"Student '{student_id}' not found."
        }

    # Verify that the student is actually enrolled in the course they want to drop
    enrolled = student.get("enrolled_courses", [])
    course_found = any(current_course.lower() in c.lower() for c in enrolled)
    if not course_found:
        return {
            "error": True,
            "error_type": "VALIDATION_ERROR",
            "message": f"Validation failed: Student '{student_id}' is not enrolled in '{current_course}'. Currently enrolled: {', '.join(enrolled)}"
        }

    # Sensitive action: Place in pending human approval queue
    approval_item = create_pending_approval(
        student_id=student_id,
        student_name=student["name"],
        action_name="request_course_change",
        title="Elective Course Change Request",
        parameters={
            "student_id": student_id,
            "current_course": current_course,
            "requested_course": requested_course,
            "reason": reason
        },
        reason=reason
    )

    return {
        "success": True,
        "requires_human_approval": True,
        "approval_request_id": approval_item["request_id"],
        "status": "PENDING_APPROVAL",
        "current_course": current_course,
        "requested_course": requested_course,
        "message": (
            f"ACTION PENDING HUMAN APPROVAL: Course change from '{current_course}' to '{requested_course}' "
            f"requires authorization from Faculty Advisor {student.get('academic_advisor', 'Assigned Advisor')}. "
            f"Request [{approval_item['request_id']}] has been queued. The course swap will ONLY take effect "
            f"once explicit approval is granted."
        )
    }


# Tool Registry & Groq / OpenAI Function Calling Schema
GROQ_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_student_record",
            "description": "Retrieves the academic record, CGPA, attendance, advisor, and enrolled courses of the signed-in student.",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string",
                        "description": "The student ID (e.g. 'S101'). Must match the signed-in student."
                    }
                },
                "required": ["student_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_fee_status",
            "description": "Checks the tuition fee status, balance amount, payment deadlines, and payment history for a student.",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string",
                        "description": "The student ID (e.g. 'S101'). Must match the signed-in student."
                    }
                },
                "required": ["student_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_scholarship_status",
            "description": "Checks the merit scholarship status, awarded percentage/amount, and disbursement details for a student.",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string",
                        "description": "The student ID (e.g. 'S101'). Must match the signed-in student."
                    }
                },
                "required": ["student_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_support_request",
            "description": "Creates an official institutional support ticket for technical issues, portal problems, hostel or fee queries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string",
                        "description": "The student ID submitting the ticket."
                    },
                    "category": {
                        "type": "string",
                        "enum": ["IT_PORTAL", "FEES_ACCOUNTS", "ACADEMIC", "HOSTEL_CAMPUS", "GENERAL"],
                        "description": "Category of the inquiry."
                    },
                    "subject": {
                        "type": "string",
                        "description": "Brief summary of the issue."
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed explanation of the support request."
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["Low", "Medium", "High", "Urgent"],
                        "description": "Priority level."
                    }
                },
                "required": ["student_id", "category", "subject", "description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "request_course_change",
            "description": "Initiates a formal elective/course modification. Note: This is a sensitive action that requires faculty advisor approval before execution.",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string",
                        "description": "The student ID requesting the change."
                    },
                    "current_course": {
                        "type": "string",
                        "description": "The enrolled course to drop/change from (e.g. 'BDA504: Cloud Computing & MLOps')."
                    },
                    "requested_course": {
                        "type": "string",
                        "description": "The new course requested to enroll in (e.g. 'AI602: Natural Language Processing & LLMs')."
                    },
                    "reason": {
                        "type": "string",
                        "description": "Academic justification for the change."
                    }
                },
                "required": ["student_id", "current_course", "requested_course", "reason"]
            }
        }
    }
]


TOOL_MAPPING = {
    "get_student_record": get_student_record,
    "get_fee_status": get_fee_status,
    "get_scholarship_status": get_scholarship_status,
    "create_support_request": create_support_request,
    "request_course_change": request_course_change
}
