"""Template rendering service.

Uses a simple regex-based ``{{variable_name}}`` substitution engine. No
``eval``/``exec`` is used — rendering is pure string replacement.

Rollback policy:
    ``rollback_version`` repoints ``templates.current_version_id`` to the
    requested prior version without creating a new version row.  The prior
    version thus becomes current again; version numbers are never renumbered.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_PLACEHOLDER_RE = re.compile(r"\{\{(\s*[\w.]+\s*)\}\}")
_SCRIPT_RE = re.compile(r"<script", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Core rendering helpers
# ---------------------------------------------------------------------------

def _extract_placeholders(text: str | None) -> set[str]:
    """Return the set of placeholder names referenced in *text*."""
    if not text:
        return set()
    return {m.group(1).strip() for m in _PLACEHOLDER_RE.finditer(text)}


def _render(text: str | None, variables: dict[str, str]) -> str:
    """Replace every ``{{name}}`` occurrence in *text* with the matching value.

    Unknown placeholders (no matching key in *variables*) are left as-is so
    callers can detect them after the fact.
    """
    if not text:
        return text or ""

    def _replace(m: re.Match) -> str:  # type: ignore[type-arg]
        name = m.group(1).strip()
        return variables.get(name, m.group(0))

    return _PLACEHOLDER_RE.sub(_replace, text)


# ---------------------------------------------------------------------------
# Public dataclasses
# ---------------------------------------------------------------------------

@dataclass
class RenderResult:
    subject: str
    body_html: str | None
    body_text: str
    used_placeholders: list[str] = field(default_factory=list)
    missing_placeholders: list[str] = field(default_factory=list)
    unknown_payload_keys: list[str] = field(default_factory=list)
    html_safety_warnings: list[str] = field(default_factory=list)


@dataclass
class InspectResult:
    used_placeholders: list[str]
    missing_placeholders: list[str]
    unknown_payload_keys: list[str]
    all_present: bool


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

def render_template(
    subject_template: str,
    body_html_template: str | None,
    body_text_template: str,
    variables: dict[str, str],
) -> RenderResult:
    """Render a template version against *variables*.

    Returns a :class:`RenderResult` that includes the rendered strings plus
    inspector metadata (used/missing/unknown placeholders, HTML safety warnings).
    """
    used = (
        _extract_placeholders(subject_template)
        | _extract_placeholders(body_html_template)
        | _extract_placeholders(body_text_template)
    )
    missing = sorted(used - set(variables.keys()))
    unknown = sorted(set(variables.keys()) - used)

    rendered_subject = _render(subject_template, variables)
    rendered_html = _render(body_html_template, variables) if body_html_template else None
    rendered_text = _render(body_text_template, variables)

    warnings: list[str] = []
    if body_html_template and _SCRIPT_RE.search(body_html_template):
        warnings.append("HTML body contains a <script> tag — this may be blocked by email clients.")
    if rendered_html and _SCRIPT_RE.search(rendered_html) and not warnings:
        warnings.append(
            "Rendered HTML body contains a <script> tag — this may be blocked by email clients."
        )

    return RenderResult(
        subject=rendered_subject,
        body_html=rendered_html,
        body_text=rendered_text,
        used_placeholders=sorted(used),
        missing_placeholders=missing,
        unknown_payload_keys=unknown,
        html_safety_warnings=warnings,
    )


def inspect_placeholders(
    subject_template: str,
    body_html_template: str | None,
    body_text_template: str,
    variables: dict[str, str],
) -> InspectResult:
    """Return placeholder inspector results without rendering."""
    used = (
        _extract_placeholders(subject_template)
        | _extract_placeholders(body_html_template)
        | _extract_placeholders(body_text_template)
    )
    missing = sorted(used - set(variables.keys()))
    unknown = sorted(set(variables.keys()) - used)
    return InspectResult(
        used_placeholders=sorted(used),
        missing_placeholders=missing,
        unknown_payload_keys=unknown,
        all_present=len(missing) == 0,
    )
