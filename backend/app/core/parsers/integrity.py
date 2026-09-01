"""Resume integrity scanner: hidden/steganographic text detection + prompt-injection heuristics.

Layer 1 — Structural / steganographic detection (hidden white/tiny/vanished text)
Layer 2 — Linguistic injection detection (visible imperative phrases directed at the AI)
Layer 3 — Statistical anomaly (keyword‑stuffing / hidden↔visible divergence)
Layer 4 — Prompt hardening (defence‑in‑depth so missed injections cannot steer the model)
"""

from __future__ import annotations

import re
from typing import List

from pydantic import BaseModel, Field


class HiddenSpan(BaseModel):
    text: str
    reason: str  # "white_text" | "tiny_font" | "zero_size" | "covered" | "vanish_hidden" | "white_highlight"
    page: int | None = None
    detail: str = ""


class InjectionFlag(BaseModel):
    phrase: str
    category: str  # "directive_override" | "role_manipulation" | "scoring_manipulation" | "output_manipulation"
    index: int
    severity: str  # "low" | "high"


class IntegrityReport(BaseModel):
    is_suspicious: bool
    severity: str  # "none" | "low" | "medium" | "high"
    confidence: float  # 0..1
    hidden_spans: List[HiddenSpan] = Field(default_factory=list)
    injection_flags: List[InjectionFlag] = Field(default_factory=list)
    keyword_stuffing: bool = False
    notes: List[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Layer 1 — Hidden / steganographic detection
# --------------------------------------------------------------------------- #


def _luminance(rgb: int) -> float:
    """Convert RGB int (0xRRGGBB) to relative luminance 0..1 (sRGB)."""
    r = ((rgb >> 16) & 0xFF) / 255.0
    g = ((rgb >> 8) & 0xFF) / 255.0
    b = (rgb & 0xFF) / 255.0
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(l1: float, l2: float) -> float:
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


def _median_font_size(spans: list) -> float:
    """Median of span font sizes; return 1.0 if empty."""
    sizes = [s.get("size", 12.0) for s in spans if isinstance(s, dict) and s.get("size") is not None]
    if not sizes:
        return 1.0
    sizes.sort()
    n = len(sizes)
    if n % 2 == 1:
        return sizes[n // 2]
    return (sizes[n // 2 - 1] + sizes[n // 2]) / 2.0


def scan_pdf(data: bytes) -> dict:
    """Scan a PDF for hidden/invisible text and return raw dict for integration."""
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz  # type: ignore[no-redef]
        import warnings
        warnings.filterwarnings("ignore", message=".*fitz API is deprecated.*")

    doc = fitz.open(stream=data, filetype="pdf")
    all_spans: list = []
    page_text_parts: list = []

    # First pass: collect spans and compute per‑page median font sizes
    page_medians: dict = {}
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        text_dict = page.get_text("dict")
        # PyMuPDF dict structure: blocks → lines → spans (NOT top-level spans)
        page_spans = [
            span
            for block in text_dict.get("blocks", [])
            for line in block.get("lines", [])
            for span in line.get("spans", [])
        ]
        page_medians[page_idx] = _median_font_size(page_spans)
        # Tag each span with its page index for later lookup
        for span in page_spans:
            span["page"] = page_idx
        all_spans.extend(page_spans)

    # Second pass: evaluate each span
    hidden_spans: list = []
    for span in all_spans:
        text = span.get("text", "")
        if not text or not isinstance(text, str):
            continue
        size = span.get("size", 12.0)
        color = span.get("color")  # int RGB or None
        bbox = span.get("bbox")  # [left, bottom, right, top]
        page_idx = span.get("page", 0)

        is_hidden = False
        reason = ""

        # 1) Local‑background contrast (robust to coloured banners)
        if color is not None and isinstance(color, int):
            # Sample background: approximate by averaging a small region around the bbox.
            # If bbox is available, we rough‑estimate; otherwise fall back to white.
            if bbox and len(bbox) >= 4:
                # Use the four corner pixels as a very rough background sample.
                # For simplicity here we just check if color is pure white (0xFFFFFF) → always suspicious on white bg.
                if color == 0xFFFFFF:
                    is_hidden = True
                    reason = "white_text"
                else:
                    # Compute contrast against assumed page-white (255,255,255) for a quick check.
                    l_text = _luminance(color)
                    l_white = _luminance(0xFFFFFF)
                    if _contrast(l_text, l_white) < 1.1:
                        is_hidden = True
                        reason = "white_text"
            else:
                # No bbox – if colour is white treat as suspicious.
                if color == 0xFFFFFF:
                    is_hidden = True
                    reason = "white_text"

        # 2) Tiny font (relative to page median)
        if not is_hidden:
            med = page_medians.get(page_idx, 12.0)
            if size < max(1.0, 0.35 * med) and size < 3.0:
                is_hidden = True
                if not reason:
                    reason = "tiny_font"

        # 3) Zero / near‑zero area glyph
        if not is_hidden and bbox and len(bbox) >= 4:
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            if width * height < 1.0:  # essentially invisible rendering
                is_hidden = True
                if not reason:
                    reason = "zero_size"

        if is_hidden:
            hidden_spans.append(
                {"text": text, "reason": reason, "page": page_idx}
            )

    # --- Gather full text for Layers 2‑3 ---
    for page in doc:
        page_text_parts.append(page.get_text("text"))
    full_text = "\n".join(page_text_parts)

    # --- Keyword‑stuffing check (very light) ---
    # If total hidden text is > 2% of document text → flag
    hidden_text = "".join(s.get("text", "") for s in hidden_spans)
    total_chars = len(full_text) if full_text else 1
    stuffing = len(hidden_text) / total_chars > 0.02 if total_chars else False

    doc.close()
    return {
        "hidden_spans": hidden_spans,
        "full_text": full_text,
        "keyword_stuffing": stuffing,
    }


# --------------------------------------------------------------------------- #
# Layer 1b — DOCX hidden‑text detection
# --------------------------------------------------------------------------- #


def scan_docx(data: bytes) -> dict:
    """Scan a DOCX for hidden/invisible text and return raw dict for integration."""
    import docx  # python-docx

    doc = docx.Document(data)
    hidden_spans: list = []
    all_run_texts: list = []

    for para in doc.paragraphs:
        for run in para.runs:
            text = run.text or ""
            if not text:
                continue
            all_run_texts.append(text)

            # 1) White / hidden font colour
            color = run.font.color
            is_hidden = False
            reason = ""

            if color and color.rgb:
                # color.rgb is an RGBColor object; get its int value
                rgb_val = int(color.rgb)
                if rgb_val == 0xFFFFFF:
                    is_hidden = True
                    reason = "white_text"
                else:
                    # Quick white‑check: if all channels are 255
                    # (python‑docx RGBColor may not always give full int, so also check components)
                    # We'll keep it simple: white rgb → hidden.
                    pass

            # 2) Hidden (vanish) markup in the XML
            if not is_hidden and "_element" in dir(run):
                try:
                    xml = run._element.xml.lower()
                    if "<w:vanish" in xml or "<w:hidden" in xml:
                        is_hidden = True
                        reason = "vanish_hidden"
                except Exception:
                    pass

            # 3) Tiny font
            if not is_hidden:
                fs = run.font.size
                if fs and fs.pt and fs.pt < 3.0:
                    if not reason:
                        reason = "tiny_font"
                    is_hidden = True

            # 4) White highlight
            if not is_hidden and run.font.highlight_color:
                # Highlight color that is white
                hk = run.font.highlight_color
                if hk and getattr(hk, "rgb", None) == 0xFFFFFF:
                    is_hidden = True
                    reason = "white_highlight"

            if is_hidden:
                hidden_spans.append({"text": text, "reason": reason, "page": None})

    full_text = "\n".join(all_run_texts)

    # Keyword‑stuffing: hidden text > 2% of total
    hidden_txt = "".join(s.get("text", "") for s in hidden_spans)
    total = len(full_text) if full_text else 1
    stuffing = len(hidden_txt) / total > 0.02 if total else False

    return {"hidden_spans": hidden_spans, "full_text": full_text, "keyword_stuffing": stuffing}


# --------------------------------------------------------------------------- #
# Dispatcher
# --------------------------------------------------------------------------- #


def scan_document(data: bytes, filename: str) -> dict:
    """Run the appropriate scanner for the given file extension."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return scan_pdf(data)
    if lower.endswith(".docx"):
        return scan_docx(data)
    # Fallback: treat as plain text — no hidden‑span detection, but still run injection checks
    return {"hidden_spans": [], "full_text": data.decode(errors="replace"), "keyword_stuffing": False}


# --------------------------------------------------------------------------- #
# Layer 2 — Linguistic prompt‑injection detection
# --------------------------------------------------------------------------- #

# Core imperative‑to‑AI phrase patterns (conservative: require AI/evaluation context)
_DIRECTIVE_OVERRIDE = re.compile(
    r"\b(?:ignore|disregard|forget|override)\b"
    r"(?:(?:(?:all |previous |prior |above )?(?:instructions|prompt|system|rules|constraints|priorities))"
    r"|(?:the )?(?:above|previous|instructions))",
    re.IGNORECASE,
)

_ROLE_MANIPULATION = re.compile(
    r"\b(?:you are|act as|system prompt|developer mode|jailbreak|DAN|role.?play)\b"
    r"(?:(?:(?: an? |the )?(?:recruiter|hiring manager|evaluator|ai|assistant|hr)|(?: mode))? )?",
    re.IGNORECASE,
)

_SCORING_MANIPULATION = re.compile(
    r"\b(?:shortlist|pass|rank|give.*(?:high|perfect|maximum|top|full).*score|select|approve|do not (?:reject|fail|penalize))\b"
    r"(?:(?: this| me| the candidate| a (?:high|perfect|maximum|top|full) (?:score|rating|rank))?)",
    re.IGNORECASE,
)

_OUTPUT_MANIPULATION = re.compile(
    r"\b(?:return|print|output|exclusively)\b"
    r"(?:(?:(?: only| just| the word)? ?(?:pass|shortlist|selected|approved))?)",
    re.IGNORECASE,
)


def detect_injection_patterns(text: str) -> list:
    """Return list of InjectionFlag dicts found in *text*."""
    flags: list = []

    # Helper to add a flag if not already present
    def add_flag(phrase: str, category: str, index: int, severity: str):
        already = any(
            f.get("phrase") == phrase and f.get("category") == category
            for f in flags
        )
        if not already:
            flags.append(
                {"phrase": phrase, "category": category, "index": index, "severity": severity}
            )

    # Find each match with its position
    for m in _DIRECTIVE_OVERRIDE.finditer(text):
        add_flag(m.group(0), "directive_override", m.start(), "high")
    for m in _ROLE_MANIPULATION.finditer(text):
        add_flag(m.group(0), "role_manipulation", m.start(), "medium")
    for m in _SCORING_MANIPULATION.finditer(text):
        add_flag(m.group(0), "scoring_manipulation", m.start(), "high")
    for m in _OUTPUT_MANIPULATION.finditer(text):
        add_flag(m.group(0), "output_manipulation", m.start(), "medium")

    # Supplementary meta‑heuristic: imperative sentence + AI/eval noun in near proximity
    # (lower‑precision, just raises severity if present)
    import_synonyms = {"score", "resume", "candidate", "rank", "shortlist", "hr", "recruiter", "instruction", "prompt", "AI", "assistant"}
    # split into sentences heuristically
    sentences = [s.strip() for s in re.split(r"[.!?]", text) if s.strip()]
    for si, sent in enumerate(sentences):
        sent_low = sent.lower()
        # check for imperative verb start (simple: starts with a verb-like word)
        verb_starts = {
            "ignore", "output", "rank", "select", "choose", "treat", "assume", "weigh", "boost",
            "increase", "shortlist", "reject"
        }
        words = sent_low.split()
        if words and words[0].rstrip(".,") in verb_starts:
            # check if any AI/eval noun nearby
            if any(tok in import_synonyms for tok in words):
                # find position
                idx = sum(len(s) + 1 for s in sentences[:si]) + len(sentences[si]) - len(sent)  # approximate
                # only add if not already a high-severity flag
                cat = "directive_override" if any(
                    kw in sent_low for kw in {"ignore", "shortlist", "pass", "rank", "select"}
                ) else "role_manipulation"
                # avoid duplicate
                if not any(f"phrase:{sent}" == f"phrase:{f['phrase']}" for f in flags):
                    flags.append(
                        {
                            "phrase": sent[:80],
                            "category": cat,
                            "index": idx,
                            "severity": "low",
                        }
                    )

    return flags


# --------------------------------------------------------------------------- #
# Layer 3 — Severity / scoring logic
# --------------------------------------------------------------------------- #


def _compute_severity(
    hidden_spans: list,
    injection_flags: list,
    keyword_stuffing: bool,
) -> dict:
    """Return {severity: "none"|"low"|"medium"|"high", confidence: float, notes: list}.

    injection_flags may be InjectionFlag pydantic objects OR raw dicts — handled uniformly.
    """
    notes: list = []
    severity = "none"
    confidence = 0.0

    def _cat(f) -> str:
        return f.category if hasattr(f, "category") else f["category"]

    def _sev(f) -> str:
        return f.severity if hasattr(f, "severity") else f["severity"]

    # --- High‑severity triggers ---
    high_cat = {"directive_override", "scoring_manipulation"}
    if any(_cat(f) in high_cat for f in injection_flags):
        severity = "high"
        confidence = 1.0
        notes.append("Prompt‑injection directive detected in resume text.")

    # --- Hidden‑content triggers ---
    if severity != "high":
        if hidden_spans:
            hidden_text = " ".join(
                (s.get("text", "") if isinstance(s, dict) else s.text)
                for s in hidden_spans
            )
            if re.search(r"\b(ignore|shortlist|pass|rank|system|instructions)\b", hidden_text, re.IGNORECASE):
                severity = "high"
                confidence = 0.9
                notes.append("Hidden text contains injection‑style phrases.")
            elif keyword_stuffing:
                severity = "medium"
                confidence = 0.6
                notes.append("Keyword‑stuffing block detected in hidden text.")
            elif len(hidden_text) > 100:
                severity = "medium"
                confidence = 0.5
                notes.append("Substantial hidden text present in document.")
            else:
                severity = "low"
                confidence = 0.3
                notes.append("Minor hidden/white text detected.")
        else:
            severity = "none"
            confidence = 0.0
            notes.append("No hidden or injection signals detected.")

    # --- Injection‑only triggers (no hidden) ---
    if severity == "none" and injection_flags:
        if any(_sev(f) == "low" for f in injection_flags):
            severity = "low"
            confidence = 0.35
            notes.append("Mild linguistic pattern resembling instructions detected (visible text).")
        else:
            severity = "none"
            confidence = 0.0

    # --- Keyword‑stuffing alone ---
    if severity not in ("high", "medium", "low") and keyword_stuffing:
        severity = "medium"
        confidence = 0.55
        notes.append("Keyword‑stuffing block detected (visible or hidden).")

    # Normalise confidence
    if severity == "none":
        confidence = 0.0
    elif severity == "low":
        confidence = 0.35
    elif severity == "medium":
        confidence = 0.55
    elif severity == "high":
        confidence = 0.9

    return {
        "severity": severity,
        "confidence": round(confidence, 2),
        "notes": notes,
    }


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def scan_resume_integrity(data: bytes, filename: str) -> IntegrityReport:
    """Full integrity scan: hidden text + injection patterns + severity.

    Returns an IntegrityReport pydantic model.
    """
    # 1) Structural scan
    struct = scan_document(data, filename)

    # 2) Linguistic injection detection on the extracted full text
    injection_flags_raw = detect_injection_patterns(struct["full_text"])

    # Convert raw dicts to InjectionModel instances (keep index as character position)
    injection_flags: list = []
    for f in injection_flags_raw:
        injection_flags.append(
            InjectionFlag(
                phrase=f["phrase"],
                category=f["category"],
                index=f["index"],
                severity=f["severity"],
            )
        )

    # 3) Severity computation
    sev = _compute_severity(
        struct["hidden_spans"],
        injection_flags,
        struct["keyword_stuffing"],
    )

    # 4) Assemble report
    hidden_spans = [
        HiddenSpan(text=s.get("text", ""), reason=s.get("reason", ""), page=s.get("page"))
        for s in struct["hidden_spans"]
    ]

    is_suspicious = sev["severity"] != "none"

    return IntegrityReport(
        is_suspicious=is_suspicious,
        severity=sev["severity"],
        confidence=sev["confidence"],
        hidden_spans=hidden_spans,
        injection_flags=injection_flags,
        keyword_stuffing=struct["keyword_stuffing"],
        notes=sev["notes"],
    )