# HopeLink — NGO Operations Management System

**A modern, responsive nonprofit operations web app built with Python, Flask and SQLite.**

HopeLink is an independent portfolio project for managing community campaigns, coordinating volunteers, tracking supplies and recording sample pledges. It demonstrates practical full-stack development without requiring cloud services or a payment gateway.

## Features

- **Overview:** Responsive landing page with sample operations statistics and clear navigation.
- **Campaigns:** Funding targets, progress indicators, activity status and admin-created initiatives.
- **Volunteer management:** Registration form, skills, availability and an admin directory.
- **Inventory:** Categorized resource list and admin-controlled stock additions.
- **Pledge workflow:** Fictional contribution entries with **clearly labeled non-payment confirmation records**. No money moves.
- **Operations dashboard:** Pledge totals, campaign visualizations and volunteer records.
- **SQLite persistence:** Local data survives application restarts.
- **Mobile support:** Navigation menu, forms, grids and tables adjust to smaller screens.

## Tech stack

| Layer | Tools |
| --- | --- |
| Server | Python 3, Flask, Jinja |
| Data | SQLite |
| Frontend | HTML, CSS, JavaScript |
| UI | Custom responsive CSS; no frontend framework, font CDN or chart library |

## Run locally

1. Extract the ZIP and open `HopeLink_NGO_Portfolio` in VS Code on Windows.
2. Open Terminal → New Terminal (PowerShell).
3. Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run-Local.ps1
```

The first run creates an isolated `.venv` and installs the packages listed in `requirements.txt`. Enter a private **local administrator password** when prompted. Then visit **http://127.0.0.1:5000**.

- **Username:** `admin`
- **Password:** the private password you set locally
- **Stop server:** `Ctrl+C`

For subsequent launches, the existing environment will be reused. If your terminal cannot accept a hidden password prompt, set the `NGO_ADMIN_PASSWORD` environment variable in your *current PowerShell session* before launching. Never publish or commit this value.

## Public browser preview

This is a Flask application and **requires Python hosting**. A static-only service such as GitHub Pages cannot run the backend.

A read-only preview is recommended for public portfolios:

- Install packages with `pip install -r requirements.txt`.
- Run the WSGI app with `gunicorn app:app` on Linux.
- Set `NGO_READ_ONLY=1` to block all write actions.
- Set `FLASK_SECRET_KEY` to a strong private value, and `NGO_SECURE_COOKIES=1` when serving over HTTPS.
- Set `NGO_ADMIN_PASSWORD` to a private password; do not share admin access publicly.
- SQLite is stored under `instance/hopelink_demo.db` by default. On hosts with ephemeral filesystems, data may reset after restart. A durable deployment requires suitable persistent storage.

## Portfolio data and payment limitations

This is a **software showcase, not a real NGO website**. Seed records contain fictional people, fictional campaigns and illustrative contribution amounts. The pledge workflow simulates recording an amount and generates a sample record. **No bank transfer, payment processing, financial verification or receipt of funds occurs.** Do not submit genuine personal or financial information.

The repository includes CSRF checking, login protection for administrative operations and server-side form validation. The one-account administrator model is intentionally limited and not appropriate for an actual public nonprofit platform processing private records or real payments.

## Project structure

- `app.py` — Flask routes, SQLite initialization and validation
- `templates/` — Jinja pages (shared `base.html` layout)
- `static/css/site.css` — responsive design system
- `static/js/site.js` — mobile navigation and simple form interactions
- `tests/test_smoke.py` — route, login, CSRF and data workflow smoke tests
- `Run-Local.ps1` — local Windows launcher

Run tests after installing requirements:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Developer

Built as an independent project by [Tafseer Ibn Abbas](https://github.com/Tafseer-ibn-Abbas).
