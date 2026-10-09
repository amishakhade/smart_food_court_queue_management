"""
Application entry point and CLI management commands.
"""
import os
import click
from app import create_app
from app.extensions import db

app = create_app(os.getenv('FLASK_ENV', 'development'))


@app.cli.command("init-db")
def init_db_command():
    """Create all database tables in MySQL without dropping existing data."""
    with app.app_context():
        db.create_all()
        click.echo(click.style("Database tables created successfully in MySQL!", fg="green"))


@app.cli.command("seed-db")
def seed_db_command():
    """Populate database with demo categories, food items, and settings."""
    from scripts.seed_data import seed_database
    with app.app_context():
        seed_database()
        click.echo(click.style("Demo food court data seeded successfully!", fg="green"))


@app.cli.command("create-admin")
@click.option("--username", prompt="Admin username", default="admin")
@click.option("--email", prompt="Admin email", default="admin@foodcourt.edu")
@click.option("--password", prompt="Admin password", hide_input=True, confirmation_prompt=True)
@click.option("--fullname", prompt="Full name", default="Food Court Administrator")
def create_admin_command(username, email, password, fullname):
    """Interactively create an administrator account."""
    from app.models import User, UserRole
    with app.app_context():
        existing = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing:
            click.echo(click.style(f"User with username '{username}' or email '{email}' already exists.", fg="red"))
            return

        admin_user = User(
            username=username,
            email=email,
            full_name=fullname,
            role=UserRole.ADMIN,
            is_active=True
        )
        admin_user.set_password(password)
        db.session.add(admin_user)
        db.session.commit()
        click.echo(click.style(f"Administrator '{username}' created successfully!", fg="green"))


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
