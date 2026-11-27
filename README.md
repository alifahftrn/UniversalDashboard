# Universal Dashboard Studio

Self-Service Multi-Source Business Intelligence Platform.

## Project Information

- Architecture: Extraction-First
- Pattern: Modular Monolith
- Team: 4 Developers
- Development Period: 8 Weeks
- Reference: RFC v2.3 Final

## Technology Stack

- Python 3.13.17
- Django 5.2 LTS
- PostgreSQL 18.7
- SQLAlchemy
- Pandas
- NumPy
- HTML, CSS, JavaScript
- Apache ECharts (planned)
- GridStack.js (planned)

## Architecture

External Data Sources
    -> Extraction
    -> Internal PostgreSQL (Raw Dataset)
    -> Transformation
    -> Validation
    -> Analytics
    -> Visualization
    -> Dashboard

External databases are read-only.
Analytics must run on internal datasets only.

## Team Responsibilities

| PIC | Responsibility |
| --- | --- |
| PIC 1 | Core Backend and Integration |
| PIC 2 | Data Connectivity and Extraction |
| PIC 3 | Data Processing and Analytics |
| PIC 4 | Visualization and Dashboard |

## Installation

### 1. Clone Repository

Clone the team repository and open its root folder.

### 2. Create Virtual Environment

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
```

Required Python version: 3.13.17.

### 3. Install Dependencies

```powershell
python -m pip install -r requirements.txt
python -m pip check
```

### 4. Create PostgreSQL Database

Login as PostgreSQL administrator.

```powershell
psql -U postgres -h localhost -p 5432
```

Run the following commands if the user and database
do not already exist:

```sql
CREATE USER uds_app;
\password uds_app

CREATE DATABASE universal_dashboard_db
OWNER uds_app;
```

Exit PostgreSQL:

```sql
\q
```

### 5. Configure Environment

```powershell
Copy-Item .env.example .env
```

Generate a Django secret key:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Edit .env using your own secret key
and PostgreSQL password.

Never commit the .env file.

### 6. Initialize Database Schemas

```powershell
psql -U uds_app -h localhost -p 5432 -d universal_dashboard_db -v ON_ERROR_STOP=1 -f scripts/init_schemas.sql
```

### 7. Run Database Migration

```powershell
python manage.py migrate
```

### 8. Create Local Admin Account

```powershell
python manage.py createsuperuser
```

### 9. Run Application

```powershell
python manage.py runserver
```

Application:

http://127.0.0.1:8000/

Administration:

http://127.0.0.1:8000/admin/

## Development Workflow

- main: Stable version
- develop: Integration branch
- feature/*: Development branches

Create feature branches from develop.
Submit pull requests to develop.
Do not push directly to main.

## Integration Contracts

See docs/contracts/README.md.

Synthetic test datasets are available
in tests/fixtures/.

## Security Rules

- Never commit passwords or secret keys.
- Never commit real company datasets.
- Never modify external source databases.
- Never run analytical queries on source databases.
- Use a separate local database for each developer.

## Current Status

Phase 1 - Foundation.

Core application, database configuration,
navigation, proposed integration contracts,
and synthetic fixtures are available.

Business modules are under development.