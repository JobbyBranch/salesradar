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


# ── PROSPECTING SIGNALS ───────────────────────────────────────────────────────
# Sentences on the vacancy page that mention cold calling, telephone prospecting,
# outbound lead generation, hunting for new accounts, etc. These are the jobs
# where an outsourced cold-calling service is most relevant, so the dashboard
# lists them under "Topjobs" and highlights the matched wording.
#
# Each entry is a regex (case-insensitive). Keep them specific: a generic word
# like "klanten" would flag every page.
import re as _re

SIGNAL_PATTERNS = [
    # cold calling
    r"cold[\s-]*call\w*", r"koud\w*\s+(bellen|acquisitie|prospect\w*|benader\w*)",
    r"koude\s+(acquisitie|prospectie|bel\w*)", r"appels?\s+à\s+froid", r"prospection\s+à\s+froid",
    # telephone prospecting
    r"telefonisch\w*\s+(prospect\w*|acquisitie|benader\w*|contact\w*|verkoop\w*|klantenwerv\w*)",
    r"prospect\w*\s+(per|via|aan\s+de)\s+telefoon", r"prospection\s+t[ée]l[ée]phonique",
    r"t[ée]l[ée]prospect\w*", r"phoning", r"telesales", r"tele-?marketing",
    r"phone\s+prospect\w*", r"outbound\s+(calls?|calling|sales|prospect\w*|lead\w*)",
    r"bellen\s+(van|naar)\s+(prospect|nieuwe|potenti)\w*", r"actief\s+(uit)?bellen",
    # prospecting / acquisition in general
    r"prospect\w*", r"prospection", r"acquisitie", r"acquisition\s+de\s+(nouveaux\s+)?clients",
    r"new\s+business\s+(development|generation|hunting)?", r"hunt\w*",
    r"nieuwe\s+klanten\s+(te\s+)?(werv\w*|binnenhal\w*|aantrekk\w*|zoek\w*|vind\w*|benader\w*|overtuig\w*)",
    r"klanten\s*werv\w*", r"klantenwerving", r"canvass\w*", r"d[ée]marchage",
    r"lead\s*gen\w*", r"leadgeneratie", r"g[ée]n[ée]ration\s+de\s+leads",
    r"cold\s+outreach", r"outreach", r"appointment\s+setting",
    r"afspraken\s+(maken|(in)?plan\w*|vastleggen|boeken)", r"plan\w*\s+afspraken", r"(d[ée]croch\w*|fix\w*|prendre|prenez)\s+des\s+rendez-vous",
    r"pipeline\s+(opbouwen|building|vullen|uitbouwen)", r"build\w*\s+(a|your|the)(\s+own)?\s+pipeline",
]
SIGNAL_RE = _re.compile("|".join(f"({p})" for p in SIGNAL_PATTERNS), _re.I)

_SENTENCE_SPLIT = _re.compile(r"(?<=[.!?;])\s+|\n+|\s{3,}|\s[•·▪–—-]\s")


def find_signals(page_text: str, max_quotes: int = 6) -> dict:
    """Return {"terms": [...], "quotes": [...]} for a vacancy page.

    quotes = verbatim sentences (trimmed to ~240 chars) that contain a signal,
    strongest first; terms = the distinct matched words, lowercase.
    """
    text = _re.sub(r"[ \t\r\f\v]+", " ", page_text or "")
    terms, quotes, seen = [], [], set()
    for raw in _SENTENCE_SPLIT.split(text):
        s = raw.strip(" -•·|")
        if len(s) < 15:
            continue
        hits = [m.group(0).lower() for m in SIGNAL_RE.finditer(s)]
        if not hits:
            continue
        for h in hits:
            if h not in terms:
                terms.append(h)
        if len(s) > 240:
            # keep the window around the first hit
            i = max(0, SIGNAL_RE.search(s).start() - 100)
            s = ("…" if i else "") + s[i:i + 240].rstrip() + "…"
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        quotes.append({"text": s, "hits": len(hits)})
    quotes.sort(key=lambda q: -q["hits"])
    return {"terms": terms[:12], "quotes": [q["text"] for q in quotes[:max_quotes]]}
