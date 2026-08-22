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
