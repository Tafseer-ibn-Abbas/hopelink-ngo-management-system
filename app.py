"""HopeLink: small, clearly labeled NGO operations portfolio demo.

No real payments are accepted or processed. The SQLite dataset is synthetic.
"""

import hmac
import math
import os
import re
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get('NGO_DB_PATH', str(BASE_DIR / 'instance' / 'hopelink_demo.db')))
READ_ONLY = os.environ.get('NGO_READ_ONLY', '0') == '1'
ADMIN_USERNAME = os.environ.get('NGO_ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('NGO_ADMIN_PASSWORD')

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)
app.config.update(
    MAX_CONTENT_LENGTH=32 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.environ.get('NGO_SECURE_COOKIES', '0') == '1',
)


@contextmanager
def database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(DB_PATH), timeout=10)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    """Create a *new* local demo dataset; never package real donor records."""
    new_db = not DB_PATH.exists()
    with database() as db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS donations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                donor_name TEXT NOT NULL, donor_email TEXT NOT NULL,
                amount REAL NOT NULL, cause TEXT NOT NULL,
                payment_method TEXT NOT NULL, transaction_id TEXT UNIQUE NOT NULL,
                message TEXT
            );
            CREATE TABLE IF NOT EXISTS volunteers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, phone TEXT NOT NULL, email TEXT NOT NULL,
                skill TEXT NOT NULL, availability TEXT NOT NULL, reason TEXT
            );
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL, category TEXT NOT NULL,
                quantity INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE, description TEXT NOT NULL,
                target_amount REAL NOT NULL, current_amount REAL DEFAULT 0,
                status TEXT NOT NULL
            );
        ''')
        if new_db:
            db.executemany('''INSERT INTO projects
                (title, description, target_amount, current_amount, status)
                VALUES (?, ?, ?, ?, ?)''', [
                ('Community Learning Kits', 'Supplying school materials to community learning centers.', 12000, 3400, 'ACTIVE TRACK'),
                ('Mobile Health Outreach', 'Coordinating medical supplies and neighborhood health outreach.', 25000, 7200, 'ACTIVE TRACK'),
                ('Emergency Food Packs', 'Organizing essential food support for local communities.', 8000, 8000, 'CLOSED/ARCHIVED'),
            ])
            db.executemany('''INSERT INTO donations
                (donor_name, donor_email, amount, cause, payment_method, transaction_id, message)
                VALUES (?, ?, ?, ?, ?, ?, ?)''', [
                ('Alex Morgan (Demo)', 'alex@example.test', 3400, 'Community Learning Kits', 'Demo pledge', 'DEMO-A001', 'Fictional sample'),
                ('Sam Rivera (Demo)', 'sam@example.test', 7200, 'Mobile Health Outreach', 'Demo pledge', 'DEMO-A002', 'Fictional sample'),
                ('Taylor Reed (Demo)', 'taylor@example.test', 8000, 'Emergency Food Packs', 'Demo pledge', 'DEMO-A003', 'Fictional sample'),
            ])
            db.executemany('''INSERT INTO volunteers
                (name, phone, email, skill, availability, reason)
                VALUES (?, ?, ?, ?, ?, ?)''', [
                ('Jamie Parker (Demo)', '03000000001', 'jamie@example.test', 'Teaching', 'Weekends', 'Fictional sample'),
                ('Jordan Lee (Demo)', '03000000002', 'jordan@example.test', 'Healthcare', 'Weekdays', 'Fictional sample'),
                ('Casey Noor (Demo)', '03000000003', 'casey@example.test', 'Logistics', 'Flexible', 'Fictional sample'),
            ])
            db.executemany('INSERT INTO inventory (item_name, category, quantity) VALUES (?, ?, ?)', [
                ('School supply kits', 'Education', 80),
                ('First aid boxes', 'Healthcare', 24),
                ('Food packages', 'Disaster Relief', 110),
                ('Transport crates', 'Logistics', 14),
            ])


@app.context_processor
def common_template_values():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_urlsafe(32)
    return {'csrf_token': session['_csrf_token'], 'read_only': READ_ONLY}


@app.before_request
def validate_post():
    if request.method != 'POST':
        return
    token = request.form.get('_csrf_token', '')
    expected = session.get('_csrf_token', '')
    if not expected or not hmac.compare_digest(token, expected):
        abort(400, description='Invalid form token. Reload the page and retry.')
    if READ_ONLY and request.endpoint != 'login':
        flash('Public preview is read-only. Run locally to try editing workflows.', 'info')
        return redirect(url_for('index'))


@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['X-Frame-Options'] = 'DENY'
    return response


def clean(name, max_length=150):
    value = request.form.get(name, '').strip()
    if not value or len(value) > max_length:
        raise ValueError('Check the required form fields and their lengths.')
    return value


def optional(name, max_length=500):
    value = request.form.get(name, '').strip()
    if len(value) > max_length:
        raise ValueError('Text is too long.')
    return value


def amount(name, allow_zero=False):
    try:
        raw = request.form.get(name, '')
        value = float(raw if str(raw).strip() else ('0' if allow_zero else ''))
    except ValueError as exc:
        raise ValueError('Enter a valid number.') from exc
    if not math.isfinite(value) or value > 1_000_000 or (value < 0 if allow_zero else value <= 0):
        raise ValueError('Enter a valid amount between 0 and 1,000,000.')
    return round(value, 2)


def valid_email(value):
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
        raise ValueError('Please enter a valid email address.')
    return value


def admin_required():
    if session.get('logged_in') is not True:
        abort(403, description='Please sign in as administrator.')


@app.get('/')
def index():
    with database() as db:
        funds = db.execute('SELECT COALESCE(SUM(amount), 0) FROM donations').fetchone()[0]
        volunteers = db.execute('SELECT COUNT(*) FROM volunteers').fetchone()[0]
        completed = db.execute("SELECT COUNT(*) FROM projects WHERE status = 'CLOSED/ARCHIVED'").fetchone()[0]
    return render_template('index.html', total_funds=funds,
                           total_volunteers=volunteers, completed_projects=completed)


@app.get('/donate')
def donate():
    with database() as db:
        campaigns = [row[0] for row in db.execute(
            "SELECT title FROM projects WHERE status = 'ACTIVE TRACK' ORDER BY id")]
    return render_template('donate.html', campaigns=campaigns)


@app.get('/volunteer')
def volunteer():
    return render_template('volunteer.html')


@app.get('/projects')
def projects():
    with database() as db:
        raw = db.execute('SELECT id, title, description, target_amount, current_amount, status FROM projects ORDER BY id').fetchall()
    records = [dict(id=p[0], title=p[1], description=p[2], target_amount=p[3],
                    current_amount=p[4], status=p[5],
                    percentage=min(100, (p[4] / p[3] * 100) if p[3] > 0 else 0)) for p in raw]
    return render_template('projects.html', projects=records)


@app.get('/inventory')
def inventory():
    with database() as db:
        items = db.execute('SELECT id, item_name, category, quantity FROM inventory ORDER BY id').fetchall()
    return render_template('inventory.html', items=items)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if ADMIN_PASSWORD and hmac.compare_digest(username, ADMIN_USERNAME) and hmac.compare_digest(password, ADMIN_PASSWORD):
            session.clear()
            session['logged_in'] = True
            session['username'] = ADMIN_USERNAME
            session['_csrf_token'] = secrets.token_urlsafe(32)
            return redirect(url_for('admin'))
        flash('Invalid credentials or administrator password not configured.', 'error')
        return redirect(url_for('login'))
    return render_template('login.html')


@app.get('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.get('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    with database() as db:
        donations = db.execute('SELECT id, donor_name, donor_email, amount, cause, payment_method, transaction_id FROM donations ORDER BY id DESC').fetchall()
        volunteers = db.execute('SELECT id, name, phone, email, skill, availability, reason FROM volunteers ORDER BY id DESC').fetchall()
        chart = db.execute('SELECT cause, SUM(amount) FROM donations GROUP BY cause ORDER BY cause').fetchall()
    return render_template('admin.html', donations=donations, volunteers=volunteers,
                           labels=[r[0] for r in chart], values=[r[1] for r in chart])


@app.post('/submit-donation')
def submit_donation():
    try:
        name = clean('donor_name', 100)
        email = valid_email(clean('donor_email', 150))
        donation = amount('donation_amount')
        cause = clean('donation_cause', 150)
        msg = optional('donor_message')
        with database() as db:
            if not db.execute("SELECT 1 FROM projects WHERE title = ? AND status = 'ACTIVE TRACK'", (cause,)).fetchone():
                raise ValueError('Please select an active campaign.')
            txn_id = 'DEMO-' + secrets.token_hex(6).upper()
            cursor = db.execute('''INSERT INTO donations
                (donor_name, donor_email, amount, cause, payment_method, transaction_id, message)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (name, email, donation, cause, 'Demo pledge', txn_id, msg))
            db.execute('UPDATE projects SET current_amount = current_amount + ? WHERE title = ?', (donation, cause))
            receipt_id = cursor.lastrowid
        receipt_ids = session.get('receipt_ids', [])[-9:]
        session['receipt_ids'] = receipt_ids + [receipt_id]
        return redirect(url_for('receipt', id=receipt_id))
    except ValueError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('donate'))


@app.get('/receipt/<int:id>')
def receipt(id):
    if id not in session.get('receipt_ids', []) and not session.get('logged_in'):
        abort(404)
    with database() as db:
        record = db.execute('SELECT id, donor_name, donor_email, amount, cause, payment_method, transaction_id, message FROM donations WHERE id = ?', (id,)).fetchone()
    if record is None:
        abort(404)
    return render_template('receipt.html', data=record)


@app.post('/submit-volunteer')
def submit_volunteer():
    try:
        name = clean('v_name', 100)
        phone = clean('v_phone', 24)
        if len(re.sub(r'\D', '', phone)) < 10:
            raise ValueError('Please enter a valid contact number.')
        email = valid_email(clean('v_email', 150))
        skill = clean('v_skill', 100)
        availability = clean('v_availability', 60)
        reason = optional('v_reason')
        with database() as db:
            db.execute('''INSERT INTO volunteers (name, phone, email, skill, availability, reason)
                          VALUES (?, ?, ?, ?, ?, ?)''',
                       (name, phone, email, skill, availability, reason))
        flash('Volunteer registration saved.', 'success')
        return redirect(url_for('volunteer'))
    except ValueError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('volunteer'))


@app.post('/add-inventory')
def add_inventory():
    admin_required()
    try:
        item_name = clean('item_name', 100)
        category = clean('item_category', 60)
        qty = int(request.form.get('item_qty', ''))
        if qty <= 0 or qty > 100000:
            raise ValueError('Quantity must be between 1 and 100,000.')
        with database() as db:
            db.execute('INSERT INTO inventory (item_name, category, quantity) VALUES (?, ?, ?)',
                       (item_name, category, qty))
        flash('Inventory item added.', 'success')
    except (ValueError, TypeError):
        flash('Please enter a valid inventory item and positive quantity.', 'error')
    return redirect(url_for('inventory'))


@app.post('/delete-donation/<int:id>')
def delete_donation(id):
    admin_required()
    with database() as db:
        record = db.execute('SELECT amount, cause FROM donations WHERE id = ?', (id,)).fetchone()
        if record:
            db.execute('DELETE FROM donations WHERE id = ?', (id,))
            db.execute('''UPDATE projects SET current_amount = MAX(0, current_amount - ?)
                          WHERE title = ?''', (record[0], record[1]))
    flash('Pledge record removed.', 'success')
    return redirect(url_for('admin'))


@app.post('/add-project')
def add_project():
    admin_required()
    try:
        title = clean('p_title', 120)
        desc = clean('p_desc', 500)
        target = amount('p_target')
        current = amount('p_current', allow_zero=True)
        status = clean('p_status', 30)
        if status not in {'ACTIVE TRACK', 'CLOSED/ARCHIVED'}:
            raise ValueError('Invalid project status.')
        with database() as db:
            db.execute('''INSERT INTO projects (title, description, target_amount, current_amount, status)
                          VALUES (?, ?, ?, ?, ?)''', (title, desc, target, current, status))
        flash('Campaign created.', 'success')
    except (ValueError, sqlite3.IntegrityError) as exc:
        flash('Could not create project: ' + str(exc), 'error')
    return redirect(url_for('projects'))


init_db()


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT', '5000')), debug=False)
