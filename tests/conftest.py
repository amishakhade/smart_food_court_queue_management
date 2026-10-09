"""
Pytest fixtures and test environment setup.
Uses isolated in-memory SQLite database for deterministic, zero-side-effect test execution.
"""
import sys
from pathlib import Path
import pytest
from decimal import Decimal

# Add root directory to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.extensions import db
from app.models import User, UserRole, Category, MenuItem, ApplicationSetting


@pytest.fixture(scope='session')
def app():
    """Create Flask application in testing mode."""
    _app = create_app('testing')
    with _app.app_context():
        db.create_all()
        yield _app
        db.drop_all()


@pytest.fixture(autouse=True)
def clean_db(app):
    """Clean and seed baseline records before each test."""
    with app.app_context():
        # Clear tables
        db.session.remove()
        db.drop_all()
        db.create_all()

        # Seed default settings
        ApplicationSetting.set_value('avg_preparation_time_mins', '8')
        ApplicationSetting.set_value('cancellation_time_limit_mins', '5')
        ApplicationSetting.set_value('food_court_name', 'Campus Smart Food Court')

        # Seed categories
        cat_snacks = Category(name='Snacks', icon='bi-cup-hot', display_order=1)
        cat_meals = Category(name='Meals', icon='bi-egg-fried', display_order=2)
        db.session.add_all([cat_snacks, cat_meals])
        db.session.flush()

        # Seed menu items
        samosa = MenuItem(
            category_id=cat_snacks.id,
            name='Crispy Samosa',
            price=Decimal('30.00'),
            preparation_time_mins=5,
            is_veg=True,
            is_available=True
        )
        biryani = MenuItem(
            category_id=cat_meals.id,
            name='Chicken Biryani',
            price=Decimal('150.00'),
            preparation_time_mins=12,
            is_veg=False,
            is_available=True
        )
        sold_out_roll = MenuItem(
            category_id=cat_snacks.id,
            name='Paneer Roll (Sold Out)',
            price=Decimal('90.00'),
            preparation_time_mins=8,
            is_veg=True,
            is_available=False
        )
        db.session.add_all([samosa, biryani, sold_out_roll])

        # Seed users
        admin = User(
            username='admin',
            email='admin@foodcourt.edu',
            full_name='Food Court Admin',
            role=UserRole.ADMIN,
            is_active=True
        )
        admin.set_password('Admin@123')

        staff = User(
            username='staff',
            email='staff@foodcourt.edu',
            full_name='Kitchen Lead',
            role=UserRole.STAFF,
            is_active=True
        )
        staff.set_password('Staff@123')

        student = User(
            username='student',
            email='student@campus.edu',
            full_name='Aarav Student',
            role=UserRole.STUDENT,
            is_active=True
        )
        student.set_password('Student@123')

        db.session.add_all([admin, staff, student])
        db.session.commit()

        yield


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()
