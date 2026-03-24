from enum import Enum

from pydantic import BaseModel, Field


class DocumentKind(str, Enum):
    INVOICE = "invoice"
    CONTRACT = "contract"
    OTHER = "other"
    UNKNOWN = "unknown"


class IngestionStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class IngestionResult(BaseModel):
    job_id: str
    status: IngestionStatus
    original_filename: str
    stored_path: str | None = None
    document_kind: DocumentKind = DocumentKind.UNKNOWN
    kind_confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    needs_ocr: bool = False
    page_count: int | None = None
    rejection_reason: str | None = None
    notes: str | None = None


class ExtractionStatus(str, Enum):
    OK = "ok"
    SKIPPED_OCR = "skipped_ocr"
    FAILED = "failed"


class ExtractedEntities(BaseModel):
    """Эвристики без LLM: кандидаты из текста."""

    inn_candidates: list[str] = Field(default_factory=list)
    date_candidates: list[str] = Field(default_factory=list)
    money_candidates: list[str] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    job_id: str
    status: ExtractionStatus
    document_kind: DocumentKind = DocumentKind.UNKNOWN
    text_char_count: int = 0
    text_preview: str | None = None
    entities: ExtractedEntities | None = None
    rejection_reason: str | None = None
    notes: str | None = None


class MatchStatus(str, Enum):
    OK = "ok"
    NO_MATCH = "no_match"
    SKIPPED = "skipped"
    FAILED = "failed"


class CRMMatchItem(BaseModel):
    inn: str
    company_name: str
    account_manager: str
    segment: str
    source: str = "local_registry"


class MatchingResult(BaseModel):
    job_id: str
    status: MatchStatus
    checked_inn: list[str] = Field(default_factory=list)
    matches: list[CRMMatchItem] = Field(default_factory=list)
    rejection_reason: str | None = None
    notes: str | None = None


class RouteStatus(str, Enum):
    READY_FOR_TEMPLATE = "ready_for_template"
    REVIEW_REQUIRED = "review_required"
    REJECTED = "rejected"
    FAILED = "failed"


class RoutingResult(BaseModel):
    job_id: str
    status: RouteStatus
    queue: str | None = None
    priority: str | None = None
    reasons: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    rejection_reason: str | None = None
    notes: str | None = None


class TemplateStatus(str, Enum):
    READY = "ready"
    SKIPPED = "skipped"
    FAILED = "failed"


class TemplateResult(BaseModel):
    job_id: str
    status: TemplateStatus
    template_path: str | None = None
    rejection_reason: str | None = None
    notes: str | None = None


class EmailSendStatus(str, Enum):
    SENT = "sent"
    FAILED = "failed"


class EmailSendResult(BaseModel):
    job_id: str
    status: EmailSendStatus
    recipient_email: str
    subject: str
    rejection_reason: str | None = None
    notes: str | None = None
