"""Legacy / optional Gmail prefilter helpers (header/subject heuristics).

Primary classification is LLM- or Cursor-based via scripts/dump_threads.py →
classify_threads.py → apply_decisions.py. This module remains for optional
noise prefilters and shared header helpers — not the source of truth.
"""

import re
from email.header import decode_header
from email.utils import getaddresses

from blacklist import blacklist
from participant_config import load_participant_config, my_emails

_config = load_participant_config()
MY_EMAILS = my_emails(_config)
BLACKLIST = {addr.lower() for addr in blacklist}

PERSONAL_EMAIL = re.compile(
    r"@(gmail|yahoo|hotmail|outlook|icloud|comcast|aol|live)\.",
    re.I,
)

ATS_DOMAIN = re.compile(
    r"(greenhouse-mail\.io|myworkday\.com|mail\.amazon\.jobs|"
    r"talent\.icims\.com|freshteam\.com|smartrecruiters\.com|"
    r"email\.amazon\.com|workablemail\.com|careers\.tiktok|"
    r"hire\.lever\.co|\.roche\.com|chime\.com|pinterest\.com|"
    r"bytedance\.com)",
    re.I,
)

EXCLUDE_SENDER = re.compile(
    r"(slack\.com|quora\.com|jobalerts-noreply@linkedin|curiosity-noreply|"
    r"messaging-digest-noreply|mailer-daemon|reply\.craigslist|sfballet|"
    r"reef\.org|jefit|library|notices\.rei|ce\.angi|aicollective|"
    r"hojykubpbnb|oncueapp|e-vanguard|topds\.us|"
    r"english-personalized-digest|datainterview\.com|turing\.com|"
    r"meta\.com|facebookmail\.com|progressiveautomations|"
    r"autozone\.com|ebay\.|turbotax|intuit\.com|firstrepublic\.com|"
    r"moving\.com|haulingmoses|fb_terminations|facebookcontracts|"
    r"sftoyota|sanfranciscotoyota|metaquest|jobot\.|humana\.com|"
    r"otta\.|hellofromotta|diverdan|kohls\.)",
    re.I,
)

EXCLUDE_SUBJECT = re.compile(
    r"(unread messages|quora digest|new jobs for|30\+ new jobs|"
    r"job openings at|library news|weekly workout|roof quote|"
    r"sublease|302a kipling|loan document|first republic|\bploc\b|"
    r"move is confirmed|move quote|\bxmas\b|documentation request|"
    r"\bseverance\b|employment claims|\blawsuit\b|"
    r"why most candidates flunk|approach the current job market|"
    r"you missed \d+ us job offers|hotel uses video|gear mail|"
    r"password reset|docuSign.*rental|american housewrights|"
    r"biotech park - hype|progressive automations|john elmund phone|"
    r"recently updated near|1br/1ba|1bd/1ba|\bapartment\b|condo w/parking|"
    r"muni transportation|spacious 1 bdrm|dolores park view|"
    r"amazing one bedroom|stunning 1bd|dreamy unit|top, third floor|"
    r"beautiful, sunny apartment|video! jr 1bd|epic rea-|"
    r"order.?s confirmed|order is on the road|vehicle service payment|"
    r"booking confirmed|spring sale|return accepted|maintenance window|"
    r"repayment letter|leaving facebook|supplemental privacy policy|"
    r"important information|msci sector|recommended jobs|"
    r"rate your experience working with the talent acq|"
    r"tell us about your experience applying|"
    r"thanks for your interest in apple\.?$|alice thinks you would|"
    r"digital ops|everything worked out|linkedin next steps!$|"
    r"you may know someone|team match availability|"
    r"opportunities at \w+|final stages at \w+|"
    r"new match:|hello from otta|thanks for applying to \w+$|"
    r"notifications \d+$|"
    r"new jobs match your search|new appointment with|"
    r"message about your appointment|free onsite estimate|"
    r"next steps: movers|order update|"
    r"signed:.*repayment letter)",
    re.I,
)

def _recruit_subject_pattern() -> str:
    core = (
        r"(interview|offer|application|applied|applying|role|position|"
        r"opportunity|recruit|hiring|engineer|scientist|"
        r"machine learning|candidate|phone screen|screening|onsite|"
        r"compensation|salary|resume|intro call|introductory call|"
        r"intro:|meeting|schedul|call with|chat with|"
        r"connect:|follow.?up from|follow.?up on|next step|"
        r"thank you for (your )?(interest|applying)|"
        r"status update|greenhouse|inmail|declined:|invitation:|"
        r"prep call|direct.?hire|remote|opening|\bjob\b|"
        r"staff engineer|senior engineer|data engineer|data scientist|"
        r"ml engineer|software engineer|principal |lead data|"
        r"phone interview|onsite interview|take.?home|"
        r"thanks for applying|update on your application|your application to|"
        r"application received|application update|"
        r"confirmation of your interview|regarding your application|"
        r"eeo survey|tetrascience|tiktok:|netflix application|"
        r"workable|recruiting team|microsoft recruiting|"
        r"hello from [A-Za-z]|new hire agenda|"
        r"betfanatics|gridware|roblox|lyft|glean|moveworks|portal|vir\.|"
        r"affirm|apella|trm labs|lutron|apixio|genentech|akili|"
        r"vmware|gsk|bristol|vizgen|betfanatics|gridmatic|"
        r"eightfold|gauntlet|pikky|ndt|agilent|fanatics|"
        r"merck role|data function|lead the data|"
        r"job opportunities for you|exciting career|we want you @|"
        r"remote swe|direct hire|direct-hire|canceled event: interview|"
        r"referred to intuit|imprivata recruiting|"
        r"spring health|resideo|chegg|"
        r"senior/principal data|sr\. data scientist|"
        r"ml/nlp opportunities|data science opportunity|"
        r"quality control iii"
    )
    names = [
        re.escape(_config["participant"].get("first_name", "")),
        re.escape(_config["participant"].get("last_name", "")),
    ]
    names = [n for n in names if n]
    if names:
        core += r"|" + "|".join(names)
    return core + r")"


RECRUIT_SUBJECT = re.compile(_recruit_subject_pattern(), re.I)

AUTO_LOCAL = re.compile(
    r"(noreply|no-reply|no_reply|donotreply|do-not-reply|notification|"
    r"notifications|notify|mailer-daemon|bounce|newsletter|digest|"
    r"jobalerts|jobs-noreply|messages-noreply|postmaster|autoreply|"
    r"workdaynotification|english-personalized-digest|participant_services)",
    re.I,
)


def decode_header_value(raw: str) -> str:
    parts = []
    for fragment, charset in decode_header(raw or ""):
        if isinstance(fragment, bytes):
            parts.append(fragment.decode(charset or "utf-8", errors="replace"))
        else:
            parts.append(fragment)
    return "".join(parts)


def parse_from(msg) -> tuple[str, str]:
    addrs = getaddresses([msg.get("From", "")])
    if not addrs:
        return "", ""
    display, addr = addrs[0]
    return decode_header_value(display), addr.lower()


def is_mine(addr: str) -> bool:
    return addr.lower() in MY_EMAILS


def sender_kind(display: str, addr: str, msg) -> str:
    """Return mine, exclude, ats, auto, or human."""
    addr = (addr or "").lower()
    display = decode_header_value(display or "")

    if is_mine(addr):
        return "mine"
    if addr in BLACKLIST or EXCLUDE_SENDER.search(addr):
        return "exclude"
    if EXCLUDE_SENDER.search(display):
        return "exclude"

    if msg.get("Auto-Submitted", "").lower() not in ("", "no"):
        if ATS_DOMAIN.search(addr) or "automatic reply" in display.lower():
            return "human"
        return "auto"

    precedence = (msg.get("Precedence") or "").lower()
    if precedence in ("bulk", "junk", "list") and not ATS_DOMAIN.search(addr):
        return "auto"

    if AUTO_LOCAL.search(addr):
        if ATS_DOMAIN.search(addr):
            return "ats"
        if addr == "inmail-hit-reply@linkedin.com":
            return "human"
        if addr.endswith("@mail.amazon.jobs") or "hire_the_best@email.amazon.com" in addr:
            return "ats"
        if "jobs-noreply@linkedin.com" in addr:
            return "ats"
        return "auto"

    if addr.endswith("@linkedin.com"):
        if _looks_like_person_name(display) and "job alert" not in display.lower():
            return "human"
        return "auto"

    return "human"


def _looks_like_person_name(display: str) -> bool:
    display = display.strip().strip('"').strip("'")
    if not display or "@" in display:
        return False
    parts = [p for p in re.split(r"\s+", display) if p]
    return len(parts) >= 2 and not (display.isupper() and len(display) > 10)


def is_excluded_topic(subject: str) -> bool:
    return bool(EXCLUDE_SUBJECT.search(decode_header_value(subject)))


def is_recruit_signal(subject: str) -> bool:
    return bool(RECRUIT_SUBJECT.search(decode_header_value(subject)))


def seeds_recruiter_thread(display: str, addr: str, msg, subject: str) -> bool:
    """True if this message anchors a recruiter/job thread."""
    if is_excluded_topic(subject):
        return False

    kind = sender_kind(display, addr, msg)
    if kind == "exclude":
        return False
    if kind == "ats":
        return True
    if is_recruit_signal(subject):
        return True
    return False


def include_in_recruiter_thread(display: str, addr: str, msg, subject: str) -> bool:
    """True if this message should be kept inside a seeded thread."""
    if is_excluded_topic(subject):
        return False

    kind = sender_kind(display, addr, msg)
    if kind == "exclude":
        return False
    if kind in ("human", "mine", "ats"):
        return True
    if kind == "auto":
        if "jobalerts" in addr:
            return False
        if EXCLUDE_SENDER.search(addr):
            return False
        if is_recruit_signal(subject) or ATS_DOMAIN.search(addr):
            return True
    return False
