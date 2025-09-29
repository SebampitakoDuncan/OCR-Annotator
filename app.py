import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling_core.types.doc.document import DoclingDocument

# UI components
from monsterui.core import fast_app, Theme
from fasthtml.common import (
    Div,
    H1,
    H2,
    H3,
    P,
    Form,
    Input,
    Button,
    Textarea,
    Redirect,
)


BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
FEEDBACK_DIR = BASE_DIR / "static" / "feedback"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class AnnotatedDocument:
    doc_id: str
    filename: str
    text: str
    uploaded_at: datetime


converter = DocumentConverter(allowed_formats=[InputFormat.IMAGE, InputFormat.PDF])


def extract_text_from_docling(document: DoclingDocument) -> str:
    plain_text = document.export_to_text()
    return plain_text.strip()


def save_feedback(doc_id: str, filename: str, text: str, feedback: str) -> Path:
    payload: Dict[str, str] = {
        "document_id": doc_id,
        "filename": filename,
        "extracted_text": text,
        "feedback": feedback,
        "timestamp": datetime.utcnow().isoformat(),
    }
    output_path = FEEDBACK_DIR / f"{doc_id}.json"
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def list_feedback_entries() -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    for item in FEEDBACK_DIR.glob("*.json"):
        try:
            entries.append(json.loads(item.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    entries.sort(key=lambda entry: entry.get("timestamp", ""), reverse=True)
    return entries


def convert_upload_to_text(file_path: Path) -> AnnotatedDocument:
    doc_id = uuid.uuid4().hex
    result = converter.convert(file_path)
    text_content = extract_text_from_docling(result.document)
    return AnnotatedDocument(
        doc_id=doc_id,
        filename=file_path.name,
        text=text_content,
        uploaded_at=datetime.utcnow(),
    )


app, rt = fast_app(title="Receipt OCR Annotator", hdrs=Theme.zinc.headers())


@rt("/")
async def index(request):
    entries = list_feedback_entries()
    return Div(
        H1("Receipt OCR Annotator", cls="text-3xl mb-6 font-semibold", style="font-family: 'Avenir', sans-serif"),
        Form(
            Input(type="file", name="receipt", accept="image/*,.pdf", cls="file-input file-input-bordered w-full"),
            Button("Run OCR", type="submit", cls="btn btn-primary mt-4"),
            method="post",
            enctype="multipart/form-data",
            action="/upload",
            cls="card bg-base-200 shadow-xl p-6 gap-4"
        ),
        H2("Recent Feedback", cls="text-2xl mt-10 mb-4"),
        Div(
            *[
                Div(
                    H3(entry.get("filename", "Unknown"), cls="font-semibold"),
                    P(f"Submitted: {entry.get('timestamp', 'N/A')}", cls="text-sm opacity-70"),
                    P(entry.get("feedback", ""), cls="mt-3"),
                    cls="card bg-base-200 shadow-md p-4"
                )
                for entry in entries
            ] if entries else P("No feedback saved yet.", cls="opacity-70"),
            cls="grid gap-4"
        ),
        cls="max-w-3xl mx-auto py-10 flex flex-col gap-6"
    )


@rt("/upload", methods=["POST"])
async def upload(request):
    form = await request.form()
    receipt = form.get("receipt")
    if receipt is None or not receipt.filename:
        return Redirect("/" )

    file_path = UPLOAD_DIR / receipt.filename
    file_path.write_bytes(await receipt.read())

    document = convert_upload_to_text(file_path)

    return Div(
        H1("Review OCR Output", cls="text-3xl font-semibold mb-6", style="font-family: 'Avenir', sans-serif"),
        Div(
            Textarea(document.text, name="extracted_text", readonly=True, cls="textarea textarea-bordered h-96 w-full bg-base-200"),
            Form(
                Input(type="hidden", name="doc_id", value=document.doc_id),
                Input(type="hidden", name="filename", value=document.filename),
                Textarea(name="feedback", placeholder="Provide expert feedback...", cls="textarea textarea-bordered h-96 w-full"),
                Button("Save Feedback", type="submit", cls="btn btn-success"),
                method="post",
                action="/feedback",
                cls="flex flex-col gap-4 w-full"
            ),
            cls="grid md:grid-cols-2 gap-8"
        ),
        Button("Back", hx_get="/", cls="btn btn-ghost mt-6"),
        cls="max-w-5xl mx-auto py-10 flex flex-col"
    )


@rt("/feedback", methods=["POST"])
async def feedback(request):
    form = await request.form()
    doc_id = form.get("doc_id", "")
    filename = form.get("filename", "")
    text = form.get("extracted_text", "")
    feedback_text = form.get("feedback", "").strip()

    if doc_id and filename and feedback_text:
        save_feedback(doc_id, filename, text, feedback_text)

    return Redirect("/")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

