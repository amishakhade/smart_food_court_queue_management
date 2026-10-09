"""
Live end-to-end integration verification against real local MySQL database.
"""
import sys
from pathlib import Path
from decimal import Decimal
import json

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.extensions import db
from app.models import User, MenuItem, Order, OrderStatus, QueueStatus, PaymentStatus
from app.services.order_service import OrderService
from app.services.queue_service import QueueService
from app.services.qr_service import QRService

def run_live_mysql_verification():
    print("[*] Initializing Flask app with development (MySQL) configuration...")
    app = create_app('development')
    with app.app_context():
        # 1. Verify MySQL connection
        db.session.execute(db.text("SELECT 1;"))
        print("[+] Real MySQL connection verified!")

        # 2. Check menu items in MySQL
        items = MenuItem.query.filter_by(is_available=True).all()
        print(f"[+] Loaded {len(items)} available menu items directly from MySQL.")
        assert len(items) > 0, "No menu items in MySQL!"

        samosa = MenuItem.query.filter_by(name='Crispy Veg Samosa (2 Pcs)').first()
        thali = MenuItem.query.filter_by(name='Deluxe Veg Thali').first()
        assert samosa is not None and thali is not None

        # 3. Simulate customer placing an order
        student_user = User.query.filter_by(username='student').first()
        cart = [
            {'id': samosa.id, 'quantity': 2},  # 2 * 30 = 60
            {'id': thali.id, 'quantity': 1}    # 1 * 140 = 140 -> Total = 200
        ]
        customer_info = {
            'name': 'Aarav Sharma',
            'phone': '9876543212',
            'email': 'aarav.student@campus.edu',
            'special_instructions': 'Extra spicy mint chutney please.'
        }
        payment_info = {'payment_method': 'Cash on Pickup'}

        print("[*] Placing live order through OrderService...")
        success, order = OrderService.create_order(customer_info, cart, payment_info, user=student_user)
        assert success is True
        print(f"[+] Order #{order.order_number} created successfully in MySQL!")
        print(f"    - Total Amount: Rs. {order.total_amount}")
        print(f"    - Queue Token: {order.queue_entry.queue_display}")
        print(f"    - QR Image: {order.qr_code_path}")
        assert order.total_amount == Decimal('200.00')

        # Verify QR file exists on disk
        qr_file_path = Path(app.config['STATIC_FOLDER']) / order.qr_code_path
        assert qr_file_path.exists(), f"QR file {qr_file_path} not found on disk!"
        print(f"[+] QR code file verified at: {qr_file_path}")

        # 4. Check Queue calculations
        pos, wait_mins = QueueService.get_queue_position(order.id)
        print(f"[+] Active Queue Position: #{pos}, Estimated Wait: ~{wait_mins} mins")
        assert pos is not None and pos >= 1

        # 5. Advance Order Status through kitchen lifecycle
        print("[*] Staff advances order: Pending -> Accepted...")
        ok, msg = QueueService.update_order_status(order, OrderStatus.ACCEPTED)
        assert ok is True

        print("[*] Staff advances order: Accepted -> Preparing...")
        ok, msg = QueueService.update_order_status(order, OrderStatus.PREPARING)
        assert ok is True

        print("[*] Staff advances order: Preparing -> Ready for Pickup...")
        ok, msg = QueueService.update_order_status(order, OrderStatus.READY)
        assert ok is True
        assert order.status == OrderStatus.READY
        assert order.queue_entry.status == QueueStatus.CALLED

        # 6. Verify QR Verification Token
        qr_payload = f"FOODCOURT:VERIFY:{order.order_number}:{order.verification_token}"
        parsed = QRService.parse_qr_payload(qr_payload)
        assert parsed['order_number'] == order.order_number
        assert parsed['token'] == order.verification_token
        print("[+] QR verification payload matched exactly.")

        # 7. Complete Handover
        print("[*] Staff verifies pickup and completes order...")
        ok, msg = QueueService.update_order_status(order, OrderStatus.COMPLETED)
        assert ok is True
        assert order.status == OrderStatus.COMPLETED
        assert order.queue_entry.status == QueueStatus.COMPLETED
        assert order.payment.status == PaymentStatus.PAID
        print(f"[+] Order completed and Cash payment marked as PAID.")

        # 8. Test Duplicate Collection Prevention
        print("[*] Testing duplicate pickup attempt on completed order...")
        dup_ok, dup_msg = QueueService.update_order_status(order, OrderStatus.COMPLETED)
        assert dup_ok is False
        print(f"[+] Duplicate pickup prevented as expected! Message: '{dup_msg}'")

        # 9. Verify Admin Analytics on MySQL
        total_rev = db.session.query(db.func.sum(Order.total_amount)).filter(Order.status == OrderStatus.COMPLETED).scalar()
        print(f"[+] Admin Total Sales in MySQL: Rs. {total_rev}")
        assert total_rev >= Decimal('200.00')

        print("\n=======================================================")
        print("ALL END-TO-END MYSQL INTEGRATION WORKFLOWS PASSED 100%!")
        print("=======================================================")

if __name__ == '__main__':
    run_live_mysql_verification()
