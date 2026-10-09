"""
Create the first administrator account securely.
Usage:
    python scripts/create_admin.py --username admin --email admin@foodcourt.edu --password Admin@123 --name "Food Court Admin"
"""
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.extensions import db
from app.models import User, UserRole


def create_admin(username, email, password, full_name, phone=None):
    app = create_app()
    with app.app_context():
        # Check if already exists
        existing = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing:
            print(f"[!] User with username '{username}' or email '{email}' already exists.")
            return False

        admin = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone or "9876543210",
            role=UserRole.ADMIN,
            is_active=True
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f"[+] Administrator account '{username}' successfully created!")
        return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Create the first administrator account.")
    parser.add_argument('--username', default='admin', help='Admin username (default: admin)')
    parser.add_argument('--email', default='admin@foodcourt.edu', help='Admin email (default: admin@foodcourt.edu)')
    parser.add_argument('--password', default='Admin@123', help='Admin password (default: Admin@123)')
    parser.add_argument('--name', default='Food Court Administrator', help='Full name')
    parser.add_argument('--phone', default='9876543210', help='Phone number')

    args = parser.parse_args()
    create_admin(args.username, args.email, args.password, args.name, args.phone)
