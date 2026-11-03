# University Problem Reporting System (UPRS)

**A Django-based campus issue reporting and management platform**

**University:** University of Asia Pacific (UAP), Department of Computer Science and Engineering  
**Course:** CSE 302 — Object Oriented Programming II Lab  
**Repository:** [MH-Shanto56/University-Problem-Reporting-System](https://github.com/MH-Shanto56/University-Problem-Reporting-System)

---

## Overview

University Problem Reporting System (UPRS) provides a central place for students to report campus problems and follow their progress. Students can describe an issue, choose its location, attach a photo and view updates. University staff and administrators can review, manage and resolve reported problems.

The application is built with Django and uses separate apps for accounts, departments, locations and issues.

## Key Features

- **Student accounts:** registration, login, logout, profile management and notifications.
- **Problem reporting:** submit issues with a title, description, category, priority, location and optional image.
- **Issue management:** view issue details, update or delete reports subject to permissions, and track status.
- **Location selection:** choose buildings, floors, rooms, landmarks and equipment; use location-related management forms and a campus map view.
- **Department workflows:** department dashboard and department performance pages.
- **Admin portal:** manage reported issues, department information, locations, priority, assignments and audit/history pages.
- **Community engagement:** support/vote on issues, comment and view a leaderboard.
- **Resolution process:** work reports, resolution verification, closure and reopen requests.
- **Offline/PWA components:** manifest, service-worker endpoint, offline fallback page and offline-sync endpoint.

> These features are documented from the code, models, URL routes and templates in the repository. They are not a claim that every workflow has passed end-to-end browser testing.

## Technology Stack

| Area | Technology |
| --- | --- |
| Backend | Python, Django |
| Frontend | HTML, CSS, JavaScript, Django Templates |
| Database | SQLite |
| Image handling | Pillow and Django `ImageField` |
| Map interface | Leaflet (local static assets) |
| Version control | Git and GitHub |

Dependencies are listed in [`requirements.txt`](requirements.txt).

## Django Applications

| App | Responsibility |
| --- | --- |
| `accounts/` | Authentication, user profiles and notifications |
| `departments/` | Department records, staff dashboards and performance views |
| `locations/` | Buildings, floors, rooms, landmarks, equipment, areas and map/location management |
| `issues/` | Issue reporting, status tracking, comments, voting, resolution workflows and admin portal |

### Important Models

- **accounts:** `UserProfile`, `Notification`
- **departments:** `Department`
- **locations:** `Building`, `Floor`, `Room`, `Landmark`, `Equipment`, `Area`
- **issues:** `Issue`, `Category`, plus issue-related feedback, comments, votes and resolution/history records

The project uses Django's built-in authentication user model and relationships between these apps.

## Project Structure

```text
University-Problem-Reporting-System/
├── accounts/                 # Accounts, profiles, notifications
├── departments/              # Departments and staff views
├── locations/                # Buildings, rooms, landmarks, location tools
├── issues/                   # Problems, comments, resolution and admin views
│   └── migrations/           # Issue database migrations
├── mysite/                   # Django settings, main URLs, ASGI and WSGI
├── templates/                # HTML templates
│   ├── admin/                # Custom admin portal pages
│   ├── locations/            # Location CRUD pages
│   └── registration/         # Login, registration and profile pages
├── static/                   # CSS, icons, Leaflet assets and PWA manifest
├── manage.py
├── requirements.txt
├── .gitignore
└── README.md
```

The local SQLite database (`db.sqlite3`), virtual environment (`.venv/`) and uploaded media (`media/`) are ignored by Git.

## Getting Started (Windows / PyCharm)

### 1. Clone the repository

```powershell
git clone https://github.com/MH-Shanto56/University-Problem-Reporting-System.git
cd University-Problem-Reporting-System
```

### 2. Create and activate a virtual environment

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install the dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Create an administrator account

```powershell
python manage.py createsuperuser
```

### 5. Start the development server

```powershell
python manage.py runserver
```

Open **http://127.0.0.1:8000/** in your browser.

> This is a local development setup, not a production deployment guide.

## Main Routes

| Page | Local URL |
| --- | --- |
| Homepage | `http://127.0.0.1:8000/` |
| Register | `http://127.0.0.1:8000/register/` |
| Login | `http://127.0.0.1:8000/login/` |
| Student dashboard | `http://127.0.0.1:8000/dashboard/` |
| Report a problem | `http://127.0.0.1:8000/report/` |
| Notifications | `http://127.0.0.1:8000/notifications/` |
| Locations | `http://127.0.0.1:8000/locations/` |
| Campus map | `http://127.0.0.1:8000/map/` |
| Department dashboard | `http://127.0.0.1:8000/department/dashboard/` |
| Custom admin portal | `http://127.0.0.1:8000/admin-portal/` |
| Django admin | `http://127.0.0.1:8000/admin/` |

Certain pages require the appropriate student, staff or administrator permissions.

## Example Workflow

1. A student registers or logs in.
2. The student opens **Report a Problem**.
3. The student enters issue details, chooses a campus location and optionally uploads an image.
4. The report appears in the system for tracking and management.
5. Authorized staff or administrators review and update the issue.
6. Resolution, verification, feedback or reopening actions can be used as appropriate.

## Team Contributions

GitHub history shows contributions from four accounts:

| GitHub username | Main areas visible in commit history |
| --- | --- |
| [MH-Shanto56](https://github.com/MH-Shanto56) | Main Django configuration, issues, dashboards, templates and frontend/static assets |
| [arabin30](https://github.com/arabin30) | Location models, forms, views, URLs and templates |
| [Jannat108](https://github.com/Jannat108) | Accounts, authentication, profiles and notification templates |
| [Nur-107](https://github.com/Nur-107) | Departments, staff management and performance/dashboard templates |

See the repository's [commit history](https://github.com/MH-Shanto56/University-Problem-Reporting-System/commits/main) for the detailed contribution record. GitHub commit authorship is evidence of commits, not independently verified individual code ownership.

## Notes Before Demonstration or Deployment

- Test registration, login, issue submission, image uploads, location CRUD, department workflow and admin controls with sample data.
- Never commit real user data, `db.sqlite3`, `.venv/` or uploaded private files.
- The current settings contain a development-only secret key, `DEBUG=True` and permissive `ALLOWED_HOSTS`. Secure these settings before publishing the site to the internet.
- GitHub Pages cannot run this Django backend. A Django-capable host or a carefully configured demo tunnel is required for a live public link.

---

**University Problem Reporting System (UPRS)** — CSE 302 Project, University of Asia Pacific.
