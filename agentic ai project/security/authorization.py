"""
security/authorization.py
-------------------------
Enforces application-level access control and privacy guards for institutional student records.
CRITICAL ASSIGNMENT 2 REQUIREMENT:
Authorization must be enforced in normal application/tool Python code,
NOT solely relied upon via LLM system prompts.
"""

from typing import Tuple, Dict, Any, Optional
from datetime import datetime


class AuthorizationError(Exception):
    """Raised when an unauthorized student attempts to access or modify another student's private data."""
    pass


class SensitiveActionError(Exception):
    """Raised when an action requires human approval before execution."""
    def __init__(self, message: str, pending_action_id: str, details: Dict[str, Any]):
        super().__init__(message)
        self.pending_action_id = pending_action_id
        self.details = details


# Defined sensitive actions that strictly require human confirmation or institutional approval
SENSITIVE_ACTIONS = {
    "request_course_change": {
        "title": "Academic Course Modification",
        "description": "Modifies registered course curriculum or drops/adds electives.",
        "requires_approval": True,
        "approver_role": "Academic Faculty Advisor / Dean"
    },
    "update_scholarship_bank_account": {
        "title": "Scholarship Bank Account Update",
        "description": "Alters direct disbursement banking details.",
        "requires_approval": True,
        "approver_role": "Finance Officer"
    },
    "request_fee_concession": {
        "title": "Fee Waiver / Concession Request",
        "description": "Applies for term fee reduction or postponement.",
        "requires_approval": True,
        "approver_role": "Scholarship & Accounts Committee"
    }
}


def authorize_student_access(
    current_student_id: str,
    target_student_id: str,
    action_name: str
) -> Tuple[bool, str]:
    """
    Validates whether the signed-in student is authorized to perform an action on target_student_id.
    
    Rules:
    1. A student can only view/modify their own record.
    2. Any attempt by student X to view/modify student Y's record is strictly blocked.
    """
    curr = (current_student_id or "").strip().upper()
    target = (target_student_id or "").strip().upper()

    if not curr:
        return False, "Access Denied: No authenticated student session found."

    if not target:
        # Default target to current student if omitted by tool caller
        return True, "Authorized (Self)"

    if curr != target:
        return (
            False,
            f"ACCESS DENIED (PRIVACY VIOLATION): Student '{curr}' is not authorized "
            f"to access or modify private records of Student '{target}'. "
            f"Application security policy strictly isolates student data."
        )

    return True, "Authorized: Self-access verified."


def check_sensitive_action(action_name: str) -> Optional[Dict[str, Any]]:
    """
    Checks if an action is categorized as sensitive and requires human confirmation/approval.
    """
    return SENSITIVE_ACTIONS.get(action_name)
