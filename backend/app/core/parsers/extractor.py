"""Resume document text extraction: PDF and DOCX."""

from __future__ import annotations

import io

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


class UnsupportedFileError(ValueError):
    pass


def extract_pdf_text(data: bytes) -> str:
    import fitz  # PyMuPDF

    doc = fitz.open(stream=data, filetype="pdf")
    pages = [page.get_text("text") for page in doc]
    return "\n".join(pages)


def extract_docx_text(data: bytes) -> str:
    import docx  # python-docx

    doc = docx.Document(io.BytesIO(data))
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells]
            if any(cells):
                parts.append(" | ".join(cells))
    return "\n".join(parts)


def extract_text(data: bytes, filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return extract_pdf_text(data)
    if lower.endswith(".docx"):
        return extract_docx_text(data)
    raise UnsupportedFileError(f"Unsupported file type: {filename}")
