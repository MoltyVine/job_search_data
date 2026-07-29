# Classification criteria — recruiter / job-opportunity conversations

Shared rules for Gmail and LinkedIn classification. Applied either by the Claude Code agent working through each source's thread dump (default — no network call, no API key), or by the optional `openrouter` backend for high-volume runs (see `classification:` in `config/participant.example.yaml`).

## Unit of filtering

**Conversation / thread** — all messages sharing one ID:

- Gmail: `X-GM-THRID`
- LinkedIn: `CONVERSATION ID`

Read the **full thread** for context.

## Core decision

**Include only** when this is clearly a conversation with a **real person** (recruiter, hiring manager, referrer, or company employee) about **one or more job opportunities** (roles the participant might take).

A recruiter pitching **several** openings in the same thread still counts — do **not** exclude just because more than one role is discussed.

**When unsure, exclude** (favor precision over recall).

### Must be true for include

1. A **named human** is involved (or clearly identifiable recruiter/TA), **or** the thread is interview scheduling with a named interviewer/recruiter.
2. The discussion is about **job opportunity(ies)** for the participant — at least one concrete role and/or company / agency client hiring context (not “jobs in general” marketing).
3. It is **directed at the participant** as a candidate (outreach, interview loop, application follow-up from a person).

Automated systems alone are **not** enough.

## Include — counterpart types

| Type | When |
|------|------|
| `agency_recruiter` | Staffing / contract recruiter pitching **one or more client roles** to the participant |
| `inhouse_recruiter` | Company TA / sourcer emailing the participant about role(s) |
| `hiring_manager` | Team leader hiring for their team |
| `referral_network` | Colleague **personally** referring the participant to **named open role(s)** (not a Slack channel blast) |
| `outbound_application` | Participant messaged a **person** about posted role(s) |
| `company_rep` | Company employee personally pointing the participant to openings |

Signals: personal greeting, role title(s), company, interview times, resume/Calendly ask, back-and-forth with the participant.

## Exclude (common false positives)

| Category | Examples |
|----------|----------|
| Job-match aggregators | Otta “New match: …”, LinkedIn Job Alerts digests |
| Mass careers marketing | “Careers@…”, employer newsletters, “New Year, New Career” blasts |
| Automated application receipts only | Greenhouse/Workday/Lever **noreply** “thanks for applying” with **no human** in the thread |
| EEO / survey / onboarding admin | EEO surveys, Workday pre-boarding task nags, password resets |
| Contracts / DocuSign / repayment | Severance, repayment letters, generic DocuSign |
| Channel digests | Slack/Teams “unread messages” that merely *mention* a job link |
| Personal / colleague | Catching up, tennis, recs *for them*, neighborhood |
| Housing / banking | Apartment sublease, roommate lease, personal loans / PLOC, mortgage |
| Generic connect spam | “I'd love to connect” with no role |
| Coaching / training marketing | Interview prep sales, bootcamps |
| Unrelated appointments | Bank appointments, movers, shopping |
| Events / product promos | Demos, gift cards, SaaS trials |

## Fields to extract (included only)

| Field | Notes |
|-------|-------|
| **Company** | End employer. If an agency never names the client, use `Undisclosed (via <agency or recruiter name>)` — never the literal word AgencyName |
| **Position title** | Primary role discussed; if several, list the main ones (semicolon-separated) or `Unspecified` if include but titles missing |
| **Recruiter/contact** | Human counterpart name |
| **Type** | One of the include types above (`ats_system` is **deprecated** — do not use for include) |
| **Reason** | One short sentence |

## Cross-check

Compare Gmail kept-thread count with LinkedIn summary rows for the same window. Expect overlap in companies, not identical counts.
