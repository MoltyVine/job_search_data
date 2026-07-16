# Classification criteria — recruiter / job-opportunity conversations

Shared rules for Gmail and LinkedIn classification (local LLM or Cursor agent).

## Unit of filtering

**Conversation / thread** — all messages sharing one ID:

- Gmail: `X-GM-THRID`
- LinkedIn: `CONVERSATION ID`

Read the **full thread** for context.

## Core decision

**Include only** when this is clearly a conversation with a **real person** (recruiter, hiring manager, referrer, or company employee) about a **specific job or position**.

**When unsure, exclude** (favor precision over recall).

### Must be true for include

1. A **named human** is involved (or clearly identifiable recruiter/TA), **or** the thread is interview scheduling with a named interviewer/recruiter.
2. The discussion is about a **specific role** (title and/or company / agency client role).
3. It is **directed at the participant** as a candidate (outreach, interview loop, application follow-up from a person).

Automated systems alone are **not** enough.

## Include — counterpart types

| Type | When |
|------|------|
| `agency_recruiter` | Staffing / contract recruiter pitching a **client role** to the participant |
| `inhouse_recruiter` | Company TA / sourcer emailing the participant about a role |
| `hiring_manager` | Team leader hiring for their team |
| `referral_network` | Colleague **personally** referring the participant to a **named open role** (not a Slack channel blast) |
| `outbound_application` | Participant messaged a **person** about a specific posted role |
| `company_rep` | Company employee personally pointing the participant to openings |

Signals: personal greeting, role title, company, interview times, resume/Calendly ask, back-and-forth with the participant.

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
| **Position title** | As stated; `Unspecified` if include but title missing |
| **Recruiter/contact** | Human counterpart name |
| **Type** | One of the include types above (`ats_system` is **deprecated** — do not use for include) |
| **Reason** | One short sentence |

## Cross-check

Compare Gmail kept-thread count with LinkedIn summary rows for the same window. Expect overlap in companies, not identical counts.
