"""Local study tool implementations used by chat."""
from __future__ import annotations

from .config import Settings
from .search import search_all, vault_items
from .study import audit_derivation


def search_course_materials(settings: Settings, query: str, subject: str | None = None) -> list[dict]:
    return search_all(settings, query, subject=subject, limit=8)


def extract_formulas(settings: Settings, query: str = "") -> list[dict]:
    return vault_items(settings, item_type="formula", query=query)


def grade_derivation(problem: str, derivation: str) -> dict:
    return audit_derivation(problem, derivation)


TOOL_SCHEMAS = [
    {"type": "function", "function": {"name": "search_course_materials", "description": "Search indexed course PDFs", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "subject": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "extract_formulas", "description": "Search extracted formulas", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "grade_derivation", "description": "Audit derivation steps", "parameters": {"type": "object", "properties": {"problem": {"type": "string"}, "derivation": {"type": "string"}}, "required": ["derivation"]}}},
]
