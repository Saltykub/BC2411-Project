from __future__ import annotations

import hashlib
from pathlib import Path

APP_TITLE = "TalentFlow"
APP_ICON = "🎯"
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "outputs"

COMPANIES = {
    0: {"name": "Apex Digital Solutions", "industry": "Enterprise SaaS", "hq": "Singapore"},
    1: {"name": "NovaBridge Technologies", "industry": "Cloud Infrastructure", "hq": "San Francisco"},
    2: {"name": "Meridian Health Systems", "industry": "HealthTech", "hq": "London"},
    3: {"name": "ForgeStack Labs", "industry": "Developer Tools", "hq": "Berlin"},
}

DEPARTMENTS = {
    "Backend Developer": "Platform Engineering",
    "Database Administrator": "Data & Infrastructure",
    "DevOps Engineer": "Cloud Operations",
    "Django Developer": "Platform Engineering",
    "Flutter Developer": "Mobile Applications",
    "Full Stack Developer": "Platform Engineering",
    "iOS Developer": "Mobile Applications",
    "Java Developer": "Platform Engineering",
    "JavaScript Developer": "Web Experience",
    "Machine Learning": "AI & Data Science",
    "Network Administrator": "Cloud Operations",
    "Node js developer": "Platform Engineering",
    "PHP Developer": "Web Experience",
    "Software Engineer": "Platform Engineering",
    "Wordpress Developer": "Web Experience",
}

DEMO_USERS = {
    "mia.chen@apexdigital.com": {"password": "talent2025", "name": "Mia Chen", "role": "Lead Recruiter", "company_id": 0},
    "daniel.ong@novabridge.io": {"password": "talent2025", "name": "Daniel Ong", "role": "Hiring Manager", "company_id": 1},
    "sofia.reyes@meridianhs.com": {"password": "talent2025", "name": "Sofia Reyes", "role": "Talent Partner", "company_id": 2},
    "arjun.mehta@forgestack.dev": {"password": "talent2025", "name": "Arjun Mehta", "role": "Recruiting Lead", "company_id": 3},
    "admin@talentflow.ai": {"password": "admin2025", "name": "Jordan Lee", "role": "Platform Admin", "company_id": -1},
}

STATUS_ORDER = ["Pending", "Interview", "Advance", "Hold", "Reject"]

PAIR_WEIGHTS = {
    "w_tfidf": 0.15,
    "w_bm25": 0.15,
    "w_skill": 0.25,
    "w_coverage": 0.20,
    "w_exp": 0.10,
    "w_deg": 0.05,
    "w_length": 0.05,
}

DEG_MAP = {1: "High School", 2: "Associate", 3: "Bachelor's", 4: "Master's", 5: "PhD"}

FIRST_NAMES = [
    "Aiden", "Amara", "Ananya", "Arjun", "Ava", "Benjamin", "Caleb", "Carmen", "Chen Wei",
    "Clara", "Darius", "Elena", "Ethan", "Fatima", "Gabriel", "Grace", "Harper", "Hiroshi",
    "Imani", "Isaac", "Jasmine", "Kai", "Kenji", "Layla", "Leo", "Lina", "Lucas", "Maya",
    "Mei", "Nadia", "Nathan", "Olivia", "Omar", "Priya", "Quinn", "Ravi", "Rosa", "Ryan",
    "Sana", "Sarah", "Tariq", "Uma", "Victor", "Wei Lin", "Xavier", "Yara", "Zara", "Zoe",
    "Aditya", "Bianca", "Carlos", "Diana", "Emil", "Freya", "Gavin", "Hana", "Ivan", "Julia",
    "Kevin", "Lily", "Marco", "Nina", "Oscar", "Paula", "Rafael", "Sofia", "Thomas", "Ursula",
    "Vivian", "William", "Xander", "Yuki", "Zain", "Aaliya", "Bruno", "Chloe", "Derek", "Eva",
    "Felix", "Gina", "Hugo", "Iris", "James", "Kira", "Liam", "Mila", "Noah", "Olive",
    "Peter", "Rita", "Sam", "Tara", "Uma", "Vera", "Wade", "Xena", "Yosef", "Zion",
]
LAST_NAMES = [
    "Anderson", "Bharadwaj", "Campbell", "Diaz", "Eriksson", "Fernandez", "Gupta", "Hartmann",
    "Ibrahim", "Jensen", "Kowalski", "Liu", "Martinez", "Nakamura", "O'Brien", "Patel",
    "Quinn", "Rodriguez", "Sharma", "Tanaka", "Uribe", "Volkov", "Wang", "Xu", "Yamamoto",
    "Zhang", "Adeyemi", "Bergstrom", "Chang", "Da Silva", "El-Masri", "Flores", "Gonzalez",
    "Huang", "Ivanova", "Johansson", "Kim", "Lee", "Morales", "Nguyen", "Okonkwo", "Park",
    "Rahman", "Singh", "Torres", "Uddin", "Vasquez", "Wu", "Yang", "Zhou",
]


def candidate_name(resume_id: int) -> str:
    """Generate a deterministic full name from a resume_id."""
    h = int(hashlib.md5(str(resume_id).encode()).hexdigest(), 16)
    first = FIRST_NAMES[h % len(FIRST_NAMES)]
    last = LAST_NAMES[(h // len(FIRST_NAMES)) % len(LAST_NAMES)]
    return f"{first} {last}"
