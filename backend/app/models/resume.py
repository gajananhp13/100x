from pydantic import BaseModel, Field


class PersonalDetails(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    portfolio: str | None = None
    github: str | None = None
    linkedin: str | None = None
    headline: str | None = None


class Education(BaseModel):
    college: str | None = None
    degree: str | None = None
    branch: str | None = None
    graduation_year: str | None = None
    gpa: str | None = None


class Experience(BaseModel):
    company: str | None = None
    position: str | None = None
    duration: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)


class SkillsBreakdown(BaseModel):
    programming_languages: list[str] = Field(default_factory=list)
    frontend: list[str] = Field(default_factory=list)
    backend: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    devops: list[str] = Field(default_factory=list)
    cloud: list[str] = Field(default_factory=list)
    ai_ml: list[str] = Field(default_factory=list)
    mobile: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    testing: list[str] = Field(default_factory=list)
    other: list[str] = Field(default_factory=list)

    def flatten(self) -> list[str]:
        out: list[str] = []
        for field_name in self.model_fields:
            out.extend(getattr(self, field_name))
        return out


class Project(BaseModel):
    name: str | None = None
    description: str | None = None
    tech_stack: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    github_link: str | None = None
    live_demo: str | None = None
    apis_used: list[str] = Field(default_factory=list)
    database: str | None = None
    deployment: str | None = None


class Achievement(BaseModel):
    type: str = "other"  # hackathon | certification | award | publication | open_source | coding | other
    title: str
    description: str | None = None
    platform: str | None = None  # Devpost, Kaggle, GitHub, ...
    date: str | None = None


class ParsedResume(BaseModel):
    personal: PersonalDetails = Field(default_factory=PersonalDetails)
    education: list[Education] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    skills: SkillsBreakdown = Field(default_factory=SkillsBreakdown)
    projects: list[Project] = Field(default_factory=list)
    achievements: list[Achievement] = Field(default_factory=list)
    raw_text: str = ""

    def all_skill_names(self) -> list[str]:
        seen: list[str] = []
        for s in self.skills.flatten():
            if s and s.lower() not in (x.lower() for x in seen):
                seen.append(s)
        return seen