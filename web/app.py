import re
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from starlette.requests import Request

from agents.extract.agent import run_extract, run_extract_by_job_id
from agents.intake.agent import run_intake
from agents.match.agent import run_match_by_job_id
from agents.route.agent import run_route_by_job_id
from agents.template.agent import run_template_by_job_id, send_template_by_job_id
from core.schemas import EmailSendStatus, ExtractionResult, ExtractionStatus, IngestionResult, IngestionStatus, MatchStatus, RouteStatus

WEB_DIR = Path(__file__).resolve().parent
STATIC_DIR = WEB_DIR / "static"
# Обновление mtime → uvicorn --reload-include (см. web/run_web.py)
RELOAD_TRIGGER = WEB_DIR / "reload.trigger"


class ExtractJobBody(BaseModel):
    job_id: str = Field(min_length=1)


class MatchJobBody(BaseModel):
    job_id: str = Field(min_length=1)


class RouteJobBody(BaseModel):
    job_id: str = Field(min_length=1)


class TemplateJobBody(BaseModel):
    job_id: str = Field(min_length=1)


class SendTemplateBody(BaseModel):
    job_id: str = Field(min_length=1)
    recipient_email: str = Field(min_length=5)


def _ingestion_accepted(result: IngestionResult) -> bool:
    """Сравнение со статусом без зависимости от одного экземпляра Enum (reload/дубликаты импорта)."""
    s = result.status
    if s == IngestionStatus.ACCEPTED:
        return True
    return getattr(s, "value", s) == IngestionStatus.ACCEPTED.value


app = FastAPI(title="Document pipeline — web UI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(
        STATIC_DIR / "index.html",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.post("/api/intake")
async def intake_upload(file: UploadFile = File(...)) -> JSONResponse:
    raw_name = file.filename or "upload"
    stem = Path(raw_name).stem or "upload"
    stem_safe = re.sub(r"[^\w\-]+", "_", stem, flags=re.UNICODE).strip("_")[:48] or "upload"
    suffix = Path(raw_name).suffix.lower() or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix=f"{stem_safe}_") as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)
    try:
        result = run_intake(tmp_path)
        payload = result.model_dump(mode="json")
        ext_payload: dict | None = None
        if _ingestion_accepted(result):
            # Не читаем intake.json повторно: тот же процесс только что записал файл —
            # на Windows иногда гонка/кэш даёт «файла нет», load_intake_result → None.
            try:
                ext = run_extract(result)
                ext_payload = ext.model_dump(mode="json")
            except Exception as exc:  # noqa: BLE001 — отдаём JSON, а не 500 без extract
                ext_payload = ExtractionResult(
                    job_id=result.job_id,
                    status=ExtractionStatus.FAILED,
                    document_kind=result.document_kind,
                    rejection_reason="extract_exception",
                    notes=str(exc),
                ).model_dump(mode="json")
        return JSONResponse({"intake": payload, "extract": ext_payload})
    finally:
        tmp_path.unlink(missing_ok=True)


@app.post("/api/extract")
@app.post("/api/extract/")
async def extract_by_job(body: ExtractJobBody) -> JSONResponse:
    result = run_extract_by_job_id(body.job_id.strip())
    if result is None:
        return JSONResponse({"error": "job_not_found", "detail": "Нет каталога или intake.json"}, status_code=404)
    return JSONResponse(result.model_dump(mode="json"))


@app.post("/api/match")
@app.post("/api/match/")
async def match_by_job(body: MatchJobBody) -> JSONResponse:
    result = run_match_by_job_id(body.job_id.strip())
    if result is None:
        return JSONResponse({"error": "job_not_found", "detail": "Нет каталога или extraction.json"}, status_code=404)
    if result.status == MatchStatus.FAILED:
        return JSONResponse(result.model_dump(mode="json"), status_code=500)
    return JSONResponse(result.model_dump(mode="json"))


@app.post("/api/route")
@app.post("/api/route/")
async def route_by_job(body: RouteJobBody) -> JSONResponse:
    result = run_route_by_job_id(body.job_id.strip())
    if result is None:
        return JSONResponse(
            {"error": "job_not_found", "detail": "Нет каталога или extraction/matching manifest"},
            status_code=404,
        )
    if result.status == RouteStatus.FAILED:
        return JSONResponse(result.model_dump(mode="json"), status_code=500)
    return JSONResponse(result.model_dump(mode="json"))


@app.post("/api/template")
@app.post("/api/template/")
async def template_by_job(body: TemplateJobBody) -> JSONResponse:
    result = run_template_by_job_id(body.job_id.strip())
    if result is None:
        return JSONResponse(
            {"error": "job_not_found", "detail": "Нет каталога или extraction/matching/routing manifest"},
            status_code=404,
        )
    return JSONResponse(result.model_dump(mode="json"))


@app.post("/api/send-template")
@app.post("/api/send-template/")
async def send_template(body: SendTemplateBody) -> JSONResponse:
    recipient = body.recipient_email.strip()
    if "@" not in recipient or "." not in recipient.split("@")[-1]:
        return JSONResponse({"error": "invalid_email", "detail": "Укажите корректный email"}, status_code=400)
    result = send_template_by_job_id(body.job_id.strip(), recipient)
    if result is None:
        return JSONResponse(
            {"error": "job_not_found", "detail": "Нет template.json или prepared_document.txt"},
            status_code=404,
        )
    if result.status != EmailSendStatus.SENT:
        return JSONResponse(result.model_dump(mode="json"), status_code=500)
    return JSONResponse(result.model_dump(mode="json"))


@app.middleware("http")
async def reload_server_on_index_refresh(request: Request, call_next):
    """
    При F5 на главной: касание web/reload.trigger, чтобы сработал uvicorn --reload-include.
    Не трогаем: urllib из run_web.py, первый заход без Referer, fetch/XHR (не navigate).
    """
    response = await call_next(request)
    if request.method != "GET" or request.url.path != "/":
        return response
    accept = (request.headers.get("accept") or "").lower()
    if "text/html" not in accept:
        return response
    ua = request.headers.get("user-agent") or ""
    if ua.startswith("Python-urllib") or ua.startswith("curl/"):
        return response
    if request.headers.get("sec-fetch-mode") != "navigate":
        return response
    if not request.headers.get("referer"):
        return response
    try:
        RELOAD_TRIGGER.parent.mkdir(parents=True, exist_ok=True)
        RELOAD_TRIGGER.touch(exist_ok=True)
    except OSError:
        pass
    return response
