"""
Tests for customer ordering, server-side validation, QR code creation, and cancellation.
"""
from pathlib import Path
from decimal import Decimal
from app.models import MenuItem, Order, OrderStatus, QueueEntry, QueueStatus
from app.services.order_service import OrderService
from app.services.queue_service import QueueService


def test_public_menu_browsing(client):
    """Students can browse the food court menu without logging in."""
    resp = client.get('/menu')
    assert resp.status_code == 200
    assert b"Crispy Samosa" in resp.data
    assert b"Chicken Biryani" in resp.data


def test_valid_order_creation_and_pricing(app):
    """Verify order creation calculates correct totals on server and attaches QR."""
    with app.app_context():
        samosa = MenuItem.query.filter_by(name='Crispy Samosa').first()
        biryani = MenuItem.query.filter_by(name='Chicken Biryani').first()

        cart_items = [
            {'id': samosa.id, 'quantity': 2},    # 2 * 30 = 60
            {'id': biryani.id, 'quantity': 1}     # 1 * 150 = 150 -> Total = 210
        ]

        customer_data = {
            'name': 'Rahul Verma',
            'phone': '9876543210',
            'email': 'rahul@campus.edu'
        }

        payment_data = {'payment_method': 'Cash on Pickup'}

        success, order = OrderService.create_order(customer_data, cart_items, payment_data)

        assert success is True
        assert order.total_amount == Decimal('210.00')
        assert order.order_number.startswith('ORD-')
        assert order.status == OrderStatus.PENDING

        # Check items attached
        assert len(order.items) == 2

        # Check QR code generated
        assert order.qr_code_path is not None
        qr_file = Path(app.config['STATIC_FOLDER']) / order.qr_code_path
        assert qr_file.exists()

        # Check Queue entry
        assert order.queue_entry is not None
        assert order.queue_entry.queue_number >= 101
        assert order.queue_entry.status == QueueStatus.ACTIVE


def test_out_of_stock_item_cannot_be_ordered(app):
    """Attempting to order an out-of-stock item must be safely rejected."""
    with app.app_context():
        sold_out = MenuItem.query.filter_by(name='Paneer Roll (Sold Out)').first()
        assert sold_out.is_available is False

        cart_items = [{'id': sold_out.id, 'quantity': 1}]
        customer_data = {'name': 'Sam', 'phone': '9876543210'}
        payment_data = {'payment_method': 'Cash on Pickup'}

        success, err_msg = OrderService.create_order(customer_data, cart_items, payment_data)
        assert success is False
        assert "out of stock" in err_msg.lower()


def test_order_cancellation_updates_queue(app):
    """Cancellation transitions status to Cancelled and removes from active queue."""
    with app.app_context():
        samosa = MenuItem.query.filter_by(name='Crispy Samosa').first()
        cart_items = [{'id': samosa.id, 'quantity': 1}]
        customer_data = {'name': 'Riya', 'phone': '9876543210'}
        payment_data = {'payment_method': 'Cash on Pickup'}

        success, order = OrderService.create_order(customer_data, cart_items, payment_data)
        assert success is True

        # Initial queue position
        pos, wait = QueueService.get_queue_position(order.id)
        assert pos is not None
        assert pos >= 1

        # Student cancels while Pending
        cancel_success, msg = QueueService.update_order_status(order, OrderStatus.CANCELLED, changed_by_role='student')
        assert cancel_success is True
        assert order.status == OrderStatus.CANCELLED
        assert order.queue_entry.status == QueueStatus.CANCELLED

        # Position should now be None
        pos_after, _ = QueueService.get_queue_position(order.id)
        assert pos_after is None
