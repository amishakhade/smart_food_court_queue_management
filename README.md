# Smart Food Court and Queue Management System

A Flask-based food ordering, payment-record, QR-code, and queue-management application for a college food court. The existing interface and features use Flask-SQLAlchemy with a persistent local SQLite database.

## Technology

- Python 3.10+
- Flask, Flask-SQLAlchemy, Flask-WTF
- SQLite through Python's built-in `sqlite3` driver via SQLAlchemy's SQLite dialect
- Bootstrap 5, JavaScript, QRCode, and Pillow

## Project entry point

The Flask application factory is `create_app()` in `app/__init__.py`. The executable entry point and Flask CLI commands are in `run.py`.

## Database

The persistent database is:

```text
data/food_court.db
```

Its path is derived from the project directory, so it does not depend on the terminal's current working directory. The `data` folder is created automatically. Tables are initialized without dropping existing records:

```powershell
python -m flask --app run.py init-db
```

Demo users, categories, menu records, and settings can be added idempotently with:

```powershell
python -m flask --app run.py seed-db
```

The seeder avoids duplicates, corrects the five local food-image paths, and keeps Peri Peri French Fries out of the menu.

## Installation and startup in VS Code

Open this folder in VS Code, then run:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m flask --app run.py init-db
python -m flask --app run.py seed-db
python run.py
```

Open <http://127.0.0.1:5000>. Demo accounts are `admin` / `Admin@123`, `staff` / `Staff@123`, and `student` / `Student@123`. Change demo passwords before deployment.

## Tests

```powershell
python -m pytest -q
```

The tests use isolated in-memory SQLite; the application uses the persistent `data/food_court.db` file.

## Backups and migration status

Before the final SQLite changes, the working files and available SQLite data were backed up under a timestamped `backup_pre_sqlite_final_*` folder. The local MySQL service was not reachable on port 3306, so no live MySQL records could be exported. The current SQLite database contains the available schema and seeded records and must not be described as a complete MySQL data migration.

## GitHub

No commit or push is performed automatically. Review changes first:

```powershell
git status
git diff
git add .
git commit -m "Migrate food court database to SQLite"
git push origin main
```

Use the repository's actual branch name instead of `main` if different. `.env` files, SQLite database files, and secrets are ignored by `.gitignore`.
