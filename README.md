# Panchayat Street Light Complaint & Repair Assignment System

A robust, pole-centric complaint management and repair coordination platform designed specifically for Panchayat street-light maintenance. 

---

## 📋 Project Description

### 1. Problem Statement
In typical Panchayats, street-light complaints are logged manually via telephone calls into physical registers. This traditional workflow suffers from several issues:
* **Duplicate complaints** are registered for the same non-functional pole, since complaints are indexed by caller rather than by physical asset.
* **Redundant dispatches** occur when multiple electricians are sent to inspect or repair the same light pole.
* **Lack of visibility** makes it difficult to track which complaints are open, who they are assigned to, or how long they have been pending.
* **No audit trail** for who assigned or closed a repair ticket, hindering accountability.
* **No intelligence** on recurring issues to identify "repeat-offender" poles that need replacement rather than temporary repairs.

### 2. The Solution: Pole-Centric Model
This system addresses the root cause of these issues by transitioning from a caller-centric design to a **pole-centric design**. 
* Every complaint is anchored to a unique, pre-registered **Pole ID**.
* Before registering a new complaint, the system performs a lookup for active (non-closed) complaints on that pole. If an active complaint exists, the operator is prompted with the existing ticket details, preventing duplicates.
* Historical records stay permanently linked to the specific pole, facilitating effortless health reporting and analysis.

### 3. Key Features
* **Pole Registry:** Detailed records of each pole (unique pole number, ward number, location, status).
* **Smart Intake:** Complaint submission with automatic duplicate checking.
* **Ward-wise Aggregation:** Open complaints grouped dynamically by ward for easy daily task dispatching.
* **Electrician Registry:** Active/Inactive status management to prevent assigning tickets to unavailable personnel.
* **State Machine Workflow:** Governed lifecycle transitions: `OPEN` ➔ `ASSIGNED` (➔ `IN_PROGRESS`) ➔ `CLOSED`.
* **Repeat-Offender Analyzer:** Automatic SQL-based ranking of poles with the highest failure rates over a configurable time window (e.g., 12 months) to flag replacement candidates.
* **Real-time Dashboard:** KPI summaries, status distribution charts, and ward workloads powered by Chart.js.
* **Resilient Infrastructure:** 
  * **Optimistic Locking:** Double-closure race conditions are prevented using a database `version` column.
  * **Database Fail-safe:** Graceful error handling in case of DB connection loss with friendly user messages instead of app crashes.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | **Python 3**, **Flask** | Server logic, modular routes, and RESTful API endpoints. |
| **ORM** | **Flask-SQLAlchemy** | Object-Relational Mapping for database queries and updates. |
| **Database** | **MySQL** (Primary) / **SQLite** (Fallback) | Relational storage for poles, electricians, complaints, and work records. |
| **Frontend** | **HTML5**, **CSS3**, **Vanilla JS** | Interactive shell pages built with **Bootstrap 5** and **Font Awesome**. |
| **Visualizations** | **Chart.js** | Live interactive charts on the dashboard. |
| **Testing** | **pytest** | Unit and integration test suites. |
| **Tooling** | **python-dotenv**, **venv** | Environment configuration and isolated dependency management. |

---

## ⚙️ System Architecture

```
                       ┌─────────────────────────┐
                       │ Browser Client          │
                       │ (HTML5/CSS3/JS/Chart.js)│
                       └────────────┬────────────┘
                                    │
                                    ▼ HTTP REST APIs
                       ┌─────────────────────────┐
                       │ Flask Application       │
                       │ (app.py)                │
                       └────────────┬────────────┘
                                    │
                                    ▼ Registers Blueprints
                       ┌─────────────────────────┐
                       │ Blueprints & Routes     │
                       │ (routes/*.py)           │
                       └────────────┬────────────┘
                                    │
                                    ▼ Maps Database
                       ┌─────────────────────────┐
                       │ SQLAlchemy Models       │
                       │ (models/*.py)           │
                       └────────────┬────────────┘
                                    │
                        ┌───────────┴───────────┐
                        ▼                       ▼
            ┌──────────────────────┐  ┌──────────────────┐
            │ MySQL Database       │  │ SQLite Fallback  │
            │ (Production / Demo)  │  │ (Zero-Setup Dev) │
            └──────────────────────┘  └──────────────────┘
```

---

## 🗄️ Database Schema & Relationships

```
 ┌──────────────┐         ┌───────────────┐         ┌─────────────────┐         ┌──────────────┐
 │    POLES     │         │  COMPLAINTS   │         │  WORK_RECORDS   │         │ ELECTRICIANS │
 ├──────────────┤         ├───────────────┤         ├─────────────────┤         ├──────────────┤
 │ PK | id      │1       *│ PK | id       │1       1│ PK | id         │*       1│ PK | id      │
 │    pole_num  ├────────>│ FK | pole_id  ├────────>│ FK | complaint_id│<────────┤    name      │
 │    ward      │         │    caller_name│         │ FK | elect_id   │        │    phone     │
 │    location  │         │    phone      │         │    assigned_by  │        │    is_active │
 │    status    │         │    status     │         │    assigned_at  │        └──────────────┘
 └──────────────┘         │    version    │         │    closed_by    │
                          └───────────────┘         │    closed_at    │
                                                    │    repair_note  │
                                                    │    replaced_item│
                                                    └─────────────────┘
```

---

## 🚀 Installation & Execution Steps

### Prerequisites
* **Python 3.8+** installed on your system.
* (Optional) **MySQL Server** running locally.

---

### Step 1: Clone the Repository
Open a terminal/command prompt and clone the workspace:
```bash
git clone <repository_url>
cd panchayat-street-light/panchayat-street-light
```

### Step 2: Set up a Virtual Environment
Create and activate an isolated Python environment:

* **On Windows:**
  ```powershell
  python -m venv venv
  .\venv\Scripts\activate
  ```
* **On macOS/Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### Step 3: Install Dependencies
Run `pip` to install the required Python packages:
```bash
pip install -r requirements.txt
```

### Step 4: Environment Configuration (`.env`)
Copy the template `.env.example` file to create your local configurations:
```bash
cp .env.example .env
```
Open the `.env` file in an editor. You can configure the system to run on **SQLite** (requires zero setup) or **MySQL**.

#### Option A: Quick-start Configuration using SQLite (Recommended)
Edit your `.env` to specify `sqlite` as the engine:
```env
DB_ENGINE=sqlite
REPEAT_OFFENDER_MONTHS=12
SECRET_KEY=dev-secret-change-me
```
*A local database file (`panchayat.db`) will be automatically created in the project root.*

#### Option B: Production Setup using MySQL
Ensure your MySQL server is running, then configure your connection details:
```env
DB_ENGINE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=panchayat_street_light
REPEAT_OFFENDER_MONTHS=12
SECRET_KEY=dev-secret-change-me
```
*Note: Make sure to create the database inside MySQL before continuing:*
```sql
CREATE DATABASE panchayat_street_light;
```

---

### Step 5: Database Seeding
Populate the database tables and insert initial test data (registered poles, sample complaints, and electricians):
```bash
python seed/seed_data.py
```

### Step 6: Start the Application
Launch the Flask development server:
```bash
python app.py
```
* The application will run at **`http://localhost:5000`**.
* Open your browser and navigate to `http://localhost:5000` to access the Dashboard.

---

<<<<<<< HEAD
## 18. Demo Flow (2 minutes)
1. Open **Dashboard** — point out KPIs and the "open complaints by ward" chart.
2. Go to **Register Complaint**, enter pole **P-002** — show the existing-open-complaint warning card, explain this is how duplicate dispatch is avoided.
3. Register a complaint on a pole with no open complaint — show the success card.
4. Go to **Assign**, assign the new complaint to an active electrician.
5. Try (via a second browser tab or curl) assigning an **inactive** electrician to show it gets rejected.
6. Go back to **Assign**, close the complaint with a repair note and replaced item.
7. Open **Open Complaints** — show it grouped by ward, and that the closed complaint is gone.
8. Open **Repeat-Offender Poles** — show P-002 at/near the top with its complaint count, and explain that this ranking is computed live from the database, flagging poles that may need replacement instead of continued repair.
#   s i h - h a c k a t h o n 
 
 #   s i h - h a c k a t h o n 
 
 
## demonstration video link

https://drive.google.com/file/d/1bYYAY_J493YanaFYxsSrfFlkmYe3qg5x/view?t=88.899




#NEW CHANGED PROJECT DEMONSTRATION VIDEO


https://drive.google.com/file/d/12GEiWst78WdPpASWl9jcD72Mre8GBaw2/view?t=6.309
=======
## 🧪 Testing

To run the automated test suite, execute the following command in the project directory:
```bash
pytest tests/ -v
```
*The test suite automatically spins up an isolated, in-memory SQLite database, running all test scenarios without affecting your active development data.*

### Verified Test Cases
1. **Pole Creation:** Registering new poles and preventing duplicate pole numbers.
2. **Intake Validation:** Rejecting complaints filed on non-existent poles.
3. **Duplicate Prevention:** Alerting and blocking new complaints on poles with existing active complaints.
4. **Aggregations:** Correctly grouping open complaints ward-wise.
5. **Assignment Logic:** Assigning tickets to active electricians while rejecting assignments to inactive ones.
6. **Concurrency/Race Conditions:** Validating optimistic locking behavior under double-closure attempts.

---

## 💡 Failure Recovery Features

* **Double Closure Resolution (Optimistic Locking):** 
  If two dashboard users attempt to close the same complaint at the same time, the system matches the ticket's `version` number. The transaction updates the state only if the version is unchanged. The second request is rejected with a `409 Conflict` status, informing the user that the complaint has already been resolved.
* **Electrician Availability Safeguards:** 
  The backend strictly evaluates the electrician’s active status in database records prior to assignment. Client-side attempts to assign inactive operators by modifying API request payloads are caught and rejected with a `400 Bad Request`.
* **Database Connection Failure handling:** 
  All routes wrapping DB access capture `SQLAlchemyError`. If the database crashes or disconnects, the API triggers an automatic fallback message, informing the client of database unavailability, rather than exposing internal stack traces.
>>>>>>> c54c3f5 ( final change)

 demonstration video of changed 
 
https://drive.google.com/file/d/12GEiWst78WdPpASWl9jcD72Mre8GBaw2/view?t=6.309
