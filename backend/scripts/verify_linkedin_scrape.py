#!/usr/bin/env python3
"""
Verify LinkedIn Scraping - Test the real scraper with a saved session.

This script uses the saved session file (created by create_session.py) to scrape
a real LinkedIn profile and prints the extracted Experience, Certifications, and Skills.

Usage:
    python scripts/verify_linkedin_scrape.py [profile_handle]

If no handle is provided, it will scrape the logged-in user's own profile
(using the "me" redirect).

Requirements:
- LINKEDIN_SESSION_PATH must be set in .env and the session file must exist
- Or LINKEDIN_SCRAPE_ENABLED=true with valid credentials
"""
import asyncio
import sys
import json
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from linkedin_scraper import BrowserManager
from linkedin_scraper.scrapers import PersonScraper
from linkedin_scraper.core import load_credentials_from_env


async def verify_scrape(handle: str | None = None):
    """Scrape a LinkedIn profile and print the key sections."""
    session_path = settings.linkedin_session_path
    email, password = load_credentials_from_env()
    
    has_session = session_path and Path(session_path).exists()
    has_creds = bool(email and password)
    
    if not has_session and not has_creds:
        print("❌ No session file found and no credentials configured.")
        print(f"   Session path: {session_path}")
        print(f"   Email configured: {bool(email)}")
        print("\nRun 'python scripts/create_session.py' first to create a session.")
        return
    
    if handle:
        url = f"https://www.linkedin.com/in/{handle}"
    else:
        # Use "me" to scrape the logged-in user's own profile
        url = "https://www.linkedin.com/in/me"
        print("ℹ️  No handle provided — scraping your own profile (linkedin.com/in/me)")
    
    print("="*70)
    print("LinkedIn Scraping Verification")
    print("="*70)
    print(f"Target URL: {url}")
    print(f"Using session: {has_session}")
    print(f"Using credentials: {has_creds}")
    print("-"*70)
    
    async with BrowserManager(headless=True) as browser:
        if has_session:
            print(f"Loading session from {session_path}...")
            await browser.load_session(session_path)
        else:
            print("Logging in with credentials...")
            from linkedin_scraper.core import login_with_credentials
            await login_with_credentials(browser.page, email, password)
            # Save session for next time
            if session_path:
                Path(session_path).parent.mkdir(parents=True, exist_ok=True)
                await browser.save_session(session_path)
                print(f"Session saved to {session_path}")
        
        print("Scraping profile...")
        scraper = PersonScraper(browser.page)
        person = await scraper.scrape(url)
        
        # Print results
        print("\n" + "="*70)
        print(f"✅ Scraped: {person.name}")
        print(f"   Location: {person.location or 'N/A'}")
        print(f"   Headline: {person.about[:80] + '...' if person.about and len(person.about) > 80 else person.about or 'N/A'}")
        print(f"   Profile URL: {person.linkedin_url}")
        print("="*70)
        
        # Experience
        print(f"\n📋 EXPERIENCE ({len(person.experiences)} entries)")
        print("-"*70)
        for i, exp in enumerate(person.experiences[:5], 1):
            duration = f"{exp.from_date or '?'} – {exp.to_date or 'Present'}"
            if exp.duration:
                duration += f" ({exp.duration})"
            print(f"  {i}. {exp.position_title or 'Unknown'} @ {exp.institution_name or 'Unknown'}")
            print(f"     {duration}")
            if exp.location:
                print(f"     Location: {exp.location}")
            if exp.description:
                desc = exp.description[:200] + ("..." if len(exp.description) > 200 else "")
                print(f"     {desc}")
        
        if len(person.experiences) > 5:
            print(f"  ... and {len(person.experiences) - 5} more")
        
        # Certifications
        certs = [c for c in person.accomplishments if c.category == "certification"]
        print(f"\n🏆 CERTIFICATIONS ({len(certs)} entries)")
        print("-"*70)
        if certs:
            for i, cert in enumerate(certs, 1):
                print(f"  {i}. {cert.title}")
                if cert.issuer:
                    print(f"     Issuer: {cert.issuer}")
                if cert.issued_date:
                    print(f"     Issued: {cert.issued_date}")
                if cert.credential_id:
                    print(f"     Credential ID: {cert.credential_id}")
        else:
            print("  No certifications found.")
        
        # Skills
        print(f"\n🛠️  SKILLS ({len(person.skills)} entries)")
        print("-"*70)
        if person.skills:
            for i, skill in enumerate(person.skills[:20], 1):
                endorsements = f" ({skill.endorsements} endorsements)" if skill.endorsements else ""
                print(f"  {i}. {skill.name}{endorsements}")
            if len(person.skills) > 20:
                print(f"  ... and {len(person.skills) - 20} more")
        else:
            print("  No skills found.")
        
        # Output as JSON for programmatic use
        print("\n" + "="*70)
        print("JSON OUTPUT (for debugging)")
        print("="*70)
        output = {
            "name": person.name,
            "location": person.location,
            "about": person.about,
            "profile_url": person.linkedin_url,
            "experiences": [
                {
                    "position_title": e.position_title,
                    "company": e.institution_name,
                    "from_date": e.from_date,
                    "to_date": e.to_date,
                    "duration": e.duration,
                    "location": e.location,
                    "description": e.description,
                }
                for e in person.experiences
            ],
            "certifications": [
                {
                    "title": c.title,
                    "issuer": c.issuer,
                    "issued_date": c.issued_date,
                    "credential_id": c.credential_id,
                    "credential_url": c.credential_url,
                }
                for c in certs
            ],
            "skills": [
                {"name": s.name, "endorsements": s.endorsements, "url": s.linkedin_url}
                for s in person.skills
            ],
        }
        print(json.dumps(output, indent=2, default=str))
        
        return output


if __name__ == "__main__":
    handle = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(verify_scrape(handle))