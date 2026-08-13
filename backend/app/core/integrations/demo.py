"""Demo candidate — a one-click test persona with a realistic resume and
handles for every supported platform, so the whole pipeline can be exercised
without any real accounts. GitHub demo data is simulated (labelled in the UI).
"""

from __future__ import annotations

DEMO_NAME = "Aarav Mehta"

DEMO_RESUME_TEXT = """AARAV MEHTA
Bangalore, India | +91 98765 43210 | aarav.mehta.dev@gmail.com | github.com/aarav-mehta | linkedin.com/in/aaravmehta
Software Engineer (Backend) with 3 years of experience building scalable services.

EDUCATION
B.Tech in Computer Science and Engineering, National Institute of Technology, 2022, CGPA 8.7

EXPERIENCE
Backend Developer | TechNova Technologies | 2023 – Present
- Built and maintained REST APIs for a payments platform serving 2M+ users
- Reduced API latency by 40% by introducing Redis caching and query optimization
- Designed microservice architecture with Kafka for event-driven processing
- Wrote unit and integration tests with JUnit and PyTest; CI/CD with GitHub Actions
- Deployed services on AWS (EC2, S3, Lambda) using Docker and Kubernetes
Software Engineer Intern | CloudSprint Pvt Ltd | 2022 – 2023
- Developed Spring Boot microservices and PostgreSQL data models
- Implemented OAuth 2.0 authentication and role-based access control
- Improved deployment pipeline with Docker and Terraform

SKILLS
Python, Java, JavaScript, TypeScript, SQL, C++, Spring Boot, Django, Node.js, React,
Next.js, Redux, REST APIs, GraphQL, Kafka, RabbitMQ, MySQL, PostgreSQL, MongoDB, Redis,
Elasticsearch, Docker, Kubernetes, Jenkins, GitHub Actions, Terraform, AWS, Azure, GCP,
TensorFlow, PyTorch, scikit-learn, Pandas, NLP, React Native, Git, Linux, Postman, Figma,
JUnit, PyTest, Selenium, Cypress, Agile, System Design

PROJECTS
[1] PayStream — Real-time payment analytics dashboard
   Description: Dashboard streaming transaction analytics for fintech teams; Kafka ingestion, Redis caching, WebSocket live updates.
   Tech Stack: [TypeScript, React, Node.js, Kafka, Redis, PostgreSQL, Docker]
   Features: live charts, alerting rules, role-based access
   GitHub: https://github.com/aarav-mehta/paystream
   Live: https://paystream.vercel.app
[2] SkillBridge — AI resume-to-job matching platform
   Description: Matches candidate profiles to roles using NLP embeddings (LLM APIs) with FastAPI backend.
   Tech Stack: [Python, FastAPI, PyTorch, LangChain, MongoDB, Docker]
   Features: semantic search, scoring engine, feedback loop
   GitHub: https://github.com/aarav-mehta/skillbridge
   Live: https://skillbridge.onrender.com
[3] DevLens — Code review analytics for GitHub repos
   Description: Analyzes PR review patterns and generates team insights; GitHub Actions integration.
   Tech Stack: [Python, Django, PostgreSQL, GitHub API, Celery]
   Features: review heatmaps, bottleneck detection, weekly reports
   GitHub: https://github.com/aarav-mehta/devlens

ACHIEVEMENTS
- Finalist, Smart India Hackathon 2023 (Devpost)
- 3-star CodeChef, rating 1740
- LeetCode 450+ problems solved, Knight badge
- AWS Certified Cloud Practitioner (2024)
- Google Cloud Associate Engineer certificate (2023)
- Published article "Caching Strategies for Payment APIs" on Medium (2.1k claps)
- Open source contributor — merged 4 PRs into open-source React libraries
- Winner, Campus-level coding contest (2021)
"""

DEMO_PROFILES: dict[str, str] = {
    "github": "aarav-mehta",
    "gitlab": "aarav-mehta",
    "bitbucket": "aarav-mehta",
    "linkedin": "aaravmehta",
    "portfolio": "aaravmehta.dev",
    "devpost": "aaravmehta",
    "kaggle": "aaravmehta",
    "leetcode": "aaravmehta",
    "codeforces": "aaravmehta",
    "codechef": "aaravmehta",
    "geeksforgeeks": "aaravmehta",
    "hackerrank": "aaravmehta",
    "stackoverflow": "aaravmehta",
    "medium": "aarav.mehta.dev",
    "hashnode": "aaravmehta",
    "devto": "aaravmehta",
    "twitter": "aaravmehta",
}
