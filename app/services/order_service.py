"""
Order management service.
Handles cart validation, server-side price calculation, inventory availability check,
atomic order generation, and QR code attachment.
"""
from datetime import datetime, date
from decimal import Decimal
import secrets
from app.extensions import db
from app.models import Order, OrderItem, MenuItem, OrderStatus, PaymentRecord, PaymentMethod, PaymentStatus, QueueEntry, QueueStatus
from app.services.queue_service import QueueService
from app.services.qr_service import QRService


class OrderService:
    """Service handling order checkout, stock validation, and persistence."""

    @staticmethod
    def generate_unique_order_number():
        """
        Generate a unique human-friendly order number e.g. ORD-20261009-8472.
        Ensures uniqueness against database records.
        """
        today_str = datetime.utcnow().strftime('%Y%m%d')
        for _ in range(10):
            rand_suffix = secrets.randbelow(9000) + 1000  # 4-digit number
            candidate = f"ORD-{today_str}-{rand_suffix}"
            if not Order.query.filter_by(order_number=candidate).first():
                return candidate
        # Fallback with hex
        return f"ORD-{today_str}-{secrets.token_hex(3).upper()}"

    @classmethod
    def create_order(cls, customer_data, cart_items, payment_data, user=None):
        """
        Atomically validate cart items, verify availability, calculate server-side totals,
        create Order + OrderItems + QueueEntry + PaymentRecord, and generate QR code.

        Returns (success: bool, result_or_error: Order or str)
        """
        if not cart_items:
            return False, "Your shopping cart is empty."

        customer_name = (customer_data.get('name') or '').strip()
        customer_phone = (customer_data.get('phone') or '').strip()
        customer_email = (customer_data.get('email') or '').strip() or None
        instructions = (customer_data.get('special_instructions') or '').strip() or None

        if not customer_name:
            return False, "Customer name is required."
        if not customer_phone or len(customer_phone) < 7:
            return False, "Valid contact mobile number is required."

        payment_method = payment_data.get('payment_method', PaymentMethod.CASH)
        if payment_method not in PaymentMethod.CHOICES:
            payment_method = PaymentMethod.CASH

        # Start atomic transaction
        try:
            # 1. Validate items and compute server-verified prices
            verified_order_items = []
            calculated_total = Decimal('0.00')

            for item in cart_items:
                item_id = item.get('id')
                quantity = int(item.get('quantity', 1))

                if quantity <= 0:
                    continue

                # Query database with lock or fresh state
                menu_item = MenuItem.query.filter_by(id=item_id).first()
                if not menu_item:
                    return False, f"Selected menu item (ID #{item_id}) no longer exists."

                if not menu_item.is_available:
                    return False, f"Sorry, '{menu_item.name}' is currently out of stock and cannot be ordered."

                subtotal = Decimal(str(menu_item.price)) * Decimal(str(quantity))
                calculated_total += subtotal

                verified_order_items.append({
                    'menu_item': menu_item,
                    'name': menu_item.name,
                    'price': Decimal(str(menu_item.price)),
                    'quantity': quantity,
                    'subtotal': subtotal
                })

            if not verified_order_items:
                return False, "No valid items to place an order."

            # 2. Generate unique order number and verification token
            order_number = cls.generate_unique_order_number()
            verification_token = QRService.generate_token()

            # 3. Create Order instance
            order = Order(
                order_number=order_number,
                user_id=user.id if user else None,
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_email=customer_email,
                total_amount=calculated_total,
                status=OrderStatus.PENDING,
                special_instructions=instructions,
                verification_token=verification_token
            )
            db.session.add(order)
            db.session.flush()  # Generate order.id

            # 4. Attach snapshot OrderItems
            for v_item in verified_order_items:
                order_item = OrderItem(
                    order_id=order.id,
                    menu_item_id=v_item['menu_item'].id,
                    item_name=v_item['name'],
                    unit_price=v_item['price'],
                    quantity=v_item['quantity'],
                    subtotal=v_item['subtotal']
                )
                db.session.add(order_item)

            # 5. Assign Queue Entry
            q_num, q_disp = QueueService.generate_next_queue_number()
            queue_entry = QueueEntry(
                order_id=order.id,
                queue_number=q_num,
                queue_display=q_disp,
                status=QueueStatus.ACTIVE,
                joined_at=datetime.utcnow()
            )
            db.session.add(queue_entry)

            # 6. Create Payment Record
            payment_status = PaymentStatus.PENDING
            txn_ref = None
            if payment_method == PaymentMethod.UPI:
                # Demo UPI mock transaction
                txn_ref = f"UPI-{secrets.token_hex(6).upper()}"
                payment_status = PaymentStatus.PAID  # Demo UPI marks as paid upon checkout confirmation

            payment_record = PaymentRecord(
                order_id=order.id,
                payment_method=payment_method,
                amount=calculated_total,
                status=payment_status,
                transaction_reference=txn_ref,
                paid_at=datetime.utcnow() if payment_status == PaymentStatus.PAID else None
            )
            db.session.add(payment_record)

            # 7. Generate QR code image
            qr_relative_path = QRService.generate_order_qr(order)
            order.qr_code_path = qr_relative_path

            # Commit the atomic transaction
            db.session.commit()
            return True, order

        except Exception as e:
            db.session.rollback()
            return False, f"Failed to place order due to a system error: {str(e)}"
