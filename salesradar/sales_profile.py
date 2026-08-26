"""
sales_profile.py — the only thing that makes SalesRadar different from JobRadar.

JobRadar's scraper.py decides per job title whether it is an IT vacancy (keyword
pre-filter + Claude classification) and then extracts a tech stack. This module
provides the sales equivalents. Wire it into scraper.py where the IT decision is
made (see README.md, section "scraper.py"):

    from sales_profile import looks_like_sales, CLASSIFY_PROMPT, TAGS_PROMPT, NEGATIVE_RE

Output schema stays identical to JobRadar's latest.json, so the dashboard reads it
unchanged: title, url, company, source, first_seen, stack (used for sales tags),
experience, in_belgium, contact.
"""

import re

# ── 1. Keyword pre-filter (cheap, runs before any LLM call) ────────────────────
# NL / FR / EN. Case-insensitive; matched against the job title only.
SALES_KEYWORDS = [
    # English
    r"\bsales\b", r"account\s*manag", r"account\s*executive", r"key\s*account",
    r"business\s*develop", r"\bbdm\b", r"\bbdr\b", r"\bsdr\b", r"inside\s*sales",
    r"sales\s*engineer", r"pre-?sales", r"solutions?\s*consultant", r"technical\s*sales",
    r"customer\s*success", r"partner\s*manag", r"channel\s*manag", r"revenue",
    r"head\s*of\s*sales", r"chief\s*commercial", r"\bcro\b", r"new\s*business",
    r"sales\s*rep", r"field\s*sales", r"territory\s*manag", r"export\s*manag",
    r"tender\s*manag", r"bid\s*manag",
    # Dutch
    r"commerci[eë]", r"vertegenwoordig", r"verkoop", r"verkoper", r"accountbeheer",
    r"binnendienst\s*(verkoop|sales|commerci)", r"buitendienst", r"klantenbeheer",
    r"relatiebeheer", r"zakelijk\s*adviseur",
    # French
    r"commercial", r"repr[ée]sentant", r"d[ée]l[ée]gu[ée]\s*commercial", r"charg[ée]\s*d'affaires",
    r"charg[ée]\s*de\s*client", r"responsable\s*(des\s*)?ventes", r"technico-?commercial",
    r"business\s*developer",
]
SALES_RE = re.compile("|".join(SALES_KEYWORDS), re.I)

# Titles that contain a sales word but are not sales jobs (or are jobs we never
# want): sales *support* admin, marketing, retail cashiers, recruiters, etc.
NEGATIVE_KEYWORDS = [
    r"sales\s*(support|admin|assistant|administrat)", r"order\s*(desk|entry|handling)",
    r"marketing\s*(manager|specialist|coordinator)(?!.*sales)", r"cashier|kassa",
    r"winkelmedewerker|shop\s*assistant|retail\s*assistant|verkoopmedewerker\s*winkel",
    r"recruit", r"talent\s*acquisition", r"stage\b|stagiair|intern(ship)?\b",
    r"student(enjob)?\b", r"call\s*center\s*agent|klantendienst(?!.*sales)",
    r"after-?sales\s*(technician|technieker|engineer)",  # technical after-sales is service, not sales
    r"software\s*(engineer|developer)|devops|data\s*engineer",  # IT titles that mention 'revenue' etc.
]
NEGATIVE_RE = re.compile("|".join(NEGATIVE_KEYWORDS), re.I)


def looks_like_sales(title: str) -> bool:
    """Cheap first pass. True = worth sending to the LLM classifier."""
    t = (title or "").strip()
    if not t:
        return False
    if NEGATIVE_RE.search(t):
        return False
    return bool(SALES_RE.search(t))


# ── 2. LLM classification prompt (replaces the IT prompt in scraper.py) ────────
# Ask for strict JSON so the parsing code in scraper.py can stay the same.
CLASSIFY_PROMPT = """You screen job vacancies for a Belgian recruitment agency that places SALES and
COMMERCIAL profiles: account managers, key account managers, business developers,
inside sales / SDR / BDR, sales engineers and presales, field sales and
vertegenwoordigers, customer success (commercial), partner/channel managers, sales
managers and directors.

NOT in scope: marketing-only roles, sales support / order administration, retail
shop staff and cashiers, customer service without a selling target, recruiters,
internships and student jobs, and any technical or IT role.

Given the vacancy below, answer with JSON only, no prose:
{
  "is_sales": true|false,
  "role_type": "account_manager"|"business_development"|"inside_sales"|"sales_engineer"|"field_sales"|"sales_management"|"customer_success"|"other_sales"|null,
  "tags": [up to 6 short tags: sector (e.g. "SaaS", "industrial", "FMCG", "logistics"), market ("B2B"/"B2C"), territory ("Benelux", "Flanders", "EMEA"), language requirements ("NL/FR/EN"), and seniority ("junior"/"senior")],
  "experience": "e.g. 3+ yrs" or null,
  "in_belgium": true|false|null
}

Title: {title}
Company: {company}
Page text:
{text}
"""

# scraper.py currently stores the tech stack in the "stack" field. For sales we
# store the "tags" list there instead — the dashboard shows whatever is in "stack"
# as chips, so no dashboard change is needed.
TAGS_FIELD = "stack"

# Dedup / state files should not collide with JobRadar if you ever run both
# scrapers from one checkout. Use these names in scraper.py for the sales run.
STATE_FILE = "state/seen_sales.json"
OUTPUT_FILE = "output/latest.json"
