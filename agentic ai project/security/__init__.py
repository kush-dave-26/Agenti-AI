"""
security package initialization
"""
from security.authorization import (
    authorize_student_access,
    check_sensitive_action,
    AuthorizationError,
    SensitiveActionError,
    SENSITIVE_ACTIONS
)
from security.approval_manager import (
    create_pending_approval,
    resolve_approval,
    get_pending_approvals,
    get_approval_by_id
)
from security.audit_logger import (
    log_audit_event,
    get_all_audit_logs
)

__all__ = [
    "authorize_student_access",
    "check_sensitive_action",
    "AuthorizationError",
    "SensitiveActionError",
    "SENSITIVE_ACTIONS",
    "create_pending_approval",
    "resolve_approval",
    "get_pending_approvals",
    "get_approval_by_id",
    "log_audit_event",
    "get_all_audit_logs",
]
