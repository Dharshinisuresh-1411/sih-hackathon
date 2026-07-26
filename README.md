# Panchayat Street Light Complaint and Repair Assignment System

## 1. Project Title
**Panchayat Street Light Complaint and Repair Assignment System** — a pole-centric complaint management platform for Panchayat street-light maintenance.

## 2. Problem Statement
A Panchayat currently records street-light complaints by telephone in a manual register. This leads to duplicate complaints for the same pole, electricians being dispatched multiple times to the same location, no visibility into which complaints are still open, no accountability for who assigned/closed a repair, and no way to identify poles that fail repeatedly and may need replacement instead of repeated repair.

## 3. Problem Understanding
The root cause of the duplication problem is that complaints are conceptually tied to **callers** (whoever phoned in), not to the physical **asset** (the pole) that is actually broken. Two people calling about the same dark pole today look, in a caller-centric system, like two unrelated complaints. A pole-centric model fixes this at the data-model level.

## 4. Proposed Solution
Every complaint is created against a specific, pre-registered **pole** (identified by a unique pole number). Before a new complaint is accepted, the system checks whether that pole already has an **active** (non-closed) complaint. If it does, the clerk is shown the existing complaint instead of a duplicate work order being silently created. All complaint history remains attached to the pole, so the Panchayat can see, per pole, how many times it has failed and when.

## 5. Key Innovation
> **Anchoring complaints to poles instead of callers solves the duplicate-complaint problem because "has this been reported already?" becomes a simple lookup on the pole's current open complaint — not a fuzzy match on caller name, phone number, or free-text description.** It also makes the repeat-offender question trivial: it's just `GROUP BY pole_id, COUNT(*)` over the complaints table, something that is effectively impossible to compute reliably from a caller-centric register.

## 6. Features
- Pole registry with ward/location/status
- Complaint intake with automatic duplicate-active-complaint detection
- Complaint list with filters (status, ward, pole, keyword)
- Open Complaints view grouped by ward ("what needs doing today")
- Electrician registry with active/inactive flag (server-enforced)
- Assignment workflow (OPEN → ASSIGNED)
- Repair & closure workflow with repair notes / replaced item (→ CLOSED)
- Repeat-Offender ranking view, calculated purely via SQL aggregation
- Dashboard with KPIs and Chart.js visualizations
- Optimistic-locking protection against double-closure race conditions
- Graceful handling of database-unavailable errors

## 7. Technology Stack
**Frontend:** HTML5, CSS3, vanilla JavaScript, Bootstrap 5, Font Awesome, Chart.js
**Backend:** Python 3, Flask, Flask-SQLAlchemy, Flask-CORS
**Database:** MySQL (primary) via PyMySQL, with a documented SQLite fallback
**Tooling:** VS Code, Git, GitHub, `venv`, pytest

## 8. System Architecture
```
Browser (Bootstrap + Chart.js + vanilla JS)
        │  fetch() calls
        ▼
Flask app (app.py) ── Blueprints ──▶ routes/*.py  (validation, business logic)
                                          │
                                          ▼
                                   Flask-SQLAlchemy models (models/*.py)
                                          │
                                          ▼
                                MySQL (or SQLite fallback)
```
Server-rendered Jinja2 pages provide the shell/navigation; all data is loaded client-side via the REST API. This keeps the frontend simple (no build step) while still being interactive.

## 9. ER Diagram
```
 POLES (1) ────────< (many) COMPLAINTS (1) ──── (1) WORK_RECORDS >──── (many-to-1) ELECTRICIANS
   id PK                     id PK                    id PK                         id PK
   pole_number UQ            pole_id FK                complaint_id FK UQ            name
   ward                      caller_name               electrician_id FK             phone
   location                  caller_phone               assigned_by                  is_active
   status                    description                assigned_at
   created_at                status                     closed_by
                             created_at                 closed_at
                             updated_at                 repair_note
                             version                     replaced_item
```
A text-based diagram is included above; `docs/er_diagram.png` is reserved as a placeholder for a drawn version (e.g. from dbdiagram.io) before your final submission.

## 10. Database Schema
**poles** — id PK, pole_number (unique, not null), ward (not null, indexed), location (not null), status (enum-like string), created_at
**complaints** — id PK, pole_id FK → poles.id (not null, indexed), caller_name, caller_phone, description, status (indexed), created_at (indexed), updated_at, version (int, for optimistic locking)
**electricians** — id PK, name, phone, is_active (bool, not null), created_at
**work_records** — id PK, complaint_id FK → complaints.id (unique — one work record per complaint), electrician_id FK → electricians.id, assigned_by, assigned_at, closed_by, closed_at, repair_note, replaced_item

**Design note:** `work_records` is deliberately kept as one row per complaint (created at assignment, updated at closure) rather than splitting into a separate `assignments` table, because in this workflow a complaint is assigned at most once before closure — a single-row accountability record is simpler and still captures "who assigned / who closed / what was repaired" without extra joins. If future requirements allow re-assignment (e.g. an electrician marked unavailable mid-job), splitting into `assignments` (many rows) becomes the better model.

## 11. Complaint State Machine
```
OPEN ──assign──▶ ASSIGNED ──start──▶ IN_PROGRESS ──close──▶ CLOSED
                     └───────────────────close───────────────▶ CLOSED
```
Allowed transitions are enforced centrally in `models/complaint.py` (`ALLOWED_TRANSITIONS`). Any request that doesn't match an allowed transition is rejected with `409 Conflict`. `CLOSED` is a terminal state — no further transitions are allowed from it.

## 12. API Documentation
All endpoints return JSON. Base URL: `http://localhost:5000`.

| Method | URL | Purpose | Request Body | Response |
|---|---|---|---|---|
| GET | `/api/poles` | List poles (optional `?ward=`) | — | `200` array of poles |
| GET | `/api/poles/<pole_number>` | Get one pole | — | `200` pole / `404` |
| POST | `/api/poles` | Create pole | `{pole_number, ward, location, status?}` | `201` pole / `400` / `409` |
| GET | `/api/complaints` | List complaints (`?status=&ward=&pole_number=&q=`) | — | `200` array |
| POST | `/api/complaints` | Register complaint | `{pole_number, caller_name, caller_phone, description}` | `201` new complaint, or `200` with `duplicate: true` and `existing_complaint`, or `404` if pole unknown |
| GET | `/api/complaints/open` | Open complaints grouped by ward | — | `200` `{ward: [complaints]}` |
| GET | `/api/complaints/<id>` | Get one complaint | — | `200` / `404` |
| POST | `/api/complaints/<id>/assign` | Assign to electrician | `{electrician_id, assigned_by}` | `200` updated complaint / `400` inactive electrician / `404` / `409` invalid transition |
| POST | `/api/complaints/<id>/start` | Mark work started | — | `200` / `409` |
| POST | `/api/complaints/<id>/close` | Close complaint with repair info | `{closed_by, repair_note, replaced_item?, version}` | `200` / `400` / `409` (version conflict / already closed) |
| GET | `/api/electricians` | List electricians (`?active_only=true`) | — | `200` array |
| POST | `/api/electricians` | Create electrician | `{name, phone, is_active?}` | `201` |
| POST | `/api/electricians/<id>/toggle` | Toggle active/inactive | — | `200` |
| GET | `/api/reports/summary` | Dashboard KPIs | — | `200` |
| GET | `/api/reports/open-by-ward` | Open complaint counts by ward | — | `200` array |
| GET | `/api/reports/status-distribution` | Complaint counts by status | — | `200` object |
| GET | `/api/reports/repeat-offenders` | Repeat-offender ranking | — | `200` `{ranking_period_months, poles: [...]}` |

## 13. Repeat-Offender Calculation
- **Ranking period:** last **12 months** by default (`REPEAT_OFFENDER_MONTHS` in `.env`, defaults to 12).
- **SQL logic** (see `routes/report_routes.py::repeat_offenders`):
  ```sql
  SELECT poles.*, COUNT(complaints.id) AS total_complaints, MAX(complaints.created_at) AS last_complaint_date
  FROM poles JOIN complaints ON complaints.pole_id = poles.id
  WHERE complaints.created_at >= NOW() - INTERVAL 12 MONTH
  GROUP BY poles.id
  ORDER BY total_complaints DESC;
  ```
- Complaints are grouped strictly by `pole_id`; the rank is the row's position after sorting by count descending. Poles with `total_complaints >= 4` are flagged `high_frequency` in the API response and highlighted in the UI as replacement candidates. Nothing here is manually entered — it is computed fresh on every request.

## 14. Failure Handling
- **Double closure (two staff closing the same complaint):** the client always sends the `version` number it last saw. Closure is performed as a single conditional `UPDATE ... WHERE id = :id AND version = :version`. If the row count affected is 0, another request already closed it first, and the server returns `409 Conflict` — "Complaint has already been closed by another user." This is optimistic locking; no explicit row locks are held, which keeps the implementation simple and safe for a 2-day build while still being correct under concurrent requests.
- **Inactive electrician:** enforced strictly server-side in `POST /api/complaints/<id>/assign` — the electrician's `is_active` flag is checked from the database regardless of what the client sends, so even a hand-crafted API request is rejected with `400` and a clear message.
- **Database unavailable:** every route wraps its DB access in try/except around `SQLAlchemyError`; the session is rolled back and the client is given a generic, safe message ("Unable to process your request because the database is temporarily unavailable. Please try again.") instead of a stack trace or a false success response. The frontend's `apiFetch()` wrapper also catches network-level failures with the same message.

## 15. Installation

### Using MySQL (primary)
1. Clone the repository: `git clone <your-repo-url> && cd panchayat-street-light`
2. Create a virtual environment: `python3 -m venv venv`
3. Activate it: `source venv/bin/activate` (Windows: `venv\Scripts\activate`)
4. Install dependencies: `pip install -r requirements.txt`
5. Create the MySQL database: `mysql -u root -p -e "CREATE DATABASE panchayat_street_light;"`
6. Copy `.env.example` to `.env` and fill in your MySQL credentials
7. Initialize + seed the database: `python seed/seed_data.py` (this creates all tables and inserts sample data)
8. Run the app: `python app.py`
9. Open `http://localhost:5000`

### Using SQLite (fallback, zero setup)
Set `DB_ENGINE=sqlite` in `.env` (or `export DB_ENGINE=sqlite`) and follow steps 1–4, 7–9 above — no MySQL server needed. A `panchayat.db` file is created automatically in the project root.

## 16. Testing
Run the automated suite: `pytest tests/ -v` (uses an in-memory SQLite database, independent of your dev database).

Covers: pole creation, duplicate pole rejection, unknown-pole complaint rejection, open-complaint duplicate detection, open-by-ward aggregation, assignment to active electrician, inactive-electrician rejection, successful closure, and rejection of a second closure attempt (409).

**Manual end-to-end scenario:** Register Complaint (new pole, no duplicate) → Assign to an active electrician → (optionally) Start → Close with repair note/replaced item → verify it disappears from Open Complaints → verify it now counts toward that pole's total in Repeat-Offender Poles.

## 17. Screenshots
_(Add screenshots here before submission)_
- Dashboard — `docs/screenshot_dashboard.png`
- Complaint Entry — `docs/screenshot_complaint_entry.png`
- Existing Open Complaint Warning — `docs/screenshot_duplicate_warning.png`
- Open Complaints — `docs/screenshot_open_complaints.png`
- Assignment — `docs/screenshot_assignment.png`
- Closure — `docs/screenshot_closure.png`
- Repeat-Offender View — `docs/screenshot_repeat_offenders.png`

## 18. Demo Flow (2 minutes)
1. Open **Dashboard** — point out KPIs and the "open complaints by ward" chart.
2. Go to **Register Complaint**, enter pole **P-002** — show the existing-open-complaint warning card, explain this is how duplicate dispatch is avoided.
3. Register a complaint on a pole with no open complaint — show the success card.
4. Go to **Assign**, assign the new complaint to an active electrician.
5. Try (via a second browser tab or curl) assigning an **inactive** electrician to show it gets rejected.
6. Go back to **Assign**, close the complaint with a repair note and replaced item.
7. Open **Open Complaints** — show it grouped by ward, and that the closed complaint is gone.
8. Open **Repeat-Offender Poles** — show P-002 at/near the top with its complaint count, and explain that this ranking is computed live from the database, flagging poles that may need replacement instead of continued repair.
#   s i h - h a c k a t h o n  
 #   s i h - h a c k a t h o n  
 