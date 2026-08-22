"""Premium PDF rendering of the Candidate Report (reportlab platypus).

Sections: Candidate Overview, Resume Summary, Skills Breakdown, Technical
Verification, GitHub Analysis, Coding Platform Analysis, Project Verification,
Achievement Verification, Strengths, Improvement Areas, AI Summary, Final Scores
(progress bars + radar chart).
"""

from __future__ import annotations

import math
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    Flowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ...models.analysis import AnalysisBundle
from ...models.report import CandidateReport

INDIGO = colors.HexColor("#5B5BD6")
INDIGO_DARK = colors.HexColor("#4338CA")
INK = colors.HexColor("#0F172A")
MUTED = colors.HexColor("#64748B")
BORDER = colors.HexColor("#E2E8F0")
BG = colors.HexColor("#F8FAFC")
EMERALD = colors.HexColor("#10B981")
AMBER = colors.HexColor("#F59E0B")
ROSE = colors.HexColor("#F43F5E")
SLATE = colors.HexColor("#94A3B8")

STATUS_COLORS = {
    "verified": EMERALD,
    "strong_evidence": colors.HexColor("#34D399"),
    "partial_evidence": AMBER,
    "limited_evidence": colors.HexColor("#FB923C"),
    "no_public_evidence": SLATE,
}

STATUS_LABEL = {
    "verified": "Verified",
    "strong_evidence": "Strong Evidence",
    "partial_evidence": "Partial Evidence",
    "limited_evidence": "Limited Evidence",
    "no_public_evidence": "No Public Evidence",
}


def _styles() -> dict:
    s = {}
    s["h1"] = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=INK, spaceAfter=2)
    s["subtitle"] = ParagraphStyle("subtitle", fontName="Helvetica", fontSize=10, leading=14, textColor=MUTED)
    s["section"] = ParagraphStyle("section", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=INDIGO_DARK, spaceBefore=14, spaceAfter=6)
    s["body"] = ParagraphStyle("body", fontName="Helvetica", fontSize=9, leading=13, textColor=INK)
    s["small"] = ParagraphStyle("small", fontName="Helvetica", fontSize=7.5, leading=10.5, textColor=MUTED)
    s["cell"] = ParagraphStyle("cell", fontName="Helvetica", fontSize=8.5, leading=12, textColor=INK)
    s["cellb"] = ParagraphStyle("cellb", fontName="Helvetica-Bold", fontSize=8.5, leading=12, textColor=INK)
    s["score"] = ParagraphStyle("score", fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=INDIGO_DARK)
    return s


class ProgressBar(Flowable):
    def __init__(self, value: float, width: float = 110, height: float = 7, color=INDIGO) -> None:
        super().__init__()
        self.value = max(0.0, min(100.0, value))
        self.bar_w = width
        self.bar_h = height
        self.color = color

    def wrap(self, *args):
        return (self.bar_w, self.bar_h)

    def draw(self) -> None:
        c = self.canv
        c.setFillColor(BORDER)
        c.roundRect(0, 0, self.bar_w, self.bar_h, self.bar_h / 2, stroke=0, fill=1)
        w = max(self.bar_h, self.bar_w * self.value / 100.0)
        c.setFillColor(self.color)
        c.roundRect(0, 0, w, self.bar_h, self.bar_h / 2, stroke=0, fill=1)


class StatusBadge(Flowable):
    def __init__(self, status: str, scale: float = 1.0) -> None:
        super().__init__()
        self.status = status
        self.label = STATUS_LABEL.get(status, status.replace("_", " "))
        self.color = STATUS_COLORS.get(status, SLATE)
        self.scale = scale

    def wrap(self, *args):
        w = stringWidth(self.label, "Helvetica-Bold", 7.5) + 10
        return (w * self.scale, 12 * self.scale)

    def draw(self) -> None:
        c = self.canv
        w, h = self.wrap()
        c.setFillColor(self.color)
        c.roundRect(0, 0, w, h, 3, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 7.5 * self.scale)
        c.drawCentredString(w / 2, (h - 8) / 2, self.label)


class RadarChart(Flowable):
    """10-axis radar (spider) chart drawn with reportlab graphics."""

    def __init__(self, items: list[tuple[str, float]], size: float = 150, max_value: float = 100.0) -> None:
        super().__init__()
        self.items = items
        self.size = size
        self.max_value = max_value

    def wrap(self, *args):
        return (self.size, self.size)

    def draw(self) -> None:
        c = self.canv
        cx = cy = self.size / 2
        r = self.size / 2 - 12
        n = len(self.items)
        if n < 3:
            return
        c.saveState()
        for ring in (0.25, 0.5, 0.75, 1.0):
            c.setStrokeColor(BORDER, alpha=0.8)
            c.setLineWidth(0.5)
            pts = [(cx + r * ring * math.cos(2 * math.pi * i / n - math.pi / 2),
                    cy + r * ring * math.sin(2 * math.pi * i / n - math.pi / 2)) for i in range(n)]
            c.setFillAlpha(0.0)
            p = c.beginPath()
            p.moveTo(*pts[0])
            for pt in pts[1:]:
                p.lineTo(*pt)
            p.close()
            c.drawPath(p, stroke=1, fill=0)
        # axes + labels
        c.setFont("Helvetica", 6)
        for i, (label, value) in enumerate(self.items):
            ang = 2 * math.pi * i / n - math.pi / 2
            x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
            c.setStrokeColor(BORDER)
            c.setLineWidth(0.5)
            c.line(cx, cy, x, y)
            lx, ly = cx + (r + 10) * math.cos(ang), cy + (r + 10) * math.sin(ang)
            c.setFillColor(MUTED)
            c.drawCentredString(lx, ly - 2, label[:12])
        # data polygon
        norm = max(self.max_value, 1)
        c.setFillColor(INDIGO)
        c.setFillAlpha(0.22)
        c.setStrokeColor(INDIGO_DARK)
        c.setLineWidth(1.4)
        pts = []
        for i, (_, value) in enumerate(self.items):
            ang = 2 * math.pi * i / n - math.pi / 2
            rr = r * min(1.0, value / norm)
            pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
        p = c.beginPath()
        p.moveTo(*pts[0])
        for pt in pts[1:]:
            p.lineTo(*pt)
        p.close()
        c.drawPath(p, stroke=1, fill=1)
        c.setFillAlpha(1.0)
        c.restoreState()


def _section_header(name: str) -> Flowable:
    st = _styles()["section"]
    return Paragraph(name, st)


def _table(rows: list[list], col_widths: list[float], header: bool = True, zebra: bool = True) -> Table:
    t = Table(rows, colWidths=col_widths, hAlign="LEFT")
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, BORDER),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), BG), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    if zebra:
        style += [("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG])]
    t.setStyle(TableStyle(style))
    return t


def _score_cell(value: float) -> Flowable:
    return ProgressBar(value, 110)


def render_pdf(report) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=12 * mm, bottomMargin=12 * mm, title="100x Resume — Candidate Report")
    st = _styles()
    story: list[Flowable] = []
    a = report.analysis
    p = a.resume.personal
    scores = {s.key: s for s in a.scores}

    # ---------- Header ----------
    story.append(Paragraph(p.name or "Candidate", st["h1"]))
    headline = p.headline or (a.resume.experience[0].position if a.resume.experience else "")
    story.append(Paragraph(headline or "Candidate Verification Report", st["subtitle"]))
    story.append(Spacer(1, 4))
    meta = " | ".join(x for x in [p.email, p.phone, p.location] if x)
    story.append(Paragraph(meta, st["subtitle"]))
    story.append(Spacer(1, 8))
    story.append(ProgressBar(a.overall_score, width=180, height=10, color=EMERALD if a.overall_score >= 60 else AMBER))
    story.append(Paragraph(f"Overall Candidate Score — {round(a.overall_score)}/100", st["small"]))
    story.append(PageBreak())

    # ---------- 1. Candidate Overview ----------
    story.append(_section_header("1. Candidate Overview"))
    edu = a.resume.education[0] if a.resume.education else None
    rows = [["Name", p.name or "—"], ["Email", p.email or "—"], ["Phone", p.phone or "—"],
            ["Location", p.location or "—"]]
    if edu:
        rows.append(["Education", f"{edu.degree or 'Degree'} — {edu.branch or ''} @ {edu.college or 'College'} ({edu.graduation_year or ''}) GPA {edu.gpa or ''}".replace("  ", " ")])
    for e in a.resume.experience[:2]:
        comp_str = f" @ {e.company}" if e.company else ""
        rows.append(["Experience", f"{e.position or ''}{comp_str} ({e.duration or ''})"])
    links = [x for x in [p.linkedin and Paragraph(f"LinkedIn: {p.linkedin}", st["small"]).getPlainText(), p.github, p.portfolio] if x]
    rows.append(["Contact Links", ", ".join(links) if links else "—"])
    story.append(_table([[Paragraph(c, st["cellb"]), Paragraph(str(v), st["cell"])] for c, v in rows], [28 * mm, 145 * mm]))

    # ---------- 2. Resume Summary ----------
    story.append(_section_header("2. Resume Summary"))
    experiences = a.resume.experience
    current_exp = next((e for e in experiences if e.is_current), None)
    past_exps = [e for e in experiences if not e.is_current]

    def _fmt_exp(e: Experience) -> str:
        pos = e.position or "Unknown Role"
        comp = e.company
        return f"{pos} @ {comp}" if comp else pos

    if current_exp:
        exp_brief = f"Currently: {_fmt_exp(current_exp)}"
        if past_exps:
            exp_brief += ". Past: " + "; ".join(_fmt_exp(e) for e in past_exps)
    else:
        exp_brief = "; ".join(_fmt_exp(e) for e in experiences[:3]) or "No experience listed"

    skills_brief = ", ".join(a.resume.all_skill_names()[:14])
    proj_brief = "; ".join(pr.name or "" for pr in a.resume.projects[:4]) or "No projects listed"
    story.append(Paragraph(
        f"{p.name or 'The candidate'} is a {len(experiences)}-role professional ({exp_brief}). "
        f"Skills include {skills_brief}. Portfolio projects: {proj_brief}.",
        st["body"]))

    # ---------- 3. Skills Breakdown ----------
    story.append(_section_header("3. Skills Breakdown"))
    for field, label in [("programming_languages", "Programming Languages"), ("frontend", "Frontend"),
                         ("backend", "Backend"), ("databases", "Databases"), ("devops", "DevOps"),
                         ("cloud", "Cloud"), ("ai_ml", "AI / ML"), ("mobile", "Mobile"),
                         ("tools", "Tools"), ("testing", "Testing"), ("other", "Other")]:
        vals = getattr(a.resume.skills, field)
        if vals:
            story.append(Paragraph(f"<b>{label}:</b> {', '.join(vals)}", st["body"]))

    # ---------- 4. Technical Verification ----------
    story.append(_section_header("4. Technical Verification"))
    rows = [["Technology", "Category", "Confidence", "Status"]]
    for v in a.skill_verifications:
        rows.append([Paragraph(v.technology, st["cell"]), Paragraph(v.category.replace("_", " "), st["cell"]),
                     _score_cell(v.confidence * 100), StatusBadge(v.status.value)])
    story.append(_table(rows, [32 * mm, 30 * mm, 55 * mm, 45 * mm]))

    # ---------- 5. GitHub Analysis ----------
    story.append(_section_header("5. GitHub Analysis"))
    if a.github:
        g = a.github
        story.append(Paragraph(
            f"@{g.username} — {g.public_repos} public repositories, {g.total_stars} stars, {g.total_forks} forks, "
            f"{g.followers} followers. CI on {g.repos_with_ci} repos, Docker on {g.repos_with_docker}, "
            f"READMEs on {g.repos_with_readme} (avg quality {round(g.avg_readme_quality * 100)}%).", st["body"]))
        story.append(Spacer(1, 4))
        rows = [["Metric", "Value", "Score", ""]]
        for label, key in [("Engineering", "score_engineering"), ("Repository Quality", "score_repo_quality"),
                           ("Open Source", "score_open_source"), ("Documentation", "score_documentation")]:
            val = getattr(g, key)
            rows.append([Paragraph(label, st["cellb"]), Paragraph(str(round(val)), st["cell"]), _score_cell(val), Paragraph("", st["cell"])])
        story.append(_table(rows, [40 * mm, 20 * mm, 60 * mm, 40 * mm]))
        story.append(Spacer(1, 5))
        rows = [["Repository", "Stars", "Forks", "Commits", "README", "CI", "Docker"]]
        for r in g.repos[:8]:
            rows.append([Paragraph(r.name, st["cell"]), str(r.stars), str(r.forks), str(r.commits_count),
                         f"{round(r.readme_quality * 100)}%" if r.has_readme else "—",
                         "✓" if r.has_ci else "—", "✓" if r.has_dockerfile else "—"])
        story.append(_table(rows, [45 * mm, 18 * mm, 18 * mm, 20 * mm, 22 * mm, 16 * mm, 20 * mm]))
    else:
        story.append(Paragraph("No GitHub profile was connected. Engineering evidence unavailable.", st["body"]))

    # ---------- 6. Coding Platform Analysis ----------
    story.append(_section_header("6. Coding Platform Analysis"))
    if a.coding and a.coding.platforms:
        rows = [["Platform", "Handle", "Key Stats"]]
        for cp in a.coding.platforms:
            key = cp.stats.get("total_solved") or cp.stats.get("rating") or cp.stats.get("coding_score") or cp.stats.get("medals")
            detail = f"{key}" if key else "active"
            rows.append([Paragraph(cp.platform_label, st["cellb"]), Paragraph(cp.handle, st["cell"]),
                         Paragraph(str(detail), st["cell"])])
        story.append(_table(rows, [35 * mm, 40 * mm, 85 * mm]))
        story.append(Spacer(1, 5))
        story.append(Paragraph(f"<b>Combined Problem Solving Score: {round(a.coding.problem_solving_score)}/100</b>", st["body"]))
        story.append(Paragraph(a.coding.explanation, st["small"]))
    else:
        story.append(Paragraph("No coding platform profiles were connected.", st["body"]))

    # ---------- 7. Project Verification ----------
    story.append(_section_header("7. Project Verification"))
    for pv in a.project_verifications:
        status = pv.status.value
        head = f"<b>{pv.project_name}</b> — {round(pv.score)}/100"
        story.append(Paragraph(head, st["cellb"]))
        story.append(StatusBadge(status))
        story.append(Spacer(1, 2))
        for ev in pv.evidence:
            story.append(Paragraph(f"• {ev}", st["small"]))
        story.append(Spacer(1, 3))

    # ---------- 8. Achievement Verification ----------
    story.append(_section_header("8. Achievement Verification"))
    for av in a.achievement_verifications:
        story.append(Paragraph(f"<b>{av.title}</b> ({av.type.replace('_', ' ')})", st["cell"]))
        story.append(StatusBadge(av.status.value))
        story.append(Spacer(1, 2))
        for ev in av.evidence:
            story.append(Paragraph(f"• {ev}", st["small"]))
        story.append(Spacer(1, 3))

    # ---------- 9. LinkedIn Certifications ----------
    linkedin_profiles = [p for p in a.profiles if p.platform == "linkedin" and p.status == "collected"]
    linkedin_certs = []
    for prof in linkedin_profiles:
        for c in (prof.data or {}).get("certifications") or []:
            linkedin_certs.append(c)
    if linkedin_profiles:
        story.append(_section_header("9. LinkedIn Certifications"))
        if linkedin_certs:
            rows = [["Certification", "Issuer", "Issued", "Credential ID"]]
            for c in linkedin_certs:
                rows.append([
                    Paragraph(c.get("title") or "—", st["cell"]),
                    Paragraph(c.get("issuer") or "—", st["cell"]),
                    Paragraph(c.get("issued_date") or "—", st["cell"]),
                    Paragraph(c.get("credential_id") or "—", st["cell"]),
                ])
            story.append(_table(rows, [58 * mm, 50 * mm, 30 * mm, 35 * mm]))
        else:
            story.append(Paragraph("No certifications listed on the connected LinkedIn profile.", st["body"]))
        story.append(Spacer(1, 4))

    # ---------- 10. Strengths ----------
    story.append(_section_header("10. Strengths"))
    for s in a.strengths:
        story.append(Paragraph(f"• {s}", st["body"]))

    # ---------- 11. Improvement Areas ----------
    story.append(_section_header("11. Improvement Areas"))
    for s in a.improvements:
        story.append(Paragraph(f"• {s}", st["body"]))

    # ---------- 12. AI Summary ----------
    story.append(_section_header("12. AI Summary"))
    for key, label in [("technical_strengths", "Technical Strengths"), ("engineering_profile", "Engineering Profile"),
                       ("coding_ability", "Coding Ability"), ("project_quality", "Project Quality"),
                       ("collaboration_indicators", "Collaboration Indicators"),
                       ("learning_consistency", "Learning Consistency"), ("areas_to_improve", "Areas to Improve")]:
        if a.ai_summary.get(key):
            story.append(Paragraph(f"<b>{label}:</b> {a.ai_summary[key]}", st["body"]))
            story.append(Spacer(1, 3))

    # ---------- 13. Final Scores ----------
    story.append(PageBreak())
    story.append(_section_header("13. Final Scores"))
    score_items = a.scores
    story.append(RadarChart([(s.label.replace(" Score", ""), s.value) for s in score_items], size=165))
    story.append(Spacer(1, 10))
    rows = [["Score", "Value", "", "How it was calculated"]]
    for s in score_items:
        rows.append([Paragraph(s.label, st["cellb"]), Paragraph(f"{round(s.value)}", st["score"]),
                     _score_cell(s.value), Paragraph(s.explanation, st["small"])])
    story.append(_table(rows, [38 * mm, 12 * mm, 28 * mm, 82 * mm]))

    doc.build(story)
    return buf.getvalue()
