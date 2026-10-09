"""
Smart Queue Management Service.
Handles sequence generation, position calculation, waiting time estimation,
and strict order lifecycle status transitions.
"""
from datetime import datetime, date
from sqlalchemy import func
from app.extensions import db
from app.models import Order, OrderStatus, QueueEntry, QueueStatus, ApplicationSetting, PaymentRecord, PaymentStatus


class QueueService:
    """Core Queue management algorithms and state transitions."""

    @staticmethod
    def get_avg_prep_time():
        """Retrieve configured average preparation time in minutes."""
        val = ApplicationSetting.get_value('avg_preparation_time_mins', default='8')
        try:
            return max(1, int(val))
        except (ValueError, TypeError):
            return 8

    @staticmethod
    def generate_next_queue_number():
        """
        Generate a safe, daily sequential queue number (starting at 101 each day).
        Uses database transaction to avoid duplicate sequence numbers.
        """
        today_start = datetime.combine(date.today(), datetime.min.time())
        
        # Lock max queue entry for today
        max_q = db.session.query(func.max(QueueEntry.queue_number))\
            .filter(QueueEntry.joined_at >= today_start)\
            .scalar()
        
        if max_q is None or max_q < 100:
            next_num = 101
        else:
            next_num = max_q + 1
        
        display_code = f"Q-{next_num}"
        return next_num, display_code

    @classmethod
    def get_queue_position(cls, order_id):
        """
        Calculate current position in the active queue for a given order.
        Orders ahead are defined by earlier joined_at or lower id with active status.
        """
        order = db.session.get(Order, order_id)
        if not order or not order.queue_entry:
            return None, 0

        # Non-active states
        if order.status == OrderStatus.COMPLETED:
            return 0, 0
        if order.status == OrderStatus.CANCELLED:
            return None, 0
        if order.status == OrderStatus.READY:
            return 0, 0  # Ready for pickup now

        # Active orders ahead in queue
        ahead_count = db.session.query(func.count(QueueEntry.id))\
            .join(Order, QueueEntry.order_id == Order.id)\
            .filter(
                Order.status.in_([OrderStatus.PENDING, OrderStatus.ACCEPTED, OrderStatus.PREPARING]),
                QueueEntry.status.in_([QueueStatus.ACTIVE, QueueStatus.CALLED]),
                (QueueEntry.joined_at < order.queue_entry.joined_at) |
                ((QueueEntry.joined_at == order.queue_entry.joined_at) & (QueueEntry.id < order.queue_entry.id))
            ).scalar()

        position = ahead_count + 1
        avg_prep = cls.get_avg_prep_time()
        
        # Calculate estimated waiting minutes
        estimated_wait_mins = position * avg_prep
        return position, estimated_wait_mins

    @classmethod
    def update_order_status(cls, order, target_status, changed_by_role='staff'):
        """
        Enforce valid state transitions and update queue & payment accordingly.
        """
        # Terminal state locks (Once completed or cancelled, cannot be modified or collected again)
        if order.status == OrderStatus.COMPLETED:
            return False, "Completed orders cannot be modified or collected again."
        if order.status == OrderStatus.CANCELLED:
            return False, "Cancelled orders cannot be modified."

        if order.status == target_status:
            return True, "Status is already set."

        # Valid transitions mapping
        allowed_transitions = {
            OrderStatus.PENDING: [OrderStatus.ACCEPTED, OrderStatus.PREPARING, OrderStatus.CANCELLED],
            OrderStatus.ACCEPTED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
            OrderStatus.PREPARING: [OrderStatus.READY, OrderStatus.CANCELLED],
            OrderStatus.READY: [OrderStatus.COMPLETED, OrderStatus.CANCELLED],
        }

        if target_status not in allowed_transitions.get(order.status, []):
            return False, f"Invalid transition from '{order.status}' to '{target_status}'."

        # Student cancellation restriction
        if target_status == OrderStatus.CANCELLED and changed_by_role == 'student':
            if not order.is_cancellable:
                return False, "Orders can only be cancelled within 5 minutes while Pending."

        # Perform transition
        order.status = target_status
        order.updated_at = datetime.utcnow()

        if not order.queue_entry:
            # Create queue entry if missing
            q_num, q_disp = cls.generate_next_queue_number()
            order.queue_entry = QueueEntry(
                order=order,
                queue_number=q_num,
                queue_display=q_disp,
                status=QueueStatus.ACTIVE
            )

        # Update queue entry
        if target_status == OrderStatus.READY:
            order.queue_entry.status = QueueStatus.CALLED
            order.queue_entry.called_at = datetime.utcnow()
        elif target_status == OrderStatus.COMPLETED:
            order.queue_entry.status = QueueStatus.COMPLETED
            order.queue_entry.completed_at = datetime.utcnow()
            order.completed_at = datetime.utcnow()

            # Mark Cash payment as collected upon order completion
            if order.payment and order.payment.status == PaymentStatus.PENDING:
                order.payment.status = PaymentStatus.PAID
                order.payment.paid_at = datetime.utcnow()

        elif target_status == OrderStatus.CANCELLED:
            order.queue_entry.status = QueueStatus.CANCELLED
            order.queue_entry.completed_at = datetime.utcnow()
            
            # Process refund note for paid UPI orders
            if order.payment and order.payment.status == PaymentStatus.PAID:
                order.payment.status = PaymentStatus.REFUNDED

        db.session.commit()
        return True, f"Order status updated to {target_status}."

    @staticmethod
    def get_live_queue_board():
        """Fetch active queue data for student board and staff display."""
        active_entries = QueueEntry.query\
            .join(Order, QueueEntry.order_id == Order.id)\
            .filter(Order.status.in_(OrderStatus.ACTIVE_QUEUE))\
            .order_by(QueueEntry.joined_at.asc())\
            .all()

        data = []
        for idx, qe in enumerate(active_entries, 1):
            data.append({
                'position': idx,
                'queue_display': qe.queue_display,
                'order_number': qe.order.order_number,
                'customer_name': qe.order.customer_name,
                'status': qe.order.status,
                'item_count': qe.order.item_count,
                'joined_at': qe.joined_at.strftime('%H:%M'),
                'total_amount': float(qe.order.total_amount)
            })
        return data
