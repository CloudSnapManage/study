"""Deterministic offline study workflows."""
from __future__ import annotations

import re

from .config import Settings
from .database import connect_db


def generate_mock_exam(settings: Settings, subject: str, count: int = 5, source_bias: str = "past_papers_weighted") -> dict:
    count = max(1, min(count, 20))
    with connect_db(settings) as db:
        rows = db.execute("""SELECT c.content,c.heading,c.page_number,c.filename,d.doc_type FROM chunks c
          JOIN documents d ON d.id=c.document_id WHERE c.subject=?
          ORDER BY CASE WHEN ?='past_papers_weighted' AND d.doc_type='past_paper' THEN 0 ELSE 1 END,c.id LIMIT ?""", (subject, source_bias, count)).fetchall()
    questions = []
    for index, row in enumerate(rows, 1):
        prompt = row["content"].splitlines()[0][:500]
        questions.append({"number": index, "prompt": prompt, "marks": 5, "model_solution": row["content"][:1500], "source_ref": f"{row['filename']}, p. {row['page_number']}"})
    return {"subject": subject, "count": len(questions), "source_bias": source_bias, "questions": questions, "fallback": True}


def audit_derivation(problem: str, derivation: str) -> dict:
    lines = [line.strip() for line in derivation.splitlines() if line.strip()]
    steps = []
    previous = ""
    first_error = None
    for number, line in enumerate(lines, 1):
        valid = True
        note = "Step is internally consistent."
        normalized = re.sub(r"\s+", "", line.lower())
        prior = re.sub(r"\s+", "", previous.lower())
        if prior and (("=-" in prior and "=+" in normalized) or ("=+" in prior and "=-" in normalized)):
            valid = False
            note = "Sign changes without a stated operation."
        if "=nan" in normalized or "/0" in normalized:
            valid = False
            note = "Undefined numerical operation."
        if not valid and first_error is None:
            first_error = number
        steps.append({"number": number, "line": line, "valid": valid, "note": note})
        previous = line
    return {"problem": problem, "status": "error" if first_error else "valid", "first_error_step": first_error, "summary": f"Error detected at Step {first_error}" if first_error else "No deterministic error detected", "steps": steps, "fallback": True}


def grade_mock_exam(questions: list[dict], answers: dict) -> dict:
    """Return a deterministic rubric while preserving generated questions."""
    graded = []
    for index, question in enumerate(questions):
        response = str(answers.get(str(index), answers.get(index, ""))).strip()
        solution = question.get("model_solution") or question.get("solution") or ""
        marks = int(question.get("marks", 5))
        score = min(marks, 1 if response else 0)
        graded.append({
            **question,
            "solution": solution,
            "response": response,
            "score": score,
            "feedback": "Response recorded for source-based review." if response else "No response was submitted.",
        })
    return {"questions": graded, "fallback": True}
