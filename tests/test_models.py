"""
Unit tests for SQLAlchemy models.
"""
from decimal import Decimal
from app.extensions import db
from app.models import User, UserRole, Category, MenuItem, Order, OrderItem, OrderStatus, PaymentRecord, PaymentStatus


def test_user_password_hashing(app):
    """Ensure user passwords are safe hashes and verify properly."""
    with app.app_context():
        user = User(
            username='test_user',
            email='test@campus.edu',
            full_name='Test Student',
            role=UserRole.STUDENT
        )
        user.set_password('SecretPass123')
        assert user.password_hash != 'SecretPass123'
        assert user.check_password('SecretPass123') is True
        assert user.check_password('WrongPass') is False


def test_user_roles(app):
    """Verify role checks on student, staff, and admin."""
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        staff = User.query.filter_by(username='staff').first()
        student = User.query.filter_by(username='student').first()

        assert admin.is_admin is True
        assert admin.is_staff is True
        assert admin.is_student is False

        assert staff.is_admin is False
        assert staff.is_staff is True
        assert staff.is_student is False

        assert student.is_admin is False
        assert student.is_staff is False
        assert student.is_student is True


def test_historical_price_preservation(app):
    """Ensure OrderItem preserves historical purchase price if menu price changes later."""
    with app.app_context():
        samosa = MenuItem.query.filter_by(name='Crispy Samosa').first()
        assert samosa.price == Decimal('30.00')

        # Create order
        order = Order(
            order_number='ORD-TEST-001',
            customer_name='Tester',
            customer_phone='9999999999',
            total_amount=Decimal('60.00'),
            verification_token='testtoken123'
        )
        db.session.add(order)
        db.session.flush()

        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=samosa.id,
            item_name=samosa.name,
            unit_price=samosa.price,
            quantity=2,
            subtotal=Decimal('60.00')
        )
        db.session.add(order_item)
        db.session.commit()

        # Now change menu price in database to 45.00
        samosa.price = Decimal('45.00')
        db.session.commit()

        # Historical order item price must remain preserved at 30.00
        saved_item = OrderItem.query.filter_by(order_id=order.id).first()
        assert saved_item.unit_price == Decimal('30.00')
        assert saved_item.subtotal == Decimal('60.00')
