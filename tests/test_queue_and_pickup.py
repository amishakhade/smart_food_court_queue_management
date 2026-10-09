"""
Tests for Queue Service transitions, Pickup Verification, and Duplicate Prevention.
"""
from decimal import Decimal
from app.models import MenuItem, Order, OrderStatus, QueueStatus, PaymentStatus
from app.services.order_service import OrderService
from app.services.queue_service import QueueService
from app.services.qr_service import QRService


def test_order_lifecycle_and_duplicate_pickup_prevention(app):
    """
    Test full lifecycle transitions:
    Pending -> Accepted -> Preparing -> Ready for Pickup -> Completed.
    Verify that Once Completed, it CANNOT be modified or collected again.
    """
    with app.app_context():
        samosa = MenuItem.query.filter_by(name='Crispy Samosa').first()
        cart_items = [{'id': samosa.id, 'quantity': 1}]
        customer = {'name': 'Ananya', 'phone': '9876543210'}
        payment = {'payment_method': 'Cash on Pickup'}

        _, order = OrderService.create_order(customer, cart_items, payment)
        assert order.status == OrderStatus.PENDING

        # Step 1: Accept
        ok, _ = QueueService.update_order_status(order, OrderStatus.ACCEPTED)
        assert ok is True
        assert order.status == OrderStatus.ACCEPTED

        # Step 2: Preparing
        ok, _ = QueueService.update_order_status(order, OrderStatus.PREPARING)
        assert ok is True
        assert order.status == OrderStatus.PREPARING

        # Step 3: Ready for Pickup
        ok, _ = QueueService.update_order_status(order, OrderStatus.READY)
        assert ok is True
        assert order.status == OrderStatus.READY
        assert order.queue_entry.status == QueueStatus.CALLED

        # Step 4: Completed
        ok, _ = QueueService.update_order_status(order, OrderStatus.COMPLETED)
        assert ok is True
        assert order.status == OrderStatus.COMPLETED
        assert order.queue_entry.status == QueueStatus.COMPLETED
        assert order.payment.status == PaymentStatus.PAID  # Cash marked paid on handover

        # Step 5: Duplicate Pickup Attempt must FAIL
        dup_ok, dup_msg = QueueService.update_order_status(order, OrderStatus.COMPLETED)
        assert dup_ok is False
        assert "completed orders cannot be modified or collected again" in dup_msg.lower()


def test_invalid_status_transition_rejected(app):
    """Transitioning directly from Pending to Completed or illegal backwards transition must fail."""
    with app.app_context():
        samosa = MenuItem.query.filter_by(name='Crispy Samosa').first()
        cart_items = [{'id': samosa.id, 'quantity': 1}]
        customer = {'name': 'Vijay', 'phone': '9876543210'}
        payment = {'payment_method': 'Cash on Pickup'}

        _, order = OrderService.create_order(customer, cart_items, payment)

        # Illegal leap directly to Completed
        ok, msg = QueueService.update_order_status(order, OrderStatus.COMPLETED)
        assert ok is False
        assert "invalid transition" in msg.lower()


def test_qr_payload_parsing_and_token_match(app):
    """Ensure QR payload parsing correctly extracts order number and token."""
    with app.app_context():
        samosa = MenuItem.query.filter_by(name='Crispy Samosa').first()
        _, order = OrderService.create_order(
            {'name': 'Kavya', 'phone': '9876543210'},
            [{'id': samosa.id, 'quantity': 1}],
            {'payment_method': 'Cash on Pickup'}
        )

        sample_qr_string = f"FOODCOURT:VERIFY:{order.order_number}:{order.verification_token}"
        parsed = QRService.parse_qr_payload(sample_qr_string)

        assert parsed['order_number'] == order.order_number
        assert parsed['token'] == order.verification_token

        # Fallback raw input parsing
        manual_parsed = QRService.parse_qr_payload(order.order_number)
        assert manual_parsed['order_number'] == order.order_number
        assert manual_parsed['token'] is None


def test_unique_order_number_generation(app):
    """Ensure order numbers are unique."""
    with app.app_context():
        num1 = OrderService.generate_unique_order_number()
        num2 = OrderService.generate_unique_order_number()
        assert num1 != num2
        assert num1.startswith('ORD-')
