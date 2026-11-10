# BuildShield: An SDLC Infrastructure Security Dashboard

BCS 3106 Software Engineering group project. A Django web dashboard that records
security findings across the five SITF pillars (Endpoint/IDE, VCS, CI/CD,
Registry, Production) and charts them with Matplotlib.

## Run it on your computer

Requires Python 3.12 (3.10+ works).

```bash
python -m venv venv
# Windows: venv\Scripts\activate    macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

# Development settings (Windows PowerShell: $env:DJANGO_DEBUG="true")
export DJANGO_DEBUG=true

python manage.py migrate
python manage.py seed_sitf --demo      # pillars, techniques, demo users and findings
python manage.py runserver
```

Open http://127.0.0.1:8000 and log in with a demo user. `seed_sitf --demo`
prints a random password for each one: `dev1` (Developer), `analyst1`
(Security Analyst) and `admin1` (Administrator). To make your own superuser:
`python manage.py createsuperuser`.

## Run the tests

```bash
python manage.py test -v 2
```

TC-01 (`TC01FindingStatusTests`) and TC-02 (`TC02AccessControlTests`) are the two
test cases in the Part 2 test plan.

## CI/CD

`.circleci/config.yml` runs on every push: install dependencies, Django checks,
a Bandit security scan, then the unit tests. Connect the GitHub repository at
https://circleci.com (log in with GitHub, then "Set up project").

## What each role can do

| Role | Can |
| --- | --- |
| Developer | View dashboard and findings, report findings, update status of findings they reported or own |
| Security Analyst | Everything a developer can, on any finding, plus assign owners and download the summary report |
| Administrator | Manage projects, and users and roles through `/admin/` |

## Secure coding practices used

- Secret key and debug mode come from environment variables; the app refuses to start in production without a key.
- Every view requires login; roles are checked on the server (`accounts/permissions.py`), not only hidden in the menu.
- Object-level checks: a developer cannot change someone else's finding.
- All input goes through Django forms; query filters accept only known values.
- Django ORM only (no raw SQL), CSRF tokens on every form, template auto-escaping.
- Secure cookies, HSTS, clickjacking and MIME-sniffing protection when `DEBUG` is off.
- Passwords need 10+ characters and are checked against common passwords.
- CSV export neutralises spreadsheet formula injection.
- Charts are drawn in memory; no user input is used in file paths.

## Project structure

```
accounts/      custom User model with roles, role_required decorator
findings/      models, forms, views, Matplotlib dashboard service, tests
templates/     HTML templates
static/css/    styling
.circleci/     CI/CD pipeline
```
## System Architecture

FactoryGuard follows a Django-based Model-View-Template (MVT)
architecture.

- Frontend: HTML, CSS and Django Templates
- Backend: Python and Django
- Database: SQLite (development)
- Visualization: Matplotlib
- Authentication: Django Authentication System
- Security: Role-based access control

## Development Team

FactoryGuard is developed collaboratively as part
of the BCS 3106 Software Engineering group project.

The project encourages collaborative development,
version control and secure software engineering practices.