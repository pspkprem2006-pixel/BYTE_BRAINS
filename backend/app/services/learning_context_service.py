"""Learning Context assembly.

``LearningContextService`` combines uploaded study materials and selected
web resources into a single, bounded, clearly-delimited context block that
the AI Tutor / Quiz / Study Plan consume.

SECURITY CONTRACT
-----------------
Web-resource metadata is UNTRUSTED DATA. This service only labels and
bounds it. It never interprets it, never logs it, and the rendering always
keeps it inside a delimited "[WEB LEARNING RESOURCE]" block that the AI
prompt marks as untrusted reference data — never as instructions.
"""

import logging
import uuid
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models import LearningResourceSelection, Material, Subject
from app.services import resource_selection_service

logger = logging.getLogger(__name__)

MAX_WEB_RESOURCES_IN_CONTEXT = 5
MAX_MATERIALS_IN_CONTEXT = 3
MAX_MATERIAL_EXCERPT_CHARS = 6000
MAX_CONTEXT_CHARS = 24000


@dataclass
class ContextMaterial:
    """One uploaded material excerpt, labeled with its filename."""

    filename: str
    excerpt: str


@dataclass
class LearningContext:
    """Bounded learning context assembled from user-owned sources."""

    subject_name: str | None = None
    subject_id: uuid.UUID | None = None
    materials: list[ContextMaterial] = field(default_factory=list)
    web_resources: list[LearningResourceSelection] = field(default_factory=list)

    @property
    def has_material(self) -> bool:
        return bool(self.materials)

    @property
    def has_web(self) -> bool:
        return bool(self.web_resources)

    @property
    def is_empty(self) -> bool:
        return not self.has_material and not self.has_web

    def render(self) -> str:
        """Render the context as a single bounded, labeled text block."""
        parts: list[str] = []
        for index, material in enumerate(self.materials, start=1):
            parts.append(
                f"[UPLOADED MATERIAL {index}]\n"
                f"Filename: {material.filename}\n"
                f"{material.excerpt}"
            )
        for index, resource in enumerate(self.web_resources, start=1):
            parts.append(_render_web_resource(resource, index))
        if not parts:
            return ""
        return "\n\n".join(parts)


def _render_web_resource(
    resource: LearningResourceSelection, index: int
) -> str:
    """Render one selection as labeled metadata (never as instructions)."""
    lines = [
        f"[WEB LEARNING RESOURCE {index}]",
        f"Title: {resource.title}",
        f"URL: {resource.url}",
        f"Domain: {resource.domain or '-'}",
        f"Type: {resource.resource_type}",
        f"Official: {'yes' if resource.is_official else 'no'}",
    ]
    if resource.difficulty:
        lines.append(f"Difficulty: {resource.difficulty}")
    if resource.description:
        lines.append(f"Description: {resource.description}")
    return "\n".join(lines)


class LearningContextService:
    """Assemble bounded learning context from the database."""

    def build_context(
        self,
        db: Session,
        user_id: uuid.UUID,
        *,
        material: Material | None = None,
        subject: Subject | None = None,
        question: str = "",
    ) -> LearningContext:
        """Build a context from an optional material and/or subject.

        - material: includes that material's retrieval excerpt (when the
          material has extracted text)
        - subject: includes the subject's processed materials (bounded) and
          the user's web-resource selections for that subject (bounded)
        """
        context = LearningContext()
        subject_name_parts: list[str] = []

        if material is not None and material.extracted_text and material.extracted_text.strip():
            context.materials.append(
                ContextMaterial(
                    filename=material.original_filename,
                    excerpt=_material_excerpt(material.extracted_text, question),
                )
            )
            if material.subject is not None:
                context.subject_id = material.subject.id
                subject_name_parts.append(material.subject.name)
        if subject is not None:
            context.subject_id = subject.id
            subject_name_parts.append(subject.name)

            subject_materials = (
                db.query(Material)
                .filter(
                    Material.subject_id == subject.id,
                    Material.user_id == user_id,
                )
                .order_by(Material.created_at.desc())
                .limit(MAX_MATERIALS_IN_CONTEXT)
                .all()
            )
            for item in subject_materials:
                if item.id == (material.id if material is not None else None):
                    continue  # already included above
                if item.extracted_text and item.extracted_text.strip():
                    context.materials.append(
                        ContextMaterial(
                            filename=item.original_filename,
                            excerpt=_material_excerpt(item.extracted_text, question),
                        )
                    )
                if len(context.materials) >= MAX_MATERIALS_IN_CONTEXT:
                    break

            context.web_resources = resource_selection_service.list_selections(
                db,
                user_id,
                subject_id=subject.id,
                limit=MAX_WEB_RESOURCES_IN_CONTEXT,
            )

        context.subject_name = " / ".join(
            dict.fromkeys(name for name in subject_name_parts if name)
        ) or None
        self._enforce_size_limits(context)
        return context

    def _enforce_size_limits(self, context: LearningContext) -> None:
        """Cap the rendered context so AI requests stay bounded."""
        rendered = context.render()
        if len(rendered) <= MAX_CONTEXT_CHARS:
            return
        # Drop web resources first (lowest fidelity), then truncate text.
        while context.web_resources and len(rendered) > MAX_CONTEXT_CHARS:
            context.web_resources.pop()
            rendered = context.render()
        if len(rendered) > MAX_CONTEXT_CHARS:
            kept: list[ContextMaterial] = []
            used = 0
            for material in context.materials:
                excerpt = material.excerpt
                budget = MAX_CONTEXT_CHARS - used
                if budget <= 0:
                    break
                if len(excerpt) > budget:
                    excerpt = excerpt[:budget]
                kept.append(ContextMaterial(material.filename, excerpt))
                used += len(material.filename) + len(excerpt)
            context.materials = kept

    def build_web_resource_context(
        self,
        db: Session,
        user_id: uuid.UUID,
        *,
        subject_id: uuid.UUID,
        limit: int = MAX_WEB_RESOURCES_IN_CONTEXT,
    ) -> tuple[str, list[LearningResourceSelection]]:
        """Render only the subject's web resources (for study plans).

        Returns the rendered text block and the selections, so the caller
        can mark them as used. Empty string when there are no selections.
        """
        selections = resource_selection_service.list_selections(
            db, user_id, subject_id=subject_id, limit=limit
        )
        parts = [
            _render_web_resource(resource, index)
            for index, resource in enumerate(selections, start=1)
        ]
        return "\n\n".join(parts), selections


def _material_excerpt(text: str, question: str) -> str:
    """Retrieve a bounded excerpt of material text for the question."""
    from app.services import ai_service

    if not question:
        return text[:MAX_MATERIAL_EXCERPT_CHARS]
    retrieved = ai_service._retrieve_relevant_chunks(text, question)
    return retrieved[:MAX_MATERIAL_EXCERPT_CHARS]