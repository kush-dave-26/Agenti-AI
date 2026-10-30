"""
agent/policy_retriever.py
-------------------------
Selective Context Retrieval from the Student Policy Handbook.
Assignment 1 Requirements:
- Retrieve only relevant information rather than sending the whole document every time.
- Context selection: the model receives the current question plus only the information needed.
- Graceful handling when the available policy does not contain enough information.
"""

import os
import re
import math
from typing import List, Dict, Any, Tuple

POLICY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "student_handbook_policy.md")

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "can", "did", "do", "does", "doing", "don", "down", "during", "each", "few", "for",
    "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just",
    "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once",
    "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own", "s", "same", "she",
    "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves",
    "then", "there", "these", "they", "this", "those", "through", "to", "too", "under", "until",
    "up", "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom",
    "why", "will", "with", "would", "you", "your", "yours", "yourself", "yourselves"
}


def _tokenize(text: str) -> List[str]:
    words = re.findall(r"\b[a-zA-Z0-9_\-\.\₹]+\b", text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 1]


class PolicyKnowledgeBase:
    def __init__(self, policy_file: str = POLICY_PATH):
        self.policy_file = policy_file
        self.chunks: List[Dict[str, Any]] = []
        self._load_and_chunk_policy()

    def _load_and_chunk_policy(self):
        """Loads and splits the student handbook into structured chunks by Chunk ID headers."""
        if not os.path.exists(self.policy_file):
            return

        with open(self.policy_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Split on markdown headers with Chunk ID
        chunk_patterns = re.split(r"(####\s+Chunk\s+ID:\s*[^\n]+)", content)
        
        current_chunk_header = ""
        current_section = "General Policy"

        for part in chunk_patterns:
            part = part.strip()
            if not part:
                continue

            if part.startswith("#### Chunk ID:"):
                current_chunk_header = part
            elif current_chunk_header:
                # Extract chunk ID and optional title
                header_line = current_chunk_header.replace("#### Chunk ID:", "").strip()
                chunk_id = header_line.split()[0].replace(":", "").strip()
                title = header_line[len(chunk_id):].strip().strip("()") or chunk_id
                
                chunk_text = part
                self.chunks.append({
                    "chunk_id": chunk_id,
                    "title": title,
                    "content": chunk_text,
                    "tokens": _tokenize(f"{chunk_id} {title} {chunk_text}")
                })
                current_chunk_header = ""

    def retrieve(self, query: str, top_k: int = 2, min_score_threshold: float = 0.12) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Retrieves top_k policy chunks relevant to the query.
        Returns: (chunks_list, is_policy_covered)
        If query is outside domain (e.g. pet monkeys in lab), is_policy_covered is False.
        """
        query_tokens = _tokenize(query)
        if not query_tokens or not self.chunks:
            return [], False

        # Calculate BM25 / TF-IDF style similarity score
        scored_chunks = []
        for chunk in self.chunks:
            chunk_tokens = chunk["tokens"]
            token_count = len(chunk_tokens)
            if token_count == 0:
                continue

            # Term match frequency
            matches = 0
            for qt in query_tokens:
                # Direct match or substring match for key terms
                match_weight = 0
                for ct in chunk_tokens:
                    if qt == ct:
                        match_weight += 1.0
                    elif qt in ct or ct in qt:
                        match_weight += 0.5
                matches += match_weight

            score = matches / (math.sqrt(token_count) + 5.0)

            # Extra weight if chunk title matches query keywords
            title_lower = chunk["title"].lower()
            if any(qt in title_lower for qt in query_tokens):
                score *= 1.4

            if score > 0:
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        selected = []
        for score, chunk in scored_chunks[:top_k]:
            if score >= min_score_threshold:
                selected.append({
                    "chunk_id": chunk["chunk_id"],
                    "title": chunk["title"],
                    "content": chunk["content"],
                    "score": round(score, 3)
                })

        is_covered = len(selected) > 0
        return selected, is_covered


# Global retriever instance
policy_kb = PolicyKnowledgeBase()
