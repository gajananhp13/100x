"""System prompts for the OpenAI provider."""

PARSE_SYSTEM = """You are an expert resume parser for a candidate verification platform.
Extract structured data from the resume text exactly as provided. Rules:
- Use ONLY information present in the text. Never guess or invent values.
- Leave fields null/empty when absent.
- personal.name should be the candidate's name.
- personal.github / personal.linkedin should be full URLs when found.
- skills: categorize every technology into the 11 given categories
  (programming_languages, frontend, backend, databases, devops, cloud, ai_ml,
  mobile, tools, testing, other). Use canonical names (e.g. "TypeScript",
  "Next.js", "PostgreSQL", "scikit-learn").
- projects: extract name, description, tech_stack (list), features (list of
  bullet-like short phrases), github_link, live_demo, apis_used, database,
  deployment.
- achievements.type is one of: hackathon, certification, award, publication,
  open_source, coding, other. Set platform when identifiable (Devpost, Kaggle,
  GitHub, LeetCode, ...).
- experience.technologies: technologies mentioned in that role.
- experience.is_current: set to true if the duration includes "present" or
  "current" (indicating the role is ongoing). Otherwise false.
- Return JSON only, matching the schema provided in the user message."""

SUMMARY_SYSTEM = """You are an AI recruiting analyst at a candidate verification platform.
Given a candidate's parsed resume and the public evidence collected from their
developer profiles, write a professional, evidence-based, recruiter-ready
assessment. Rules:
- Base every statement on the evidence provided. Never speculate.
- Clearly differentiate 'no public evidence found' from 'skill absent'.
- Never accuse the candidate of dishonesty; use neutral phrasing like
  'no public evidence was found for this claim'.
- Keep the summary concise and professional.
Return JSON with exactly these keys:
  technical_strengths, engineering_profile, coding_ability, project_quality,
  collaboration_indicators, learning_consistency, areas_to_improve
Each value is a 1-3 sentence string."""

SUMMARY_SCHEMA_HINT = (
    "{\"technical_strengths\": \"...\", \"engineering_profile\": \"...\", "
    "\"coding_ability\": \"...\", \"project_quality\": \"...\", "
    "\"collaboration_indicators\": \"...\", \"learning_consistency\": \"...\", "
    "\"areas_to_improve\": \"...\"}"
)

PARSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "personal": {
            "type": "object",
            "properties": {
                "name": {"type": ["string", "null"]},
                "email": {"type": ["string", "null"]},
                "phone": {"type": ["string", "null"]},
                "location": {"type": ["string", "null"]},
                "portfolio": {"type": ["string", "null"]},
                "github": {"type": ["string", "null"]},
                "linkedin": {"type": ["string", "null"]},
                "headline": {"type": ["string", "null"]},
            },
        },
        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "college": {"type": ["string", "null"]},
                    "degree": {"type": ["string", "null"]},
                    "branch": {"type": ["string", "null"]},
                    "graduation_year": {"type": ["string", "null"]},
                    "gpa": {"type": ["string", "null"]},
                },
            },
        },
        "experience": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company": {"type": ["string", "null"]},
                    "position": {"type": ["string", "null"]},
                    "duration": {"type": ["string", "null"]},
                    "is_current": {"type": "boolean"},
                    "responsibilities": {"type": "array", "items": {"type": "string"}},
                    "technologies": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "skills": {
            "type": "object",
            "properties": {
                "programming_languages": {"type": "array", "items": {"type": "string"}},
                "frontend": {"type": "array", "items": {"type": "string"}},
                "backend": {"type": "array", "items": {"type": "string"}},
                "databases": {"type": "array", "items": {"type": "string"}},
                "devops": {"type": "array", "items": {"type": "string"}},
                "cloud": {"type": "array", "items": {"type": "string"}},
                "ai_ml": {"type": "array", "items": {"type": "string"}},
                "mobile": {"type": "array", "items": {"type": "string"}},
                "tools": {"type": "array", "items": {"type": "string"}},
                "testing": {"type": "array", "items": {"type": "string"}},
                "other": {"type": "array", "items": {"type": "string"}},
            },
        },
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": ["string", "null"]},
                    "description": {"type": ["string", "null"]},
                    "tech_stack": {"type": "array", "items": {"type": "string"}},
                    "features": {"type": "array", "items": {"type": "string"}},
                    "github_link": {"type": ["string", "null"]},
                    "live_demo": {"type": ["string", "null"]},
                    "apis_used": {"type": "array", "items": {"type": "string"}},
                    "database": {"type": ["string", "null"]},
                    "deployment": {"type": ["string", "null"]},
                },
            },
        },
        "achievements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": ["string", "null"]},
                    "platform": {"type": ["string", "null"]},
                    "date": {"type": ["string", "null"]},
                },
            },
        },
    },
}