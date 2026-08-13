"""Skill knowledge base: category mapping + code signature detection.

This module is the single source of truth for technology recognition. It is used by:
- the mock resume parser (extract skills from resume text),
- the code-evidence scanner (match technologies against repo file contents),
- the mock evidence engine (synthesize believable repo evidence).
"""

from __future__ import annotations

from dataclasses import dataclass

CATEGORY_LABELS = {
    "programming_languages": "Programming Languages",
    "frontend": "Frontend",
    "backend": "Backend",
    "databases": "Databases",
    "devops": "DevOps",
    "cloud": "Cloud",
    "ai_ml": "AI / ML",
    "mobile": "Mobile",
    "tools": "Tools",
    "testing": "Testing",
    "other": "Other Technologies",
}


@dataclass(frozen=True)
class SkillDef:
    name: str
    category: str
    # regex-ish patterns matched against resume text (case-insensitive substring).
    resume_patterns: tuple[str, ...]
    # file signatures matched against repo tree paths (lowercase, substring match).
    file_signatures: tuple[str, ...] = ()


SKILLS: list[SkillDef] = [
    # --- Programming languages ---
    SkillDef("Python", "programming_languages", ("python", "py3"), ("\\.py", "requirements.txt", "setup.py", "pyproject.toml")),
    SkillDef("Java", "programming_languages", ("java",), ("\\.java", "pom.xml", "build.gradle")),
    SkillDef("JavaScript", "programming_languages", ("javascript", "js", "node.js", "nodejs"), ("\\.js$", "package.json")),
    SkillDef("TypeScript", "programming_languages", ("typescript", "ts",), ("\\.ts$", "\\.tsx", "tsconfig.json")),
    SkillDef("C++", "programming_languages", ("c++", "cpp", "c plus plus"), ("\\.cpp", "\\.hpp", "\\.cc$")),
    SkillDef("C", "programming_languages", ("\\bc\\b",), ("\\.c$", "\\.h$")),
    SkillDef("C#", "programming_languages", ("c#", "c sharp"), ("\\.cs$", "\\.csproj")),
    SkillDef("Go", "programming_languages", ("\\bgo\\b", "golang"), ("\\.go$", "go.mod")),
    SkillDef("Rust", "programming_languages", ("rust",), ("\\.rs$", "cargo.toml")),
    SkillDef("Ruby", "programming_languages", ("ruby",), ("\\.rb$", "gemfile")),
    SkillDef("PHP", "programming_languages", ("php",), ("\\.php$", "composer.json")),
    SkillDef("Kotlin", "programming_languages", ("kotlin",), ("\\.kt$",)),
    SkillDef("Swift", "programming_languages", ("swift",), ("\\.swift$",)),
    SkillDef("Scala", "programming_languages", ("scala",), ("\\.scala$",)),
    SkillDef("Dart", "programming_languages", ("dart",), ("\\.dart$",)),
    SkillDef("SQL", "programming_languages", ("sql",), ("\\.sql$",)),
    SkillDef("Bash", "programming_languages", ("bash", "shell scripting"), ("\\.sh$",)),
    SkillDef("HTML", "programming_languages", ("html",), ("\\.html$",)),
    SkillDef("CSS", "programming_languages", ("css",), ("\\.css$",)),
    # --- Frontend ---
    SkillDef("React", "frontend", ("react", "react.js", "reactjs"), ("react\\.", "\\/react\\/", "\\-react")),
    SkillDef("Next.js", "frontend", ("next.js", "nextjs", "next js"), ("next\\.config", "\\.next\\/")),
    SkillDef("Vue", "frontend", ("vue", "vue.js"), ("\\.vue$",)),
    SkillDef("Angular", "frontend", ("angular",), ("angular\\.json", "\\.angular")),
    SkillDef("Svelte", "frontend", ("svelte",), ("\\.svelte$",)),
    SkillDef("Tailwind CSS", "frontend", ("tailwind",), ("tailwind\\.config")),
    SkillDef("Redux", "frontend", ("redux",), ("redux",)),
    SkillDef("Bootstrap", "frontend", ("bootstrap",), ("bootstrap",)),
    SkillDef("jQuery", "frontend", ("jquery",), ("jquery",)),
    SkillDef("Webpack", "frontend", ("webpack",), ("webpack\\.config")),
    SkillDef("Vite", "frontend", ("vite",), ("vite\\.config")),
    # --- Backend ---
    SkillDef("Node.js", "backend", ("node.js", "nodejs", "express"), ("node_modules", "express")),
    SkillDef("Express", "backend", ("express",), ("express",)),
    SkillDef("Spring Boot", "backend", ("spring boot", "springboot", "spring"), ("pom.xml", "application\\.yml", "application\\.properties")),
    SkillDef("Django", "backend", ("django",), ("django", "manage\\.py")),
    SkillDef("Flask", "backend", ("flask",), ("flask",)),
    SkillDef("FastAPI", "backend", ("fastapi",), ("fastapi",)),
    SkillDef("NestJS", "backend", ("nestjs", "nest js"), ("nestjs",)),
    SkillDef("Rails", "backend", ("rails", "ruby on rails"), ("rails",)),
    SkillDef("Laravel", "backend", ("laravel",), ("laravel",)),
    SkillDef("REST APIs", "backend", ("rest api", "restful", "rest apis"), ("api\\/", "rest")),
    SkillDef("GraphQL", "backend", ("graphql",), ("graphql",)),
    SkillDef("gRPC", "backend", ("grpc",), ("grpc",)),
    SkillDef("Microservices", "backend", ("microservice",), ("microservice",)),
    SkillDef("RabbitMQ", "backend", ("rabbitmq", "rabbit mq"), ("rabbitmq",)),
    SkillDef("Kafka", "backend", ("kafka",), ("kafka",)),
    SkillDef("WebSockets", "backend", ("websocket", "socket.io", "socketio"), ("socket",)),
    # --- Databases ---
    SkillDef("MySQL", "databases", ("mysql",), ("mysql",)),
    SkillDef("PostgreSQL", "databases", ("postgresql", "postgres", "psql"), ("postgres", "pg_")),
    SkillDef("MongoDB", "databases", ("mongodb", "mongo db", "mongo"), ("mongo",)),
    SkillDef("Redis", "databases", ("redis",), ("redis",)),
    SkillDef("SQLite", "databases", ("sqlite",), ("sqlite",)),
    SkillDef("Elasticsearch", "databases", ("elasticsearch", "elastic search"), ("elasticsearch",)),
    SkillDef("Cassandra", "databases", ("cassandra",), ("cassandra",)),
    SkillDef("DynamoDB", "databases", ("dynamodb", "dynamo db"), ("dynamodb",)),
    SkillDef("Firebase", "databases", ("firebase",), ("firebase",)),
    SkillDef("Supabase", "databases", ("supabase",), ("supabase",)),
    SkillDef("Oracle", "databases", ("oracle",), ("oracle",)),
    # --- DevOps ---
    SkillDef("Docker", "devops", ("docker",), ("dockerfile", "\\.dockerignore", "docker-compose")),
    SkillDef("Kubernetes", "devops", ("kubernetes", "k8s", "kubectl"), ("deployment\\.yaml", "k8s", "helm")),
    SkillDef("Jenkins", "devops", ("jenkins",), ("jenkinsfile",)),
    SkillDef("GitHub Actions", "devops", ("github actions", "ci/cd", "cicd", "githubaction"), ("\\.github\\/workflows",)),
    SkillDef("GitLab CI", "devops", ("gitlab ci",), ("\\.gitlab-ci\\.yml",)),
    SkillDef("Terraform", "devops", ("terraform",), ("\\.tf$", "terraform")),
    SkillDef("Ansible", "devops", ("ansible",), ("ansible",)),
    SkillDef("Helm", "devops", ("helm",), ("charts\\/", "helm")),
    SkillDef("Nginx", "devops", ("nginx",), ("nginx",)),
    SkillDef("Grafana", "devops", ("grafana",), ("grafana",)),
    SkillDef("Prometheus", "devops", ("prometheus",), ("prometheus",)),
    # --- Cloud ---
    SkillDef("AWS", "cloud", ("aws", "amazon web services", "ec2", "s3", "lambda"), ("aws", "\\/s3", "lambda")),
    SkillDef("Azure", "cloud", ("azure",), ("azure",)),
    SkillDef("Google Cloud", "cloud", ("google cloud", "gcp", "googlecloud"), ("gcp",)),
    SkillDef("Serverless", "cloud", ("serverless",), ("serverless",)),
    SkillDef("Vercel", "cloud", ("vercel",), ("vercel\\.json",)),
    SkillDef("Netlify", "cloud", ("netlify",), ("netlify",)),
    SkillDef("Heroku", "cloud", ("heroku",), ("heroku",)),
    SkillDef("Cloudflare", "cloud", ("cloudflare",), ("cloudflare",)),
    SkillDef("Firebase Hosting", "cloud", ("firebase hosting",), ("firebase\\.json",)),
    # --- AI/ML ---
    SkillDef("TensorFlow", "ai_ml", ("tensorflow", "tf keras"), ("tensorflow",)),
    SkillDef("PyTorch", "ai_ml", ("pytorch", "torch"), ("torch", "pytorch")),
    SkillDef("scikit-learn", "ai_ml", ("scikit-learn", "scikit learn", "sklearn"), ("sklearn", "scikit")),
    SkillDef("Keras", "ai_ml", ("keras",), ("keras",)),
    SkillDef("Pandas", "ai_ml", ("pandas",), ("pandas",)),
    SkillDef("NumPy", "ai_ml", ("numpy",), ("numpy",)),
    SkillDef("Matplotlib", "ai_ml", ("matplotlib", "matplot"), ("matplotlib",)),
    SkillDef("OpenCV", "ai_ml", ("opencv", "computer vision", "cv2"), ("opencv", "cv2")),
    SkillDef("NLP", "ai_ml", ("nlp", "natural language processing"), ("nlp",)),
    SkillDef("LLM", "ai_ml", ("llm", "large language model", "gpt"), ("llm",)),
    SkillDef("OpenAI", "ai_ml", ("openai", "chatgpt"), ("openai",)),
    SkillDef("LangChain", "ai_ml", ("langchain",), ("langchain",)),
    SkillDef("Hugging Face", "ai_ml", ("hugging face", "huggingface", "transformers"), ("huggingface", "transformers")),
    SkillDef("MLOps", "ai_ml", ("mlops",), ("mlops",)),
    # --- Mobile ---
    SkillDef("React Native", "mobile", ("react native",), ("react-native", "react_native")),
    SkillDef("Flutter", "mobile", ("flutter",), ("flutter", "pubspec\\.yaml")),
    SkillDef("Android", "mobile", ("android",), ("android", "gradle")),
    SkillDef("iOS", "mobile", ("ios",), ("ios", "\\.xcodeproj")),
    # --- Tools ---
    SkillDef("Git", "tools", ("git",), ("\\.git",)),
    SkillDef("GitHub", "tools", ("github",), ("github",)),
    SkillDef("GitLab", "tools", ("gitlab",), ("gitlab",)),
    SkillDef("Jira", "tools", ("jira",), ("jira",)),
    SkillDef("Figma", "tools", ("figma",), ("figma",)),
    SkillDef("Postman", "tools", ("postman",), ("postman",)),
    SkillDef("Linux", "tools", ("linux", "ubuntu"), ("\\.sh$",)),
    SkillDef("VS Code", "tools", ("vs code", "vscode"), ("\\.vscode",)),
    SkillDef("IntelliJ", "tools", ("intellij",), ("intellij",)),
    SkillDef("GitHub Actions", "tools", (), ()),  # placeholder, real entry above
    # --- Testing ---
    SkillDef("JUnit", "testing", ("junit",), ("junit",)),
    SkillDef("Jest", "testing", ("jest",), ("jest\\.config",)),
    SkillDef("PyTest", "testing", ("pytest", "py test"), ("pytest",)),
    SkillDef("Selenium", "testing", ("selenium",), ("selenium",)),
    SkillDef("Cypress", "testing", ("cypress",), ("cypress",)),
    SkillDef("Playwright", "testing", ("playwright",), ("playwright",)),
    SkillDef("Mocha", "testing", ("mocha",), ("mocha",)),
    SkillDef("Chai", "testing", ("chai",), ("chai",)),
]

# Normalize alias -> canonical skill name for synonyms used in resumes.
ALIASES: dict[str, str] = {
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "node": "Node.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "express.js": "Express",
    "reactjs": "React",
    "react.js": "React",
    "nextjs": "Next.js",
    "next.js": "Next.js",
    "vue.js": "Vue",
    "vuejs": "Vue",
    "angularjs": "Angular",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "docker": "Docker",
    "sklearn": "scikit-learn",
    "scikit-learn": "scikit-learn",
    "tf": "TensorFlow",
    "pytorch": "PyTorch",
    "aws": "AWS",
    "gcp": "Google Cloud",
    "git": "Git",
    "github": "GitHub",
    "ci/cd": "GitHub Actions",
    "cicd": "GitHub Actions",
    "ml": "Machine Learning",
    "ai": "AI / ML",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "sql": "SQL",
    "java": "Java",
    "python": "Python",
    "html": "HTML",
    "css": "CSS",
    "rest": "REST APIs",
    "graphql": "GraphQL",
}

CANONICAL_CATEGORY: dict[str, str] = {s.name: s.category for s in SKILLS}
CANONICAL_CATEGORY["Machine Learning"] = "ai_ml"
CANONICAL_CATEGORY["Deep Learning"] = "ai_ml"

# Additional standalone technologies (rare on GitHub trees) recognized by name only.
NAME_ONLY_TECHNOLOGIES: dict[str, str] = {
    "Machine Learning": "ai_ml",
    "Deep Learning": "ai_ml",
    "Data Structures": "other",
    "Algorithms": "other",
    "Object-Oriented Programming": "other",
    "System Design": "other",
    "Agile": "other",
    "Scrum": "other",
    "REST": "backend",
}

# Technologies commonly listed on resumes but invisible in public code; used to
# keep verification honest ("no public evidence" rather than "absent").
NON_CODE_EVIDENCE_TECHS = {"Jira", "Figma", "Postman", "VS Code", "IntelliJ", "Agile", "Scrum"}

PROJECT_DEPLOYMENT_MARKERS = ("vercel.app", "netlify.app", "github.io", "herokuapp.com",
                              "surge.sh", "firebaseapp.com", "render.com", "onrender.com",
                              "railway.app", "pages.dev", "fly.dev", "deno.dev", "glitch.me")


def normalize_skill(raw: str) -> str | None:
    """Map a raw resume token to a canonical skill name (None if unknown)."""
    token = raw.strip().lower()
    if not token:
        return None
    if token in ALIASES:
        return ALIASES[token]
    for s in SKILLS:
        if s.name.lower() == token:
            return s.name
    return None


def detect_skills_in_text(text: str, max_results: int = 200) -> list[str]:
    """Detect canonical skill names present in resume text (case-insensitive)."""
    lowered = text.lower()
    found: list[str] = []
    for s in SKILLS:
        if s.name in ("GitHub Actions",) and not s.resume_patterns:
            continue
        for pat in s.resume_patterns:
            if pat in lowered and s.name not in found:
                found.append(s.name)
                break
    for name, cat in NAME_ONLY_TECHNOLOGIES.items():
        if name.lower() in lowered and name not in found:
            found.append(name)
    return found[:max_results]


def category_of(name: str) -> str:
    if name in CANONICAL_CATEGORY:
        return CANONICAL_CATEGORY[name]
    if name in NAME_ONLY_TECHNOLOGIES:
        return NAME_ONLY_TECHNOLOGIES[name]
    return "other"


def file_signature_hits(name: str, tree_paths: set[str]) -> list[str]:
    """File paths in the repo tree that indicate usage of `name`."""
    lower_paths = [p.lower() for p in tree_paths]
    hits: list[str] = []
    for s in SKILLS:
        if s.name != name:
            continue
        for sig in s.file_signatures:
            for p in lower_paths:
                if sig.replace("\\", "") and (sig in p or sig.rstrip("$") in p):
                    hits.append(p)
    return hits


def signature_present(name: str, tree_paths: set[str]) -> bool:
    return len(file_signature_hits(name, tree_paths)) > 0
