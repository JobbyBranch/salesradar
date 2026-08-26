"""
sales_profile.py — loaded by scraper.py when RADAR_PROFILE=sales.

Everything that makes SalesRadar differ from JobRadar lives here: which titles
count, the yes/no question for the Claude classifier, and what the enrichment
step extracts per vacancy. The output schema of latest.json is unchanged, so the
dashboard reads it as-is (sales tags are stored in the "stack" field).

Keyword semantics follow scraper._match_any(): lowercase substring match for
terms longer than 4 characters, whole-word match for terms of 4 characters or
less. Exclusions always win over inclusions, and the Claude classifier decides
the rest.
"""

RADAR_NAME = "SalesRadar"
JOB_NOUN = "sales vacancies"

# ── Titles must contain at least one of these (NL / FR / EN) ─────────────────
INCLUDE_KEYWORDS = [
    # English
    "sales", "account manager", "accountmanager", "account executive",
    "key account", "business develop", "bdm", "bdr", "sdr", "presales",
    "pre-sales", "solution consultant", "solutions consultant",
    "customer success", "partner manager", "channel manager", "revenue",
    "export manager", "territory manager", "tender manager", "bid manager",
    "growth manager", "hunter", "new business",
    # Dutch
    "commercieel", "commerciële", "commerciele", "vertegenwoordig", "verkoop",
    "verkoper", "accountbeheer", "klantenbeheer", "relatiebeheer",
    "buitendienst", "binnendienst", "zakelijk adviseur", "klantenadviseur",
    # French
    "commercial", "représentant", "representant", "délégué", "delegue",
    "chargé d'affaires", "charge d'affaires", "chargé de clientèle",
    "charge de clientele", "responsable ventes", "responsable des ventes",
    "technico-commercial", "développement commercial",
]

# ── ...and none of these. Exclusions win over inclusions ─────────────────────
EXCLUDE_KEYWORDS = [
    # sales-adjacent but not a selling role
    "sales support", "sales assistant", "sales admin", "sales administrat",
    "order desk", "order entry", "orderverwerking", "order handling",
    "marketeer", "digital marketing", "content marketing", "marketing assistant",
    "marketing intern", "social media", "copywriter", "communicat",
    "after-sales tech", "aftersales tech", "after sales tech", "service technic",
    "customer care", "klantendienst", "helpdesk", "call center agent",
    # retail floor / cashier
    "cashier", "kassa", "winkelmedewerker", "winkelbediende", "shop assistant",
    "retail assistant", "store manager", "filiaal",
    # HR / finance / legal
    "recruit", "talent acquisition", "hr business", "human resources",
    "payroll", "accountant", "boekhoud", "controller", "jurist", "legal",
    # students / internships
    "stagiair", "internship", "studentenjob", "jobstudent", "werkstudent",
    # technical / IT / trades
    "software", "devops", "data engineer",
    "system engineer", "network engineer", "security engineer",
    "mechanical", "elektricien", "electricien", "lasser", "monteur",
    "chauffeur", "driver", "magazijn", "warehouse", "productie", "operator",
    "cleaning", "schoonma", "verpleeg", "nurse", "zorgkundige",
]

# ── Yes/no question for the Claude classifier (title-level) ──────────────────
CLASSIFY_QUESTION = (
    "Is this a SALES or COMMERCIAL job with a selling responsibility (account "
    "manager, key account manager, business developer, inside sales / SDR / BDR, "
    "sales engineer or presales, field sales / vertegenwoordiger, customer "
    "success with commercial targets, partner or channel manager, sales manager "
    "or director)? NOT sales: marketing-only roles, sales support / order "
    "administration, retail shop staff and cashiers, customer service without "
    "a selling target, recruiters, HR, finance, legal, internships and student "
    "jobs, technical / IT / engineering roles, after-sales service technicians, "
    "and bare category words that are not a concrete vacancy (like 'Sales', "
    "'Jobs', 'Commercieel'). If the title clearly states a work location "
    "outside Belgium (e.g. a Dutch, German or French city), answer no. Judge in "
    "the context of the company. "
)

# ── Per-vacancy enrichment prompt (page-level). Must return the same JSON keys
#    as JobRadar's prompt: stack, experience, contact_name, contact_email,
#    in_belgium. For sales, "stack" carries short commercial tags instead of
#    technologies — the dashboard shows them as chips.
ENRICH_INSTRUCTIONS = (
    "Extract from this sales vacancy: up to 6 short TAGS describing the "
    "commercial context (sector such as 'SaaS', 'industrial', 'FMCG', "
    "'logistics', 'construction'; market 'B2B' or 'B2C'; territory such as "
    "'Benelux', 'Flanders', 'Wallonia', 'EMEA'; required languages like "
    "'NL/FR/EN'; seniority 'junior' or 'senior'; 'hunter' or 'farmer' when "
    "the page says so), the required years of experience, and the CONTACT "
    "PERSON for applications (the recruiter/hiring manager named on the page, "
    "with their e-mail if shown — pick from the found addresses when they "
    "match; null when the page names nobody). Reply ONLY with JSON: "
    '{"stack": ["B2B", "SaaS", ...], "experience": "3+ yrs" or null, '
    '"contact_name": "Hilde Peeters" or null, '
    '"contact_email": "hilde@bedrijf.be" or null, '
    '"in_belgium": true/false/null}. For in_belgium: true when the job is '
    "located in Belgium or remote-from-Belgium; false when the location is "
    "clearly another country (Netherlands, France, Germany, US...); null when "
    "unclear."
)
