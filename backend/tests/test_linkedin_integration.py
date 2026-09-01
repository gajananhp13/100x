"""Tests for the LinkedIn real-scrape integration and report certifications."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from linkedin_scraper.models import (  # noqa: E402
    Accomplishment,
    Experience,
    Person,
    Skill,
)
from app.core.integrations.platforms.linkedin import (  # noqa: E402
    LinkedInIntegration,
    person_to_scrape_data,
)
from app.core.integrations.base import ProfileCollectError  # noqa: E402
from app.config import settings  # noqa: E402


def _fake_person() -> Person:
    return Person(
        linkedin_url="https://www.linkedin.com/in/aaravmehta",
        name="Aarav Mehta",
        location="Bangalore, India",
        about="Backend engineer with 3 years of experience.",
        experiences=[
            Experience(position_title="Backend Developer", institution_name="TechNova")
        ],
        skills=[
            Skill(name="Python", endorsements=12),
            Skill(name="Kafka", endorsements=None),
        ],
        accomplishments=[
            Accomplishment(
                category="certification",
                title="AWS Certified Cloud Practitioner",
                issuer="Amazon Web Services",
                issued_date="2024",
                credential_id="ABC-123",
                credential_url="https://www.credly.com/badge/x",
            ),
            Accomplishment(category="honor", title="Employee of the Month"),
        ],
    )


def test_person_to_scrape_data_maps_certifications_and_skills():
    data = person_to_scrape_data(_fake_person(), "aaravmehta")
    assert data["_source"] == "linkedin-scraper"
    assert data["username"] == "aaravmehta"
    assert data["about"].startswith("Backend engineer")
    # Certifications are filtered out of the generic accomplishments list
    assert len(data["certifications"]) == 1
    cert = data["certifications"][0]
    assert cert["title"] == "AWS Certified Cloud Practitioner"
    assert cert["issuer"] == "Amazon Web Services"
    assert cert["credential_id"] == "ABC-123"
    # Skills carry endorsement counts
    assert {s["name"]: s["endorsements"] for s in data["skills"]} == {
        "Python": 12,
        "Kafka": None,
    }
    assert data["endorsements"] == 12
    # Experience mapping
    assert len(data["experiences"]) == 1
    exp = data["experiences"][0]
    assert exp["position_title"] == "Backend Developer"
    assert exp["company"] == "TechNova"
    # linkedin_url is not mapped for experiences in person_to_scrape_data


def test_person_to_scrape_data_maps_experience_fields():
    """Verify full experience field mapping including dates, location, description."""
    person = Person(
        linkedin_url="https://www.linkedin.com/in/test",
        name="Test User",
        location="San Francisco, CA",
        experiences=[
            Experience(
                position_title="Senior Engineer",
                institution_name="Acme Corp",
                from_date="2022",
                to_date="Present",
                duration="2 yrs",
                location="San Francisco, CA",
                description="Built scalable systems.",
            ),
            Experience(
                position_title="Junior Engineer",
                institution_name="Startup Inc",
                from_date="2020",
                to_date="2022",
                duration="2 yrs",
                location="Remote",
                description="Early stage product work.",
            ),
        ],
    )
    data = person_to_scrape_data(person, "testuser")
    assert len(data["experiences"]) == 2
    exp1 = data["experiences"][0]
    assert exp1["position_title"] == "Senior Engineer"
    assert exp1["company"] == "Acme Corp"
    assert exp1["from_date"] == "2022"
    assert exp1["to_date"] == "Present"
    assert exp1["duration"] == "2 yrs"
    assert exp1["location"] == "San Francisco, CA"
    assert exp1["description"] == "Built scalable systems."
    exp2 = data["experiences"][1]
    assert exp2["position_title"] == "Junior Engineer"
    assert exp2["company"] == "Startup Inc"


def test_person_to_scrape_data_maps_skills_with_endorsements():
    """Verify skills include name, endorsements, and URL."""
    person = Person(
        linkedin_url="https://www.linkedin.com/in/test",
        name="Test User",
        skills=[
            Skill(name="Python", endorsements=42, linkedin_url="https://linkedin.com/skill/python"),
            Skill(name="Go", endorsements=0),
            Skill(name="Rust"),
        ],
    )
    data = person_to_scrape_data(person, "testuser")
    assert len(data["skills"]) == 3
    skills_by_name = {s["name"]: s for s in data["skills"]}
    assert skills_by_name["Python"]["endorsements"] == 42
    assert skills_by_name["Python"]["url"] == "https://linkedin.com/skill/python"
    assert skills_by_name["Go"]["endorsements"] == 0
    assert skills_by_name["Rust"]["endorsements"] is None
    assert skills_by_name["Rust"]["url"] is None
    assert data["endorsements"] == 42  # sum of non-None endorsements


def test_gated_when_disabled_returns_mock(monkeypatch):
    monkeypatch.setattr(settings, "linkedin_scrape_enabled", False)
    integration = LinkedInIntegration(simulate=False)
    data = integration.collect("aaravmehta")
    assert data["_source"] == "mock"


def test_real_scrape_without_auth_raises(monkeypatch):
    monkeypatch.setattr(settings, "linkedin_scrape_enabled", True)
    monkeypatch.setattr(settings, "linkedin_session_path", "no/such/session.json")
    monkeypatch.setattr(settings, "linkedin_email", None)
    monkeypatch.setattr(settings, "linkedin_password", None)
    integration = LinkedInIntegration(simulate=False)
    with pytest.raises(ProfileCollectError):
        integration.collect("aaravmehta")


def test_simulate_flag_returns_mock(monkeypatch):
    monkeypatch.setattr(settings, "linkedin_scrape_enabled", True)
    integration = LinkedInIntegration(simulate=True)
    data = integration.collect("aaravmehta")
    assert data["_source"] == "mock"
