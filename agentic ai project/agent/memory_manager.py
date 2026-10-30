"""
agent/memory_manager.py
-----------------------
Persistent Cross-Session Memory Management with Strict Privacy & Ephemeral Filters.
Assignment 1 & 2 Requirements:
- Persistent memory across sessions for useful information (programme, elective preferences, career goals).
- Temporary information (feelings, meals, battery, casual chatter) MUST NOT be stored.
- Sensitive information (OTPs, passwords, CVVs, pins) MUST NOT become persistent memory.
"""

import json
import os
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

MEMORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "student_memory.json")

# Regex patterns for sensitive data
SENSITIVE_PATTERNS = [
    (r"\b(otp|one[-\s]?time[-\s]?password|verification\s*code|pin)\s*(is|:)?\s*([0-9]{4,8})\b", "OTP / Verification Code"),
    (r"\b(password|pwd|passcode)\s*(is|:)?\s*(\S+)\b", "Password / Passcode"),
    (r"\b([0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4})\b", "Credit/Debit Card Number"),
    (r"\b(cvv|cvc)\s*(is|:)?\s*([0-9]{3,4})\b", "Card CVV/CVC"),
    (r"\b(secret[-\s]?key|api[-\s]?key|token)\s*(is|:)?\s*([a-zA-Z0-9_\-]{16,})\b", "Secret API Token / Key")
]

# Patterns for temporary / fleeting statements
TEMPORARY_PATTERNS = [
    r"\b(feeling|felt)\s+(very\s+|extremely\s+|really\s+|a\s+bit\s+|so\s+)?(tired|sleepy|hungry|exhausted|bored|happy|sad|sick|unwell)\b",
    r"\b(going to|having|had|eating|ate)\s+(lunch|dinner|breakfast|snack|coffee|tea|nap)\b",
    r"\b(battery|phone\s*charge)\s+(is|at)?\s*([0-9]+%|low|dying)\b",
    r"\b(today\s*is\s*hot|cold|raining|weather)\b",
    r"\b(be\s*right\s*back|brb|gotta\s*run|talk\s*later|see\s*ya)\b",
    r"\b(just\s*checking|testing\s*the\s*chat|hello|hey|good\s*morning|good\s*evening)\b"
]

# Permanent useful preference cues
PREFERENCE_KEYWORDS = [
    ("specialization_track", [r"specializ(e|ation)\s+in\s+([a-zA-Z0-9\s&]+)", r"interested\s+in\s+the\s+([a-zA-Z0-9\s&]+)\s+track"]),
    ("preferred_career_role", [r"(aiming\s+to\s+become|career\s+goal\s+is|want\s+to\s+work\s+as)\s+an?\s+([a-zA-Z0-9\s&]+)"]),
    ("target_elective", [r"(planning\s+to\s+take|prefer\s+elective|want\s+to\s+enroll\s+in)\s+([a-zA-Z0-9\s&:\-]+)"]),
    ("preferred_contact_method", [r"(prefer|reach\s+me\s+via|contact\s+me\s+on)\s+(email|phone|whatsapp|teams|portal)"])
]


class StudentMemoryManager:
    def __init__(self, memory_file: str = MEMORY_FILE):
        self.memory_file = memory_file
        self.memories = self._load()

    def _load(self) -> Dict[str, Any]:
        if not os.path.exists(self.memory_file):
            return {}
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self):
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self.memories, f, indent=2)

    def get_student_memory(self, student_id: str) -> Dict[str, Any]:
        student_id = student_id.upper()
        return self.memories.get(student_id, {
            "student_id": student_id,
            "persistent_facts": {},
            "rejected_memories": [],
            "last_session_timestamp": None
        })

    def get_context_memory_strings(self, student_id: str) -> List[str]:
        """Returns formatted memory bullets to include in agent prompt."""
        mem = self.get_student_memory(student_id)
        facts = mem.get("persistent_facts", {})
        return [f"- {k.replace('_', ' ').capitalize()}: {v}" for k, v in facts.items()]

    def filter_and_extract_memory(
        self,
        student_id: str,
        user_input: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Analyzes user input.
        Returns:
            (classification, key_or_reason, extracted_fact)
            classification is one of: 'SENSITIVE_REJECTED', 'TEMPORARY_REJECTED', 'STORED', 'IGNORED'
        """
        text = user_input.strip()

        # 1. Check for SENSITIVE data (OTP, password, credentials)
        for pattern, label in SENSITIVE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                reason = f"Contains sensitive credential ({label}). Strictly blocked from persistent memory."
                self._record_rejection(student_id, text, reason)
                return "SENSITIVE_REJECTED", reason, None

        # 2. Check for TEMPORARY / EPHEMERAL statements
        for pattern in TEMPORARY_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                reason = "Temporary emotional state, greeting, or ephemeral detail. Excluded from long-term memory."
                self._record_rejection(student_id, text, reason)
                return "TEMPORARY_REJECTED", reason, None

        # 3. Check for USEFUL LONG-TERM PREFERENCES
        for fact_key, patterns in PREFERENCE_KEYWORDS:
            for pat in patterns:
                match = re.search(pat, text, re.IGNORECASE)
                if match:
                    extracted_val = match.group(match.lastindex).strip()
                    self._store_persistent_fact(student_id, fact_key, extracted_val)
                    return "STORED", fact_key, extracted_val

        return "IGNORED", None, None

    def _record_rejection(self, student_id: str, content: str, reason: str):
        student_id = student_id.upper()
        if student_id not in self.memories:
            self.memories[student_id] = {
                "student_id": student_id,
                "persistent_facts": {},
                "rejected_memories": [],
                "last_session_timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Redact any obvious 6 digit code in the audit record preview
        masked_content = re.sub(r"\b\d{4,8}\b", "[REDACTED_SECRET]", content)
        self.memories[student_id].setdefault("rejected_memories", []).append({
            "content": masked_content,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self._save()

    def _store_persistent_fact(self, student_id: str, key: str, value: str):
        student_id = student_id.upper()
        if student_id not in self.memories:
            self.memories[student_id] = {
                "student_id": student_id,
                "persistent_facts": {},
                "rejected_memories": [],
                "last_session_timestamp": datetime.now(timezone.utc).isoformat()
            }
        self.memories[student_id]["persistent_facts"][key] = value
        self.memories[student_id]["last_session_timestamp"] = datetime.now(timezone.utc).isoformat()
        self._save()

    def get_rejected_memories(self, student_id: str) -> List[Dict[str, Any]]:
        mem = self.get_student_memory(student_id)
        return mem.get("rejected_memories", [])


# Global memory instance
student_memory_mgr = StudentMemoryManager()
